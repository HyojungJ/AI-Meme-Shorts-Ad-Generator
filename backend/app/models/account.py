"""
계정 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Account(Base):
    """계정 공통 테이블"""
    __tablename__ = "accounts"
    
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    account_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("account_type IN ('client', 'admin')", name='accounts_account_type_check'),
    )
    
    # 관계
    client = relationship("Client", back_populates="account", uselist=False)
    admin = relationship("Admin", back_populates="account", uselist=False)
    company_members = relationship("CompanyMember", back_populates="account")


class Client(Base):
    """클라이언트 (비밀번호 로그인)"""
    __tablename__ = "clients"
    
    client_id = Column(Integer, primary_key=True, autoincrement=True)
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
    
    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    account = relationship("Account", back_populates="admin")
    youtube_channel = relationship("AdminYoutubeChannel", back_populates="admin", uselist=False)
