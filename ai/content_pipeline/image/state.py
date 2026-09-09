from typing import Literal, TypedDict


class ImageState(TypedDict, total=False):
    script_id: int
    scene_number: int
    scene_key: str
    character_id: int
    character_prompt: str
    scenario_prompt: str
    prompt: str
    character_image_path: str
    character_image_url: str
    character_output_path: str
    character_metadata_path: str
    character_metadata_json: dict
    character_storage_path: str
    character_storage_backend: str
    
    product_image_path: str
    product_image_url: str
    aspect_ratio: str
    output_path: str
    scene_output_path: str
    output_dir: str
    model: str

    # 검증 관련 필드
    verification_result: dict
    modification_request: str
    original_image_url: str
    retry_count: int

    status: Literal["ok", "failed"]
    error: str

    metadata_path: str
    size_bytes: int
    created_at: str
    image_url: str
    metadata_json: dict
    storage_path: str
    storage_backend: str


def get_initial_state(
    *,
    script_id: int | None = None,
    scene_number: int | None = None,
    scene_key: str | None = None,
    character_id: int | None = None,
    prompt: str | None = None,
    character_prompt: str | None = None,
    scenario_prompt: str | None = None,
    product_image_path: str | None = None,
    product_image_url: str | None = None,
    character_image_path: str | None = None,
    character_image_url: str | None = None,
    aspect_ratio: str = "9:16",
    output_dir: str | None = None,
    output_path: str | None = None,
    character_output_path: str | None = None,
) -> ImageState:
    state: ImageState = {
        "aspect_ratio": aspect_ratio
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
    if prompt:
        state["prompt"] = prompt
    if character_prompt:
        state["character_prompt"] = character_prompt
    if scenario_prompt:
        state["scenario_prompt"] = scenario_prompt
    if product_image_path:
        state["product_image_path"] = product_image_path
    if product_image_url:
        state["product_image_url"] = product_image_url
    if character_image_path:
        state["character_image_path"] = character_image_path
    if character_image_url:
        state["character_image_url"] = character_image_url
    if output_dir:
        state["output_dir"] = output_dir
    if output_path:
        state["output_path"] = output_path
    if character_output_path:
        state["character_output_path"] = character_output_path
    return state
