"""
영상 다운로드 및 승인/거부 API
작성일: 2026-01-22
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock S3 사용 (테스트용)
from generation.s3_handler_mock import generate_presigned_url

from .database import (
    get_db,
    get_video_by_id,
    approve_video,
    reject_video,
    get_video_with_project_info
)

# auth v3 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'auth', 'v3'))
from auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/videos", tags=["영상 다운로드 및 승인"])


# ============================================
# 요청/응답 모델
# ============================================
class VideoDownloadResponse(BaseModel):
    """영상 다운로드 정보 응답"""
    video_id: int
    title: str
    description: Optional[str]
    
    # 다운로드 링크
    download_url: str
    download_expires_at: str
    
    # 썸네일
    thumbnail_url: Optional[str]
    
    # 영상 메타데이터
    file_size_bytes: Optional[int]
    file_size_mb: Optional[float]
    duration_seconds: Optional[int]
    resolution: Optional[str]
    format: Optional[str]
    
    # 제작 정보
    production_cost_usd: Optional[float]
    processing_time_minutes: Optional[int]
    
    # 상태
    status: str
    created_at: str
    completed_at: Optional[str]
    
    # 다운로드 통계 (컬럼 삭제됨, 기본값 0)
    download_count: int = 0


class VideoApprovalRequest(BaseModel):
    """영상 승인 요청"""
    approval_type: str = Field(..., description="승인 타입: 'client' 또는 'admin'")


class VideoRejectionRequest(BaseModel):
    """영상 거부 요청"""
    rejection_type: str = Field(..., description="거부 타입: 'client' 또는 'admin'")
    rejection_reason: str = Field(..., min_length=1, description="거부 사유")


class VideoApprovalResponse(BaseModel):
    """영상 승인/거부 응답"""
    video_id: int
    status: str
    message: str
    updated_at: str


# ============================================
# 1. 영상 다운로드 링크 생성
# ============================================
@router.get("/{video_id}/download", response_model=VideoDownloadResponse)
async def get_video_download_link(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 다운로드 링크 생성
    
    **기능:**
    - S3 Signed URL 생성 (7일 유효)
    - 다운로드 권한 검증 (본인 회사 영상만)
    - 영상 메타데이터 조회
    - 썸네일 URL 제공
    - 제작 비용 및 소요 시간 표시
    
    **권한:**
    - 같은 회사의 영상만 다운로드 가능
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 영상 조회 (프로젝트 정보 포함)
    video_info = get_video_with_project_info(db, video_id)
    if not video_info:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    video = video_info['video']
    project = video_info['project']
    
    # 3. 권한 확인 (같은 회사만)
    if video.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 영상 상태 확인 (completed 이상만 다운로드 가능)
    if video.status not in ['completed', 'client_approved', 'admin_approved', 'published']:
        raise HTTPException(
            status_code=400,
            detail=f"영상이 아직 완성되지 않았습니다. 현재 상태: {video.status}"
        )
    
    # 5. S3 Presigned URL 생성 (7일 유효)
    try:
        download_url = generate_presigned_url(
            video.s3_url,
            expiration=7 * 24 * 3600  # 7일
        )
        expires_at = datetime.utcnow() + timedelta(days=7)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"다운로드 링크 생성 실패: {str(e)}"
        )
    
    # 6. 썸네일 URL 생성 (있는 경우)
    thumbnail_url = None
    if video.thumbnail_url:
        try:
            thumbnail_url = generate_presigned_url(
                video.thumbnail_url,
                expiration=7 * 24 * 3600
            )
        except Exception as e:
            print(f"썸네일 URL 생성 실패: {e}")
            thumbnail_url = video.thumbnail_url
    
    # 7. 파일 크기 MB 변환
    file_size_mb = None
    if video.file_size_bytes:
        file_size_mb = round(video.file_size_bytes / (1024 * 1024), 2)
    
    # 8. 제작 비용 및 소요 시간 (프로젝트에서 가져오기)
    production_cost = None
    processing_time_minutes = None
    
    if project:
        production_cost = float(project.cost_estimate) if project.cost_estimate else None
        processing_time_minutes = project.processing_time
    
    # 9. 응답 반환
    return VideoDownloadResponse(
        video_id=video.video_id,
        title=video.title,
        description=video.description,
        download_url=download_url,
        download_expires_at=expires_at.isoformat(),
        thumbnail_url=thumbnail_url,
        file_size_bytes=video.file_size_bytes,
        file_size_mb=file_size_mb,
        duration_seconds=video.duration_seconds,
        resolution=video.resolution,
        format=video.format,
        production_cost_usd=production_cost,
        processing_time_minutes=processing_time_minutes,
        status=video.status,
        created_at=video.created_at.isoformat(),
        completed_at=video.completed_at.isoformat() if video.completed_at else None,
        download_count=0  # download_count 컬럼 삭제됨
    )


# ============================================
# 2. 영상 승인
# ============================================
@router.post("/{video_id}/approve", response_model=VideoApprovalResponse)
async def approve_video_endpoint(
    video_id: int,
    approval_request: VideoApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 승인
    
    **승인 타입:**
    - `client`: 기업 고객 승인 (completed → client_approved)
    - `admin`: Admin 승인 (client_approved → admin_approved)
    
    **권한:**
    - client: 같은 회사의 영상만 승인 가능
    - admin: 모든 영상 승인 가능 (TODO: admin 권한 체크)
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 승인 타입 검증
    if approval_request.approval_type not in ['client', 'admin']:
        raise HTTPException(
            status_code=400,
            detail="approval_type은 'client' 또는 'admin'이어야 합니다"
        )
    
    # 3. 영상 조회
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 4. 권한 확인
    if approval_request.approval_type == 'client':
        # 기업 고객: 같은 회사만
        if video.company_id != user_info["company_id"]:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 상태 확인 (completed만 승인 가능)
        if video.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"승인할 수 없는 상태입니다. 현재 상태: {video.status}"
            )
        
        # 승인 처리
        video = approve_video(db, video_id, 'client', user_info["account_id"])
        message = "영상이 승인되었습니다. Admin 검토 대기 중입니다."
        
    elif approval_request.approval_type == 'admin':
        # Admin: 모든 영상 승인 가능 (TODO: admin 권한 체크)
        # 현재는 account_type으로만 체크
        if user_info.get("account_type") != 'admin':
            raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
        
        # 상태 확인 (client_approved만 승인 가능)
        if video.status != 'client_approved':
            raise HTTPException(
                status_code=400,
                detail=f"승인할 수 없는 상태입니다. 현재 상태: {video.status}"
            )
        
        # 승인 처리
        video = approve_video(db, video_id, 'admin', user_info["account_id"])
        message = "영상이 최종 승인되었습니다. 유튜브 게시가 가능합니다."
    
    # 5. 응답 반환
    return VideoApprovalResponse(
        video_id=video.video_id,
        status=video.status,
        message=message,
        updated_at=video.updated_at.isoformat()
    )


# ============================================
# 3. 영상 거부
# ============================================
@router.post("/{video_id}/reject", response_model=VideoApprovalResponse)
async def reject_video_endpoint(
    video_id: int,
    rejection_request: VideoRejectionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 거부
    
    **거부 타입:**
    - `client`: 기업 고객 거부 (completed → client_rejected)
    - `admin`: Admin 거부 (client_approved → admin_rejected)
    
    **권한:**
    - client: 같은 회사의 영상만 거부 가능
    - admin: 모든 영상 거부 가능 (TODO: admin 권한 체크)
    
    **거부 사유:**
    - 필수 입력
    - rejection_reason 필드에 저장
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 거부 타입 검증
    if rejection_request.rejection_type not in ['client', 'admin']:
        raise HTTPException(
            status_code=400,
            detail="rejection_type은 'client' 또는 'admin'이어야 합니다"
        )
    
    # 3. 영상 조회
    video = get_video_by_id(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 4. 권한 확인
    if rejection_request.rejection_type == 'client':
        # 기업 고객: 같은 회사만
        if video.company_id != user_info["company_id"]:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
        
        # 상태 확인 (completed만 거부 가능)
        if video.status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"거부할 수 없는 상태입니다. 현재 상태: {video.status}"
            )
        
        # 거부 처리
        video = reject_video(
            db,
            video_id,
            'client',
            rejection_request.rejection_reason,
            user_info["account_id"]
        )
        message = "영상이 거부되었습니다."
        
    elif rejection_request.rejection_type == 'admin':
        # Admin: 모든 영상 거부 가능 (TODO: admin 권한 체크)
        if user_info.get("account_type") != 'admin':
            raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
        
        # 상태 확인 (client_approved만 거부 가능)
        if video.status != 'client_approved':
            raise HTTPException(
                status_code=400,
                detail=f"거부할 수 없는 상태입니다. 현재 상태: {video.status}"
            )
        
        # 거부 처리
        video = reject_video(
            db,
            video_id,
            'admin',
            rejection_request.rejection_reason,
            user_info["account_id"]
        )
        message = "영상이 거부되었습니다."
    
    # 5. 응답 반환
    return VideoApprovalResponse(
        video_id=video.video_id,
        status=video.status,
        message=message,
        updated_at=video.updated_at.isoformat()
    )
