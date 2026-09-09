"""
성과 분석 관련 CRUD 로직
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any, Set
import uuid

logger = logging.getLogger(__name__)

from app.models.video import Video
from app.models.youtube import AdminVideoPost
from app.models.meme import Meme
from app.models.company import Company
from app.models.analytics import PerformanceMetric
from app.models.ad_request import AdRequest


def get_latest_metrics_by_video(
    db: Session,
    company_video_ids: Optional[Set[int]] = None,
) -> Dict[int, PerformanceMetric]:
    """각 video_id별 최신 PerformanceMetric을 반환.

    post_id -> video_id 역참조를 LEFT JOIN으로 처리한다.
    company_video_ids가 주어지면 해당 영상만 필터링한다.
    """
    # LEFT JOIN으로 post_id -> video_id 역참조를 한 번에 해결
    rows = (
        db.query(
            PerformanceMetric,
            case(
                (PerformanceMetric.video_id.isnot(None), PerformanceMetric.video_id),
                else_=AdminVideoPost.video_id,
            ).label("resolved_video_id"),
        )
        .outerjoin(
            AdminVideoPost,
            and_(
                PerformanceMetric.video_id.is_(None),
                PerformanceMetric.post_id == AdminVideoPost.post_id,
            ),
        )
        .all()
    )

    latest_by_video: Dict[int, PerformanceMetric] = {}
    for metric, resolved_video_id in rows:
        if not resolved_video_id:
            continue
        if company_video_ids is not None and resolved_video_id not in company_video_ids:
            continue
        if resolved_video_id not in latest_by_video:
            latest_by_video[resolved_video_id] = metric
        elif metric.captured_at > latest_by_video[resolved_video_id].captured_at:
            latest_by_video[resolved_video_id] = metric

    return latest_by_video


def get_dashboard_data(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """전체 대시보드 데이터 조회 - 유튜브 채널의 모든 영상 데이터"""

    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    logger.debug("get_dashboard_data 호출됨")
    logger.debug("기간: %s ~ %s", date_from.date(), date_to.date())

    latest_by_video = get_latest_metrics_by_video(db)
    latest_metrics = list(latest_by_video.values())
    logger.debug("최신 데이터만 필터링 후: %d개", len(latest_metrics))
    
    # 수동으로 집계
    total_views = sum(m.views or 0 for m in latest_metrics)
    total_likes = sum(m.likes or 0 for m in latest_metrics)
    total_comments = sum(m.comments or 0 for m in latest_metrics)
    total_shares = sum(m.shares or 0 for m in latest_metrics)
    total_videos = len(latest_metrics)
    
    logger.debug("집계 결과: total_views=%d, total_likes=%d, total_videos=%d", total_views, total_likes, total_videos)
    
    # 평균 시청 시간
    durations = [m.average_view_duration for m in latest_metrics if m.average_view_duration]
    avg_view_duration = sum(durations) / len(durations) if durations else 0.0

    # 평균 참여율 계산
    average_engagement_rate = 0.0
    if total_views > 0:
        total_engagements = total_likes + total_comments + total_shares
        average_engagement_rate = round((total_engagements / total_views) * 100, 2)

    # 이전 기간 데이터 (증감률 계산용)
    period_length = (date_to - date_from).days
    prev_from = date_from - timedelta(days=period_length)
    prev_to = date_from

    # 이전 기간의 데이터 필터링
    all_metrics = db.query(PerformanceMetric).all()
    prev_metrics_by_video = {}
    for metric in all_metrics:
        if prev_from <= metric.captured_at < prev_to:
            video_id = metric.video_id
            if video_id not in prev_metrics_by_video:
                prev_metrics_by_video[video_id] = metric
            else:
                if metric.captured_at > prev_metrics_by_video[video_id].captured_at:
                    prev_metrics_by_video[video_id] = metric
    
    prev_metrics = list(prev_metrics_by_video.values())
    
    prev_views = sum(m.views or 0 for m in prev_metrics)
    prev_likes = sum(m.likes or 0 for m in prev_metrics)
    prev_comments = sum(m.comments or 0 for m in prev_metrics)
    prev_shares = sum(m.shares or 0 for m in prev_metrics)

    # 조회수 증감률
    views_growth = 0.0
    if prev_views > 0:
        views_growth = round(((total_views - prev_views) / prev_views) * 100, 1)

    # 참여율 증감률
    prev_engagement_rate = 0.0
    if prev_views > 0:
        prev_engagements = prev_likes + prev_comments + prev_shares
        prev_engagement_rate = (prev_engagements / prev_views) * 100

    engagement_growth = 0.0
    if prev_engagement_rate > 0:
        engagement_growth = round(((average_engagement_rate - prev_engagement_rate) / prev_engagement_rate) * 100, 1)

    # 영상 수 증감률 (기간 내 생성된 영상 기준)
    current_period_videos = db.query(func.count(Video.video_id)).filter(
        Video.created_at >= date_from,
        Video.created_at <= date_to,
    ).scalar() or 0

    prev_period_videos = db.query(func.count(Video.video_id)).filter(
        Video.created_at >= prev_from,
        Video.created_at < prev_to,
    ).scalar() or 0

    video_count_growth = 0.0
    if prev_period_videos > 0:
        video_count_growth = round(((current_period_videos - prev_period_videos) / prev_period_videos) * 100, 1)

    # 회사 수
    total_companies = db.query(func.count(func.distinct(Video.company_id))).filter(
        Video.created_at >= date_from,
        Video.created_at <= date_to,
    ).scalar() or 0

    # 최근 생성 영상 Top 5 (성과 데이터 포함)
    recent_videos = db.query(Video).filter(
        Video.created_at >= date_from,
        Video.created_at <= date_to,
    ).order_by(Video.created_at.desc()).limit(5).all()

    # 회사 이름 배치 조회 (N+1 방지)
    recent_company_ids = {v.company_id for v in recent_videos if v.company_id}
    company_names = {}
    if recent_company_ids:
        for c in db.query(Company.company_id, Company.company_name).filter(Company.company_id.in_(recent_company_ids)).all():
            company_names[c.company_id] = c.company_name

    top_performing_videos = []
    for v in recent_videos:
        metric = latest_by_video.get(v.video_id)

        views = metric.views or 0 if metric else 0
        likes = metric.likes or 0 if metric else 0
        comments = metric.comments or 0 if metric else 0
        shares = metric.shares or 0 if metric else 0

        engagement_rate = 0.0
        if views > 0:
            engagement_rate = round(((likes + comments + shares) / views) * 100, 2)

        top_performing_videos.append({
            'video_id': v.video_id,
            'title': v.title,
            'company_name': company_names.get(v.company_id) or f'회사 #{v.company_id or ""}',
            'views': views,
            'engagement_rate': engagement_rate,
            'published_at': v.created_at.isoformat() if v.created_at else None,
        })

    # Video + AdRequest + Meme 배치 조회 (N+1 -> JOIN)
    video_ids = list(latest_by_video.keys())
    video_ad_meme_rows = (
        db.query(Video.video_id, AdRequest.item_category, Meme.meme_name)
        .join(AdRequest, AdRequest.ad_id == Video.ad_id)
        .outerjoin(Meme, Meme.meme_id == AdRequest.meme_id)
        .filter(Video.video_id.in_(video_ids))
        .all()
    ) if video_ids else []

    category_views: Dict[str, int] = {}
    meme_views: Dict[str, int] = {}
    for vid, item_category, meme_name in video_ad_meme_rows:
        metric = latest_by_video.get(vid)
        if not metric:
            continue
        views_val = metric.views or 0
        if item_category:
            category_views[item_category] = category_views.get(item_category, 0) + views_val
        if meme_name:
            meme_views[meme_name] = meme_views.get(meme_name, 0) + views_val

    top_category = max(category_views.items(), key=lambda x: x[1])[0] if category_views else None
    top_meme_type = max(meme_views.items(), key=lambda x: x[1])[0] if meme_views else None

    result = {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'summary': {
            'total_videos': total_videos,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'average_engagement_rate': average_engagement_rate,
            'average_view_duration_seconds': avg_view_duration,
            'total_companies': total_companies,
            'active_companies': total_companies,
        },
        'trends': {
            'views_growth': views_growth,
            'engagement_growth': engagement_growth,
            'video_count_growth': video_count_growth,
        },
        'top_performing_videos': top_performing_videos,
        'top_companies': [],
        'top_category': top_category,
        'top_meme_type': top_meme_type,
    }
    
    logger.debug("최종 응답 summary: %s", result['summary'])
    return result


def get_meme_performance(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'views',
    limit: int = 20
) -> Dict[str, Any]:
    """밈별 성과 비교"""

    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    rows = db.query(
        Meme.meme_id,
        Meme.meme_name,
        Meme.meme_type,
        func.count(Video.video_id).label('video_count'),
    ).join(AdRequest, AdRequest.meme_id == Meme.meme_id
    ).join(Video, Video.ad_id == AdRequest.ad_id
    ).filter(
        Video.created_at >= date_from,
        Video.created_at <= date_to,
    ).group_by(Meme.meme_id, Meme.meme_name, Meme.meme_type
    ).order_by(func.count(Video.video_id).desc()
    ).limit(limit).all()

    memes = []
    for row in rows:
        memes.append({
            'meme_id': row.meme_id,
            'meme_name': row.meme_name,
            'category': row.meme_type,
            'video_count': row.video_count,
            'total_views': 0,
            'average_views_per_video': 0,
            'average_engagement_rate': 0.0,
        })

    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'memes': memes,
        'total_memes_used': len(memes),
    }


def get_meme_performance_paginated(
    db: Session,
    page: int = 1,
    limit: int = 20,
    sort_by: str = 'meme_name',
    sort_order: str = 'desc',
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Tuple[List[Dict], int]:
    """페이지네이션 밈 성과 조회. Returns (items, total_count)"""

    logger.debug("get_meme_performance_paginated 호출")
    logger.debug("sort_by=%s, sort_order=%s, search=%s", sort_by, sort_order, search)

    latest_by_video = get_latest_metrics_by_video(db)

    # 밈별 성과 집계 (JOIN으로 N+1 방지)
    video_ids = list(latest_by_video.keys())
    video_meme_rows = (
        db.query(Video.video_id, Video.title, Meme.meme_id, Meme.meme_name, Meme.meme_type)
        .join(AdRequest, AdRequest.ad_id == Video.ad_id)
        .join(Meme, Meme.meme_id == AdRequest.meme_id)
        .filter(Video.video_id.in_(video_ids))
        .all()
    ) if video_ids else []

    meme_stats = {}
    for vid, vtitle, meme_id, meme_name, meme_type in video_meme_rows:
        metric = latest_by_video.get(vid)
        if not metric:
            continue
        meme_key = (meme_id, meme_name, meme_type)
        if meme_key not in meme_stats:
            meme_stats[meme_key] = {
                'videos': [],
                'total_views': 0,
                'total_engagement_rate': 0,
                'total_duration': 0,
            }

        views = metric.views or 0
        engagement_rate = metric.engagement_rate or 0
        duration = metric.average_view_duration or 0

        meme_stats[meme_key]['videos'].append({
            'video_id': vid,
            'title': vtitle,
            'views': views,
            'engagement_rate': engagement_rate
        })
        meme_stats[meme_key]['total_views'] += views
        meme_stats[meme_key]['total_engagement_rate'] += engagement_rate
        meme_stats[meme_key]['total_duration'] += duration
    
    logger.debug("집계된 밈 수: %d", len(meme_stats))
    
    # 검색 필터
    if search:
        search_lower = search.lower()
        meme_stats = {k: v for k, v in meme_stats.items() if search_lower in k[1].lower()}
    
    # 결과 생성
    items = []
    for (meme_id, meme_name, meme_type), stats in meme_stats.items():
        video_count = len(stats['videos'])
        total_views = stats['total_views']
        avg_views = total_views // video_count if video_count > 0 else 0
        avg_engagement = stats['total_engagement_rate'] / video_count if video_count > 0 else 0
        avg_duration = stats['total_duration'] / video_count if video_count > 0 else 0
        
        # 최고 성과 영상
        top_video = max(stats['videos'], key=lambda x: x['views']) if stats['videos'] else None
        
        items.append({
            'meme_id': meme_id,
            'meme_name': meme_name,
            'category': meme_type,
            'usage_count': video_count,
            'total_views': total_views,
            'average_views_per_video': avg_views,
            'average_engagement_rate': round(avg_engagement, 2),
            'average_view_duration': round(avg_duration, 2),
            'top_performing_video': {
                'video_id': top_video['video_id'],
                'title': top_video['title'],
                'views': top_video['views'],
                'engagement_rate': top_video['engagement_rate']
            } if top_video else None
        })
    
    total = len(items)
    
    # 정렬
    sort_key_map = {
        'views': 'total_views',
        'video_count': 'usage_count',
        'engagement_rate': 'average_engagement_rate',
        'meme_name': 'meme_name',
    }
    sort_key = sort_key_map.get(sort_by, 'total_views')
    items.sort(key=lambda x: x[sort_key], reverse=(sort_order == 'desc'))
    
    logger.debug("정렬 후 총 %d개 밈", len(items))
    if items:
        logger.debug("첫 번째 밈: %s, views=%d", items[0]['meme_name'], items[0]['total_views'])
    
    # 페이지네이션
    offset = (page - 1) * limit
    paginated_items = items[offset:offset + limit]
    
    return paginated_items, total


def get_category_performance(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, Any]:
    """카테고리별 성과 분석"""

    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)

    rows = db.query(
        AdRequest.item_category,
        func.count(Video.video_id).label('video_count'),
    ).join(Video, Video.ad_id == AdRequest.ad_id
    ).filter(
        Video.created_at >= date_from,
        Video.created_at <= date_to,
        AdRequest.item_category.isnot(None),
    ).group_by(AdRequest.item_category
    ).order_by(func.count(Video.video_id).desc()).all()

    categories = []
    for row in rows:
        categories.append({
            'category': row.item_category or 'unknown',
            'video_count': row.video_count,
            'total_views': 0,
            'average_engagement_rate': 0.0,
            'top_memes': [],
        })

    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'categories': categories,
    }


def get_category_performance_paginated(
    db: Session,
    page: int = 1,
    limit: int = 20,
    sort_by: str = 'video_count',
    sort_order: str = 'desc',
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Tuple[List[Dict], int]:
    """페이지네이션 제품 카테고리 성과 조회. Returns (items, total_count)"""

    logger.debug("get_category_performance_paginated 호출")
    logger.debug("sort_by=%s, sort_order=%s, search=%s", sort_by, sort_order, search)

    latest_by_video = get_latest_metrics_by_video(db)

    # 카테고리별 성과 집계 (JOIN으로 N+1 방지)
    video_ids = list(latest_by_video.keys())
    cat_rows = (
        db.query(Video.video_id, AdRequest.item_category, Meme.meme_name)
        .join(AdRequest, AdRequest.ad_id == Video.ad_id)
        .outerjoin(Meme, Meme.meme_id == AdRequest.meme_id)
        .filter(Video.video_id.in_(video_ids), AdRequest.item_category.isnot(None))
        .all()
    ) if video_ids else []

    category_stats = {}
    for vid, item_category, meme_name in cat_rows:
        metric = latest_by_video.get(vid)
        if not metric:
            continue

        if item_category not in category_stats:
            category_stats[item_category] = {
                'videos': [],
                'total_views': 0,
                'total_engagement_rate': 0,
                'memes': {}
            }

        views = metric.views or 0
        engagement_rate = metric.engagement_rate or 0

        category_stats[item_category]['videos'].append(vid)
        category_stats[item_category]['total_views'] += views
        category_stats[item_category]['total_engagement_rate'] += engagement_rate

        if meme_name:
            if meme_name not in category_stats[item_category]['memes']:
                category_stats[item_category]['memes'][meme_name] = {
                    'count': 0,
                    'total_engagement': 0
                }
            category_stats[item_category]['memes'][meme_name]['count'] += 1
            category_stats[item_category]['memes'][meme_name]['total_engagement'] += engagement_rate
    
    logger.debug("집계된 카테고리 수: %d", len(category_stats))
    
    # 검색 필터
    if search:
        search_lower = search.lower()
        category_stats = {k: v for k, v in category_stats.items() if search_lower in k.lower()}
    
    # 결과 생성
    items = []
    for category, stats in category_stats.items():
        video_count = len(stats['videos'])
        total_views = stats['total_views']
        avg_engagement = stats['total_engagement_rate'] / video_count if video_count > 0 else 0
        
        # 상위 밈 3개
        top_memes = []
        for meme_name, meme_data in sorted(stats['memes'].items(), key=lambda x: x[1]['count'], reverse=True)[:3]:
            avg_meme_engagement = meme_data['total_engagement'] / meme_data['count'] if meme_data['count'] > 0 else 0
            top_memes.append({
                'meme_name': meme_name,
                'usage_count': meme_data['count'],
                'average_engagement_rate': round(avg_meme_engagement, 2)
            })
        
        items.append({
            'category': category,
            'video_count': video_count,
            'total_views': total_views,
            'average_engagement_rate': round(avg_engagement, 2),
            'top_memes': top_memes
        })
    
    total = len(items)
    
    # 정렬
    sort_key_map = {
        'views': 'total_views',
        'video_count': 'video_count',
        'engagement_rate': 'average_engagement_rate',
    }
    sort_key = sort_key_map.get(sort_by, 'video_count')
    items.sort(key=lambda x: x[sort_key], reverse=(sort_order == 'desc'))
    
    logger.debug("정렬 후 총 %d개 카테고리", len(items))
    if items:
        logger.debug("첫 번째 카테고리: %s, views=%d", items[0]['category'], items[0]['total_views'])
    
    # 페이지네이션
    offset = (page - 1) * limit
    paginated_items = items[offset:offset + limit]
    
    return paginated_items, total


def get_trend_data(
    db: Session,
    date_from: datetime,
    date_to: datetime,
    granularity: str = 'day',
    metric: str = 'views'
) -> Dict[str, Any]:
    """시계열 성과 추이 — 일별 조회수/참여율 반환"""
    
    logger.debug("get_trend_data 호출: metric=%s, granularity=%s", metric, granularity)
    
    # PerformanceMetric 데이터를 날짜별로 집계
    # captured_at 기준으로 그룹화
    if granularity == 'day':
        trunc_func = func.date_trunc('day', PerformanceMetric.captured_at)
    elif granularity == 'week':
        trunc_func = func.date_trunc('week', PerformanceMetric.captured_at)
    else:  # month
        trunc_func = func.date_trunc('month', PerformanceMetric.captured_at)
    
    if metric == 'views':
        # 일별 조회수 합계
        rows = db.query(
            trunc_func.label('period'),
            func.sum(PerformanceMetric.views).label('value'),
        ).filter(
            PerformanceMetric.captured_at >= date_from,
            PerformanceMetric.captured_at <= date_to,
        ).group_by('period').order_by('period').all()
    elif metric == 'engagement_rate':
        # 일별 평균 참여율
        rows = db.query(
            trunc_func.label('period'),
            func.avg(PerformanceMetric.engagement_rate).label('value'),
        ).filter(
            PerformanceMetric.captured_at >= date_from,
            PerformanceMetric.captured_at <= date_to,
        ).group_by('period').order_by('period').all()
    else:  # video_count
        # 일별 영상 생성 수
        trunc_func_video = func.date_trunc(granularity, Video.created_at)
        rows = db.query(
            trunc_func_video.label('period'),
            func.count(Video.video_id).label('value'),
        ).filter(
            Video.created_at >= date_from,
            Video.created_at <= date_to,
        ).group_by('period').order_by('period').all()

    data_points = []
    for row in rows:
        value = int(row.value or 0) if metric in ['views', 'video_count'] else round(float(row.value or 0), 2)
        data_points.append({
            'date': row.period.date().isoformat() if row.period else None,
            'value': value,
            'video_count': value if metric == 'video_count' else 0,
        })
    
    logger.debug("조회된 데이터 포인트 수: %d", len(data_points))
    if data_points:
        logger.debug("첫 번째 포인트: %s", data_points[0])

    values = [dp['value'] for dp in data_points] if data_points else [0]
    total = sum(values)
    average = round(total / len(values), 1) if values else 0

    peak_dp = max(data_points, key=lambda x: x['value']) if data_points else {'date': date_from.date().isoformat(), 'value': 0}
    lowest_dp = min(data_points, key=lambda x: x['value']) if data_points else {'date': date_from.date().isoformat(), 'value': 0}

    # 인사이트 생성
    insights = []
    
    # 대시보드 데이터 가져오기 (증감률 확인용)
    dashboard_data = get_dashboard_data(db, date_from, date_to)
    views_growth = dashboard_data['trends']['views_growth']
    engagement_growth = dashboard_data['trends']['engagement_growth']
    
    # 1. 조회수 증감 인사이트
    if views_growth > 20:
        insights.append({
            'type': 'positive',
            'title': f'조회수 {views_growth}% 상승',
            'description': f'이전 기간 대비 조회수가 {views_growth}% 증가했습니다. 현재 추세가 매우 좋습니다.'
        })
    elif views_growth > 10:
        insights.append({
            'type': 'positive',
            'title': f'조회수 {views_growth}% 상승',
            'description': '조회수가 안정적으로 증가하고 있습니다.'
        })
    elif views_growth < -10:
        insights.append({
            'type': 'negative',
            'title': '조회수 감소 주의',
            'description': f'이전 기간 대비 조회수가 {abs(views_growth)}% 감소했습니다. 콘텐츠 전략 점검이 필요합니다.'
        })
    
    # 2. 참여율 인사이트
    avg_engagement = dashboard_data['summary']['average_engagement_rate']
    if avg_engagement > 5:
        insights.append({
            'type': 'positive',
            'title': f'높은 참여율 {avg_engagement}%',
            'description': '시청자들의 참여도가 매우 높습니다. 좋아요, 댓글, 공유가 활발합니다.'
        })
    elif avg_engagement < 2:
        insights.append({
            'type': 'neutral',
            'title': f'참여율 개선 필요',
            'description': f'현재 참여율이 {avg_engagement}%입니다. 시청자 참여를 유도하는 콘텐츠 개선을 권장합니다.'
        })
    
    # 3. 최고 성과 카테고리/밈
    if dashboard_data['top_category']:
        insights.append({
            'type': 'neutral',
            'title': f"'{dashboard_data['top_category']}' 카테고리 최고 성과",
            'description': '해당 카테고리의 영상이 가장 많은 조회수를 기록했습니다.'
        })
    
    if dashboard_data['top_meme_type']:
        insights.append({
            'type': 'neutral',
            'title': f"'{dashboard_data['top_meme_type']}' 밈 인기",
            'description': '해당 밈을 활용한 영상의 성과가 우수합니다.'
        })
    
    # 최대 5개만 반환
    insights = insights[:5]

    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'granularity': granularity,
        'metric': metric,
        'data_points': data_points,
        'summary': {
            'total': total,
            'average': average,
            'peak': peak_dp,
            'lowest': lowest_dp,
        },
        'insights': insights
    }


def create_export_job(
    db: Session,
    report_type: str,
    date_from: str,
    date_to: str,
    format: str,
    include_details: bool,
    filters: Optional[Dict] = None
) -> Dict[str, Any]:
    """데이터 내보내기 작업 생성"""
    
    export_id = f"exp_{uuid.uuid4().hex[:12]}"
    estimated_completion = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    
    return {
        'export_id': export_id,
        'status': 'processing',
        'estimated_completion': estimated_completion,
        'message': '데이터 내보내기가 시작되었습니다'
    }


def get_export_status(db: Session, export_id: str) -> Optional[Dict[str, Any]]:
    """내보내기 상태 조회"""
    
    return {
        'export_id': export_id,
        'status': 'processing',
        'download_url': None,
        'file_size_mb': None,
        'expires_at': None,
        'created_at': datetime.utcnow().isoformat(),
        'completed_at': None
    }


def get_company_performance(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'total_views',
    limit: int = 20
) -> Dict[str, Any]:
    """회사별 성과 비교"""
    
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    
    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'companies': [],
        'total_companies': 0
    }
