"""영상 관리 엔드포인트"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session

from .common import (
    logger,
    admin_crud,
    get_db,
    Company,
    Video,
    AdRequest,
    get_presigned_url,
    check_admin_permission,
    VideoListResponse,
)

router = APIRouter()


@router.get("/videos/all", response_model=VideoListResponse)
async def get_all_videos(
    request: Request,
    company_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """전체 영상 목록 조회"""
    await check_admin_permission(request)

    videos, total_count = admin_crud.get_all_videos_filtered(
        db=db,
        company_id=company_id,
        status=status,
        offset=offset,
        limit=limit
    )

    company_ids = {v.company_id for v in videos if v.company_id}
    companies = {c.company_id: c for c in db.query(Company).filter(Company.company_id.in_(company_ids)).all()} if company_ids else {}

    video_list = []
    for video in videos:
        company = companies.get(video.company_id)

        # file_size를 MB로 변환
        file_size_mb = None
        if video.file_size_bytes:
            file_size_mb = round(video.file_size_bytes / (1024 * 1024), 2)

        video_list.append({
            'video_id': video.video_id,
            'ad_id': video.ad_id,
            'company_id': video.company_id,
            'company_name': company.company_name if company else 'Unknown',
            'title': video.title,
            'status': video.status,
            'duration_seconds': video.duration_seconds,
            'file_size_mb': file_size_mb,
            'created_at': video.created_at.isoformat(),
            'completed_at': video.completed_at.isoformat() if video.completed_at else None
        })

    return VideoListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        videos=video_list
    )


@router.get("/videos/pending")
async def get_pending_videos(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """게시 대기 영상 목록"""
    await check_admin_permission(request)

    videos, total_count = admin_crud.get_pending_videos(db, offset, limit)

    video_list = []
    for video in videos:
        video_list.append({
            'video_id': video.video_id,
            'ad_id': video.ad_id,
            'company_id': video.company_id,
            'title': video.title,
            'status': video.status,
            'video_url': get_presigned_url(video.s3_url) if video.s3_url else None,
            'created_at': video.created_at.isoformat()
        })

    return {
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'videos': video_list
    }


@router.get("/videos/{video_id}")
async def get_video_detail(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)

    # video_id 또는 ad_id로 조회 (프론트엔드 호환)
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        video = db.query(Video).filter(Video.ad_id == video_id).first()
    if not video:
        raise HTTPException(404, detail="영상을 찾을 수 없습니다")

    ad_request = db.query(AdRequest).filter(AdRequest.ad_id == video.ad_id).first()
    company = db.query(Company).filter(Company.company_id == video.company_id).first()

    return {
        'id': str(video.video_id),
        'video_id': video.video_id,
        'ad_id': video.ad_id,
        'title': video.title,
        'status': video.status,
        'companyName': company.company_name if company else None,
        'productCategory': ad_request.item_category if ad_request else None,
        'productHighlight': ad_request.item_description if ad_request else None,  # item_keymessage -> item_description
        'views': 0,
        'createdAt': video.created_at.isoformat(),
        'duration_seconds': video.duration_seconds,
        'videoUrl': get_presigned_url(video.s3_url) if video.s3_url else None,
        'thumbnail_url': video.thumbnail_url,
        'completed_at': video.completed_at.isoformat() if video.completed_at else None
    }


@router.get("/videos/{video_id}/analytics")
async def get_video_analytics(
    video_id: int,
    request: Request,
    snapshot_type: Optional[str] = Query(None, description="daily, monthly, realtime"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """영상 성능 지표 조회"""
    await check_admin_permission(request)

    # 영상 존재 확인
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    # 성능 지표 조회
    metrics = admin_crud.get_video_performance_metrics(
        db=db,
        video_id=video_id,
        snapshot_type=snapshot_type,
        limit=limit
    )

    metric_list = []
    for metric in metrics:
        metric_list.append({
            'metric_id': metric.metric_id,
            'captured_at': metric.captured_at.isoformat(),
            'snapshot_type': metric.snapshot_type,
            'views': metric.views,
            'likes': metric.likes,
            'dislikes': metric.dislikes,
            'comments': metric.comments,
            'shares': metric.shares,
            'watch_time_seconds': metric.watch_time_seconds,
            'average_view_duration': metric.average_view_duration,
            'audience_retention_rate': metric.audience_retention_rate,
            'engagement_rate': metric.engagement_rate,
            'subscribers_gained': metric.subscribers_gained
        })

    return {
        'video_id': video_id,
        'yt_video_id': video.yt_video_id if hasattr(video, 'yt_video_id') else None,
        'total_metrics': len(metric_list),
        'metrics': metric_list
    }


@router.post("/videos/{video_id}/analytics/collect")
async def collect_video_analytics(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 성능 지표 수집 (YouTube API에서 조회)"""
    await check_admin_permission(request)

    # 영상 존재 확인
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    # YouTube 게시 정보 조회
    from app.models.youtube import AdminVideoPost, AdminYoutubeChannel

    post = db.query(AdminVideoPost).filter(
        AdminVideoPost.video_id == video_id
    ).first()

    if not post or not post.yt_video_id:
        raise HTTPException(status_code=400, detail="YouTube에 게시되지 않은 영상입니다")

    # YouTube 채널 정보 조회
    channel = db.query(AdminYoutubeChannel).filter(
        AdminYoutubeChannel.channel_id == post.channel_id
    ).first()

    if not channel:
        raise HTTPException(status_code=404, detail="YouTube 채널을 찾을 수 없습니다")

    try:
        # YouTube 서비스 초기화
        from app.services.youtube_service import YouTubeService

        youtube_service = YouTubeService(
            access_token=channel.access_token,
            refresh_token=channel.refresh_token,
            token_expiry=channel.token_expires_at
        )

        # 기본 통계 조회
        analytics_result = youtube_service.get_video_analytics(post.yt_video_id)

        if not analytics_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"YouTube 통계 조회 실패: {analytics_result['error']}"
            )

        # 성능 지표 저장
        metric = admin_crud.save_performance_metrics(
            db=db,
            video_id=video_id,
            post_id=post.post_id,
            snapshot_type='daily',
            views=analytics_result.get('views', 0),
            likes=analytics_result.get('likes', 0),
            dislikes=analytics_result.get('dislikes', 0),
            comments=analytics_result.get('comments', 0),
            shares=analytics_result.get('favorites', 0)
        )

        return {
            'success': True,
            'metric_id': metric.metric_id,
            'message': '성능 지표가 수집되었습니다',
            'data': {
                'views': metric.views,
                'likes': metric.likes,
                'comments': metric.comments,
                'captured_at': metric.captured_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"성능 지표 수집 중 오류: {str(e)}"
        )
