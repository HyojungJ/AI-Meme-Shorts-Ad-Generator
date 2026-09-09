from functools import lru_cache
from langgraph.graph import StateGraph, END

from backend.video.state import VideoState
from backend.video.nodes import (
    prepare_node,
    tts_node,
    sora_node,
    compose_node,
    finalize_node,
)


def should_continue(state: VideoState) -> str:
    if state.get("status") == "failed":
        return "end"

    phase = state.get("phase", "done")
    if phase == "done":
        return "end"

    return phase


def after_prepare(state: VideoState) -> str:
    if state.get("status") == "failed":
        return "end"

    if state.get("use_sora_audio", False):
        return "sora"

    return "tts"


def create_video_graph():
    workflow = StateGraph(VideoState)

    workflow.add_node("prepare", prepare_node)
    workflow.add_node("tts", tts_node)
    workflow.add_node("sora", sora_node)
    workflow.add_node("compose", compose_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("prepare")

    workflow.add_conditional_edges("prepare", after_prepare, {
        "tts": "tts",
        "sora": "sora",
        "end": END,
    })

    workflow.add_conditional_edges("tts", should_continue, {
        "sora": "sora",
        "end": END,
    })

    workflow.add_conditional_edges("sora", should_continue, {
        "compose": "compose",
        "end": END,
    })

    workflow.add_conditional_edges("compose", should_continue, {
        "finalize": "finalize",
        "end": END,
    })

    workflow.add_edge("finalize", END)

    return workflow.compile()


@lru_cache(maxsize=1)
def get_video_graph():
    return create_video_graph()


def reset_video_graph():
    get_video_graph.cache_clear()
