from functools import lru_cache

from langgraph.graph import END, StateGraph

from content_pipeline.image.nodes import generate_character_image_node, generate_scene_image_node
from content_pipeline.image.state import ImageState


def _route_after_character(state: ImageState) -> str:
    if state.get("status") == "failed":
        return END
    return "generate_scene"


def create_image_graph():
    graph = StateGraph(ImageState)
    graph.add_node("generate_character", generate_character_image_node)
    graph.add_node("generate_scene", generate_scene_image_node)
    graph.set_entry_point("generate_character")
    graph.add_conditional_edges(
        "generate_character",
        _route_after_character,
        {"generate_scene": "generate_scene", END: END},
    )
    graph.add_edge("generate_scene", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_image_graph():
    return create_image_graph()


def reset_image_graph():
    get_image_graph.cache_clear()
