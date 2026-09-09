"""
Admin 관련 CRUD 로직
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import uuid

from app.models.video import Video
from app.models.workflow import WorkflowExecution
from app.models.youtube import AdminVideoPost
from app.models.company import Company


def get_all_videos_filtered(
    db: Session,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 20
):
    """전체 영상 목록 조회 (필터링)"""
    query = db.query(Video)
    
    if company_id:
        query = query.filter(Video.company_id == company_id)
    if status:
        query = query.filter(Video.status == status)
    if date_from:
        query = query.filter(Video.created_at >= date_from)
    if date_to:
        query = query.filter(Video.created_at <= date_to)
    
    # 정렬
    if sort_by == 'created_at':
        query = query.order_by(
            Video.created_at.desc() if order == 'desc' else Video.created_at.asc()
        )
    elif sort_by == 'completed_at':
        query = query.order_by(
            Video.completed_at.desc() if order == 'desc' else Video.completed_at.asc()
        )
    
    total_count = query.count()
    videos = query.offset(offset).limit(limit).all()
    
    return videos, total_count


def get_video_with_company(db: Session, video_id: int):
    """영상과 회사 정보 함께 조회 (video_id 또는 ad_id로 조회)"""
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        video = db.query(Video).filter(Video.ad_id == video_id).first()
    if not video:
        return None
    
    company = db.query(Company).filter(Company.company_id == video.company_id).first()
    
    return {
        'video': video,
        'company': company
    }


def get_pending_videos(db: Session, offset: int = 0, limit: int = 20):
    """게시 대기 영상 목록"""
    query = db.query(Video).filter(Video.status == 'client_approved')
    
    total_count = query.count()
    videos = query.offset(offset).limit(limit).all()
    
    return videos, total_count


def create_video_post(
    db: Session,
    video_id: int,
    channel_id: int,
    yt_title: str,
    yt_description: Optional[str] = None,
    scheduled_at: Optional[datetime] = None
):
    """영상 게시 레코드 생성"""
    post = AdminVideoPost(
        video_id=video_id,
        channel_id=channel_id,
        yt_title=yt_title,
        yt_description=yt_description,
        scheduled_at=scheduled_at,
        post_status='pending'
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_workflows_by_filter(db: Session, status_filter: str = 'all', offset: int = 0, limit: int = 20):
    """워크플로우 목록 조회 (status_filter별 분기)"""
    query = db.query(WorkflowExecution)

    if status_filter == 'active':
        query = query.filter(WorkflowExecution.status.in_([
            'created', 'processing', 'generating_character',
            'generating_scenario', 'generating_video', 'pending_approval',
        ]))
    elif status_filter == 'failed':
        query = query.filter(WorkflowExecution.status == 'failed')
    elif status_filter == 'completed':
        query = query.filter(WorkflowExecution.status == 'completed')
    # 'all' → 필터 없음

    total_count = query.count()
    workflows = query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(limit).all()

    return workflows, total_count


def get_failed_workflows(db: Session, offset: int = 0, limit: int = 20):
    """실패한 워크플로우 목록"""
    query = db.query(WorkflowExecution).filter(WorkflowExecution.status == 'failed')
    
    total_count = query.count()
    workflows = query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(limit).all()
    
    return workflows, total_count


def get_workflow_with_stages(db: Session, execution_id: str):
    """워크플로우와 단계 정보 조회"""
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        return None
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == exec_uuid
    ).first()
    
    if not workflow:
        return None
    
    # TODO: WorkflowStage 조회 추가
    
    return {
        'workflow': workflow,
        'stages': []
    }


def retry_workflow(db: Session, execution_id: str):
    """워크플로우 재시도"""
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        return None
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == exec_uuid
    ).first()
    
    if workflow:
        workflow.status = 'processing'
        workflow.retry_count += 1
        workflow.error_message = None
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
    
    return workflow


def cancel_workflow(db: Session, execution_id: str):
    """워크플로우 취소"""
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        return None
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == exec_uuid
    ).first()
    
    if workflow:
        workflow.status = 'cancelled'
        workflow.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workflow)
    
    return workflow


def save_performance_metrics(
    db: Session,
    video_id: Optional[int] = None,
    post_id: Optional[int] = None,
    snapshot_type: str = 'daily',
    views: int = 0,
    likes: int = 0,
    dislikes: int = 0,
    comments: int = 0,
    shares: int = 0,
    watch_time_seconds: int = 0,
    average_view_duration: Optional[float] = None,
    audience_retention_rate: Optional[float] = None,
    engagement_rate: Optional[float] = None,
    subscribers_gained: int = 0
):
    """성능 지표 저장"""
    from app.models.analytics import PerformanceMetric
    
    metric = PerformanceMetric(
        video_id=video_id,
        post_id=post_id,
        captured_at=datetime.utcnow(),
        snapshot_type=snapshot_type,
        views=views,
        likes=likes,
        dislikes=dislikes,
        comments=comments,
        shares=shares,
        watch_time_seconds=watch_time_seconds,
        average_view_duration=average_view_duration,
        audience_retention_rate=audience_retention_rate,
        engagement_rate=engagement_rate,
        subscribers_gained=subscribers_gained
    )
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


def get_video_performance_metrics(
    db: Session,
    video_id: int,
    snapshot_type: Optional[str] = None,
    limit: int = 30
):
    """영상 성능 지표 조회"""
    from app.models.analytics import PerformanceMetric
    
    query = db.query(PerformanceMetric).filter(PerformanceMetric.video_id == video_id)
    
    if snapshot_type:
        query = query.filter(PerformanceMetric.snapshot_type == snapshot_type)
    
    metrics = query.order_by(PerformanceMetric.captured_at.desc()).limit(limit).all()
    
    return metrics


def get_post_performance_metrics(
    db: Session,
    post_id: int,
    snapshot_type: Optional[str] = None,
    limit: int = 30
):
    """게시 성능 지표 조회"""
    from app.models.analytics import PerformanceMetric
    
    query = db.query(PerformanceMetric).filter(PerformanceMetric.post_id == post_id)
    
    if snapshot_type:
        query = query.filter(PerformanceMetric.snapshot_type == snapshot_type)
    
    metrics = query.order_by(PerformanceMetric.captured_at.desc()).limit(limit).all()
    
    return metrics
