from dataclasses import asdict

from langchain_core.messages import AIMessage

from backend.scenario.state import ScenarioState
from backend.scenario.schema import ScenarioOutput
from backend.scenario.evaluation import ScenarioEvaluator


def evaluate_node(state: ScenarioState) -> ScenarioState:
    scenario_dict = state.get("scenario")
    meme_data = state["meme_data"]
    save_to_db = state.get("save_to_db", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if not scenario_dict:
        return {
            "messages": [AIMessage(content="[evaluate] scenario 데이터 없음")],
            "errors": state.get("errors", []) + ["scenario 데이터 없음"],
            "phase": "done",
        }

    try:
        scenario = ScenarioOutput(**scenario_dict)
        evaluator = ScenarioEvaluator()
        eval_result = evaluator.evaluate(scenario, meme_data)
        score = eval_result.total_score

        if score < 60 and retry_count < max_retries:
            next_phase = "skeleton"
            retry_msg = f" → retry ({retry_count + 1}/{max_retries})"
        elif save_to_db:
            next_phase = "save"
            retry_msg = ""
        else:
            next_phase = "done"
            retry_msg = ""

        return {
            "messages": [AIMessage(content=f"[evaluate] 품질 점수: {score}/100{retry_msg}")],
            "phase": next_phase,
            "quality_score": score,
            "evaluation": asdict(eval_result),
            "retry_count": retry_count + 1 if next_phase == "skeleton" else retry_count,
        }

    except Exception as e:
        next_phase = "save" if save_to_db else "done"
        return {
            "messages": [AIMessage(content=f"[evaluate] 평가 실패: {e}")],
            "errors": state.get("errors", []) + [str(e)],
            "phase": next_phase,
        }
