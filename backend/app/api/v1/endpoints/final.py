"""
영상 다운로드 및 승인 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.video import (
    VideoDownloadResponse,
    VideoApprovalRequest,
    VideoRejectionRequest,
    VideoApprovalResponse,
    VideoPreviewResponse,
    VideoReviseRequest,
    VideoReviseResponse
)
from app.crud import final as final_crud
from app.core.security import get_current_user
from app.db.session import get_db
from app.core.config import settings

# S3 서비스 import (Mock 모드 지원)
if settings.MOCK_MODE:
    from scripts.generation.s3_handler_mock import generate_presigned_url
else:
    from app.services.s3_service import generate_presigned_url

from app.services.ai_pipeline_factory import AIPipelineClient

router = APIRouter()


@router.get("/{video_id}/download", response_model=VideoDownloadResponse)
async def get_video_download_link(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 다운로드 링크 생성"""
    user_info = await get_current_user(request)
    
    video = final_crud.get_video_for_download(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 권한 확인 (Admin이 아닌 경우)
    if user_info.get("account_type") != 'admin':
        if video.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # S3 Pre-signed URL 생성 (7일 유효)
    try:
        download_url = generate_presigned_url(
            s3_url=video.s3_url,
            expiration=604800  # 7일 (초 단위)
        )
        expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"다운로드 링크 생성 실패: {str(e)}"
        )
    
    return VideoDownloadResponse(
        video_id=video_id,
        download_url=download_url,
        expires_at=expires_at,
        file_size=video.file_size_bytes,
        format='mp4'
    )


@router.get("/{video_id}/preview", response_model=VideoPreviewResponse)
async def get_video_preview_link(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 미리보기 링크 생성 (승인 전)"""
    user_info = await get_current_user(request)
    
    video = final_crud.get_video_for_download(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 권한 확인 (Admin이 아닌 경우)
    if user_info.get("account_type") != 'admin':
        if video.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # S3 Pre-signed URL 생성 (1시간 유효)
    try:
        preview_url = generate_presigned_url(
            s3_url=video.s3_url,
            expiration=3600  # 1시간 (초 단위)
        )
        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"미리보기 링크 생성 실패: {str(e)}"
        )
    
    return VideoPreviewResponse(
        video_id=video_id,
        preview_url=preview_url,
        expires_at=expires_at,
        duration_seconds=video.duration_seconds,
        thumbnail_url=video.thumbnail_url
    )


@router.post("/{video_id}/approve", response_model=VideoApprovalResponse)
async def approve_video(
    video_id: int,
    approval_request: VideoApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 승인"""
    user_info = await get_current_user(request)
    
    video = final_crud.get_video_for_approval(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 권한 확인
    if video.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 영상 승인 처리
    updated_video = final_crud.approve_video(
        db=db,
        video_id=video_id,
        approved_by=user_info["account_id"],
        feedback=approval_request.feedback
    )
    
    return VideoApprovalResponse(
        video_id=video_id,
        status=updated_video.status,
        message='영상이 승인되었습니다'
    )


@router.post("/{video_id}/reject", response_model=VideoApprovalResponse)
async def reject_video(
    video_id: int,
    rejection_request: VideoRejectionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 거부"""
    user_info = await get_current_user(request)
    
    video = final_crud.get_video_for_approval(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 권한 확인
    if video.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 영상 거부 처리
    updated_video = final_crud.reject_video(
        db=db,
        video_id=video_id,
        rejected_by=user_info["account_id"],
        rejection_reason=rejection_request.reason,
        feedback=rejection_request.feedback
    )
    
    return VideoApprovalResponse(
        video_id=video_id,
        status=updated_video.status,
        message='영상이 거부되었습니다'
    )


@router.post("/{video_id}/revise", response_model=VideoReviseResponse)
async def revise_video(
    video_id: int,
    revise_request: VideoReviseRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 수정 요청 (재생성)"""
    user_info = await get_current_user(request)
    
    video = final_crud.get_video_for_approval(db, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")
    
    # 권한 확인
    if video.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    try:
        # AI 파이프라인에 영상 재생성 요청
        ai_client = AIPipelineClient()
        
        # 수정 요청 내용을 AI 파이프라인에 전달
        result = await ai_client.regenerate_video(
            video_id=video_id,
            ad_id=video.ad_id,
            revision_notes=revise_request.revision_notes,
            feedback=revise_request.feedback,
            company_id=user_info["company_id"]
        )
        
        # 영상 상태 업데이트 (재생성 중)
        video.status = 'processing'  # regenerating 대신 processing 사용
        video.updated_at = datetime.utcnow()
        
        # 수정 요청 내용 저장 (review_result JSONB)
        revision_data = {
            'revision_notes': revise_request.revision_notes,
            'feedback': revise_request.feedback,
            'requested_by': user_info["account_id"],
            'requested_at': datetime.utcnow().isoformat()
        }
        
        if video.review_result:
            current_reviews = video.review_result
            if not isinstance(current_reviews, dict):
                current_reviews = {'history': []}
            if 'history' not in current_reviews:
                current_reviews['history'] = []
            current_reviews['history'].append(revision_data)
            current_reviews['latest'] = revision_data
            video.review_result = current_reviews
        else:
            video.review_result = {
                'latest': revision_data,
                'history': [revision_data]
            }
        
        db.commit()
        db.refresh(video)
        
        return VideoReviseResponse(
            video_id=video_id,
            status='processing',  # regenerating 대신 processing
            message='영상 재생성이 요청되었습니다'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"영상 재생성 요청 실패: {str(e)}"
        )
