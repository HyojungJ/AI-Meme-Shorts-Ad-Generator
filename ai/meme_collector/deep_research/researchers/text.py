"""TextResearcher: True ReAct Agent for text-based meme research.

Uses create_react_agent from LangGraph for dynamic tool selection and reasoning.
"""
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from common import config, is_valid_korean_definition
from meme_collector.state import MemeState
from meme_collector.tools.namuwiki import search_namuwiki, search_namuwiki_section
from meme_collector.tools.naver_search import search_naver_blog, search_naver_news
from meme_collector.tools.web_search import search_web

TEXT_TOOLS = [search_namuwiki, search_namuwiki_section, search_naver_blog, search_naver_news, search_web]

TEXT_SYSTEM_PROMPT = """당신은 인터넷 밈 연구 전문가입니다.

목표: 밈의 정의, 유래, 핵심 대사, 관련 인물 정보를 수집하세요.

## 핵심 원칙 (매우 중요)
1. **모든 응답은 반드시 한국어로 작성하세요.** 영어 금지!
2. 검색 결과에서 찾은 정보만 사용하세요. 절대 지어내지 마세요.
3. **확실하지 않으면 빈 문자열 ""을 반환하세요.**
4. 잘못된 정보보다 빈 문자열이 낫습니다.

## 필드 규칙

### key_phrase (핵심 대사 추출)
- 밈에서 사람들이 실제로 따라하는 대사/문구만
- 나무위키에서 "원문", "대사", "유행어" 섹션 확인
- 블로그에서 따옴표("")로 인용된 문구 우선
- 이모지, ㅋㅋ, ㅎㅎ, !!, ~ 등 원래 형태 그대로 보존
- 설명문 절대 금지
- 대사 없는 밈(댄스, 이미지)은 빈 문자열

### definition (정의 작성)
- 200자 이상, 5-8문장으로 작성
- 포함 필수: 의미, 유래, 사용 맥락, 유행 이유
- 마크다운(**, ##, -, * 등) 절대 금지 - 순수 텍스트만
- 예: "무야호는 2020년 MBC 예능..."처럼 자연스럽게 서술

### creator (가장 엄격)
- **실제 사람의 본명만** 반환
- 예능/방송: 출연자의 실제 이름
- 노래: 부른 가수의 실제 이름
- 드라마/영화: **배우의 실제 이름** (절대 캐릭터 이름 아님!)
- 나무위키 "유래" 섹션에서 최초 사용자 확인
- **절대 반환하면 안 되는 것**:
  - 영화 감독 (밈을 직접 말한 사람 아님)
  - 캐릭터 이름 (실제 사람 아님)
  - 불확실한 경우
- **모르면 빈 문자열 반환** - 추측 금지

### origin (유래 세부 정보)
- source: 원본 콘텐츠 이름 (예: "놀면 뭐하니?", "그 해 우리는")
- date: YYYY 또는 YYYY-MM 형식 (예: "2020", "2021-12")
- platform: 최초 유행 플랫폼 (예: "유튜브", "트위터", "인스타그램")

## 검색 전략
1. 나무위키 먼저 검색
2. "유래", "출처" 섹션 확인
3. 나무위키에서 못 찾으면 네이버 검색"""


class ResearchNotes(BaseModel):
    definition: str = Field(..., description="밈의 정의 (한국어 2-3문장, 의미/유래/사용맥락 포함, 반드시 한국어로!)")
    origin: str = Field(..., description="밈의 유래 (한국어로, 출처, 시기, 국가/플랫폼)")
    key_phrase: str = Field("", description="핵심 대사/문구만 (설명 금지, 실제 밈 문장만, 예: '무야호~!', '답장 아직이려나💦❓')")
    creator: str = Field("", description="이름만 (문장 금지, 없으면 빈 문자열, 예: '버벌진트', '유야호')")
    risk_info: str = Field("", description="사용 시 주의사항 (한국어로, 민감한 맥락 등)")


