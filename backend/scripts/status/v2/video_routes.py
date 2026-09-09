"""
영상 제작 상태 추적 API V2
새로운 스키마 적용
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

from status.v2.database_v2 import (
    get_db,
    get_workflow_by_id,
    get_workflow_stages,
    get_stage_summary,
    calculate_estimated_completion,
    get_workflows_by_company_filtered
)

# auth v3 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))
from auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/status", tags=["영상 상태 추적 V2"])


# ============================================
# 요청/응답 모델
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
    progress_percentage: int
    
    # 단계별 정보
    completed_stages: List[StageInfo]
    current_stage: Optional[StageInfo]
    pending_stages: List[str]
    
    # 시간 정보
    estimated_completion: Optional[str]
    estimated_remaining_seconds: Optional[int]
    
    # 기타
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class WorkflowStatusResponse(BaseModel):
    """워크플로우 기본 상태 응답"""
    execution_id: str
    project_id: int
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답"""
    total_count: int
    offset: int
    limit: int
    workflows: List[WorkflowStatusResponse]


# ============================================
# 1. 워크플로우 상세 상태 조회
# ============================================
@router.get("/{execution_id}/detail", response_model=WorkflowStatusDetailResponse)
async def get_video_status_detail(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 생성 상세 상태 조회 (단계별 정보 포함)
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **응답:**
    - 완료된 단계 목록 (소요 시간 포함)
    - 현재 진행 중인 단계
    - 대기 중인 단계 목록
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
    
    # 4. 권한 확인
    if workflow.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 단계 정보 조회
    stages = get_workflow_stages(db, exec_uuid)
    completed, current, pending = get_stage_summary(workflow, stages)
    estimated_time, remaining_seconds = calculate_estimated_completion(db, workflow, stages)
    
    # 6. 응답 반환
    return WorkflowStatusDetailResponse(
        execution_id=str(workflow.execution_id),
        project_id=workflow.project_id,
        status=workflow.status,
        progress_percentage=workflow.progress_percentage,
        completed_stages=[
            StageInfo(
                stage_name=s.stage_name,
                stage_order=s.stage_order,
                status=s.status,
                started_at=s.started_at.isoformat() if s.started_at else None,
                completed_at=s.completed_at.isoformat() if s.completed_at else None,
                duration_seconds=s.duration_seconds,
                error_message=s.error_message
            ) for s in completed
        ],
        current_stage=StageInfo(
            stage_name=current.stage_name,
            stage_order=current.stage_order,
            status=current.status,
            started_at=current.started_at.isoformat() if current.started_at else None,
            completed_at=current.completed_at.isoformat() if current.completed_at else None,
            duration_seconds=current.duration_seconds,
            error_message=current.error_message
        ) if current else None,
        pending_stages=pending,
        estimated_completion=estimated_time,
        estimated_remaining_seconds=remaining_seconds,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
    )


# ============================================
# 2. 워크플로우 기본 상태 조회
# ============================================
@router.get("/{execution_id}", response_model=WorkflowStatusResponse)
async def get_video_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 생성 기본 상태 조회
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **응답:**
    - 작업 상태, 진행률 등 기본 정보
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
    
    # 4. 권한 확인
    if workflow.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 응답 반환
    return WorkflowStatusResponse(
        execution_id=str(workflow.execution_id),
        project_id=workflow.project_id,
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress_percentage=workflow.progress_percentage,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
    )


# ============================================
# 3. 내 프로젝트 목록 조회 (필터링, 페이지네이션)
# ============================================
@router.get("/my-projects", response_model=ProjectListResponse)
async def get_my_projects(
    request: Request,
    # 페이지네이션
    offset: int = 0,
    limit: int = 10,
    # 필터링
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    # 정렬
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session = Depends(get_db)
):
    """
    내 영상 제작 프로젝트 목록 조회 (필터링, 페이지네이션)
    
    **쿼리 파라미터:**
    - offset: 시작 위치 (기본 0)
    - limit: 조회 개수 (기본 10, 최대 100)
    - status: 상태 필터 (created, processing, completed, failed 등)
    - date_from: 시작 날짜 (ISO 8601 형식)
    - date_to: 종료 날짜 (ISO 8601 형식)
    - sort_by: 정렬 기준 (created_at, completed_at)
    - order: 정렬 순서 (asc, desc)
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 파라미터 검증
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 10
    if offset < 0:
        offset = 0
    
    if sort_by not in ['created_at', 'completed_at']:
        sort_by = 'created_at'
    if order not in ['asc', 'desc']:
        order = 'desc'
    
    # 3. 날짜 파싱
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from 형식이 잘못되었습니다 (ISO 8601 형식 필요)")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to 형식이 잘못되었습니다 (ISO 8601 형식 필요)")
    
    # 4. 워크플로우 목록 조회
    workflows, total_count = get_workflows_by_company_filtered(
        db=db,
        company_id=user_info["company_id"],
        status=status,
        date_from=date_from_dt,
        date_to=date_to_dt,
        sort_by=sort_by,
        order=order,
        offset=offset,
        limit=limit
    )
    
    # 5. 응답 변환
    result = []
    for workflow in workflows:
        result.append(WorkflowStatusResponse(
            execution_id=str(workflow.execution_id),
            project_id=workflow.project_id,
            status=workflow.status,
            current_stage=workflow.current_stage,
            progress_percentage=workflow.progress_percentage,
            error_message=workflow.error_message,
            created_at=workflow.created_at.isoformat(),
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
        ))
    
    return ProjectListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        workflows=result
    )
