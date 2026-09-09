"""
유튜브 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

from app.db.base import Base
from app.core.security import encrypt_token, decrypt_token


class AdminYoutubeChannel(Base):
    """어드민 유튜브 채널"""
    __tablename__ = "admin_youtube_channels"
    
    channel_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id", ondelete="CASCADE"), unique=True, nullable=False)
    yt_channel_id = Column(String(255), unique=True, nullable=False)
    channel_name = Column(String(255), nullable=False)
    channel_handle = Column(String(255))
    _access_token = Column("access_token", Text, nullable=False)  # 암호화된 토큰
    _refresh_token = Column("refresh_token", Text, nullable=False)  # 암호화된 토큰
    token_expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_synced_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    admin = relationship("Admin", back_populates="youtube_channel")
    video_posts = relationship("AdminVideoPost", back_populates="channel")
    
    # 암호화된 토큰 프로퍼티
    @hybrid_property
    def access_token(self) -> str:
        """암호화된 access_token 복호화"""
        if self._access_token:
            try:
                return decrypt_token(self._access_token)
            except Exception:
                return self._access_token  # 복호화 실패 시 원본 반환
        return None
    
    @access_token.setter
    def access_token(self, value: str):
        """access_token 암호화해서 저장"""
        if value:
            self._access_token = encrypt_token(value)
        else:
            self._access_token = None
    
    @hybrid_property
    def refresh_token(self) -> str:
        """암호화된 refresh_token 복호화"""
        if self._refresh_token:
            try:
                return decrypt_token(self._refresh_token)
            except Exception:
                return self._refresh_token  # 복호화 실패 시 원본 반환
        return None
    
    @refresh_token.setter
    def refresh_token(self, value: str):
        """refresh_token 암호화해서 저장"""
        if value:
            self._refresh_token = encrypt_token(value)
        else:
            self._refresh_token = None


class AdminVideoPost(Base):
    """어드민 비디오 게시"""
    __tablename__ = "admin_video_posts"
    
    post_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("admin_youtube_channels.channel_id", ondelete="CASCADE"), nullable=False)
    yt_video_id = Column(String(255), unique=True)
    yt_title = Column(String(255))
    yt_description = Column(Text)
    post_status = Column(String(20), nullable=False, default='pending')
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_channel_status', 'channel_id', 'post_status'),
        Index('idx_scheduled', 'scheduled_at', postgresql_where=(post_status == 'pending')),
    )
    
    # 관계
    video = relationship("Video", back_populates="admin_video_posts")
    channel = relationship("AdminYoutubeChannel", back_populates="video_posts")
    performance_metrics = relationship("PerformanceMetric", back_populates="post")
