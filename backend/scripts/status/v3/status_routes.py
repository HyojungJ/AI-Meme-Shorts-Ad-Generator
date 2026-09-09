"""
영상 제작 상태 조회 API V3
새로운 스키마: ad_requests, workflow_execution, workflow_stages
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from generation.v3.database_v3 import (
    get_db,
    get_workflow_by_id,
    get_workflow_stages,
    get_average_processing_time
)

# auth v3 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))
from auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/videos", tags=["영상 상태 조회 V3"])


# ============================================
# 응답 모델
# ============================================
class StageInfo(BaseModel):
    """단계 정보"""
    stage_name: str
    stage_order: int
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    error_message: Optional[str]


class WorkflowStatusDetailResponse(BaseModel):
    """워크플로우 상세 상태 응답"""
    execution_id: str
    project_id: int
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    
    # 단계별 정보
    stages: List[StageInfo]
    
    # 시간 정보
    estimated_completion_time: Optional[str]
    estimated_remaining_seconds: Optional[int]
    
    # 비용 및 에러
    total_cost_usd: float
    retry_count: int
    error_message: Optional[str]
    
    # 생성/완료 시간
    created_at: str
    completed_at: Optional[str]


# ============================================
# 1. 워크플로우 상세 상태 조회
# ============================================
@router.get("/status/{execution_id}", response_model=WorkflowStatusDetailResponse)
async def get_workflow_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 제작 상세 상태 조회 (단계별 정보 포함)
    
    **경로 파라미터:**
    - execution_id: 워크플로우 고유 ID (UUID)
    
    **응답:**
    - 워크플로우 기본 정보 (상태, 진행률, 비용 등)
    - 단계별 상세 정보 (각 단계의 상태, 소요 시간)
    - 예상 완료 시간
    """
    
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. Execution ID 검증
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 Execution ID 형식입니다")
    
    # 3. 워크플로우 조회
    workflow = get_workflow_by_id(db, exec_uuid)
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 Execution ID를 찾을 수 없습니다")
    
    # 4. 권한 확인 (같은 회사만 조회 가능)
    if workflow.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 단계 정보 조회
    stages = get_workflow_stages(db, exec_uuid)
    
    # 6. 단계 정보 변환
    stage_list = []
    for stage in stages:
        stage_list.append(StageInfo(
            stage_name=stage.stage_name,
            stage_order=stage.stage_order,
            status=stage.status,
            started_at=stage.started_at.isoformat() if stage.started_at else None,
            completed_at=stage.completed_at.isoformat() if stage.completed_at else None,
            duration_seconds=stage.duration_seconds,
            error_message=stage.error_message
        ))
    
    # 7. 예상 완료 시간 계산
    estimated_time, remaining_seconds = calculate_estimated_completion(workflow, stages)
    
    # 8. 응답 반환
    return WorkflowStatusDetailResponse(
        execution_id=str(workflow.execution_id),
        project_id=workflow.project_id,
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress_percentage=workflow.progress_percentage,
        stages=stage_list,
        estimated_completion_time=estimated_time,
        estimated_remaining_seconds=remaining_seconds,
        total_cost_usd=float(workflow.total_cost_usd) if workflow.total_cost_usd else 0.0,
        retry_count=workflow.retry_count,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
    )


# ============================================
# 예상 완료 시간 계산 로직
# ============================================
def calculate_estimated_completion(workflow, stages):
    """
    예상 완료 시간 계산
    
    로직:
    1. 완료된 단계들의 평균 소요 시간 계산
    2. 남은 단계 수 × 평균 소요 시간 = 예상 남은 시간
    3. 현재 시간 + 예상 남은 시간 = 예상 완료 시간
    
    Returns:
        estimated_completion: 예상 완료 시각 (ISO format)
        estimated_remaining_seconds: 남은 예상 시간 (초)
    """
    # 이미 완료된 워크플로우
    if workflow.status in ['completed', 'failed', 'cancelled']:
        return None, 0
    
    # 완료된 단계들의 소요 시간 수집
    completed_stages = [s for s in stages if s.status == 'completed' and s.duration_seconds]
    
    if not completed_stages:
        # 완료된 단계가 없으면 평균 처리 시간 사용
        avg_time = get_average_processing_time(None, workflow.company_id)
        return (datetime.utcnow().timestamp() + avg_time), avg_time
    
    # 평균 소요 시간 계산
    avg_duration = sum(s.duration_seconds for s in completed_stages) / len(completed_stages)
    
    # 남은 단계 수 (pending + processing)
    remaining_stages = len([s for s in stages if s.status in ['pending', 'processing']])
    
    # 예상 남은 시간
    estimated_remaining = int(avg_duration * remaining_stages)
    
    # 예상 완료 시각
    estimated_completion = datetime.utcnow().timestamp() + estimated_remaining
    estimated_completion_iso = datetime.fromtimestamp(estimated_completion).isoformat()
    
    return estimated_completion_iso, estimated_remaining
