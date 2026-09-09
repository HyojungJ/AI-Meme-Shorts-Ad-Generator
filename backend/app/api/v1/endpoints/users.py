"""
사용자 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.schemas.users import (
    UserListResponse,
    UserDetailResponse,
    UpdateStatusRequest,
    UpdateStatusResponse,
    UpdateRoleRequest,
    UpdateRoleResponse,
    ActivityLogResponse,
    DeleteUserRequest,
    DeleteUserResponse,
    UserStatisticsResponse,
    BulkActionRequest,
    BulkActionResponse
)
from app.crud import users
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()


async def check_admin_permission(request: Request):
    """Admin 권한 확인"""
    user_info = await get_current_user(request)
    
    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
    
    return user_info


@router.get("", response_model=UserListResponse)
async def get_all_users(
    request: Request,
    account_type: Optional[str] = Query(None, description="계정 유형 (client, admin)"),
    status: Optional[str] = Query(None, description="상태 (active, inactive, suspended)"),
    company_id: Optional[int] = Query(None, description="회사 ID"),
    search: Optional[str] = Query(None, description="이름 또는 이메일 검색"),
    sort_by: str = Query('created_at', description="정렬 기준"),
    order: str = Query('desc', description="정렬 순서 (asc, desc)"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    전체 사용자 목록 조회
    
    플랫폼의 모든 사용자를 조회합니다.
    """
    admin_info = await check_admin_permission(request)
    
    user_list, total_count = users.get_all_users(
        db, account_type, status, company_id, search, sort_by, order, offset, limit
    )
    
    return {
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'users': user_list
    }


@router.get("/{account_id}", response_model=UserDetailResponse)
async def get_user_detail(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 상세 정보 조회
    
    특정 사용자의 상세 정보를 조회합니다.
    """
    await check_admin_permission(request)
    
    user_detail = users.get_user_detail(db, account_id)
    
    if not user_detail:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return user_detail


@router.patch("/{account_id}/status", response_model=UpdateStatusResponse)
async def update_user_status(
    account_id: int,
    status_request: UpdateStatusRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 활성화/비활성화
    
    사용자 계정을 활성화하거나 비활성화합니다.
    """
    admin_info = await check_admin_permission(request)
    
    if status_request.status not in ['active', 'inactive', 'suspended']:
        raise HTTPException(status_code=400, detail="status는 active, inactive, suspended 중 하나여야 합니다")
    
    result = users.update_user_status(
        db,
        account_id,
        status_request.status,
        admin_info.get('email', 'admin'),
        status_request.reason
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # TODO: notify_user가 True면 이메일 전송
    
    return result


@router.patch("/{account_id}/role", response_model=UpdateRoleResponse)
async def update_user_role(
    account_id: int,
    role_request: UpdateRoleRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 권한 변경
    
    회사 내 사용자의 권한을 변경합니다.
    """
    admin_info = await check_admin_permission(request)
    
    if role_request.role not in ['manager', 'member']:
        raise HTTPException(status_code=400, detail="role은 manager 또는 member여야 합니다")
    
    result = users.update_user_role(
        db,
        account_id,
        role_request.company_id,
        role_request.role,
        admin_info.get('email', 'admin'),
        role_request.reason
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="사용자 또는 회사 멤버십을 찾을 수 없습니다")
    
    return result


@router.get("/{account_id}/activity-logs", response_model=ActivityLogResponse)
async def get_user_activity_logs(
    account_id: int,
    request: Request,
    action_type: Optional[str] = Query(None, description="활동 유형"),
    date_from: Optional[str] = Query(None, description="시작 날짜"),
    date_to: Optional[str] = Query(None, description="종료 날짜"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    사용자 활동 로그 조회
    
    사용자의 활동 내역을 조회합니다.
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
    
    logs, total_count = users.get_user_activity_logs(
        db, account_id, action_type, date_from_dt, date_to_dt, offset, limit
    )
    
    return {
        'account_id': account_id,
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'logs': logs
    }


@router.delete("/{account_id}", response_model=DeleteUserResponse)
async def delete_user(
    account_id: int,
    delete_request: DeleteUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 계정 삭제

    사용자 계정을 완전히 삭제합니다. (주의: 복구 불가)
    """
    admin_info = await check_admin_permission(request)

    if delete_request.confirmation != "DELETE":
        raise HTTPException(status_code=400, detail="confirmation 필드에 'DELETE'를 입력해야 합니다")

    result = users.delete_user(
        db,
        account_id,
        admin_info.get('email', 'admin'),
        delete_request.reason,
        delete_request.delete_videos
    )

    if not result:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return result


@router.post("/{account_id}/delete", response_model=DeleteUserResponse)
async def delete_user_post(
    account_id: int,
    delete_request: DeleteUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 계정 삭제 (POST)

    DELETE 메서드 대신 POST로 삭제 (프론트엔드 호환)
    """
    return await delete_user(account_id, delete_request, request, db)


@router.get("/statistics/summary", response_model=UserStatisticsResponse)
async def get_user_statistics(
    request: Request,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    사용자 통계 요약
    
    전체 사용자 통계를 요약합니다.
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
    
    stats = users.get_user_statistics(db, date_from_dt, date_to_dt)
    return stats


@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_action(
    bulk_request: BulkActionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    대량 사용자 작업
    
    여러 사용자에게 동시에 작업을 수행합니다.
    """
    admin_info = await check_admin_permission(request)
    
    if bulk_request.action not in ['activate', 'deactivate', 'suspend', 'send_notification']:
        raise HTTPException(
            status_code=400,
            detail="action은 activate, deactivate, suspend, send_notification 중 하나여야 합니다"
        )
    
    if not bulk_request.account_ids:
        raise HTTPException(status_code=400, detail="account_ids는 비어있을 수 없습니다")
    
    result = users.bulk_update_users(
        db,
        bulk_request.action,
        bulk_request.account_ids,
        admin_info.get('email', 'admin'),
        bulk_request.reason
    )
    
    return result
