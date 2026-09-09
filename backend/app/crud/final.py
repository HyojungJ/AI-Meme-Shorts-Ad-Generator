"""
영상 다운로드 및 승인 관련 CRUD 로직
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

from app.models.video import Video
from app.models.ad_request import AdRequest
from app.models.workflow import WorkflowExecution


def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    """영상 조회"""
    return db.query(Video).filter(Video.video_id == video_id).first()


def get_video_with_ad_info(db: Session, video_id: int) -> Optional[Dict]:
    """영상과 광고 요청 정보 함께 조회"""
    video = get_video_by_id(db, video_id)
    if not video:
        return None
    
    ad_request = None
    if video.ad_id:
        ad_request = db.query(AdRequest).filter(AdRequest.ad_id == video.ad_id).first()
    
    return {
        'video': video,
        'ad_request': ad_request
    }


def get_video_for_download(db: Session, video_id: int) -> Optional[Video]:
    """다운로드용 영상 조회"""
    return get_video_by_id(db, video_id)


def get_video_for_approval(db: Session, video_id: int) -> Optional[Video]:
    """승인용 영상 조회"""
    return get_video_by_id(db, video_id)


def _sync_workflow_status(db: Session, ad_id: int, new_status: str, new_stage: str):
    """video 상태 변경 시 workflow_execution, ad_request 상태도 동기화"""
    # workflow_execution 업데이트
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.ad_id == ad_id
    ).order_by(WorkflowExecution.created_at.desc()).first()
    if workflow:
        workflow.status = new_status
        workflow.current_stage = new_stage
        logger.info("워크플로우 상태 동기화: ad_id=%d, status=%s, stage=%s", ad_id, new_status, new_stage)

    # ad_request 업데이트
    ad_request = db.query(AdRequest).filter(AdRequest.ad_id == ad_id).first()
    if ad_request:
        ad_request.status = new_stage
        ad_request.updated_at = datetime.utcnow()


def approve_video(
    db: Session,
    video_id: int,
    approved_by: int,
    feedback: Optional[str] = None
) -> Optional[Video]:
    """영상 승인 (클라이언트)"""
    video = get_video_by_id(db, video_id)
    if not video:
        return None
    
    video.status = 'client_approved'
    video.updated_at = datetime.utcnow()
    
    # workflow_execution, ad_request 상태 동기화
    if video.ad_id:
        _sync_workflow_status(db, video.ad_id, 'pending_approval', 'client_approved')
    
    # TODO: feedback 저장 로직 추가
    
    db.commit()
    db.refresh(video)
    
    logger.info("영상 승인: video_id=%d, approved_by=%d", video_id, approved_by)
    return video


def reject_video(
    db: Session,
    video_id: int,
    rejected_by: int,
    rejection_reason: str,
    feedback: Optional[str] = None
) -> Optional[Video]:
    """영상 거부 (클라이언트)"""
    video = get_video_by_id(db, video_id)
    if not video:
        return None
    
    video.status = 'client_rejected'
    video.rejection_reason = rejection_reason
    video.rejected_by_account_id = rejected_by
    video.rejected_at = datetime.utcnow()
    video.updated_at = datetime.utcnow()
    
    # workflow_execution, ad_request 상태 동기화
    if video.ad_id:
        _sync_workflow_status(db, video.ad_id, 'rejected', 'client_rejected')
    
    # TODO: feedback 저장 로직 추가
    
    db.commit()
    db.refresh(video)
    
    logger.info("영상 거부: video_id=%d, rejected_by=%d", video_id, rejected_by)
    return video
