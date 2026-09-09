"""
워크플로우 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class WorkflowExecution(Base):
    """워크플로우 실행"""
    __tablename__ = "workflow_execution"
    
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    status = Column(String(50), nullable=False, default='created', index=True)
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    approval_status = Column(String(50))
    total_cost_usd = Column(Numeric(10, 4), default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, index=True)
    completed_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("status IN ('created', 'generating_character', 'generating_voice', 'generating_scenario', 'generating_video', 'content_generating', 'pending_approval', 'approved', 'rejected', 'processing', 'completed', 'failed', 'cancelled')", name='workflow_execution_status_check'),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name='workflow_execution_progress_percentage_check'),
        CheckConstraint("retry_count >= 0 AND retry_count <= 10", name='workflow_execution_retry_count_check'),
    )
    
    # 관계
    ad_request = relationship("AdRequest", back_populates="workflow_executions")
    workflow_stages = relationship("WorkflowStage", back_populates="execution")


class WorkflowStage(Base):
    """워크플로우 단계별 로그"""
    __tablename__ = "workflow_stages"
    
    stage_id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_execution.execution_id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'skipped')", name='workflow_stages_status_check'),
        UniqueConstraint('execution_id', 'stage_order', name='uq_execution_stage'),
    )
    
    # 관계
    execution = relationship("WorkflowExecution", back_populates="workflow_stages")