def _clean_key_phrase(key_phrase: str, meme_name: str = "") -> str:
    """임의 생성된 문구 필터링. 설명문이나 번역문이면 빈 문자열 반환."""
    if not key_phrase:
        return ""

    key_phrase = key_phrase.strip().strip('"\'')

    # 괄호 안 내용 제거
    for open_p in ["(", "（"]:
        if open_p in key_phrase:
            key_phrase = key_phrase.split(open_p)[0].strip()

    # "!!" 이후 내용 제거 (예: "햄부기!! 귀여워" → "햄부기")
    if "!!" in key_phrase:
        key_phrase = key_phrase.split("!!")[0].strip()

    # "X 또는 Y" 등 패턴 → 첫 번째 값만
    for sep in [" 또는 ", " / ", " - ", "', '"]:
        if sep in key_phrase:
            key_phrase = key_phrase.split(sep)[0].strip().strip('"\'!?')
            break

    # 끝 정리 (!, ?, ~, ' 등)
    key_phrase = key_phrase.rstrip('!"\'?~').strip()

    # ~ 제거 및 공백 정리
    key_phrase = key_phrase.replace("~", "")
    key_phrase = " ".join(key_phrase.split())

    # 첫 번째 문장만 (., ! 로 끝나는 경우)
    for end_char in [". ", "! ", "? "]:
        if end_char in key_phrase:
            key_phrase = key_phrase.split(end_char)[0].strip()

    # 댄스 밈은 key_phrase 없음
    dance_keywords = ["댄스", "dance", "챌린지", "challenge"]
    for kw in dance_keywords:
        if kw.lower() in meme_name.lower():
            return ""

    # 설명문 패턴 → 빈 문자열
    bad_patterns = [
        "사용된다", "표현하는", "의미한다", "나타낸다", "뜻한다",
        "~을", "~를", "~가", "~는", "~에",
        "자주 사용", "많이 사용", "유행하",
        "밈으로", "밈에서", "밈의",
        "변형하여", "부르는", "으로 사용",
        "귀여워", "웃기", "재밌",
        "연기한", "라고 할", "지금부터",
        "비롯", "라고 하면", "짜증",  # 설명 맥락
    ]
    for pattern in bad_patterns:
        if pattern in key_phrase.lower():
            return ""

    # 너무 긴 문구는 설명문
    if len(key_phrase) > 25:
        return ""

    return key_phrase


def _clean_creator(creator: str) -> str:
    """피처링 아티스트 제거 및 메인 아티스트만 추출. 비특정 창작자면 빈 문자열 반환."""
    if not creator:
        return ""

    creator = creator.strip()

    # 쉼표로 구분된 여러 이름 → 첫 번째만 사용 (불확실하면 빈 문자열)
    if "," in creator:
        parts = creator.split(",")
        if len(parts) > 2:
            return ""
        creator = parts[0].strip()

    # 괄호 안 내용 먼저 제거
    for open_paren in ["(", "（", "[", "【"]:
        if open_paren in creator:
            creator = creator.split(open_paren)[0].strip()

    # 문장 형태 → 빈 문자열
    sentence_patterns = [
        "으로", "에서", "이다", "입니다", "유명", "한다", "했다", "된다",
        "에 의해", "보다는", "라기보다", "않고", "이며", "하며",
    ]
    for pattern in sentence_patterns:
        if pattern in creator:
            return ""

    # "국가/지역 + 직업 + 이름" 패턴 → 이름만 추출
    # 예: "인도네시아 스트리머 DEANKT" → "DEANKT"
    job_titles = ["스트리머", "유튜버", "가수", "배우", "래퍼", "아티스트", "크리에이터", "인플루언서"]
    for job in job_titles:
        if job in creator:
            parts = creator.split(job)
            if len(parts) > 1 and parts[1].strip():
                creator = parts[1].strip()
                break

    # 직책/역할 키워드가 포함되면 creator 아님
    role_keywords = ["감독", "연출", "제작", "작가", "PD", "Director", "director"]
    for kw in role_keywords:
        if kw in creator:
            return ""

    # 너무 긴 creator는 문장일 가능성 높음
    if len(creator) > 20:
        return ""

    # 캐릭터명 패턴
    if "캐릭터" in creator or "등장인물" in creator or "character" in creator.lower():
        return ""

    # 비특정 창작자 패턴
    non_creator_keywords = [
        "사용자", "커뮤니티", "인터넷", "네티즌", "SNS", "온라인",
        "불특정", "익명", "다수", "여러", "없음", "미상", "미정", "알 수 없",
        "제작진", "제작팀", "배우들", "출연자들", "스태프",
        "참가자", "참여자", "작성자", "게시물", "특정 개인",
        "정보는", "제공되", "확인되",  # 불확실 표현
        "플랫폼", "채널", "방송사", "회사",  # 조직/플랫폼
    ]
    for keyword in non_creator_keywords:
        if keyword in creator:
            return ""

    # "X 역을 맡은 Y" 패턴 → Y만 추출
    if "역을 맡은" in creator:
        parts = creator.split("역을 맡은")
        if len(parts) > 1:
            creator = parts[1].strip()

    # feat. 패턴
    feat_pattern = r"^(.+?)\s*[\(\[]?\s*[Ff]eat\.?\s*.+[\)\]]?$"
    match = re.match(feat_pattern, creator)
    if match:
        return match.group(1).strip()

    return creator


