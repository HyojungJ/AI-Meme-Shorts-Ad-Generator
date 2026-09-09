"""
회사 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Company(Base):
    """회사"""
    __tablename__ = "companies"
    
    company_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    members = relationship("CompanyMember", back_populates="company")
    characters = relationship("CompanyCharacter", back_populates="company")
    ad_requests = relationship("AdRequest", back_populates="company")
    videos = relationship("Video", back_populates="company")


class CompanyMember(Base):
    """회사 멤버"""
    __tablename__ = "company_members"
    
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    member_name = Column(String(100), nullable=False)
    department = Column(String(100))
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("role IN ('manager', 'member')", name='company_members_role_check'),
        Index('idx_company_members_primary_unique', 'company_id', unique=True, postgresql_where=(is_primary == True)),
    )
    
    # 관계
    company = relationship("Company", back_populates="members")
    account = relationship("Account", back_populates="company_members")


class CompanyCharacter(Base):
    """회사별 캐릭터 자산"""
    __tablename__ = "company_characters"
    
    character_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    image_prompt = Column(Text)
    image_model = Column(String(50))
    elevenlabs_voice_id = Column(Text)
    voice_sample_url = Column(Text)
    voice_design_prompt = Column(Text)
    generation_metadata = Column(JSONB, default={})
    review_result = Column(JSONB)
    
    # 관계
    company = relationship("Company", back_populates="characters")
    ad_requests = relationship("AdRequest", back_populates="character")
    voice_generations = relationship("VoiceGeneration", back_populates="character")
    image_generations = relationship("ImageGeneration", back_populates="character")
