"""Finalize Node: 최종 결과 조합 및 DB 저장"""
import logging
import re

from common.db import save_meme_output
from meme_collector.schema import (
    MemeOutput,
    OriginInfo,
    Prosody,
    ReferenceVideo,
    SourceInfo,
    UsageExample,
)
from meme_collector.state import MemeState

log = logging.getLogger(__name__)

_DEFAULT_MOTION_PROMPT = "A person performs an action"


def _clean_definition(text: str) -> str:
    """마크다운 문법 제거 (규칙 기반)"""
    if not text:
        return ""
    # 볼드/이탤릭
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    # 헤더
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 불릿
    text = re.sub(r'^[\-\*\+]\s+', '', text, flags=re.MULTILINE)
    # 링크
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 연속 줄바꿈
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _filter_valid_examples(examples: list[dict]) -> list[dict]:
    """source_url이 있는 예시만 필터링 (LLM 생성 방지)"""
    return [ex for ex in examples if ex.get("source_url")]


def _validate_output(output: MemeOutput) -> list[str]:
    """Validate output quality, return list of warnings."""
    warnings = []
    if output.meme_type in ("quotable", "hybrid") and not output.key_phrase:
        warnings.append("quotable/hybrid 밈에 key_phrase 없음")
    if not output.usage_examples:
        warnings.append("usage_examples가 비어있음")
    if output.motion_prompt == _DEFAULT_MOTION_PROMPT:
        warnings.append("motion_prompt가 기본값임")
    return warnings


def finalize_node(state: MemeState) -> dict:
    """최종 결과 조합 및 DB 저장"""
    analysis = state.get("analysis", {})
    collected_info = state.get("collected_info", {})

    # Origin info
    origin = None
    if analysis.get("origin"):
        o = analysis["origin"]
        origin = OriginInfo(
            source=o.get("source"),
            creator=o.get("creator"),
            date=o.get("date"),
            platform=o.get("platform"),
        )

    # Reference videos from YouTube
    youtube_videos = collected_info.get("youtube_videos", [])
    reference_videos = [
        ReferenceVideo(
            video_id=v.get("video_id", ""),
            url=v.get("url", ""),
            title=v.get("title", ""),
            view_count=v.get("view_count", 0),
        )
        for v in youtube_videos[:5]
    ]

    # Usage examples: collected_info만 사용 (source_url 필수 - LLM 생성 방지)
    # analyzer의 usage_examples는 무시 (LLM이 만들어낸 것일 수 있음)
    collected_examples = collected_info.get("usage_examples", [])
    valid_examples = _filter_valid_examples(collected_examples)

    usage_examples = [
        UsageExample(
            context=ex.get("context", ""),
            usage=ex.get("usage", ""),
            tone=ex.get("tone", "playful"),
            example_type=ex.get("example_type", "good"),
            note=ex.get("note"),
            source_url=ex.get("source_url"),
        )
        for ex in valid_examples
    ]

    # Definition 우선순위:
    # 1. _text_researcher.definition (소스에서 직접 추출 - 가장 신뢰)
    # 2. analysis.definition (LLM 생성 - 폴백)
    # 3. summary (레거시 폴백)
    text_research = collected_info.get("_text_researcher", {})
    raw_definition = (
        text_research.get("definition")
        or analysis.get("definition")
        or collected_info.get("summary", "")[:500]
        or "정의 없음"
    )
    definition = _clean_definition(raw_definition)

    # Prosody from analysis
    prosody = None
    if analysis.get("prosody"):
        p = analysis["prosody"]
        prosody = Prosody(
            pitch=p.get("pitch", "medium"),
            speed=p.get("speed", "medium"),
            emotion=p.get("emotion", analysis.get("emotion", "neutral")),
            ssml=p.get("ssml"),
        )

    # Sources with URLs
    sources_raw = collected_info.get("sources", [])
    sources = [
        SourceInfo(name=s.get("name", ""), url=s.get("url"))
        for s in sources_raw
        if isinstance(s, dict)
    ]

    output = MemeOutput(
        name=state["meme_name"],
        definition=definition,
        meme_type=analysis.get("meme_type", "quotable"),
        key_phrase=analysis.get("key_phrase"),
        emotion=analysis.get("emotion"),
        prosody=prosody,
        motion_prompt=analysis.get("motion_prompt", _DEFAULT_MOTION_PROMPT),
        style_keywords=analysis.get("style_keywords", []),
        usage_examples=usage_examples,
        reference_videos=reference_videos,
        sources=sources,
        origin=origin,
        risk_level=analysis.get("risk_level", "low"),
        confidence=analysis.get("confidence", 0.0),
    )

    warnings = _validate_output(output)
    if warnings:
        log.warning(f"MemeOutput validation warnings for '{state['meme_name']}': {warnings}")

    output_dict = output.model_dump()
    meme_id = save_meme_output(output_dict)

    # situation 임베딩 (DB 저장 성공 후 독립 실행)
    try:
        from meme_collector.embed_situations import embed_by_meme_id
        embed_by_meme_id(meme_id)
    except Exception as e:
        log.warning(f"situation 임베딩 실패 (meme_id={meme_id}): {e}")

    return {"meme_output": output_dict, "meme_id": meme_id}
