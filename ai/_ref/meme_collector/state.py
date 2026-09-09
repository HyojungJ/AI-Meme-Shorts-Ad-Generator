from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class AgentV8State(TypedDict):
    messages: Annotated[list, add_messages]
    meme_name: str
    phase: str
    tool_called: bool
    phase_results: dict
    definition: str
    origin: dict
    keywords: list
    crawled_sources: list
    risk_info: dict
    youtube_shorts: list
    selected_video_id: str
    video_analysis: dict
    meme_type: str
    key_phrase: str
    needs_audio: bool
    audio_analysis: dict
    errors: list
    retry_count: int


PHASE_ORDER = [
    "definition", "risk_info", "usage_search", "crawl_examples",
    "youtube_search", "video_analysis", "meme_typing",
    "audio_analysis", "ssml_generation", "finalize",
]


def get_initial_state(meme_name):
    from langchain_core.messages import HumanMessage
    return {
        "messages": [
            HumanMessage(content=f"'{meme_name}' 밈 정보를 수집합니다.")
        ],
        "meme_name": meme_name,
        "phase": "definition",
        "tool_called": False,
        "phase_results": {},
        "definition": "",
        "origin": {},
        "keywords": [],
        "crawled_sources": [],
        "risk_info": {},
        "youtube_shorts": [],
        "selected_video_id": None,
        "video_analysis": {},
        "meme_type": "",
        "key_phrase": None,
        "needs_audio": False,
        "audio_analysis": {},
        "errors": [],
        "retry_count": 0,
    }


def get_next_phase(current_phase, needs_audio=False):
    if current_phase == "finalize":
        return "done"
    if current_phase not in PHASE_ORDER:
        return "definition"

    # meme_typing 이후 조건부 분기
    if current_phase == "meme_typing":
        return "audio_analysis" if needs_audio else "finalize"
    if current_phase == "audio_analysis":
        return "ssml_generation"
    if current_phase == "ssml_generation":
        return "finalize"

    idx = PHASE_ORDER.index(current_phase)
    return PHASE_ORDER[min(idx + 1, len(PHASE_ORDER) - 1)]
