"""
분석 및 로그 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, Boolean, DateTime, ForeignKey, CheckConstraint, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class PerformanceMetric(Base):
    """성능 지표"""
    __tablename__ = "performance_metrics"
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.video_id", ondelete="CASCADE"), index=True)
    post_id = Column(Integer, ForeignKey("admin_video_posts.post_id", ondelete="CASCADE"), index=True)
    captured_at = Column(DateTime, nullable=False, index=True)
    snapshot_type = Column(String(20), nullable=False, index=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_seconds = Column(BigInteger, default=0)
    average_view_duration = Column(Float)
    audience_retention_rate = Column(Float)
    engagement_rate = Column(Float)
    subscribers_gained = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("(video_id IS NOT NULL AND post_id IS NULL) OR (video_id IS NULL AND post_id IS NOT NULL)", name='chk_video_or_post'),
        CheckConstraint("snapshot_type IN ('realtime', 'daily', 'monthly')", name='performance_metrics_snapshot_type_check'),
        Index('idx_performance_metrics_daily_unique', 'video_id', 'post_id', 'captured_at', unique=True, postgresql_where=(snapshot_type == 'daily')),
    )
    
    # 관계
    video = relationship("Video", back_populates="performance_metrics")
    post = relationship("AdminVideoPost", back_populates="performance_metrics")


class PromptVersion(Base):
    """프롬프트 버전 관리"""
    __tablename__ = "prompt_versions"
    
    version_id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSONB, default=[])
    model_config = Column(JSONB)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('uq_prompt_name_version', 'prompt_name', 'version', unique=True),
        Index('idx_prompt_versions_active', 'prompt_name', unique=True, postgresql_where=(is_active == True)),
    )
    
    # 관계
    scenario_scripts = relationship("ScenarioScript", back_populates="prompt_version")
    usage_logs = relationship("PromptUsageLog", back_populates="prompt_version")


class PromptUsageLog(Base):
    """프롬프트 사용 로그"""
    __tablename__ = "prompt_usage_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    version_id = Column(Integer, ForeignKey("prompt_versions.version_id", ondelete="CASCADE"), nullable=False, index=True)
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id", ondelete="CASCADE"), index=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id", ondelete="CASCADE"))
    latency_ms = Column(Integer)
    token_usage = Column(JSONB)
    quality_score = Column(Numeric(3, 2))
    success = Column(Boolean, nullable=False)
    error_log = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # 관계
    prompt_version = relationship("PromptVersion", back_populates="usage_logs")
    ad_request = relationship("AdRequest", back_populates="prompt_usage_logs")
    script = relationship("ScenarioScript", back_populates="prompt_usage_logs")


class RetryQueue(Base):
    """재시도 큐"""
    __tablename__ = "retry_queue"
    
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    meme_name = Column(String(255), nullable=False)
    failed_stage = Column(String(50))
    error_message = Column(Text)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    last_attempted_at = Column(DateTime)
    status = Column(String(20), default='pending', index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name='retry_queue_status_check'),
        Index('idx_retry_queue_next_retry', 'next_retry_at', postgresql_where=(status == 'pending')),
    )
