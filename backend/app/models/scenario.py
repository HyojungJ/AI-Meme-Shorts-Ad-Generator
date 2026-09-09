"""
시나리오 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, Boolean, DateTime, ForeignKey, CheckConstraint, Numeric, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class ScenarioScript(Base):
    """시나리오 스크립트"""
    __tablename__ = "scenario_scripts"
    
    script_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id", ondelete="CASCADE"), nullable=False, index=True)
    meme_id = Column(BigInteger, ForeignKey("memes.meme_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    hashtags = Column(ARRAY(Text))
    scenes = Column(JSONB, nullable=False)
    system_prompt = Column(Text)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.version_id", ondelete="SET NULL"))
    used_model = Column(String(50))
    user_prompt = Column(Text)
    full_response = Column(Text)
    quality_check_passed = Column(Boolean, default=False)
    quality_issues = Column(ARRAY(Text))
    approval_status = Column(String(20), default='pending', index=True)
    approval_requested_at = Column(DateTime)
    approved_at = Column(DateTime)
    approved_by_account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="SET NULL"))
    status = Column(String(50), default='draft')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    generation_type = Column(String(50), default='initial')
    review_result = Column(JSONB)
    used_templates = Column(ARRAY(Text))
    thinking = Column(Text)
    
    __table_args__ = (
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'auto_approved')", name='scenario_scripts_approval_status_check'),
        CheckConstraint("status IN ('draft', 'validated', 'approved', 'rejected')", name='scenario_scripts_status_check'),
        Index('idx_scenario_scripts_scenes_gin', 'scenes', postgresql_using='gin'),
        Index('idx_scenario_scripts_pending_approval', 'approval_requested_at', postgresql_where=(approval_status == 'pending')),
    )
    
    # 관계
    ad_request = relationship("AdRequest", back_populates="scenario_scripts")
    meme = relationship("Meme", back_populates="scenario_scripts")
    prompt_version = relationship("PromptVersion", back_populates="scenario_scripts")
    scene_assets = relationship("SceneAsset", back_populates="script")
    videos = relationship("Video", back_populates="script")
    voice_generations = relationship("VoiceGeneration", back_populates="script")
    image_generations = relationship("ImageGeneration", back_populates="script")
    scene_videos = relationship("SceneVideo", back_populates="script")
    prompt_usage_logs = relationship("PromptUsageLog", back_populates="script")
