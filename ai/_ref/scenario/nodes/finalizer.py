from langchain_core.messages import AIMessage
from backend.scenario.state import ScenarioState
from backend.scenario.generators import Finalizer


def finalizer_node(state: ScenarioState) -> ScenarioState:
    skeleton = state.get("skeleton")
    dialogues = state.get("dialogues")
    meme_data = state["meme_data"]
    if not skeleton or not dialogues:
        return {
            "messages": [AIMessage(content="[finalizer] 데이터 없음")],
            "errors": state.get("errors", []) + ["skeleton/dialogues 없음"],
            "phase": "done",
        }
    try:
        finalizer = Finalizer()
        scenario = finalizer.finalize(skeleton, dialogues, meme_data)
        next_phase = "evaluate" if state.get("do_evaluate") else ("save" if state.get("save_to_db") else "done")
        return {
            "messages": [AIMessage(content=f"[finalizer] 완료: {scenario.total_duration}초")],
            "phase": next_phase,
            "scenario": scenario.model_dump(),
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"[finalizer] 실패: {e}")],
            "errors": state.get("errors", []) + [str(e)],
            "phase": "done",
        }
