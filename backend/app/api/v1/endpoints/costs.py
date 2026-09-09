"""
비용 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.schemas.costs import (
    CompanyCostResponse,
    CostStatisticsResponse,
    CostDetailsResponse,
    OptimizationResponse
)
from app.crud import costs
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()


async def check_admin_permission(request: Request):
    """Admin 권한 확인"""
    user_info = await get_current_user(request)
    
    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
    
    return user_info


@router.get("/companies", response_model=CompanyCostResponse)
async def get_company_costs(
    request: Request,
    year: int = Query(..., description="연도"),
    month: int = Query(..., ge=1, le=12, description="월"),
    company_id: Optional[int] = Query(None),
    sort_by: str = Query('total_cost', description="정렬 기준"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    회사별 월별 비용 리포트
    
    각 회사의 월별 비용을 조회합니다.
    """
    await check_admin_permission(request)
    
    data = costs.get_company_costs(db, year, month, company_id, sort_by, offset, limit)
    return data


@router.get("/statistics", response_model=CostStatisticsResponse)
async def get_cost_statistics(
    request: Request,
    date_from: str = Query(..., description="시작 날짜"),
    date_to: str = Query(..., description="종료 날짜"),
    granularity: str = Query('month', description="집계 단위"),
    db: Session = Depends(get_db)
):
    """
    전체 비용 통계
    
    플랫폼 전체의 비용 통계를 조회합니다.
    """
    await check_admin_permission(request)
    
    try:
        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식")
    
    if granularity not in ['day', 'week', 'month']:
        raise HTTPException(status_code=400, detail="granularity는 day, week, month 중 하나여야 합니다")
    
    data = costs.get_cost_statistics(db, date_from_dt, date_to_dt, granularity)
    return data


@router.get("/details", response_model=CostDetailsResponse)
async def get_cost_details(
    request: Request,
    date_from: str = Query(...),
    date_to: str = Query(...),
    company_id: Optional[int] = Query(None),
    cost_type: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    비용 상세 내역
    
    특정 기간의 상세 비용 내역을 조회합니다.
    """
    await check_admin_permission(request)
    
    try:
        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식")
    
    details, total_count = costs.get_cost_details(
        db, date_from_dt, date_to_dt, company_id, cost_type, offset, limit
    )
    
    return {
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'details': details
    }


@router.get("/optimization-suggestions", response_model=OptimizationResponse)
async def get_optimization_suggestions(
    request: Request,
    company_id: Optional[int] = Query(None),
    min_savings: int = Query(10000, description="최소 절감 금액"),
    db: Session = Depends(get_db)
):
    """
    비용 최적화 제안
    
    비용 절감을 위한 제안을 제공합니다.
    """
    await check_admin_permission(request)
    
    data = costs.get_optimization_suggestions(db, company_id, min_savings)
    return data
