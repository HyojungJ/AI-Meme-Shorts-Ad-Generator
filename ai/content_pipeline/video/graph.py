from functools import lru_cache

from langgraph.graph import END, StateGraph

from content_pipeline.video.nodes import generate_video_node, merge_video_node, verify_video_node
from content_pipeline.video.state import VideoState


def _route_after_verify(state: VideoState) -> str:
    """검증 결과에 따라 재생성 또는 종료"""
    verification = state.get("verification_result", {})
    decision = verification.get("decision", "present_to_user")
    
    if decision == "auto_retry":
        return "generate"  # 재생성
    return END  # 사용자에게 제시


def create_video_graph():
    graph = StateGraph(VideoState)

    graph.add_node("generate", generate_video_node)
    graph.add_node("merge", merge_video_node)
    graph.add_node("verify", verify_video_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "merge")
    graph.add_edge("merge", "verify")
    graph.add_conditional_edges(
        "verify",
        _route_after_verify,
        {"generate": "generate", END: END},
    )

    return graph.compile()


@lru_cache(maxsize=1)
def get_video_graph():
    return create_video_graph()


def reset_video_graph():
    get_video_graph.cache_clear()
