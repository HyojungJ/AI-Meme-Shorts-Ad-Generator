import logging
from typing import Literal

from langgraph.types import Command

from common import config, get_openai, is_valid_korean_definition
from meme_collector.schema import AnalyzerOutput
from meme_collector.state import MemeState
from meme_collector.tools.video_analyzer import extract_usage_from_videos
from meme_collector.workers.context_builder import ContextBuilder
from meme_collector.prompts.analyzer_prompts import (
    ANALYZER_PROMPT_V1,
    ANALYZER_PROMPT_V2
)
log = logging.getLogger(__name__)

_context_builder = ContextBuilder()


def run_analyzer(state: MemeState) -> Command[Literal["verifier"]]:
    meme_name = state["meme_name"]
    collected_info = state.get("collected_info", {})
    reflections = state.get("reflections", [])

    # 영상에서 추가 usage_examples 추출
    collected_info = _enrich_usage_examples(collected_info, meme_name)

    # ContextBuilder로 컨텍스트 생성 (research_notes 또는 collected_info 기반)
    context = _context_builder.build(state)

    reflection_note = ""
    if reflections:
        reflection_history = "\n".join(reflections)
        reflection_note = f"\n\n## PREVIOUS FEEDBACK HISTORY (FIX THESE ISSUES)\n{reflection_history}"

    client = get_openai()

    response = client.beta.chat.completions.parse(
        model=config.models.analyzer,
        messages=[
            {"role": "system", "content": ANALYZER_PROMPT_V2},
            {
                "role": "user",
                "content": f"""## Meme Name: {meme_name}

## Collected Information
{context}{reflection_note}

Analyze this meme and generate VIDEO PRODUCTION outputs.
Pay special attention to extracting the exact key_phrase and creating a detailed motion_prompt.""",
            },
        ],
        response_format=AnalyzerOutput,
    )

    output = response.choices[0].message.parsed

    # Analyzer 출력 후처리: 영어 definition 필터링
    analysis = output.model_dump() if output else {}
    if analysis.get("definition"):
        is_valid, _ = is_valid_korean_definition(analysis["definition"], min_length=30)
        if not is_valid:
            log.warning("Analyzer가 영어 definition 생성 - 빈 문자열로 교체")
            analysis["definition"] = ""

    return Command(
        goto="verifier",
        update={
            "analysis": analysis,
            "collected_info": collected_info,  # enriched usage_examples 반영
        },
    )


def _enrich_usage_examples(collected_info: dict, meme_name: str) -> dict:
    """영상에서 추가 usage_examples를 추출해서 기존 것과 병합합니다."""
    youtube_videos = collected_info.get("youtube_videos", [])
    if not youtube_videos:
        return collected_info

    # 기존 usage_examples
    existing_examples = collected_info.get("usage_examples", [])

    # 영상에서 추출 (최대 3개 영상)
    log.info(f"영상에서 usage_examples 추출 중... ({len(youtube_videos[:3])}개 영상)")
    video_examples = extract_usage_from_videos(youtube_videos, meme_name, max_videos=3)

    if video_examples:
        log.info(f"영상에서 {len(video_examples)}개 usage_examples 추출 완료")
        # 병합 (영상 기반 예시를 뒤에 추가)
        collected_info["usage_examples"] = existing_examples + video_examples

    return collected_info
