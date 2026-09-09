from langgraph.graph import END, StateGraph

from common.db import save_meme_output
from meme_collector.schema import (
    MemeOutput,
    OriginInfo,
    ReferenceVideo,
    UsageExample,
)
from meme_collector.state import MemeState
from meme_collector.workers.analyzer import run_analyzer
from meme_collector.workers.collector import run_collector
from meme_collector.workers.verifier import run_verifier


def finalize_node(state: MemeState) -> dict:
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

    # Usage examples: collected_info 우선 (source_url 보존), analyzer는 보조
    collected_examples = collected_info.get("usage_examples", [])
    analyzer_examples = analysis.get("usage_examples", [])

    # collected_info에 예시가 있으면 우선 사용 (source_url 있음)
    if collected_examples:
        usage_examples_raw = collected_examples
    else:
        usage_examples_raw = analyzer_examples

    usage_examples = [
        UsageExample(
            context=ex.get("context", ""),
            usage=ex.get("usage", ""),
            tone=ex.get("tone", "playful"),
            example_type=ex.get("example_type", "good"),
            note=ex.get("note"),
            source_url=ex.get("source_url"),
        )
        for ex in usage_examples_raw
    ]

    # Use analyzer's definition (clean) instead of collector's summary
    definition = analysis.get("definition") or collected_info.get("summary", "")[:500] or "정의 없음"

    output = MemeOutput(
        name=state["meme_name"],
        definition=definition,
        meme_type=analysis.get("meme_type", "quotable"),
        key_phrase=analysis.get("key_phrase"),
        emotion=analysis.get("emotion"),
        motion_prompt=analysis.get("motion_prompt", "A person performs an action"),
        style_keywords=analysis.get("style_keywords", []),
        usage_examples=usage_examples,
        reference_videos=reference_videos,
        sources=collected_info.get("sources", []),
        origin=origin,
        risk_level=analysis.get("risk_level", "low"),
        confidence=analysis.get("confidence", 0.0),
    )

    output_dict = output.model_dump()

    # Save to DB
    meme_id = save_meme_output(output_dict)

    return {"meme_output": output_dict, "meme_id": meme_id}


def compile_graph(checkpointer=None):
    graph = StateGraph(MemeState)

    graph.add_node("collector", run_collector)
    graph.add_node("analyzer", run_analyzer)
    graph.add_node("verifier", run_verifier)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("collector")
    # Command API handles all routing (collector→analyzer→verifier→finalize/analyzer/END)
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer) if checkpointer else graph.compile()
