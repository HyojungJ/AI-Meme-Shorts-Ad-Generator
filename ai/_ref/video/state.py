from typing import TypedDict, List, Dict, Any, Annotated

from langgraph.graph.message import add_messages

from backend.video.config import config


class VideoState(TypedDict):
    messages: Annotated[list, add_messages]
    phase: str
    script_id: int
    script: dict
    scene_clips: List[Dict[str, Any]]
    tts_results: Dict[int, Dict[str, Any]]
    sora_results: Dict[int, Dict[str, Any]]
    composed_clips: List[str]
    gen_id: int
    final_video_path: str
    total_duration: float
    total_cost: float
    sora_model: str
    tts_model: str
    output_dir: str
    use_sora_audio: bool
    status: str
    errors: List[str]


PHASE_ORDER = ["prepare", "tts", "sora", "compose", "finalize", "done"]


def get_initial_state(
    script_id: int,
    sora_model: str = None,
    tts_model: str = None,
    output_dir: str = None,
    use_sora_audio: bool = False
) -> VideoState:
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=f"영상 생성 시작: script_id={script_id}")],
        "phase": "prepare",
        "script_id": script_id,
        "script": None,
        "scene_clips": [],
        "tts_results": {},
        "sora_results": {},
        "composed_clips": [],
        "gen_id": None,
        "final_video_path": None,
        "total_duration": 0.0,
        "total_cost": 0.0,
        "sora_model": sora_model or config.sora_model,
        "tts_model": tts_model or config.tts_model,
        "output_dir": output_dir or config.output_dir,
        "use_sora_audio": use_sora_audio,
        "status": "pending",
        "errors": [],
    }
