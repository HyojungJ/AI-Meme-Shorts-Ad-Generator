"""
데이터베이스 모델 및 함수 V3
새로운 테이블 구조: accounts, clients, admins, companies, company_members
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()


# ============================================
# 모델 정의
# ============================================

class Account(Base):
    """계정 공통 테이블"""
    __tablename__ = "accounts"
    
    account_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    account_type = Column(String(20), nullable=False)  # 'client' or 'admin'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("account_type IN ('client', 'admin')", name='chk_account_type'),
    )
    
    # 관계
    client = relationship("Client", back_populates="account", uselist=False)
    admin = relationship("Admin", back_populates="account", uselist=False)
    company_members = relationship("CompanyMember", back_populates="account")


class Client(Base):
    """클라이언트 (일반 사용자)"""
    __tablename__ = "clients"
    
    client_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime)
    reset_token = Column(Text)
    reset_expires_at = Column(DateTime)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    account = relationship("Account", back_populates="client")


class Admin(Base):
    """어드민 (비밀번호 로그인)"""
    __tablename__ = "admins"
    
    admin_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    account = relationship("Account", back_populates="admin")


class Company(Base):
    """회사"""
    __tablename__ = "companies"
    
    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    members = relationship("CompanyMember", back_populates="company")


class CompanyMember(Base):
    """회사 멤버"""
    __tablename__ = "company_members"
    
    member_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'manager' or 'member'
    member_name = Column(String(100), nullable=False)
    department = Column(String(100))
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("role IN ('manager', 'member')", name='chk_member_role'),
    )
    
    # 관계
    company = relationship("Company", back_populates="members")
    account = relationship("Account", back_populates="company_members")


# ============================================
# 데이터베이스 세션
# ============================================
def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# Account 관련 함수
# ============================================
def get_account_by_email(db, email: str):
    """이메일로 계정 조회"""
    return db.query(Account).filter(Account.email == email).first()


def get_account_by_id(db, account_id: int):
    """계정 ID로 조회"""
    return db.query(Account).filter(Account.account_id == account_id).first()


def create_account(db, email: str, account_type: str):
    """
    새 계정 생성
    account_type: 'client' or 'admin'
    """
    new_account = Account(
        email=email,
        account_type=account_type
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    print(f"새 계정 생성: {new_account.email} (type: {new_account.account_type})")
    return new_account


# ============================================
# Client 관련 함수
# ============================================
def get_client_by_account_id(db, account_id: int):
    """계정 ID로 클라이언트 조회"""
    return db.query(Client).filter(Client.account_id == account_id).first()


def create_client(db, account_id: int, hashed_password: str):
    """
    새 클라이언트 생성
    """
    new_client = Client(
        account_id=account_id,
        hashed_password=hashed_password
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    print(f"새 클라이언트 생성: account_id={account_id}")
    return new_client


def update_client_refresh_token(db, account_id: int, refresh_token: str, expires_at: datetime):
    """클라이언트의 Refresh Token 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.refresh_token = refresh_token
        client.rt_expires_at = expires_at
        client.last_login_at = datetime.utcnow()
        db.commit()
        print(f"Refresh Token 업데이트: account_id={account_id}")
        return client
    return None


def update_client_reset_token(db, account_id: int, reset_token: str, expires_at: datetime):
    """비밀번호 재설정 토큰 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.reset_token = reset_token
        client.reset_expires_at = expires_at
        db.commit()
        print(f"비밀번호 재설정 토큰 생성: account_id={account_id}")
        return client
    return None


def clear_client_reset_token(db, account_id: int):
    """비밀번호 재설정 토큰 삭제"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.reset_token = None
        client.reset_expires_at = None
        db.commit()
        return client
    return None


def update_client_password(db, account_id: int, new_hashed_password: str):
    """클라이언트 비밀번호 업데이트"""
    client = get_client_by_account_id(db, account_id)
    if client:
        client.hashed_password = new_hashed_password
        client.updated_at = datetime.utcnow()
        db.commit()
        print(f"비밀번호 변경 완료: account_id={account_id}")
        return client
    return None


def get_client_by_reset_token(db, reset_token: str):
    """재설정 토큰으로 클라이언트 조회"""
    return db.query(Client).filter(
        Client.reset_token == reset_token,
        Client.reset_expires_at > datetime.utcnow()
    ).first()


# ============================================
# Company 관련 함수
# ============================================
def get_company_by_id(db, company_id: int):
    """회사 ID로 조회"""
    return db.query(Company).filter(Company.company_id == company_id).first()


def create_company(db, company_name: str):
    """새 회사 생성"""
    new_company = Company(
        company_name=company_name
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    print(f"새 회사 생성: {new_company.company_name}")
    return new_company


# ============================================
# CompanyMember 관련 함수
# ============================================
def get_company_member(db, company_id: int, account_id: int):
    """회사 멤버 조회"""
    return db.query(CompanyMember).filter(
        CompanyMember.company_id == company_id,
        CompanyMember.account_id == account_id
    ).first()


def get_company_members_by_account(db, account_id: int):
    """계정의 모든 회사 멤버십 조회"""
    return db.query(CompanyMember).filter(
        CompanyMember.account_id == account_id
    ).all()


def create_company_member(db, company_id: int, account_id: int, role: str, member_name: str, department: str = None, is_primary: bool = False):
    """
    새 회사 멤버 생성
    role: 'manager' or 'member'
    """
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
    print(f"새 회사 멤버 생성: {member_name} (company_id={company_id}, role={role})")
    return new_member


# ============================================
# 통합 함수 (회원가입용)
# ============================================
def create_client_with_company(db, email: str, hashed_password: str, company_name: str, member_name: str):
    """
    클라이언트 회원가입: Account + Client + Company + CompanyMember 생성
    """
    # 1. Account 생성
    account = create_account(db, email, account_type='client')
    
    # 2. Client 생성
    client = create_client(db, account.account_id, hashed_password)
    
    # 3. Company 생성
    company = create_company(db, company_name)
    
    # 4. CompanyMember 생성 (manager, primary)
    member = create_company_member(
        db=db,
        company_id=company.company_id,
        account_id=account.account_id,
        role='manager',
        member_name=member_name,
        is_primary=True
    )
    
    return {
        'account': account,
        'client': client,
        'company': company,
        'member': member
    }


def get_user_info(db, account_id: int):
    """
    사용자 전체 정보 조회 (Account + Client + CompanyMember)
    """
    account = get_account_by_id(db, account_id)
    if not account:
        return None
    
    # Client 정보
    client = get_client_by_account_id(db, account_id)
    
    # 회사 멤버십 정보 (첫 번째 회사)
    members = get_company_members_by_account(db, account_id)
    primary_member = next((m for m in members if m.is_primary), members[0] if members else None)
    
    return {
        'account': account,
        'client': client,
        'member': primary_member,
        'company': primary_member.company if primary_member else None
    }
