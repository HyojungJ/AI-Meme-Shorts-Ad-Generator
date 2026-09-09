"""
Admin API 엔드포인트
작성일: 2026-01-22
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import sys
import os
import uuid

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .database import (
    get_db,
    get_all_videos_filtered,
    get_video_with_company,
    get_pending_videos,
    create_video_post,
    update_video_post_status,
    get_active_workflows,
    get_failed_workflows,
    get_workflow_with_stages,
    retry_workflow,
    cancel_workflow
)

# auth v3 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'auth', 'v3'))
from auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/admin", tags=["Admin 관리"])


# ============================================
# 요청/응답 모델
# ============================================

# 1. 전체 영상 목록 관리
class VideoListItem(BaseModel):
    """영상 목록 아이템"""
    video_id: int
    title: str
    company_id: int
    company_name: str
    status: str
    duration_seconds: Optional[int]
    file_size_mb: Optional[float]
    created_at: str
    completed_at: Optional[str]


class VideoListResponse(BaseModel):
    """영상 목록 응답"""
    total_count: int
    offset: int
    limit: int
    videos: List[VideoListItem]


# 2. 영상 게시 관리
class PendingVideoItem(BaseModel):
    """게시 대기 영상 아이템"""
    video_id: int
    title: str
    company_name: str
    s3_url: str
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int]
    completed_at: Optional[str]


class PendingVideosResponse(BaseModel):
    """게시 대기 목록 응답"""
    total_count: int
    offset: int
    limit: int
    videos: List[PendingVideoItem]


class PublishVideoRequest(BaseModel):
    """영상 게시 요청"""
    channel_id: int = Field(..., description="YouTube 채널 ID")
    yt_title: Optional[str] = Field(None, description="YouTube 제목 (없으면 원본 제목 사용)")
    yt_description: Optional[str] = Field(None, description="YouTube 설명")
    scheduled_at: Optional[str] = Field(None, description="예약 게시 시간 (ISO 8601)")


class PublishVideoResponse(BaseModel):
    """영상 게시 응답"""
    post_id: int
    video_id: int
    status: str
    message: str


# 3. 시스템 모니터링
class WorkflowListItem(BaseModel):
    """워크플로우 목록 아이템"""
    execution_id: str
    project_id: int
    company_id: int
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    retry_count: int
    created_at: str
    completed_at: Optional[str]


class WorkflowListResponse(BaseModel):
    """워크플로우 목록 응답"""
    total_count: int
    offset: int
    limit: int
    workflows: List[WorkflowListItem]


class WorkflowStageItem(BaseModel):
    """워크플로우 단계 아이템"""
    stage_name: str
    stage_order: int
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    error_message: Optional[str]


class WorkflowDetailResponse(BaseModel):
    """워크플로우 상세 응답"""
    execution_id: str
    project_id: int
    company_id: int
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    total_cost_usd: float
    retry_count: int
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]
    stages: List[WorkflowStageItem]


class WorkflowActionResponse(BaseModel):
    """워크플로우 액션 응답"""
    execution_id: str
    status: str
    message: str


# ============================================
# Admin 권한 체크 미들웨어
# ============================================
async def check_admin_permission(request: Request):
    """Admin 권한 확인"""
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # TODO: Admin 계정 타입 체크 (현재는 account_type으로만 체크)
    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
    
    return user_info


# ============================================
# 1. 전체 영상 목록 관리
# ============================================
@router.get("/videos/all", response_model=VideoListResponse)
async def get_all_videos(
    request: Request,
    company_id: Optional[int] = Query(None, description="회사 ID 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    search: Optional[str] = Query(None, description="검색어 (회사명/제품명)"),
    date_from: Optional[str] = Query(None, description="시작 날짜 (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="종료 날짜 (ISO 8601)"),
    sort_by: str = Query('created_at', description="정렬 기준"),
    order: str = Query('desc', description="정렬 순서"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    전체 영상 목록 조회 (Admin 전용)
    
    **필터링 옵션:**
    - company_id: 특정 회사의 영상만
    - status: 상태별 필터링
    - search: 회사명 또는 제품명 검색
    - date_from, date_to: 날짜 범위
    
    **정렬 옵션:**
    - sort_by: created_at, completed_at, company_name
    - order: asc, desc
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 날짜 파싱
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from 형식이 잘못되었습니다")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to 형식이 잘못되었습니다")
    
    # 영상 목록 조회
    videos, total_count = get_all_videos_filtered(
        db=db,
        company_id=company_id,
        status=status,
        search=search,
        date_from=date_from_dt,
        date_to=date_to_dt,
        sort_by=sort_by,
        order=order,
        offset=offset,
        limit=limit
    )
    
    # 응답 변환
    video_items = []
    for video in videos:
        # 회사 정보 가져오기
        video_info = get_video_with_company(db, video.video_id)
        company_name = video_info['company'].company_name if video_info else "Unknown"
        
        # 파일 크기 MB 변환
        file_size_mb = None
        if video.file_size_bytes:
            file_size_mb = round(video.file_size_bytes / (1024 * 1024), 2)
        
        video_items.append(VideoListItem(
            video_id=video.video_id,
            title=video.title,
            company_id=video.company_id,
            company_name=company_name,
            status=video.status,
            duration_seconds=video.duration_seconds,
            file_size_mb=file_size_mb,
            created_at=video.created_at.isoformat(),
            completed_at=video.completed_at.isoformat() if video.completed_at else None
        ))
    
    return VideoListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        videos=video_items
    )


# ============================================
# 2. 영상 게시 관리
# ============================================
@router.get("/videos/pending", response_model=PendingVideosResponse)
async def get_pending_videos_list(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    게시 대기 영상 목록 조회 (client_approved 상태)
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 게시 대기 영상 조회
    videos, total_count = get_pending_videos(db, offset, limit)
    
    # 응답 변환
    video_items = []
    for video in videos:
        video_info = get_video_with_company(db, video.video_id)
        company_name = video_info['company'].company_name if video_info else "Unknown"
        
        video_items.append(PendingVideoItem(
            video_id=video.video_id,
            title=video.title,
            company_name=company_name,
            s3_url=video.s3_url,
            thumbnail_url=video.thumbnail_url,
            duration_seconds=video.duration_seconds,
            completed_at=video.completed_at.isoformat() if video.completed_at else None
        ))
    
    return PendingVideosResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        videos=video_items
    )


@router.post("/videos/{video_id}/publish", response_model=PublishVideoResponse)
async def publish_video(
    video_id: int,
    publish_request: PublishVideoRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    YouTube 게시 승인 처리
    
    **기능:**
    - 영상을 YouTube 게시 대기열에 추가
    - 메타데이터 설정 (제목, 설명)
    - 예약 게시 시간 설정 가능
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 영상 조회
    video_info = get_video_with_company(db, video_id)
    if not video_info:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    video = video_info['video']
    
    # 상태 확인 (client_approved만 게시 가능)
    if video.status != 'client_approved':
        raise HTTPException(
            status_code=400,
            detail=f"게시할 수 없는 상태입니다. 현재 상태: {video.status}"
        )
    
    # 예약 시간 파싱
    scheduled_at_dt = None
    if publish_request.scheduled_at:
        try:
            scheduled_at_dt = datetime.fromisoformat(publish_request.scheduled_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="scheduled_at 형식이 잘못되었습니다")
    
    # 게시 레코드 생성
    post = create_video_post(
        db=db,
        video_id=video_id,
        channel_id=publish_request.channel_id,
        yt_title=publish_request.yt_title or video.title,
        yt_description=publish_request.yt_description or video.description,
        scheduled_at=scheduled_at_dt
    )
    
    # 영상 상태 업데이트 (admin_approved)
    video.status = 'admin_approved'
    video.updated_at = datetime.utcnow()
    db.commit()
    
    return PublishVideoResponse(
        post_id=post.post_id,
        video_id=video_id,
        status='pending',
        message="YouTube 게시 대기열에 추가되었습니다"
    )


@router.post("/videos/{video_id}/hold", response_model=PublishVideoResponse)
async def hold_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    게시 보류 처리
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 영상 조회
    video_info = get_video_with_company(db, video_id)
    if not video_info:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    video = video_info['video']
    
    # 상태 확인
    if video.status != 'client_approved':
        raise HTTPException(
            status_code=400,
            detail=f"보류할 수 없는 상태입니다. 현재 상태: {video.status}"
        )
    
    # 상태는 그대로 유지 (client_approved)
    # TODO: 보류 사유 저장 기능 추가 가능
    
    return PublishVideoResponse(
        post_id=0,
        video_id=video_id,
        status='held',
        message="게시가 보류되었습니다"
    )


# ============================================
# 3. 시스템 모니터링
# ============================================
@router.get("/workflows", response_model=WorkflowListResponse)
async def get_workflows(
    request: Request,
    status_filter: Optional[str] = Query(None, description="상태 필터 (active/failed)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    워크플로우 목록 조회
    
    **필터:**
    - status_filter: 'active' (진행 중), 'failed' (실패)
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 워크플로우 조회
    if status_filter == 'failed':
        workflows, total_count = get_failed_workflows(db, offset, limit)
    else:
        workflows, total_count = get_active_workflows(db, offset, limit)
    
    # 응답 변환
    workflow_items = []
    for workflow in workflows:
        workflow_items.append(WorkflowListItem(
            execution_id=str(workflow.execution_id),
            project_id=workflow.project_id,
            company_id=workflow.company_id,
            status=workflow.status,
            current_stage=workflow.current_stage,
            progress_percentage=workflow.progress_percentage,
            retry_count=workflow.retry_count,
            created_at=workflow.created_at.isoformat(),
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
        ))
    
    return WorkflowListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        workflows=workflow_items
    )


@router.get("/workflows/{execution_id}/logs", response_model=WorkflowDetailResponse)
async def get_workflow_logs(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    워크플로우 상세 로그 조회
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 워크플로우 조회
    workflow_data = get_workflow_with_stages(db, execution_id)
    if not workflow_data:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    
    workflow = workflow_data['workflow']
    stages = workflow_data['stages']
    
    # 단계 정보 변환
    stage_items = []
    for stage in stages:
        stage_items.append(WorkflowStageItem(
            stage_name=stage.stage_name,
            stage_order=stage.stage_order,
            status=stage.status,
            started_at=stage.started_at.isoformat() if stage.started_at else None,
            completed_at=stage.completed_at.isoformat() if stage.completed_at else None,
            duration_seconds=stage.duration_seconds,
            error_message=stage.error_message
        ))
    
    return WorkflowDetailResponse(
        execution_id=str(workflow.execution_id),
        project_id=workflow.project_id,
        company_id=workflow.company_id,
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress_percentage=workflow.progress_percentage,
        total_cost_usd=workflow.total_cost_usd,
        retry_count=workflow.retry_count,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        stages=stage_items
    )


@router.post("/workflows/{execution_id}/retry", response_model=WorkflowActionResponse)
async def retry_workflow_endpoint(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    워크플로우 수동 재시도
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 재시도
    workflow = retry_workflow(db, execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    
    return WorkflowActionResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message="워크플로우가 재시도되었습니다"
    )


@router.post("/workflows/{execution_id}/cancel", response_model=WorkflowActionResponse)
async def cancel_workflow_endpoint(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    워크플로우 취소
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 취소
    workflow = cancel_workflow(db, execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    
    return WorkflowActionResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message="워크플로우가 취소되었습니다"
    )



# ============================================
# 4. 밈 데이터 관리 - 추가 import
# ============================================
from .database import (
    get_all_memes_filtered,
    get_meme_by_id,
    create_meme,
    update_meme,
    delete_meme,
    get_meme_quality_stats,
    get_all_companies_filtered,
    get_company_detail,
    toggle_company_active,
    get_company_video_stats,
    get_company_cost_stats,
    get_company_members
)


# ============================================
# 4. 밈 데이터 관리 - 모델
# ============================================
class MemeListItem(BaseModel):
    """밈 목록 아이템"""
    meme_id: int
    meme_name: str
    definition: Optional[str]
    key_phrase: Optional[str]
    meme_type: Optional[str]
    status: str
    confidence: Optional[float]
    risk_info: Optional[str]
    created_at: str
    updated_at: str


class MemeListResponse(BaseModel):
    """밈 목록 응답"""
    total_count: int
    offset: int
    limit: int
    memes: List[MemeListItem]


class MemeDetailResponse(BaseModel):
    """밈 상세 응답"""
    meme_id: int
    meme_name: str
    definition: Optional[str]
    origin: Optional[str]
    key_phrase: Optional[str]
    sources: Optional[str]
    risk_info: Optional[str]
    meme_type: Optional[str]
    status: str
    confidence: Optional[float]
    created_at: str
    updated_at: str


class CreateMemeRequest(BaseModel):
    """밈 생성 요청"""
    meme_name: str = Field(..., min_length=1, max_length=255)
    definition: Optional[str] = None
    origin: Optional[str] = None
    key_phrase: Optional[str] = None
    meme_type: Optional[str] = Field(None, description="Dialogue, Motion, Hybrid")
    risk_info: Optional[str] = Field(None, description="low, medium, high")


class UpdateMemeRequest(BaseModel):
    """밈 수정 요청"""
    meme_name: Optional[str] = Field(None, min_length=1, max_length=255)
    definition: Optional[str] = None
    origin: Optional[str] = None
    key_phrase: Optional[str] = None
    meme_type: Optional[str] = None
    risk_info: Optional[str] = None
    status: Optional[str] = None


class MemeActionResponse(BaseModel):
    """밈 액션 응답"""
    meme_id: int
    message: str


class MemeQualityStatsResponse(BaseModel):
    """밈 품질 통계 응답"""
    total_count: int
    ready_count: int
    processing_count: int
    avg_confidence: float


# ============================================
# 5. 회사 관리 - 모델
# ============================================
class CompanyListItem(BaseModel):
    """회사 목록 아이템"""
    company_id: int
    company_name: str
    is_active: bool
    created_at: str


class CompanyListResponse(BaseModel):
    """회사 목록 응답"""
    total_count: int
    offset: int
    limit: int
    companies: List[CompanyListItem]


class CompanyMemberItem(BaseModel):
    """회사 멤버 아이템"""
    member_id: int
    account_id: int
    email: str
    member_name: str
    role: str
    department: Optional[str]
    is_primary: bool
    is_active: bool
    created_at: str


class CompanyDetailResponse(BaseModel):
    """회사 상세 응답"""
    company_id: int
    company_name: str
    is_active: bool
    member_count: int
    video_count: int
    completed_video_count: int
    created_at: str
    updated_at: str
    members: List[CompanyMemberItem]


class CompanyVideoStatsResponse(BaseModel):
    """회사 영상 통계 응답"""
    company_id: int
    total_videos: int
    status_counts: dict
    avg_processing_time_minutes: int


class CompanyCostStatsResponse(BaseModel):
    """회사 비용 통계 응답"""
    company_id: int
    total_cost_usd: float
    avg_cost_usd: float
    video_count: int


class CompanyActionResponse(BaseModel):
    """회사 액션 응답"""
    company_id: int
    is_active: bool
    message: str


# ============================================
# 4. 밈 데이터 관리 - API
# ============================================
@router.get("/memes", response_model=MemeListResponse)
async def get_memes(
    request: Request,
    status: Optional[str] = Query(None, description="상태 필터 (READY, PROCESSING, COMPLETED, FAILED, DELETED)"),
    meme_type: Optional[str] = Query(None, description="타입 필터 (Dialogue, Motion, Hybrid)"),
    search: Optional[str] = Query(None, description="검색어 (밈 이름/정의)"),
    sort_by: str = Query('created_at', description="정렬 기준"),
    order: str = Query('desc', description="정렬 순서"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    밈 목록 조회 (필터링, 검색)
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 밈 목록 조회
    memes, total_count = get_all_memes_filtered(
        db=db,
        status=status,
        meme_type=meme_type,
        search=search,
        sort_by=sort_by,
        order=order,
        offset=offset,
        limit=limit
    )
    
    # 응답 변환
    meme_items = []
    for meme in memes:
        meme_items.append(MemeListItem(
            meme_id=meme.meme_id,
            meme_name=meme.meme_name,
            definition=meme.definition,
            key_phrase=meme.key_phrase,
            meme_type=meme.meme_type,
            status=meme.status,
            confidence=meme.confidence,
            risk_info=meme.risk_info,
            created_at=meme.created_at.isoformat(),
            updated_at=meme.updated_at.isoformat()
        ))
    
    return MemeListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        memes=meme_items
    )


@router.get("/memes/{meme_id}", response_model=MemeDetailResponse)
async def get_meme_detail(
    meme_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 상세 조회
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 밈 조회
    meme = get_meme_by_id(db, meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="밈을 찾을 수 없습니다")
    
    return MemeDetailResponse(
        meme_id=meme.meme_id,
        meme_name=meme.meme_name,
        definition=meme.definition,
        origin=meme.origin,
        key_phrase=meme.key_phrase,
        sources=meme.sources,
        risk_info=meme.risk_info,
        meme_type=meme.meme_type,
        status=meme.status,
        confidence=meme.confidence,
        created_at=meme.created_at.isoformat(),
        updated_at=meme.updated_at.isoformat()
    )


@router.post("/memes", response_model=MemeActionResponse)
async def create_meme_endpoint(
    meme_request: CreateMemeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 수동 추가
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 중복 체크
    existing_meme = db.query(get_meme_by_id.__self__).filter_by(meme_name=meme_request.meme_name).first()
    if existing_meme:
        raise HTTPException(status_code=400, detail="이미 존재하는 밈 이름입니다")
    
    # 밈 생성
    meme = create_meme(
        db=db,
        meme_name=meme_request.meme_name,
        definition=meme_request.definition,
        origin=meme_request.origin,
        key_phrase=meme_request.key_phrase,
        meme_type=meme_request.meme_type,
        risk_info=meme_request.risk_info
    )
    
    return MemeActionResponse(
        meme_id=meme.meme_id,
        message="밈이 추가되었습니다"
    )


@router.put("/memes/{meme_id}", response_model=MemeActionResponse)
async def update_meme_endpoint(
    meme_id: int,
    meme_request: UpdateMemeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 정보 수정
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 밈 수정
    meme = update_meme(
        db=db,
        meme_id=meme_id,
        meme_name=meme_request.meme_name,
        definition=meme_request.definition,
        origin=meme_request.origin,
        key_phrase=meme_request.key_phrase,
        meme_type=meme_request.meme_type,
        risk_info=meme_request.risk_info,
        status=meme_request.status
    )
    
    if not meme:
        raise HTTPException(status_code=404, detail="밈을 찾을 수 없습니다")
    
    return MemeActionResponse(
        meme_id=meme.meme_id,
        message="밈 정보가 수정되었습니다"
    )


@router.delete("/memes/{meme_id}", response_model=MemeActionResponse)
async def delete_meme_endpoint(
    meme_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 삭제 (소프트 삭제)
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 밈 삭제
    success = delete_meme(db, meme_id)
    if not success:
        raise HTTPException(status_code=404, detail="밈을 찾을 수 없습니다")
    
    return MemeActionResponse(
        meme_id=meme_id,
        message="밈이 삭제되었습니다"
    )


@router.post("/memes/collect", response_model=dict)
async def trigger_meme_collection(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 수집 트리거 (자동화 파이프라인 실행)
    
    **기능:**
    - 자동화 파이프라인을 트리거하여 새로운 밈 수집 시작
    - 실제 구현은 팀원의 자동화 시스템과 연동 필요
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # TODO: 실제 자동화 파이프라인 트리거 로직 구현
    # 예: Celery task, AWS Lambda, 또는 별도 서비스 호출
    
    return {
        "message": "밈 수집이 트리거되었습니다",
        "status": "triggered",
        "note": "자동화 파이프라인 연동 필요"
    }


@router.get("/memes/stats/quality", response_model=MemeQualityStatsResponse)
async def get_meme_quality_statistics(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 품질 통계 조회
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 통계 조회
    stats = get_meme_quality_stats(db)
    
    return MemeQualityStatsResponse(
        total_count=stats['total_count'],
        ready_count=stats['ready_count'],
        processing_count=stats['processing_count'],
        avg_confidence=stats['avg_confidence']
    )


# ============================================
# 5. 회사 관리 - API
# ============================================
@router.get("/companies", response_model=CompanyListResponse)
async def get_companies(
    request: Request,
    is_active: Optional[bool] = Query(None, description="활성화 상태 필터"),
    search: Optional[str] = Query(None, description="검색어 (회사명)"),
    sort_by: str = Query('created_at', description="정렬 기준"),
    order: str = Query('desc', description="정렬 순서"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    전체 회사 목록 조회
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 회사 목록 조회
    companies, total_count = get_all_companies_filtered(
        db=db,
        is_active=is_active,
        search=search,
        sort_by=sort_by,
        order=order,
        offset=offset,
        limit=limit
    )
    
    # 응답 변환
    company_items = []
    for company in companies:
        company_items.append(CompanyListItem(
            company_id=company.company_id,
            company_name=company.company_name,
            is_active=company.is_active,
            created_at=company.created_at.isoformat()
        ))
    
    return CompanyListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        companies=company_items
    )


@router.get("/companies/{company_id}", response_model=CompanyDetailResponse)
async def get_company_details(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    회사 상세 정보 조회
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 회사 상세 조회
    company_data = get_company_detail(db, company_id)
    if not company_data:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    
    company = company_data['company']
    
    # 멤버 목록 조회
    members = get_company_members(db, company_id)
    
    member_items = []
    for member in members:
        member_items.append(CompanyMemberItem(
            member_id=member['member_id'],
            account_id=member['account_id'],
            email=member['email'],
            member_name=member['member_name'],
            role=member['role'],
            department=member['department'],
            is_primary=member['is_primary'],
            is_active=member['is_active'],
            created_at=member['created_at'].isoformat()
        ))
    
    return CompanyDetailResponse(
        company_id=company.company_id,
        company_name=company.company_name,
        is_active=company.is_active,
        member_count=company_data['member_count'],
        video_count=company_data['video_count'],
        completed_video_count=company_data['completed_video_count'],
        created_at=company.created_at.isoformat(),
        updated_at=company.updated_at.isoformat(),
        members=member_items
    )


@router.post("/companies/{company_id}/toggle-active", response_model=CompanyActionResponse)
async def toggle_company_active_endpoint(
    company_id: int,
    is_active: bool = Query(..., description="활성화 여부"),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    회사 활성화/비활성화
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 활성화 상태 변경
    company = toggle_company_active(db, company_id, is_active)
    if not company:
        raise HTTPException(status_code=404, detail="회사를 찾을 수 없습니다")
    
    return CompanyActionResponse(
        company_id=company.company_id,
        is_active=company.is_active,
        message=f"회사가 {'활성화' if is_active else '비활성화'}되었습니다"
    )


@router.get("/companies/{company_id}/stats/videos", response_model=CompanyVideoStatsResponse)
async def get_company_video_statistics(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    회사별 영상 제작 통계
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 통계 조회
    stats = get_company_video_stats(db, company_id)
    
    return CompanyVideoStatsResponse(
        company_id=company_id,
        total_videos=stats['total_videos'],
        status_counts=stats['status_counts'],
        avg_processing_time_minutes=stats['avg_processing_time_minutes']
    )


@router.get("/companies/{company_id}/stats/costs", response_model=CompanyCostStatsResponse)
async def get_company_cost_statistics(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    회사별 비용 집계
    """
    # Admin 권한 체크
    await check_admin_permission(request)
    
    # 비용 통계 조회
    stats = get_company_cost_stats(db, company_id)
    
    return CompanyCostStatsResponse(
        company_id=company_id,
        total_cost_usd=stats['total_cost_usd'],
        avg_cost_usd=stats['avg_cost_usd'],
        video_count=stats['video_count']
    )