def _clean_definition(definition: str) -> str:
    """영어 definition이면 빈 문자열 반환. 한국어면 그대로 반환."""
    if not definition:
        return ""

    # common/utils.py의 is_valid_korean_definition 사용
    is_valid, _ = is_valid_korean_definition(definition, min_length=30)
    return definition if is_valid else ""


def _extract_sources_with_urls(messages) -> list[dict]:
    """메시지에서 URL 포함 소스 정보 추출"""
    url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\])>]+'
    sources = {}  # name -> url (첫 번째 URL만 저장)

    for msg in messages:
        content = str(msg.content) if hasattr(msg, "content") else str(msg)
        urls = re.findall(url_pattern, content)

        for url in urls:
            url = url.rstrip(".,;:)")  # 끝에 붙은 구두점 제거
            if "namu.wiki" in url:
                name = "나무위키"
            elif "blog.naver" in url:
                name = "네이버 블로그"
            elif "news.naver" in url:
                name = "네이버 뉴스"
            elif "youtube.com" in url or "youtu.be" in url:
                continue  # YouTube는 reference_videos에서 처리
            else:
                name = "웹 검색"

            if name not in sources:
                sources[name] = url

    return [{"name": name, "url": url} for name, url in sources.items()]


def run_text_researcher(state: MemeState) -> dict:
    """TextResearcher: True ReAct Agent로 텍스트 기반 밈 정보 수집"""
    meme_name = state["meme_name"]
    meme_link = state.get("meme_link")

    context = f"밈 이름: {meme_name}"
    if meme_link:
        context += f"\n나무위키 링크: {meme_link}"

    agent = create_react_agent(
        model=ChatOpenAI(model=config.models.analyzer),  # gpt-4o for better accuracy
        tools=TEXT_TOOLS,
        prompt=SystemMessage(content=TEXT_SYSTEM_PROMPT),
        response_format=ResearchNotes,
    )

    result = agent.invoke({
        "messages": [HumanMessage(content=context)]
    })

    notes: ResearchNotes = result["structured_response"]

    # 사용된 소스 추출 (URL 포함)
    sources = _extract_sources_with_urls(result["messages"])

    cleaned_creator = _clean_creator(notes.creator)
    cleaned_key_phrase = _clean_key_phrase(notes.key_phrase, meme_name)
    cleaned_definition = _clean_definition(notes.definition)

    notes_text = f"""## 정의
{notes.definition}

## 유래
{notes.origin}

## 핵심 대사
{cleaned_key_phrase or '(없음)'}

## 인물
{cleaned_creator or '(미상)'}

## 주의사항
{notes.risk_info or '(없음)'}

## 출처
{', '.join(s['name'] for s in sources) if sources else '(미상)'}"""

    return {
        "research_notes": {"text": notes_text},
        "researcher_status": {"text": "done"},
        "collected_info": {
            "sources": sources,
            "_text_researcher": {
                "definition": cleaned_definition,  # 영어면 빈 문자열
                "origin": notes.origin,
                "key_phrase": cleaned_key_phrase,
                "creator": cleaned_creator,
                "risk_info": notes.risk_info,
            },
        },
    }
