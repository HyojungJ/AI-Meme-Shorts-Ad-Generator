"""
클라이언트용 성과 분석 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import Optional
from datetime import datetime, timedelta

from app.core.security import check_client_permission
from app.core.utils import parse_date_range
from app.db.session import get_db
from app.crud.analytics import get_latest_metrics_by_video
from app.models.video import Video
from app.models.workflow import WorkflowExecution
from app.models.youtube import AdminVideoPost
from app.models.analytics import PerformanceMetric
from app.models.ad_request import AdRequest
from app.models.meme import Meme

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_company_video_ids(db: Session, company_id: int) -> set:
    rows = db.query(Video.video_id).filter(Video.company_id == company_id).all()
    return {v[0] for v in rows}


@router.get("/dashboard")
async def get_my_dashboard(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """내 회사 성과 대시보드"""
    user_info = await check_client_permission(request)
    company_id = user_info["company_id"]

    date_from_dt, date_to_dt = parse_date_range(date_from, date_to)
    if not date_from_dt:
        date_from_dt = datetime.utcnow() - timedelta(days=30)
    if not date_to_dt:
        date_to_dt = datetime.utcnow()

    company_video_ids = _get_company_video_ids(db, company_id)
    latest_by_video = get_latest_metrics_by_video(db, company_video_ids)
    latest_metrics = list(latest_by_video.values())

    # 프로젝트 통계
    total_projects = db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.created_at >= date_from_dt,
        WorkflowExecution.created_at <= date_to_dt
    ).count()

    completed_projects = db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.status == 'completed',
        WorkflowExecution.created_at >= date_from_dt,
        WorkflowExecution.created_at <= date_to_dt
    ).count()

    processing_projects = db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.status.in_(['processing', 'pending_approval', 'generating_character']),
        WorkflowExecution.created_at >= date_from_dt,
        WorkflowExecution.created_at <= date_to_dt
    ).count()

    total_videos = db.query(Video).filter(
        Video.company_id == company_id,
        Video.created_at >= date_from_dt,
        Video.created_at <= date_to_dt
    ).count()

    published_videos = db.query(Video).join(AdminVideoPost).filter(
        Video.company_id == company_id,
        AdminVideoPost.post_status == 'published',
        Video.created_at >= date_from_dt,
        Video.created_at <= date_to_dt
    ).count()

    total_cost = db.query(func.sum(WorkflowExecution.total_cost_usd)).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.created_at >= date_from_dt,
        WorkflowExecution.created_at <= date_to_dt
    ).scalar() or 0

    total_views = sum(m.views or 0 for m in latest_metrics)
    total_likes = sum(m.likes or 0 for m in latest_metrics)
    total_comments = sum(m.comments or 0 for m in latest_metrics)

    avg_engagement_rate = 0
    if latest_metrics:
        engagement_rates = [float(m.engagement_rate) for m in latest_metrics if m.engagement_rate]
        avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0

    # 일별 집계 (조회수 + 참여율)
    all_metrics = db.query(PerformanceMetric).all()
    daily_data = {}
    for metric in all_metrics:
        video_id = metric.video_id
        if not video_id and metric.post_id:
            post = db.query(AdminVideoPost).filter(AdminVideoPost.post_id == metric.post_id).first()
            if post:
                video_id = post.video_id
        if not video_id or video_id not in company_video_ids:
            continue
        if metric.captured_at < date_from_dt or metric.captured_at > date_to_dt:
            continue
        date_key = metric.captured_at.date()
        if date_key not in daily_data:
            daily_data[date_key] = {}
        if video_id not in daily_data[date_key]:
            daily_data[date_key][video_id] = metric
        elif metric.captured_at > daily_data[date_key][video_id].captured_at:
            daily_data[date_key][video_id] = metric

    views_timeline = []
    engagement_timeline = []
    for date_key in sorted(daily_data.keys()):
        views_timeline.append({
            'date': str(date_key),
            'views': sum(m.views or 0 for m in daily_data[date_key].values())
        })
        rates = [float(m.engagement_rate) for m in daily_data[date_key].values() if m.engagement_rate]
        engagement_timeline.append({
            'date': str(date_key),
            'engagement_rate': sum(rates) / len(rates) if rates else 0
        })

    # 최근 영상 목록
    recent_videos = db.query(Video).filter(
        Video.company_id == company_id
    ).order_by(Video.created_at.desc()).limit(5).all()

    video_list = []
    for video in recent_videos:
        latest_metric = latest_by_video.get(video.video_id)
        video_list.append({
            'video_id': video.video_id,
            'ad_id': video.ad_id,
            'title': video.title,
            'status': video.status,
            'created_at': video.created_at.isoformat(),
            'views': latest_metric.views if latest_metric else 0,
            'likes': latest_metric.likes if latest_metric else 0,
            'engagement_rate': float(latest_metric.engagement_rate) if latest_metric and latest_metric.engagement_rate else 0
        })

    # 상태별 프로젝트 분포
    status_distribution = db.query(
        WorkflowExecution.status,
        func.count(WorkflowExecution.execution_id).label('count')
    ).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.created_at >= date_from_dt,
        WorkflowExecution.created_at <= date_to_dt
    ).group_by(WorkflowExecution.status).all()

    status_dist = {status: count for status, count in status_distribution}

    return {
        'period': {
            'from': date_from_dt.date().isoformat(),
            'to': date_to_dt.date().isoformat()
        },
        'summary': {
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'processing_projects': processing_projects,
            'total_videos': total_videos,
            'published_videos': published_videos,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'avg_engagement_rate': round(avg_engagement_rate, 2),
            'total_cost_usd': float(total_cost),
            'completion_rate': round(completed_projects / total_projects * 100, 1) if total_projects > 0 else 0
        },
        'status_distribution': status_dist,
        'views_timeline': views_timeline,
        'engagement_timeline': engagement_timeline,
        'recent_videos': video_list
    }


@router.get("/videos/{video_id}")
async def get_video_performance(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """특정 영상 성과 조회"""
    user_info = await check_client_permission(request)

    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    if video.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 성과 데이터 조회 (최신순)
    metrics = db.query(PerformanceMetric).filter(
        PerformanceMetric.video_id == video_id
    ).order_by(PerformanceMetric.captured_at.desc()).limit(30).all()

    # 최신 성과
    latest_metric = metrics[0] if metrics else None

    # 시계열 데이터
    timeline = []
    for metric in reversed(metrics):
        timeline.append({
            'captured_at': metric.captured_at.isoformat(),
            'views': metric.views,
            'likes': metric.likes,
            'comments': metric.comments,
            'shares': metric.shares,
            'engagement_rate': float(metric.engagement_rate) if metric.engagement_rate else 0
        })

    # 시간대별 조회수 집계 (captured_at의 시간대별로 그룹화)
    hourly_views = db.query(
        extract('hour', PerformanceMetric.captured_at).label('hour'),
        func.avg(PerformanceMetric.views).label('avg_views')
    ).filter(
        PerformanceMetric.video_id == video_id
    ).group_by(
        extract('hour', PerformanceMetric.captured_at)
    ).all()

    # 24시간 배열로 변환 (데이터 없는 시간대는 0)
    hourly_data = [0] * 24
    for hour, avg_views in hourly_views:
        if hour is not None and 0 <= hour < 24:
            hourly_data[int(hour)] = int(avg_views) if avg_views else 0

    hourly_views_list = [{'hour': h, 'views': hourly_data[h]} for h in range(24)]

    return {
        'video_id': video.video_id,
        'title': video.title,
        'status': video.status,
        'created_at': video.created_at.isoformat(),
        'duration_seconds': video.duration_seconds,
        'latest_performance': {
            'views': latest_metric.views if latest_metric else 0,
            'likes': latest_metric.likes if latest_metric else 0,
            'dislikes': latest_metric.dislikes if latest_metric else 0,
            'comments': latest_metric.comments if latest_metric else 0,
            'shares': latest_metric.shares if latest_metric else 0,
            'engagement_rate': float(latest_metric.engagement_rate) if latest_metric and latest_metric.engagement_rate else 0,
            'watch_time_seconds': latest_metric.watch_time_seconds if latest_metric else 0,
            'average_view_duration': float(latest_metric.average_view_duration) if latest_metric and latest_metric.average_view_duration else 0,
            'captured_at': latest_metric.captured_at.isoformat() if latest_metric else None
        },
        'timeline': timeline,
        'hourly_views': hourly_views_list
    }


@router.get("/summary")
async def get_my_summary(
    request: Request,
    db: Session = Depends(get_db)
):
    """내 회사 요약 통계 (간단 버전)"""
    user_info = await check_client_permission(request)
    company_id = user_info["company_id"]

    # 전체 통계 (기간 제한 없음)
    total_projects = db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id
    ).count()

    completed_projects = db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.status == 'completed'
    ).count()

    total_videos = db.query(Video).filter(
        Video.company_id == company_id
    ).count()

    total_cost = db.query(func.sum(WorkflowExecution.total_cost_usd)).filter(
        WorkflowExecution.company_id == company_id
    ).scalar() or 0

    return {
        'total_projects': total_projects,
        'completed_projects': completed_projects,
        'total_videos': total_videos,
        'total_cost_usd': float(total_cost)
    }


@router.get("/memes")
async def get_my_meme_performance(
    request: Request,
    db: Session = Depends(get_db)
):
    """내 회사의 밈별 성과 분석"""
    user_info = await check_client_permission(request)
    company_id = user_info["company_id"]

    company_video_ids = _get_company_video_ids(db, company_id)
    latest_by_video = get_latest_metrics_by_video(db, company_video_ids)

    # 내 회사의 밈별 성과 집계
    meme_stats = {}
    for video_id, metric in latest_by_video.items():
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if video and video.ad_id:
            ad_request = db.query(AdRequest).filter(AdRequest.ad_id == video.ad_id).first()
            if ad_request and ad_request.meme_id:
                meme = db.query(Meme).filter(Meme.meme_id == ad_request.meme_id).first()
                if meme:
                    meme_key = (meme.meme_id, meme.meme_name, meme.meme_type)
                    if meme_key not in meme_stats:
                        meme_stats[meme_key] = {
                            'videos': [],
                            'total_views': 0,
                        }
                    meme_stats[meme_key]['videos'].append(video_id)
                    meme_stats[meme_key]['total_views'] += (metric.views or 0)

    # 결과 생성
    items = []
    for (meme_id, meme_name, meme_type), stats in meme_stats.items():
        video_count = len(stats['videos'])
        total_views = stats['total_views']
        avg_views = total_views // video_count if video_count > 0 else 0

        items.append({
            'meme_id': meme_id,
            'meme_name': meme_name,
            'meme_type': meme_type,
            'video_count': video_count,
            'total_views': total_views,
            'avg_views': avg_views,
        })

    # 평균 조회수 기준 정렬
    items.sort(key=lambda x: x['avg_views'], reverse=True)

    return items


@router.get("/categories")
async def get_my_category_performance(
    request: Request,
    db: Session = Depends(get_db)
):
    """내 회사의 카테고리별 성과 분석"""
    user_info = await check_client_permission(request)
    company_id = user_info["company_id"]

    company_video_ids = _get_company_video_ids(db, company_id)
    latest_by_video = get_latest_metrics_by_video(db, company_video_ids)

    # 내 회사의 카테고리별 성과 집계
    category_stats = {}
    for video_id, metric in latest_by_video.items():
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if video and video.ad_id:
            ad_request = db.query(AdRequest).filter(AdRequest.ad_id == video.ad_id).first()
            if ad_request and ad_request.item_category:
                category = ad_request.item_category

                if category not in category_stats:
                    category_stats[category] = {
                        'videos': [],
                        'total_views': 0,
                    }

                views = metric.views or 0
                category_stats[category]['videos'].append(video_id)
                category_stats[category]['total_views'] += views

    # 결과 생성
    items = []
    for category, stats in category_stats.items():
        video_count = len(stats['videos'])
        total_views = stats['total_views']
        avg_views = total_views // video_count if video_count > 0 else 0

        items.append({
            'category': category,
            'video_count': video_count,
            'total_views': total_views,
            'avg_views': avg_views,
        })

    # 평균 조회수 기준 정렬
    items.sort(key=lambda x: x['avg_views'], reverse=True)

    return items


@router.get("/trends")
async def get_my_trends(
    request: Request,
    db: Session = Depends(get_db)
):
    """내 회사의 조회수 추이"""
    user_info = await check_client_permission(request)
    company_id = user_info["company_id"]

    date_to = datetime.utcnow()
    date_from = date_to - timedelta(days=30)

    all_metrics = db.query(PerformanceMetric).filter(
        PerformanceMetric.captured_at >= date_from,
        PerformanceMetric.captured_at <= date_to
    ).all()

    company_video_ids = _get_company_video_ids(db, company_id)

    daily_data = {}
    for metric in all_metrics:
        video_id = metric.video_id
        if not video_id and metric.post_id:
            post = db.query(AdminVideoPost).filter(AdminVideoPost.post_id == metric.post_id).first()
            if post:
                video_id = post.video_id
        if not video_id or video_id not in company_video_ids:
            continue

        date_key = metric.captured_at.date()
        if date_key not in daily_data:
            daily_data[date_key] = {}
        if video_id not in daily_data[date_key]:
            daily_data[date_key][video_id] = metric
        elif metric.captured_at > daily_data[date_key][video_id].captured_at:
            daily_data[date_key][video_id] = metric

    data_points = []
    for date_key in sorted(daily_data.keys()):
        data_points.append({
            'date': str(date_key),
            'views': sum(m.views or 0 for m in daily_data[date_key].values())
        })

    return {
        'data': data_points,
        'insights': []
    }
