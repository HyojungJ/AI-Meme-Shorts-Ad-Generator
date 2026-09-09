from typing import Literal, TypedDict


class VoiceState(TypedDict, total=False):
    script_id: int
    scene_number: int
    scene_key: str
    character_id: int
    design_text: str
    ttv_model_id: str
    text: str
    voice_id: str
    voice_name: str
    voice_description: str
    preview_index: int
    user_id: str
    settings: dict
    clone_prompt_url: str  # S3 URL of safetensors clone prompt

    # 검증 관련 필드
    verification_result: dict
    modification_request: str
    original_audio_url: str
    retry_count: int

    status: Literal["ok", "failed"]
    error: str

    audio_url: str
    storage_path: str
    duration_seconds: float
    size_bytes: int
    created_at: str
    text_hash: str

    scenario: dict  # 시나리오 데이터
    total_duration: float  # 시나리오의 총 길이 (초)
    bgm_asset_id: int  # DB 저장 후 반환되는 asset_id

DEFAULT_DESIGN_TEXT = (
    "안녕하세요. 이 문장은 보이스 디자인과 음성 합성을 테스트하기 위한 긴 문장입니다. "
    "백 자 이상을 채우기 위해 내용을 조금 더 길게 작성하고 있습니다. "
    "테스트가 정상적으로 완료되길 바랍니다."
)


def get_initial_state(
    *,
    text: str,
    script_id: int | None = None,
    scene_number: int | None = None,
    scene_key: str | None = None,
    character_id: int | None = None,
    voice_id: str | None = None,
    voice_name: str | None = None,
    voice_description: str | None = None,
    clone_prompt_url: str | None = None,
    preview_index: int | None = None,
    user_id: str | None = None,
    settings: dict | None = None,
    design_text: str | None = None,
) -> VoiceState:
    state: VoiceState = {
        "text": text,
    }
    if script_id is not None:
        state["script_id"] = script_id
    if scene_number is not None:
        state["scene_number"] = scene_number
    if scene_key:
        state["scene_key"] = scene_key
    if character_id is not None:
        state["character_id"] = character_id
    # 선택적 필드 설정
    if voice_id:
        state["voice_id"] = voice_id
    if voice_name:
        state["voice_name"] = voice_name
    if voice_description:
        state["voice_description"] = voice_description
    if clone_prompt_url:
        state["clone_prompt_url"] = clone_prompt_url
    if preview_index is not None:
        state["preview_index"] = preview_index
    if user_id:
        state["user_id"] = user_id
    if settings:
        state["settings"] = settings
    if design_text:
        state["design_text"] = design_text
    elif voice_description:
        state["design_text"] = DEFAULT_DESIGN_TEXT
    return state
