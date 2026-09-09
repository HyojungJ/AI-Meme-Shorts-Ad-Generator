from langchain_core.messages import AIMessage
from backend.scenario.state import ScenarioState
from backend.scenario.generators import SkeletonGenerator


def skeleton_node(state: ScenarioState) -> ScenarioState:
    meme_data = state["meme_data"]
    characters = state["characters"]
    try:
        generator = SkeletonGenerator()
        skeleton = generator.generate(meme_data, characters)
        return {
            "messages": [AIMessage(content=f"[skeleton] 골격 생성 완료: {skeleton.title}")],
            "phase": "dialogue",
            "skeleton": skeleton.model_dump(),
        }
    except Exception as e:
        return {
            "messages": [AIMessage(content=f"[skeleton] 실패: {e}")],
            "errors": state.get("errors", []) + [str(e)],
            "phase": "done",
        }
