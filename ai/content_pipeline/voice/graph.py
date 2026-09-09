from functools import lru_cache

from langgraph.graph import END, StateGraph

from content_pipeline.voice.nodes import design_voice_node, generate_voice_node
from content_pipeline.voice.state import VoiceState


def _route(state: VoiceState) -> str:
    return "generate" if state.get("voice_id") else "design"


def _after_design(state: VoiceState) -> str:
    return "end" if state.get("status") == "failed" else "generate"


def create_voice_graph():
    graph = StateGraph(VoiceState)

    graph.add_node("route", lambda _: {})
    graph.add_node("design", design_voice_node)
    graph.add_node("generate", generate_voice_node)

    graph.set_entry_point("route")
    graph.add_conditional_edges("route", _route, {"design": "design", "generate": "generate"})
    graph.add_conditional_edges("design", _after_design, {"generate": "generate", "end": END})
    graph.add_edge("generate", END)

    return graph.compile()


def get_voice_graph():
    return create_voice_graph()


def reset_voice_graph():
    get_voice_graph.cache_clear()
