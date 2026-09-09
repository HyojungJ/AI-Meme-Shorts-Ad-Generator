"""
영상 다운로드 및 승인/거부 데이터베이스 함수
작성일: 2026-01-22
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, TIMESTAMP, Boolean, ARRAY, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, Dict
import os

# 환경 변수에서 DB 연결 정보 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/meme_influencer"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================
# 데이터베이스 모델
# ============================================
class Video(Base):
    """영상 테이블"""
    __tablename__ = "videos"
    
    video_id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id"))  # project_id 역할
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # S3 파일 정보
    s3_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    presigned_url = Column(Text)
    presigned_expires_at = Column(TIMESTAMP)
    
    # 파일 메타데이터
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Integer)
    resolution = Column(String(20))
    format = Column(String(20))
    
    # 상태 (마이그레이션으로 확장됨)
    status = Column(String(20), nullable=False, default='processing')
    error_message = Column(Text)
    
    # 거부 관련 (마이그레이션으로 추가됨)
    rejection_reason = Column(Text)
    rejected_at = Column(TIMESTAMP)
    rejected_by_account_id = Column(Integer, ForeignKey("accounts.account_id"))
    
    # 시간 정보
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(TIMESTAMP)


class VideoProject(Base):
    """영상 프로젝트 테이블 (ad_requests 역할)"""
    __tablename__ = "ad_requests"
    
    ad_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    
    # 비용 및 시간
    cost_estimate = Column(Integer)  # NUMERIC(10, 4)로 변경 필요
    processing_time = Column(Integer)


# ============================================
# DB 세션 관리
# ============================================
def get_db():
    """DB 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# 영상 조회 함수
# ============================================
def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    """영상 ID로 조회"""
    return db.query(Video).filter(Video.video_id == video_id).first()


def get_video_with_project_info(db: Session, video_id: int) -> Optional[Dict]:
    """
    영상 정보와 프로젝트 정보를 함께 조회
    
    Returns:
        {
            'video': Video,
            'project': VideoProject
        }
    """
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        return None
    
    project = None
    if video.ad_id:
        project = db.query(VideoProject).filter(VideoProject.ad_id == video.ad_id).first()
    
    return {
        'video': video,
        'project': project
    }


# ============================================
# 영상 승인 함수
# ============================================
def approve_video(
    db: Session,
    video_id: int,
    approval_type: str,
    approved_by_account_id: int
) -> Video:
    """
    영상 승인 처리
    
    Args:
        video_id: 영상 ID
        approval_type: 'client' 또는 'admin'
        approved_by_account_id: 승인자 계정 ID
    
    Returns:
        업데이트된 Video 객체
    """
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        return None
    
    # 상태 변경
    if approval_type == 'client':
        video.status = 'client_approved'
    elif approval_type == 'admin':
        video.status = 'admin_approved'
    
    video.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(video)
    
    return video


# ============================================
# 영상 거부 함수
# ============================================
def reject_video(
    db: Session,
    video_id: int,
    rejection_type: str,
    rejection_reason: str,
    rejected_by_account_id: int
) -> Video:
    """
    영상 거부 처리
    
    Args:
        video_id: 영상 ID
        rejection_type: 'client' 또는 'admin'
        rejection_reason: 거부 사유
        rejected_by_account_id: 거부자 계정 ID
    
    Returns:
        업데이트된 Video 객체
    """
    video = db.query(Video).filter(Video.video_id == video_id).first()
    if not video:
        return None
    
    # 상태 변경
    if rejection_type == 'client':
        video.status = 'client_rejected'
    elif rejection_type == 'admin':
        video.status = 'admin_rejected'
    
    # 거부 정보 저장
    video.rejection_reason = rejection_reason
    video.rejected_at = datetime.utcnow()
    video.rejected_by_account_id = rejected_by_account_id
    video.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(video)
    
    return video
