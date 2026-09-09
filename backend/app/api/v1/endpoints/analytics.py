"""
성과 분석 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.schemas.analytics import (
    DashboardResponse,
    MemePerformanceResponse,
    CategoryPerformanceResponse,
    TrendResponse,
    ExportRequest,
    ExportResponse,
    ExportStatusResponse,
    CompanyPerformanceResponse
)
from app.crud import analytics
from app.core.security import check_admin_permission
from app.core.utils import parse_date_range
from app.db.session import get_db

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    request: Request,
    date_from: Optional[str] = Query(None, description="시작 날짜 (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="종료 날짜 (ISO 8601)"),
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)
    date_from_dt, date_to_dt = parse_date_range(date_from, date_to)
    data = analytics.get_dashboard_data(db, date_from_dt, date_to_dt)
    return data


@router.get("/memes")
async def get_meme_performance(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query('views'),
    sort_order: str = Query('desc'),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)
    date_from_dt, date_to_dt = parse_date_range(date_from, date_to)

    items, total = analytics.get_meme_performance_paginated(
        db, page, limit, sort_by, sort_order, search, date_from_dt, date_to_dt
    )

    return {
        'items': items,
        'total': total,
        'page': page,
        'total_pages': (total + limit - 1) // limit
    }


@router.get("/categories")
async def get_category_performance(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query('views'),
    sort_order: str = Query('desc'),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """카테고리별 성과 분석 (페이지네이션)"""
    await check_admin_permission(request)
    date_from_dt, date_to_dt = parse_date_range(date_from, date_to)

    items, total = analytics.get_category_performance_paginated(
        db, page, limit, sort_by, sort_order, search, date_from_dt, date_to_dt
    )

    return {
        'period': {
            'from': (date_from_dt or datetime.utcnow() - timedelta(days=30)).date().isoformat(),
            'to': (date_to_dt or datetime.utcnow()).date().isoformat()
        },
        'categories': items,
        'total': total,
        'page': page,
        'total_pages': (total + limit - 1) // limit
    }


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    request: Request,
    date_from: Optional[str] = Query(None, description="시작 날짜"),
    date_to: Optional[str] = Query(None, description="종료 날짜"),
    period: Optional[str] = Query(None, description="기간 (week, month, quarter, year)"),
    granularity: str = Query('day', description="집계 단위 (day, week, month)"),
    metric: str = Query('views', description="지표 (views, engagement_rate, video_count)"),
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)

    now = datetime.utcnow()
    if period and not (date_from and date_to):
        period_days = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}
        date_from_dt = now - timedelta(days=period_days.get(period, 30))
        date_to_dt = now
    elif date_from and date_to:
        date_from_dt, date_to_dt = parse_date_range(date_from, date_to)
    else:
        date_from_dt = now - timedelta(days=30)
        date_to_dt = now

    if granularity not in ['day', 'week', 'month']:
        raise HTTPException(status_code=400, detail="granularity는 day, week, month 중 하나여야 합니다")

    if metric not in ['views', 'engagement_rate', 'video_count']:
        raise HTTPException(status_code=400, detail="metric은 views, engagement_rate, video_count 중 하나여야 합니다")

    data = analytics.get_trend_data(db, date_from_dt, date_to_dt, granularity, metric)
    return data


@router.post("/export", response_model=ExportResponse)
async def export_data(
    export_request: ExportRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)

    if export_request.report_type not in ['dashboard', 'memes', 'categories', 'companies', 'videos']:
        raise HTTPException(status_code=400, detail="잘못된 report_type")

    if export_request.format not in ['csv', 'excel']:
        raise HTTPException(status_code=400, detail="format은 csv 또는 excel이어야 합니다")

    filters = export_request.filters.dict() if export_request.filters else None

    data = analytics.create_export_job(
        db,
        export_request.report_type,
        export_request.date_from,
        export_request.date_to,
        export_request.format,
        export_request.include_details,
        filters
    )

    return data


@router.get("/export/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)

    data = analytics.get_export_status(db, export_id)

    if not data:
        raise HTTPException(status_code=404, detail="내보내기 작업을 찾을 수 없습니다")

    return data


@router.get("/companies", response_model=CompanyPerformanceResponse)
async def get_company_performance(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort_by: str = Query('total_views', description="정렬 기준"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    await check_admin_permission(request)
    date_from_dt, date_to_dt = parse_date_range(date_from, date_to)
    data = analytics.get_company_performance(db, date_from_dt, date_to_dt, sort_by, limit)
    return data
