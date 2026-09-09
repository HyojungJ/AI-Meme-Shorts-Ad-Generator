"""
시나리오 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SceneInfo(BaseModel):
    """씬 정보"""
    scene_number: int
    scene_key: str
    text: str
    duration: Optional[float] = None


class ReviewResult(BaseModel):
    """시나리오 리뷰 결과"""
    feedback_type: str = Field(..., description="피드백 타입 (human_feedback)")
    scene_feedback: Dict[str, str] = Field(..., description="씬별 피드백 (scene1: 내용, scene2: 내용)")
    requested_at: str = Field(..., description="요청 시각 (ISO 8601)")


class ScenarioDetail(BaseModel):
    """시나리오 상세 정보"""
    script_id: int
    ad_id: int
    title: str
    description: Optional[str] = None
    scenes: List[SceneInfo]
    approval_status: str
    generation_type: Optional[str] = None
    review_result: Optional[ReviewResult] = None
    used_templates: Optional[List[str]] = None
    created_at: str


class ScenarioResponse(BaseModel):
    """시나리오 조회 응답 (단일)"""
    job_id: str
    scenario: ScenarioDetail


class ApproveResponse(BaseModel):
    script_id: int
    ad_id: int
    status: str
    message: str


class SceneRevisionRequest(BaseModel):
    """씬별 수정 요청"""
    scene_number: int = Field(..., ge=1, description="씬 번호")
    revision_notes: str = Field(..., description="해당 씬의 수정 요청 내용")


class ReviseRequest(BaseModel):
    """시나리오 수정 요청"""
    scene_revisions: List[SceneRevisionRequest] = Field(..., min_items=1, description="씬별 수정 요청 목록")


class ReviseResponse(BaseModel):
    script_id: int
    ad_id: int
    status: str
    message: str
