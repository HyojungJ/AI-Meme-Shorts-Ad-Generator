from functools import lru_cache
from langgraph.graph import StateGraph, END

from backend.scenario.state import ScenarioState
from backend.scenario.nodes import skeleton_node, dialogue_node, finalizer_node, evaluate_node, save_node


def should_evaluate(state: ScenarioState) -> str:
    if state.get("do_evaluate"):
        return "evaluate"
    if state.get("save_to_db"):
        return "save"
    return "end"


def should_retry_or_save(state: ScenarioState) -> str:
    score = state.get("quality_score")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if score is None:
        return "save" if state.get("save_to_db") else "end"
    if score < 60 and retry_count < max_retries:
        return "retry"
    return "save" if state.get("save_to_db") else "end"


def create_scenario_graph():
    workflow = StateGraph(ScenarioState)
    workflow.add_node("skeleton", skeleton_node)
    workflow.add_node("dialogue", dialogue_node)
    workflow.add_node("finalizer", finalizer_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("save", save_node)

    workflow.set_entry_point("skeleton")
    workflow.add_edge("skeleton", "dialogue")
    workflow.add_edge("dialogue", "finalizer")

    workflow.add_conditional_edges("finalizer", should_evaluate, {
        "evaluate": "evaluate", "save": "save", "end": END,
    })
    workflow.add_conditional_edges("evaluate", should_retry_or_save, {
        "retry": "skeleton", "save": "save", "end": END,
    })
    workflow.add_edge("save", END)
    return workflow.compile()


@lru_cache(maxsize=1)
def get_scenario_graph():
    return create_scenario_graph()


def reset_scenario_graph():
    get_scenario_graph.cache_clear()
