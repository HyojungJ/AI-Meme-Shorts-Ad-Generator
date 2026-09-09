import logging
from typing import Literal

from ddgs import DDGS
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from common import config, get_openai
from meme_collector.prompts.usage_extract_prompts import (
    USAGE_EXTRACT_PROMPT_V1,
    USAGE_EXTRACT_PROMPT_V2
)
log = logging.getLogger(__name__)


class UsageExampleItem(BaseModel):
    context: str = Field(..., description="상황/맥락 (예: 친구가 황당한 말 할 때)")
    usage: str = Field(..., description="사용 방법 (예: '어쩔티비~' 하고 무시한다)")
    tone: Literal["playful", "sarcastic", "aggressive", "friendly", "neutral"] = "playful"
    example_type: Literal["good", "bad"] = Field(
        "good", description="적절한 활용(good) vs 부적절한 활용(bad)"
    )
    source_url: str | None = Field(None, description="출처 URL (검색 결과에서 추출)")


class UsageExamplesResponse(BaseModel):
    examples: list[UsageExampleItem] = Field(default_factory=list)


def _search_web(query: str, max_results: int = 10) -> list[dict]:
    """DuckDuckGo 웹 검색 (다양한 소스: 커뮤니티, SNS, 블로그, 뉴스 등)"""
    try:
        ddgs = DDGS()
        return list(ddgs.text(query, region="kr-kr", max_results=max_results))
    except Exception as e:
        log.warning(f"Web search failed for '{query}': {e}")
        return []


RELEVANCE_CHECK_PROMPT = """다음 활용 예시가 "{meme_name}" 밈에 대한 것인지 판단하세요.

## 밈 정보
- 이름: {meme_name}
- 정의: {definition}
- 출처: {source}

## 활용 예시
- 상황: {context}
- 사용: {usage}
- URL: {url}

## 판단 기준
- 이 예시가 위 밈의 실제 활용 사례인가요?
- 단순히 "{meme_name}"이라는 단어가 포함된 것이 아니라, 밈 자체를 활용한 것인가요?

relevant: true/false로만 답변하세요."""


class RelevanceResponse(BaseModel):
    relevant: bool


def _check_relevance(
    example: dict,
    meme_name: str,
    definition: str,
    source: str,
) -> bool:
    """LLM으로 활용 예시의 관련성 검증"""
    client = get_openai()

    prompt = RELEVANCE_CHECK_PROMPT.format(
        meme_name=meme_name,
        definition=definition or "정의 없음",
        source=source or "출처 미상",
        context=example.get("context", ""),
        usage=example.get("usage", ""),
        url=example.get("source_url", ""),
    )

    response = client.beta.chat.completions.parse(
        model=config.models.fast,
        messages=[{"role": "user", "content": prompt}],
        response_format=RelevanceResponse,
    )

    result = response.choices[0].message.parsed
    return result.relevant if result else False


def _contains_meme_reference(usage: str, meme_name: str) -> bool:
    """usage에 밈 관련 키워드가 포함되어 있는지 확인 (변형 패턴 포함)"""
    usage_lower = usage.lower()
    meme_lower = meme_name.lower()

    # 밈 이름 전체 포함
    if meme_lower in usage_lower:
        return True

    # 밈 이름의 핵심 단어 포함 (2글자 이상)
    keywords = [w for w in meme_name.split() if len(w) >= 2]
    if any(kw.lower() in usage_lower for kw in keywords):
        return True

    # 변형 패턴 체크 (밈별 공통 패턴)
    variation_patterns = [
        "탓일까",  # "~탓일까" 패턴 (골반통신)
        "안 멈",   # "안 멈추는데", "안 멈춰"
        "멈추지 않",  # "멈추지 않아"
        "많이 된다",  # 운동 많이 된다
        "어쩔",  # 어쩔티비
        "무야호",
        "패러디",
        "밈을 활용",
        "밈 활용",
        "챌린지",
    ]
    return any(p in usage_lower for p in variation_patterns)


def _extract_with_openai(
    meme_name: str,
    blog_contents: str,
    context: dict | None = None,
) -> list[dict]:
    client = get_openai()

    try:
        response = client.beta.chat.completions.parse(
            model=config.models.default,
            messages=[
                {"role": "system", "content": USAGE_EXTRACT_PROMPT_V2},
                {"role": "user", "content": f"밈 이름: {meme_name}\n\n블로그 내용:\n{blog_contents}"},
            ],
            response_format=UsageExamplesResponse,
        )

        result = response.choices[0].message.parsed
        if not result:
            log.warning(f"OpenAI returned empty result for meme: {meme_name}")
            return []

        # 1. 문자열 필터
        candidates = [
            ex.model_dump()
            for ex in result.examples
            if _contains_meme_reference(ex.usage, meme_name)
        ]

        # 2. LLM 관련성 검증 (context가 있을 때만)
        if not context:
            return candidates

        definition = context.get("definition", "")
        source = context.get("origin", {}).get("source", "")

        verified = []
        for ex in candidates:
            if _check_relevance(ex, meme_name, definition, source):
                verified.append(ex)

        return verified
    except Exception as e:
        log.warning(f"Usage extraction failed for {meme_name}: {e}")
        return []


def _build_search_queries(meme_name: str, context: dict | None = None) -> list[str]:
    """밈 컨텍스트를 활용해 검색 쿼리 생성"""
    queries = []

    # 기본 쿼리 (밈 키워드 포함)
    queries.append(f'"{meme_name}" 밈 활용 사례')
    queries.append(f'"{meme_name}" 밈 패러디')

    if context:
        # origin.source가 있으면 함께 검색 (예: "얼음" "오징어게임")
        source = context.get("origin", {}).get("source", "")
        if source and source != meme_name:
            queries.append(f'"{meme_name}" "{source}" 밈')

        # origin.platform이 있으면 플랫폼 포함
        platform = context.get("origin", {}).get("platform", "")
        if platform:
            queries.append(f'"{meme_name}" {platform} 밈')

    # 일반 활용 쿼리
    queries.append(f'"{meme_name}" 마케팅 밈')
    queries.append(f'"{meme_name}" 브랜드 밈 협업')

    return queries[:6]


@tool
def extract_usage_examples(meme_name: str, context: dict | None = None) -> list[dict]:
    """웹에서 밈 활용 예시를 추출합니다. 커뮤니티, SNS, 블로그, 뉴스 등 다양한 소스에서 수집합니다."""
    queries = _build_search_queries(meme_name, context)
    all_contents = []

    for query in queries:
        results = _search_web(query, max_results=7)
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            all_contents.append(f"--- 출처: {href} ---\n{title}\n{body}")

    if not all_contents:
        return []

    content_text = "\n\n".join(all_contents[:25])
    return _extract_with_openai(meme_name, content_text, context)
