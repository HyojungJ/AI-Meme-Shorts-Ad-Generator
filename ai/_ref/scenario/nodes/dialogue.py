from langchain_core.messages import AIMessage
from backend.scenario.state import ScenarioState
from backend.scenario.config import config
from backend.scenario.generators import DialogueGenerator

_dialogue_generator = None
_current_model = None


def get_dialogue_generator():
    global _dialogue_generator, _current_model
    model = config.dialogue_model

    if _dialogue_generator is not None and _current_model != model:
        _dialogue_generator.unload()
        _dialogue_generator = None

    if _dialogue_generator is None:
        _dialogue_generator = DialogueGenerator()  # config에서 자동으로 모델 로드
        _current_model = model

    return _dialogue_generator


def dialogue_node(state: ScenarioState) -> ScenarioState:
    skeleton = state.get("skeleton")
    characters = state["characters"]
    meme_data = state["meme_data"]

    if not skeleton:
        error_msg = "[dialogue] skeleton 데이터 없음"
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": state.get("errors", []) + [error_msg],
            "phase": "done",
        }

    try:
        generator = get_dialogue_generator()
        dialogues = generator.generate_all(skeleton, characters, meme_data)

        # 대사 개수 요약
        dialogue_summary = ", ".join([f"{k}: {len(v)}개" for k, v in dialogues.items()])
        model_name = generator.model_name

        return {
            "messages": [AIMessage(content=f"[dialogue] 대사 생성 완료 ({model_name}): {dialogue_summary}")],
            "phase": "finalizer",
            "dialogues": dialogues,
        }

    except Exception as e:
        error_msg = f"[dialogue] 대사 생성 실패: {str(e)}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": state.get("errors", []) + [error_msg],
            "phase": "done",
        }


def unload_dialogue_model():
    global _dialogue_generator, _current_model
    if _dialogue_generator is not None:
        _dialogue_generator.unload()
        _dialogue_generator = None
        _current_model = None
