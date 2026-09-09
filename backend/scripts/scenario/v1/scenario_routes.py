"""
시나리오 검수 및 승인 API 라우트
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))

from scenario.v1.database import (
    get_db,
    get_scenarios_by_job,
    get_scenario_by_id,
    approve_scenario_by_id,
    reject_other_scenarios,
    update_workflow_after_approval,
    increment_revision_count,
    save_revision_feedback
)
from auth.v3.auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/videos", tags=["시나리오 검수"])


# ============================================
# 요청/응답 모델
# ============================================
class MemeInfo(BaseModel):
    """밈 정보"""
    meme_id: int
    meme_name: str
    definition: Optional[str]
    key_phrase: Optional[str]


class SceneInfo(BaseModel):
    """씬 정보"""
    scene_key: str
    dialogue: str
    duration: float
    visual_description: Optional[str]


class ScenarioInfo(BaseModel):
    """시나리오 정보"""
    script_id: int
    title: str
    description: Optional[str]
    hashtags: List[str]
    total_duration: float
    meme: MemeInfo
    scenes: List[dict]
    created_at: str


class ScenariosResponse(BaseModel):
    """시나리오 후보 조회 응답"""
    job_id: str
    project_id: int
    status: str
    scenarios: List[ScenarioInfo]
    approval_deadline: str


class ApproveResponse(BaseModel):
    """승인 응답"""
    message: str
    script_id: int
    approval_status: str
    approved_at: str
    next_stage: str


class ReviseRequest(BaseModel):
    """수정 요청"""
    feedback: str = Field(..., description="수정 요청 내용")
    change_meme: bool = Field(default=False, description="밈 변경 희망 여부")


class ReviseResponse(BaseModel):
    """수정 요청 응답"""
    message: str
    script_id: int
    revision_count: int
    max_revisions: int
    estimated_time_minutes: int


# ============================================
# 1. 시나리오 후보 조회
# ============================================
@router.get("/{job_id}/scenarios", response_model=ScenariosResponse)
async def get_scenarios(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    시나리오 후보 전체 조회 (2개)
    
    **경로 파라미터:**
    - job_id: 워크플로우 실행 ID (UUID)
    
    **응답:**
    - 2개의 시나리오 후보
    - 각 시나리오의 밈 정보, 씬 구조, 메타데이터
    - 승인 기한 (24시간)
    """
    
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 워크플로우 및 시나리오 조회
    workflow, scenarios = get_scenarios_by_job(db, job_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다")
    
    # 3. 권한 확인 (본인 작업만 조회 가능)
    if workflow.account_id != user_info["account_id"] and user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 시나리오가 없는 경우
    if not scenarios:
        raise HTTPException(status_code=404, detail="생성된 시나리오가 없습니다")
    
    # 5. 응답 데이터 구성
    scenario_list = []
    for scenario in scenarios:
        # 밈 정보 조회
        meme_info = MemeInfo(
            meme_id=scenario.meme.meme_id,
            meme_name=scenario.meme.meme_name,
            definition=scenario.meme.definition,
            key_phrase=scenario.meme.key_phrase
        )
        
        scenario_list.append(ScenarioInfo(
            script_id=scenario.script_id,
            title=scenario.title,
            description=scenario.description,
            hashtags=scenario.hashtags or [],
            total_duration=scenario.total_duration,
            meme=meme_info,
            scenes=scenario.scenes,
            created_at=scenario.created_at.isoformat()
        ))
    
    # 6. 승인 기한 계산 (24시간)
    approval_deadline = datetime.utcnow() + timedelta(hours=24)
    if scenarios[0].approval_requested_at:
        approval_deadline = scenarios[0].approval_requested_at + timedelta(hours=24)
    
    return ScenariosResponse(
        job_id=job_id,
        project_id=workflow.project_id,
        status=workflow.status,
        scenarios=scenario_list,
        approval_deadline=approval_deadline.isoformat()
    )


# ============================================
# 2. 시나리오 승인
# ============================================
@router.post("/{job_id}/scenarios/{script_id}/approve", response_model=ApproveResponse)
async def approve_scenario(
    job_id: str,
    script_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    시나리오 승인 및 파이프라인 트리거
    
    **경로 파라미터:**
    - job_id: 워크플로우 실행 ID (UUID)
    - script_id: 승인할 시나리오 ID
    
    **처리 내용:**
    - 선택된 시나리오 승인 처리
    - 다른 후보 시나리오 거부 처리
    - 워크플로우 상태 업데이트
    - 다음 단계(음성 생성) 트리거
    """
    
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 워크플로우 조회
    workflow, scenarios = get_scenarios_by_job(db, job_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다")
    
    # 3. 권한 확인
    if workflow.account_id != user_info["account_id"] and user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 시나리오 조회
    scenario = get_scenario_by_id(db, script_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="해당 시나리오를 찾을 수 없습니다")
    
    # 5. 이미 처리된 시나리오인지 확인
    if scenario.approval_status in ['approved', 'auto_approved']:
        raise HTTPException(status_code=409, detail="이미 승인된 시나리오입니다")
    
    if scenario.approval_status == 'rejected':
        raise HTTPException(status_code=409, detail="거부된 시나리오는 승인할 수 없습니다")
    
    # 6. 시나리오 승인 처리
    approved_scenario = approve_scenario_by_id(db, script_id, user_info["account_id"])
    
    # 7. 다른 시나리오 거부 처리
    reject_other_scenarios(db, scenario.project_id, script_id)
    
    # 8. 워크플로우 상태 업데이트
    next_stage = "audio_generation"
    update_workflow_after_approval(db, job_id, next_stage)
    
    # 9. TODO: 다음 단계 트리거 (Celery 작업)
    # from generation.tasks import generate_audio_task
    # generate_audio_task.delay(job_id, script_id)
    
    return ApproveResponse(
        message="시나리오가 승인되었습니다. 영상 제작을 시작합니다.",
        script_id=script_id,
        approval_status="approved",
        approved_at=approved_scenario.approved_at.isoformat(),
        next_stage=next_stage
    )


# ============================================
# 3. 시나리오 수정 요청
# ============================================
@router.post("/{job_id}/scenarios/{script_id}/revise", response_model=ReviseResponse)
async def revise_scenario(
    job_id: str,
    script_id: int,
    request: Request,
    revise_request: ReviseRequest,
    db: Session = Depends(get_db)
):
    """
    시나리오 수정 요청
    
    **경로 파라미터:**
    - job_id: 워크플로우 실행 ID (UUID)
    - script_id: 수정 요청할 시나리오 ID
    
    **요청 본문:**
    - feedback: 수정 요청 내용
    - change_meme: 밈 변경 희망 여부
    
    **제한사항:**
    - 최대 3회까지 수정 요청 가능
    - 3회 초과 시 400 에러 반환
    """
    
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 워크플로우 조회
    workflow, scenarios = get_scenarios_by_job(db, job_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 작업을 찾을 수 없습니다")
    
    # 3. 권한 확인
    if workflow.account_id != user_info["account_id"] and user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 시나리오 조회
    scenario = get_scenario_by_id(db, script_id)
    
    if not scenario:
        raise HTTPException(status_code=404, detail="해당 시나리오를 찾을 수 없습니다")
    
    # 5. 수정 횟수 확인
    MAX_REVISIONS = 3
    workflow, current_count = increment_revision_count(db, job_id)
    
    if current_count > MAX_REVISIONS:
        raise HTTPException(
            status_code=400,
            detail=f"최대 수정 요청 횟수({MAX_REVISIONS}회)를 초과했습니다. 고객 지원팀에 문의해주세요."
        )
    
    # 6. 피드백 저장
    save_revision_feedback(db, script_id, revise_request.feedback, revise_request.change_meme)
    
    # 7. TODO: 시나리오 재생성 워크플로우 트리거 (Celery 작업)
    # from generation.tasks import regenerate_scenario_task
    # regenerate_scenario_task.delay(job_id, revise_request.feedback, revise_request.change_meme)
    
    return ReviseResponse(
        message="수정 요청이 접수되었습니다. 새로운 시나리오를 생성합니다.",
        script_id=script_id,
        revision_count=current_count,
        max_revisions=MAX_REVISIONS,
        estimated_time_minutes=5
    )
