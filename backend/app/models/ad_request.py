"""
광고 요청 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class AdRequest(Base):
    """광고 요청"""
    __tablename__ = "ad_requests"
    
    ad_id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    character_id = Column(Integer, ForeignKey("company_characters.character_id", ondelete="SET NULL"), index=True)
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(20))
    item_url = Column(String(500))
    item_images = Column(ARRAY(Text), default=[])
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    status = Column(String(50), default='draft', index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    item_description = Column(Text)  # 제품 설명 (구 item_keymessage)
    character_image_prompt = Column(Text)
    character_voice_prompt = Column(Text)
    
    __table_args__ = (
        CheckConstraint("cardinality(item_images) <= 1", name='chk_ad_request_images_count'),
    )
    
    # 관계
    company = relationship("Company", back_populates="ad_requests")
    character = relationship("CompanyCharacter", back_populates="ad_requests")
    meme = relationship("Meme", back_populates="ad_requests")
    scenario_scripts = relationship("ScenarioScript", back_populates="ad_request")
    videos = relationship("Video", back_populates="ad_request")
    workflow_executions = relationship("WorkflowExecution", back_populates="ad_request")
    prompt_usage_logs = relationship("PromptUsageLog", back_populates="ad_request")
