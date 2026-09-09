"""
품질 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.schemas.quality import (
    LowQualityVideoResponse,
    ValidationFailureResponse,
    RetryValidationRequest,
    RetryValidationResponse,
    ApproveValidationRequest,
    ApproveValidationResponse,
    QualityTrendResponse
)
from app.crud import quality
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()


async def check_admin_permission(request: Request):
    """Admin 권한 확인"""
    user_info = await get_current_user(request)
    
    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
    
    return user_info


@router.get("/low-score-videos", response_model=LowQualityVideoResponse)
async def get_low_quality_videos(
    request: Request,
    threshold: int = Query(70, ge=0, le=100, description="품질 점수 임계값"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    sort_by: str = Query('quality_score', description="정렬 기준"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    품질 점수 낮은 영상 목록
    
    품질 점수가 낮은 영상을 조회합니다.
    """
    await check_admin_permission(request)
    
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_from 형식")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_to 형식")
    
    data = quality.get_low_quality_videos(
        db, threshold, date_from_dt, date_to_dt, sort_by, offset, limit
    )
    return data


@router.get("/validation-failures", response_model=ValidationFailureResponse)
async def get_validation_failures(
    request: Request,
    failure_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    자동 품질 검증 실패 목록
    
    자동 품질 검증에 실패한 영상을 조회합니다.
    """
    await check_admin_permission(request)
    
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_from 형식")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_to 형식")
    
    data = quality.get_validation_failures(
        db, failure_type, date_from_dt, date_to_dt, status, offset, limit
    )
    return data


@router.post("/validation/{validation_id}/retry", response_model=RetryValidationResponse)
async def retry_validation(
    validation_id: int,
    retry_request: RetryValidationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    품질 검증 재시도
    
    실패한 품질 검증을 재시도합니다.
    """
    await check_admin_permission(request)
    
    result = quality.retry_validation(
        db,
        validation_id,
        retry_request.force_reprocess,
        retry_request.skip_checks,
        retry_request.note
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="검증 작업을 찾을 수 없습니다")
    
    return result


@router.post("/validation/{validation_id}/approve", response_model=ApproveValidationResponse)
async def approve_validation(
    validation_id: int,
    approve_request: ApproveValidationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    품질 검증 승인
    
    실패한 검증을 수동으로 승인합니다.
    """
    admin_info = await check_admin_permission(request)
    
    result = quality.approve_validation(
        db,
        validation_id,
        admin_info.get('email', 'admin'),
        approve_request.reason,
        approve_request.override_checks
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="검증 작업을 찾을 수 없습니다")
    
    return result


@router.get("/trends", response_model=QualityTrendResponse)
async def get_quality_trends(
    request: Request,
    date_from: str = Query(..., description="시작 날짜"),
    date_to: str = Query(..., description="종료 날짜"),
    granularity: str = Query('week', description="집계 단위"),
    db: Session = Depends(get_db)
):
    """
    품질 트렌드 분석
    
    시간에 따른 품질 트렌드를 분석합니다.
    """
    await check_admin_permission(request)
    
    try:
        date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식")
    
    if granularity not in ['day', 'week', 'month']:
        raise HTTPException(status_code=400, detail="granularity는 day, week, month 중 하나여야 합니다")
    
    data = quality.get_quality_trends(db, date_from_dt, date_to_dt, granularity)
    return data
