from langchain_core.messages import AIMessage

from backend.scenario.state import ScenarioState
from backend.scenario.schema import ScenarioOutput
from backend.db import ScenarioRepository
from backend.scenario.evaluation import ScenarioEvaluator


def save_node(state: ScenarioState) -> ScenarioState:
    scenario_dict = state.get("scenario")
    prompt_versions = state.get("prompt_versions", {})
    evaluation = state.get("evaluation")

    if not scenario_dict:
        return {
            "messages": [AIMessage(content="[save] scenario 데이터 없음")],
            "errors": state.get("errors", []) + ["scenario 데이터 없음"],
            "phase": "done",
        }

    try:
        scenario = ScenarioOutput(**scenario_dict)
        repo = ScenarioRepository()

        db_format = scenario.to_db_format()
        db_format["prompt_version_ids"] = prompt_versions
        script_id = repo.save_script(db_format)

        if evaluation:
            from backend.scenario.evaluation import EvaluationResult
            eval_result = EvaluationResult(**evaluation)
            evaluator = ScenarioEvaluator()
            evaluator.save_evaluation(script_id, eval_result)

        return {
            "messages": [AIMessage(content=f"[save] DB 저장 완료: script_id={script_id}")],
            "phase": "done",
            "script_id": script_id,
        }

    except Exception as e:
        return {
            "messages": [AIMessage(content=f"[save] DB 저장 실패: {e}")],
            "errors": state.get("errors", []) + [str(e)],
            "phase": "done",
        }
