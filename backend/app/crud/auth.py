"""
인증 관련 CRUD 로직
"""
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.account import Account, Client, Admin
from app.models.company import Company, CompanyMember


# ============================================
# Account CRUD
# ============================================
def get_account_by_email(db: Session, email: str):
    """이메일로 계정 조회"""
    return db.query(Account).filter(Account.email == email).first()


def get_account_by_id(db: Session, account_id: int):
    """계정 ID로 조회"""
    return db.query(Account).filter(Account.account_id == account_id).first()


def create_account(db: Session, email: str, account_type: str):
    """새 계정 생성"""
    new_account = Account(email=email, account_type=account_type)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


# ============================================
# Client CRUD
# ============================================
def get_client_by_account_id(db: Session, account_id: int):
    """계정 ID로 클라이언트 조회"""
    return db.query(Client).filter(Client.account_id == account_id).first()


def get_client_by_reset_token(db: Session, reset_token: str):
    """재설정 토큰으로 클라이언트 조회"""
    return db.query(Client).filter(
        Client.reset_token == reset_token,
        Client.reset_expires_at > datetime.utcnow()
    ).first()


def create_client(db: Session, account_id: int, hashed_password: str):
    """새 클라이언트 생성"""
    new_client = Client(account_id=account_id, hashed_password=hashed_password)
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


def update_client_refresh_token(db: Session, account_id: int, refresh_token: str, expires_at: datetime):
    """클라이언트의 Refresh Token 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.refresh_token = refresh_token
        client.rt_expires_at = expires_at
        client.last_login_at = datetime.utcnow()
        db.commit()
        return client
    return None


def update_client_reset_token(db: Session, account_id: int, reset_token: str, expires_at: datetime):
    """비밀번호 재설정 토큰 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.reset_token = reset_token
        client.reset_expires_at = expires_at
        db.commit()
        return client
    return None


def clear_client_reset_token(db: Session, account_id: int):
    """비밀번호 재설정 토큰 삭제"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.reset_token = None
        client.reset_expires_at = None
        db.commit()
        return client
    return None


def update_client_password(db: Session, account_id: int, new_hashed_password: str):
    """클라이언트 비밀번호 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.hashed_password = new_hashed_password
        client.updated_at = datetime.utcnow()
        db.commit()
        return client
    return None


# ============================================
# Admin CRUD
# ============================================
def get_admin_by_account_id(db: Session, account_id: int):
    """계정 ID로 어드민 조회"""
    return db.query(Admin).filter(Admin.account_id == account_id).first()


def create_admin(db: Session, account_id: int, hashed_password: str):
    """새 어드민 생성"""
    new_admin = Admin(account_id=account_id, hashed_password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


def update_admin_refresh_token(db: Session, account_id: int, refresh_token: str, expires_at: datetime):
    """어드민의 Refresh Token 업데이트"""
    admin = get_admin_by_account_id(db, account_id)
    if admin:
        admin.refresh_token = refresh_token
        admin.rt_expires_at = expires_at
        admin.last_login_at = datetime.utcnow()
        db.commit()
        return admin
    return None


def update_admin_password(db: Session, account_id: int, new_hashed_password: str):
    """어드민 비밀번호 업데이트"""
    admin = get_admin_by_account_id(db, account_id)
    if admin:
        admin.hashed_password = new_hashed_password
        admin.updated_at = datetime.utcnow()
        db.commit()
        return admin
    return None


# ============================================
# Company CRUD
# ============================================
def get_company_by_name(db: Session, company_name: str):
    """회사명으로 회사 조회"""
    return db.query(Company).filter(Company.company_name == company_name).first()


def create_company(db: Session, company_name: str):
    """새 회사 생성"""
    new_company = Company(company_name=company_name)
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return new_company


def get_or_create_company(db: Session, company_name: str):
    """회사명으로 조회하거나 없으면 생성"""
    company = get_company_by_name(db, company_name)
    if company:
        return company
    return create_company(db, company_name)


# ============================================
# CompanyMember CRUD
# ============================================
def get_company_members_by_account(db: Session, account_id: int):
    """계정의 모든 회사 멤버십 조회"""
    return db.query(CompanyMember).filter(
        CompanyMember.account_id == account_id
    ).all()


def create_company_member(db: Session, company_id: int, account_id: int, role: str, member_name: str, department: str = None, is_primary: bool = False):
    """새 회사 멤버 생성"""
    new_member = CompanyMember(
        company_id=company_id,
        account_id=account_id,
        role=role,
        member_name=member_name,
        department=department,
        is_primary=is_primary
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member


# ============================================
# 통합 함수
# ============================================
def create_client_with_company(db: Session, email: str, hashed_password: str, company_name: str, member_name: str, department: str = None, role: str = 'member'):
    """클라이언트 회원가입: Account + Client + Company + CompanyMember 생성"""
    # role은 항상 member로 고정
    role = 'member'
    
    # Account 생성
    account = create_account(db, email, account_type='client')
    
    # Client 생성
    client = create_client(db, account.account_id, hashed_password)
    
    # Company 조회 또는 생성 (같은 회사명이면 기존 Company 사용)
    company = get_or_create_company(db, company_name)
    
    # CompanyMember 생성
    member = create_company_member(
        db=db,
        company_id=company.company_id,
        account_id=account.account_id,
        role=role,
        member_name=member_name,
        department=department,
        is_primary=True
    )
    
    return {
        'account': account,
        'client': client,
        'company': company,
        'member': member
    }


def create_admin_account(db: Session, email: str, hashed_password: str):
    """어드민 회원가입: Account + Admin 생성"""
    # Account 생성
    account = create_account(db, email, account_type='admin')
    
    # Admin 생성
    admin = create_admin(db, account.account_id, hashed_password)
    
    return {
        'account': account,
        'admin': admin
    }


def get_user_info(db: Session, account_id: int):
    """사용자 전체 정보 조회"""
    account = get_account_by_id(db, account_id)
    if not account:
        return None
    
    if account.account_type == 'client':
        client = get_client_by_account_id(db, account_id)
        members = get_company_members_by_account(db, account_id)
        primary_member = next((m for m in members if m.is_primary), members[0] if members else None)
        
        return {
            'account': account,
            'client': client,
            'member': primary_member,
            'company': primary_member.company if primary_member else None
        }
    elif account.account_type == 'admin':
        admin = get_admin_by_account_id(db, account_id)
        
        return {
            'account': account,
            'admin': admin
        }
    
    return None


def update_user_profile(db: Session, account_id: int, member_name: str = None, department: str = None, company_name: str = None):
    """사용자 프로필 업데이트 (Client만 해당)"""
    members = get_company_members_by_account(db, account_id)
    primary_member = next((m for m in members if m.is_primary), members[0] if members else None)
    
    if not primary_member:
        return None
    
    # 회사명 수정
    if company_name is not None:
        company = db.query(Company).filter(Company.company_id == primary_member.company_id).first()
        if company:
            company.company_name = company_name
            company.updated_at = datetime.utcnow()
    
    # 멤버 정보 수정
    if member_name is not None:
        primary_member.member_name = member_name
    if department is not None:
        primary_member.department = department
    
    primary_member.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(primary_member)
    
    return primary_member
