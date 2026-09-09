from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class ScenarioState(TypedDict):
    messages: Annotated[list, add_messages]
    phase: str
    meme_id: int
    meme_data: dict
    characters: list
    prompt_versions: dict
    skeleton: dict
    dialogues: dict
    scenario: dict
    quality_score: float
    evaluation: dict
    script_id: int
    save_to_db: bool
    do_evaluate: bool
    retry_count: int
    max_retries: int
    errors: list


def get_initial_state(meme_id, meme_data, characters, prompt_versions, save_to_db=False, do_evaluate=False):
    from langchain_core.messages import HumanMessage
    return {
        "messages": [
            HumanMessage(content=f"밈 '{meme_data.get('meme_name', '')}' 시나리오 생성을 시작합니다.")
        ],
        "phase": "skeleton",
        "meme_id": meme_id,
        "meme_data": meme_data,
        "characters": characters,
        "prompt_versions": prompt_versions,
        "skeleton": None,
        "dialogues": None,
        "scenario": None,
        "quality_score": None,
        "evaluation": None,
        "script_id": None,
        "save_to_db": save_to_db,
        "do_evaluate": do_evaluate,
        "retry_count": 0,
        "max_retries": 2,
        "errors": [],
    }
