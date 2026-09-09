"""
비디오 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Video(Base):
    """최종 영상"""
    __tablename__ = "videos"
    
    video_id = Column(Integer, primary_key=True, autoincrement=True)
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id", ondelete="CASCADE"), index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="SET NULL"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    s3_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    presigned_url = Column(Text)
    presigned_expires_at = Column(DateTime)
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Integer)
    resolution = Column(String(20))
    format = Column(String(20))
    status = Column(String(20), nullable=False, default='processing', index=True)
    error_message = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    rejection_reason = Column(Text)
    rejected_at = Column(DateTime)
    rejected_by_account_id = Column(Integer, ForeignKey("accounts.account_id"))
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id"))
    review_result = Column(JSONB)
    
    __table_args__ = (
        CheckConstraint("status IN ('processing', 'completed', 'client_approved', 'client_rejected', 'admin_approved', 'admin_rejected', 'published', 'failed')", name='videos_status_check'),
        Index('idx_videos_script', 'script_id', unique=True, postgresql_where=(script_id.isnot(None))),
    )
    
    # 관계
    ad_request = relationship("AdRequest", back_populates="videos")
    company = relationship("Company", back_populates="videos")
    script = relationship("ScenarioScript", back_populates="videos")
    admin_video_posts = relationship("AdminVideoPost", back_populates="video")
    performance_metrics = relationship("PerformanceMetric", back_populates="video")
