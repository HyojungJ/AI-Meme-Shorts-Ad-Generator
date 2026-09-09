"""
데이터베이스 모델 및 함수 V2
새로운 테이블 구조: users, companies
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import enum

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
# Enum 정의
# ============================================
class UserRole(str, enum.Enum):
    """사용자 역할 (UMS-AUT-02)"""
    ADMIN = "admin"
    CLIENT = "client"


# ============================================
# 모델 정의
# ============================================
class Company(Base):
    """
    기업 정보 테이블
    UMS-COM-01: 기업 프로필 관리
    """
    __tablename__ = "companies"
    
    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    users = relationship("User", back_populates="company")


class User(Base):
    """
    사용자 계정 테이블
    UMS-AUT-01: 이메일 기반 회원가입/로그인
    UMS-AUT-04: 비밀번호 bcrypt 해시화
    """
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="client")  # PostgreSQL ENUM은 SQLAlchemy에서 별도 처리
    is_active = Column(Boolean, default=True)
    
    # 보안 및 세션 관리
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime(timezone=True))
    
    # 비밀번호 재설정 (UMS-AUT-03)
    reset_token = Column(Text)
    reset_expires_at = Column(DateTime(timezone=True))
    
    # 모니터링
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    company = relationship("Company", back_populates="users")


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
# Company 관련 함수
# ============================================
def get_company_by_id(db, company_id: int):
    """회사 ID로 조회"""
    return db.query(Company).filter(Company.company_id == company_id).first()


def create_company(db, name: str, contact_email: str, contact_phone: str = None):
    """
    새 회사 생성
    UMS-COM-01: 기업 프로필 관리
    """
    new_company = Company(
        name=name,
        contact_email=contact_email,
        contact_phone=contact_phone
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    print(f"새 회사 생성: {new_company.name}")
    return new_company


# ============================================
# User 관련 함수
# ============================================
def get_user_by_email(db, email: str):
    """이메일로 사용자 조회"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id: int):
    """사용자 ID로 조회"""
    return db.query(User).filter(User.user_id == user_id).first()


def create_user(db, company_id: int, email: str, hashed_password: str, role: str = "client"):
    """
    새 사용자 생성
    UMS-AUT-01: 이메일 기반 회원가입
    """
    new_user = User(
        company_id=company_id,
        email=email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    print(f"새 사용자 생성: {new_user.email} (role: {new_user.role})")
    return new_user


def update_user_refresh_token(db, user_id: int, refresh_token: str, expires_at: datetime):
    """
    사용자의 Refresh Token 업데이트
    작업내용 3번: Refresh Token 저장
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.refresh_token = refresh_token
        user.rt_expires_at = expires_at
        user.last_login_at = datetime.utcnow()
        db.commit()
        print(f"Refresh Token 업데이트: {user.email}")
        return user
    return None


def update_user_reset_token(db, user_id: int, reset_token: str, expires_at: datetime):
    """
    비밀번호 재설정 토큰 업데이트
    UMS-AUT-03: 비밀번호 재설정
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.reset_token = reset_token
        user.reset_expires_at = expires_at
        db.commit()
        print(f"비밀번호 재설정 토큰 생성: {user.email}")
        return user
    return None


def clear_user_reset_token(db, user_id: int):
    """비밀번호 재설정 토큰 삭제"""
    user = get_user_by_id(db, user_id)
    if user:
        user.reset_token = None
        user.reset_expires_at = None
        db.commit()
        return user
    return None


def update_user_password(db, user_id: int, new_hashed_password: str):
    """
    사용자 비밀번호 업데이트
    UMS-AUT-03: 비밀번호 재설정
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.utcnow()
        db.commit()
        print(f"비밀번호 변경 완료: {user.email}")
        return user
    return None


def get_user_by_reset_token(db, reset_token: str):
    """재설정 토큰으로 사용자 조회"""
    return db.query(User).filter(
        User.reset_token == reset_token,
        User.reset_expires_at > datetime.utcnow()
    ).first()
