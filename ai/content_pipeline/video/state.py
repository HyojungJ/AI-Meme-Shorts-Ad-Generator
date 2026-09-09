from typing import Literal, TypedDict

from content_pipeline.schema import ScenarioOutput, VideoOutput


class VideoState(TypedDict, total=False):
    scenario: ScenarioOutput
    ad_id: int
    company_id: int
    account_id: int
    title: str
    description: str
    audio_path: str
    audio_url: str
    scene_outputs: list[dict]                       # 씬 단위 결과 저장을 위한 필드
    scene_inputs: list[dict]
    product_context: str
    merged_output_path: str
    merged_video_url: str
    merged_storage_path: str
    postprocess_compat: bool
    postprocess_output_path: str
    postprocess_video_url: str
    postprocess_storage_path: str

    # 검증 관련 필드
    verification_result: dict
    modification_request: str
    original_video_url: str
    retry_count: int

    status: Literal["ok", "failed"]
    error: str
    output: VideoOutput


def get_initial_state(*, scenario: ScenarioOutput) -> VideoState:
    return {"scenario": scenario}
