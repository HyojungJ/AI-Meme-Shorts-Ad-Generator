"""
사용자 관리 관련 CRUD 로직
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any

from app.models.account import Account, Client
from app.models.company import Company, CompanyMember
from app.models.ad_request import AdRequest
from app.models.video import Video


def get_all_users(
    db: Session,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Dict], int]:
    """전체 사용자 목록 조회"""
    
    query = db.query(Account)
    
    # 필터링
    if account_type:
        query = query.filter(Account.account_type == account_type)
    if status:
        # status를 is_active로 변환
        if status == 'active':
            query = query.filter(Account.is_active == True)
        elif status in ['inactive', 'suspended']:
            query = query.filter(Account.is_active == False)
    if company_id:
        query = query.join(CompanyMember).filter(CompanyMember.company_id == company_id)
    if search:
        query = query.filter(Account.email.ilike(f'%{search}%'))
    
    # 정렬
    if sort_by == 'created_at':
        sort_col = Account.created_at
    else:
        sort_col = Account.created_at
    
    if order == 'desc':
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    
    total_count = query.count()
    accounts = query.offset(offset).limit(limit).all()
    
    users = []
    for account in accounts:
        # 회사 정보 조회
        company_member = db.query(CompanyMember).filter(
            CompanyMember.account_id == account.account_id
        ).first()
        
        company_info = None
        role = None
        if company_member:
            company = db.query(Company).filter(
                Company.company_id == company_member.company_id
            ).first()
            if company:
                company_info = {
                    'company_id': company.company_id,
                    'company_name': company.company_name
                }
                role = company_member.role
        
        # 영상 수 조회 (실제 Video 기준)
        total_videos = 0
        if company_member:
            total_videos = db.query(Video).join(AdRequest).filter(
                AdRequest.account_id == account.account_id
            ).count()
        
        users.append({
            'account_id': account.account_id,
            'email': account.email,
            'member_name': company_member.member_name if company_member else None,
            'account_type': account.account_type,
            'status': 'active' if account.is_active else 'inactive',
            'company_id': company_info['company_id'] if company_info else None,
            'company_name': company_info['company_name'] if company_info else None,
            'department': company_member.department if company_member else None,
            'role': role,
            'created_at': account.created_at.isoformat(),
            'last_login_at': None,
            'video_count': total_videos
        })
    
    return users, total_count


def get_user_detail(db: Session, account_id: int) -> Optional[Dict]:
    """사용자 상세 정보 조회"""
    
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return None
    
    # 회사 정보
    company_member = db.query(CompanyMember).filter(
        CompanyMember.account_id == account_id
    ).first()
    
    company_info = None
    if company_member:
        company = db.query(Company).filter(
            Company.company_id == company_member.company_id
        ).first()
        if company:
            company_info = {
                'company_id': company.company_id,
                'company_name': company.company_name,
                'role': company_member.role,
                'joined_at': company_member.created_at.isoformat()
            }
    
    # 통계
    total_videos = 0
    total_views = 0
    total_ads = 0
    active_ads = 0
    
    if company_member:
        total_ads = db.query(AdRequest).filter(
            AdRequest.company_id == company_member.company_id,
            AdRequest.account_id == account_id
        ).count()
        
        active_ads = db.query(AdRequest).filter(
            AdRequest.company_id == company_member.company_id,
            AdRequest.account_id == account_id,
            AdRequest.status.in_(['draft', 'processing'])
        ).count()
        
        # 영상 수 (전체 Video 기준)
        total_videos = db.query(Video).join(AdRequest).filter(
            AdRequest.account_id == account_id
        ).count()
    
    # 최근 영상
    recent_videos = []
    if company_member:
        recent_ads = db.query(AdRequest).filter(
            AdRequest.company_id == company_member.company_id,
            AdRequest.account_id == account_id
        ).order_by(desc(AdRequest.created_at)).limit(5).all()
        
        for ad in recent_ads:
            final_video = db.query(Video).filter(
                Video.ad_id == ad.ad_id
            ).first()
            
            if final_video:
                recent_videos.append({
                    'video_id': final_video.video_id,
                    'title': final_video.title or ad.item_name or '제목 없음',
                    'status': final_video.status,
                    'views': 0,  # TODO: PerformanceMetric 연동
                    'created_at': ad.created_at.isoformat()
                })
    
    return {
        'account_id': account.account_id,
        'email': account.email,
        'name': company_member.member_name if company_member else 'N/A',
        'account_type': account.account_type,
        'company': company_info,
        'profile': {
            'phone': None,
            'department': company_member.department if company_member else None,
            'position': None
        },
        'statistics': {
            'total_videos': total_videos,
            'total_views': total_views,
            'total_projects': total_ads,
            'active_projects': active_ads,
            'average_engagement_rate': 0.0
        },
        'activity': {
            'created_at': account.created_at.isoformat(),
            'last_login_at': None,
            'last_video_created_at': recent_videos[0]['created_at'] if recent_videos else None,
            'login_count': 0
        },
        'recent_videos': recent_videos
    }


def update_user_status(
    db: Session,
    account_id: int,
    status: str,
    changed_by: str,
    reason: Optional[str] = None
) -> Optional[Dict]:
    """사용자 상태 변경"""
    
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return None
    
    # status를 is_active로 변환
    is_active = status == 'active'
    previous_is_active = account.is_active
    
    account.is_active = is_active
    account.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(account)
    
    return {
        'account_id': account.account_id,
        'status': status,
        'previous_status': 'active' if previous_is_active else 'inactive',
        'is_active': account.is_active,
        'changed_at': datetime.utcnow().isoformat(),
        'changed_by': changed_by,
        'reason': reason,
        'message': '사용자 상태가 변경되었습니다'
    }


def update_user_role(
    db: Session,
    account_id: int,
    company_id: int,
    new_role: str,
    changed_by: str,
    reason: Optional[str] = None
) -> Optional[Dict]:
    """사용자 권한 변경"""
    
    member = db.query(CompanyMember).filter(
        and_(
            CompanyMember.account_id == account_id,
            CompanyMember.company_id == company_id
        )
    ).first()
    
    if not member:
        return None
    
    previous_role = member.role
    member.role = new_role
    member.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(member)
    
    return {
        'account_id': account_id,
        'company_id': company_id,
        'role': member.role,
        'previous_role': previous_role,
        'changed_at': datetime.utcnow().isoformat(),
        'changed_by': changed_by,
        'reason': reason,
        'message': '사용자 권한이 변경되었습니다'
    }


def get_user_statistics(
    db: Session,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict:
    """사용자 통계 요약"""
    
    if not date_to:
        date_to = datetime.utcnow()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    
    # 전체 사용자 수
    total_users = db.query(Account).count()
    active_users = db.query(Account).filter(Account.is_active == True).count()
    inactive_users = db.query(Account).filter(Account.is_active == False).count()
    
    # 신규 사용자
    new_users = db.query(Account).filter(
        and_(
            Account.created_at >= date_from,
            Account.created_at <= date_to
        )
    ).count()
    
    # 성장률
    period_length = (date_to - date_from).days
    prev_date_from = date_from - timedelta(days=period_length)
    prev_users = db.query(Account).filter(Account.created_at < date_from).count()
    user_growth_rate = ((total_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
    
    # 계정 유형별
    client_count = db.query(Account).filter(Account.account_type == 'client').count()
    admin_count = db.query(Account).filter(Account.account_type == 'admin').count()
    
    # 권한별
    manager_count = db.query(CompanyMember).filter(CompanyMember.role == 'manager').count()
    member_count = db.query(CompanyMember).filter(CompanyMember.role == 'member').count()
    
    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'new_users_this_period': new_users,
        'user_growth_rate': round(user_growth_rate, 1),
        'by_account_type': {
            'client': client_count,
            'admin': admin_count
        },
        'by_role': {
            'manager': manager_count,
            'member': member_count
        },
        'engagement': {
            'daily_active_users': active_users,
            'weekly_active_users': active_users,
            'monthly_active_users': active_users,
            'average_videos_per_user': 0
        },
        'top_active_users': []
    }


def bulk_update_users(
    db: Session,
    action: str,
    account_ids: List[int],
    changed_by: str,
    reason: Optional[str] = None
) -> Dict:
    """대량 사용자 작업"""
    
    success_count = 0
    failed_count = 0
    errors = []
    
    for account_id in account_ids:
        try:
            account = db.query(Account).filter(Account.account_id == account_id).first()
            if not account:
                failed_count += 1
                errors.append(f"Account {account_id} not found")
                continue
            
            if action == 'activate':
                account.is_active = True
            elif action == 'deactivate':
                account.is_active = False
            elif action == 'suspend':
                account.is_active = False
            elif action == 'send_notification':
                # TODO: 알림 전송 로직
                pass
            
            account.updated_at = datetime.utcnow()
            success_count += 1
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Account {account_id}: {str(e)}")
    
    db.commit()
    
    return {
        'action': action,
        'total_requested': len(account_ids),
        'success_count': success_count,
        'failed_count': failed_count,
        'errors': errors,
        'changed_by': changed_by,
        'reason': reason,
        'message': f'{success_count}명의 사용자에게 작업이 완료되었습니다'
    }


def delete_user(
    db: Session,
    account_id: int,
    deleted_by: str,
    reason: Optional[str] = None,
    delete_videos: bool = False
) -> Optional[Dict]:
    """사용자 계정 삭제"""
    
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return None
    
    # TODO: 관련 데이터 삭제 또는 비활성화
    # - Client/Admin 레코드
    # - CompanyMember 레코드
    # - AdRequest (delete_videos=True인 경우)
    
    # 임시로 비활성화만 처리
    account.is_active = False
    account.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        'account_id': account_id,
        'status': 'deleted',
        'deleted_at': datetime.utcnow().isoformat(),
        'deleted_by': deleted_by,
        'videos_deleted': delete_videos,
        'message': '사용자가 삭제되었습니다'
    }


def get_user_activity_logs(
    db: Session,
    account_id: int,
    action_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    offset: int = 0,
    limit: int = 50
) -> Tuple[List[Dict], int]:
    """사용자 활동 로그 조회"""
    
    # TODO: 실제 활동 로그 테이블이 있다면 조회
    # 현재는 AdRequest 기반으로 임시 구현
    
    query = db.query(AdRequest).filter(AdRequest.account_id == account_id)
    
    if date_from:
        query = query.filter(AdRequest.created_at >= date_from)
    if date_to:
        query = query.filter(AdRequest.created_at <= date_to)
    
    total_count = query.count()
    ad_requests = query.order_by(desc(AdRequest.created_at)).offset(offset).limit(limit).all()
    
    logs = []
    for ad in ad_requests:
        logs.append({
            'log_id': ad.ad_id,
            'action_type': 'ad_request_created',
            'description': f'광고 요청 생성: {ad.item_name}',
            'timestamp': ad.created_at.isoformat(),
            'metadata': {
                'ad_id': ad.ad_id,
                'item_name': ad.item_name
            }
        })
    
    return logs, total_count
