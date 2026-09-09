"""
밈 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Meme(Base):
    """밈 데이터"""
    __tablename__ = "memes"
    
    meme_id = Column(BigInteger, primary_key=True, autoincrement=True)
    meme_name = Column(String(255), unique=True, nullable=False, index=True)
    definition = Column(Text)
    origin = Column(JSONB)
    key_phrase = Column(Text)
    sources = Column(JSONB, default=[])
    risk_info = Column(String(20))
    meme_type = Column(String(50))
    status = Column(String(50), default='READY', index=True)
    source_video = Column(JSONB, default={})
    video_analysis = Column(JSONB, default={})
    confidence = Column(Float)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("status IN ('READY', 'PROCESSING', 'PROCESSED', 'COMPLETED', 'FAILED')", name='memes_status_check'),
        CheckConstraint("meme_type IN ('quotable', 'performable', 'hybrid')", name='memes_meme_type_check'),
        Index('idx_memes_origin_gin', 'origin', postgresql_using='gin'),
    )
    
    # 관계
    examples = relationship("MemeExample", back_populates="meme")
    ad_requests = relationship("AdRequest", back_populates="meme")
    scenario_scripts = relationship("ScenarioScript", back_populates="meme")


class MemeExample(Base):
    """밈 사용 예시"""
    __tablename__ = "meme_examples"
    
    example_id = Column(Integer, primary_key=True, autoincrement=True)
    meme_id = Column(BigInteger, ForeignKey("memes.meme_id", ondelete="CASCADE"), nullable=False, index=True)
    situation = Column(String(255), nullable=False)
    dialogue_example = Column(Text)
    source_url = Column(String(500))
    example_type = Column(String(20), index=True)
    note = Column(Text)
    tone = Column(String(20))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 관계
    meme = relationship("Meme", back_populates="examples")
