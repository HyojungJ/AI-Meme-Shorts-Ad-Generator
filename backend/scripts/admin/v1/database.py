"""
Admin API 데이터베이스 함수
작성일: 2026-01-22
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, TIMESTAMP, Boolean, ARRAY, ForeignKey, Float, func, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, List, Dict, Tuple
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
    ad_id = Column(Integer, ForeignKey("ad_requests.ad_id"))
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id"))
    
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    s3_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    
    file_size_bytes = Column(BigInteger)
    duration_seconds = Column(Integer)
    resolution = Column(String(20))
    format = Column(String(20))
    
    status = Column(String(20), nullable=False, default='processing')
    error_message = Column(Text)
    
    rejection_reason = Column(Text)
    rejected_at = Column(TIMESTAMP)
    rejected_by_account_id = Column(Integer, ForeignKey("accounts.account_id"))
    
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(TIMESTAMP)


class Company(Base):
    """회사 테이블"""
    __tablename__ = "companies"
    
    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoProject(Base):
    """영상 프로젝트 테이블"""
    __tablename__ = "ad_requests"
    
    ad_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    cost_estimate = Column(Integer)
    processing_time = Column(Integer)


class WorkflowExecution(Base):
    """워크플로우 실행 테이블"""
    __tablename__ = "workflow_execution"
    
    execution_id = Column(UUID, primary_key=True)
    project_id = Column(Integer, ForeignKey("ad_requests.ad_id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)
    
    status = Column(String(50), nullable=False, default='created')
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    
    total_cost_usd = Column(Float, default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP)


class WorkflowStage(Base):
    """워크플로우 단계 테이블"""
    __tablename__ = "workflow_stages"
    
    stage_id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(UUID, ForeignKey("workflow_execution.execution_id"), nullable=False)
    
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    duration_seconds = Column(Integer)
    
    error_message = Column(Text)


class Meme(Base):
    """밈 테이블"""
    __tablename__ = "memes"
    
    meme_id = Column(Integer, primary_key=True, index=True)
    meme_name = Column(String(255), nullable=False, unique=True)
    definition = Column(Text)
    origin = Column(Text)  # JSONB -> Text로 단순화
    key_phrase = Column(Text)
    sources = Column(Text)  # JSONB -> Text로 단순화
    risk_info = Column(String(20))
    meme_type = Column(String(50))
    status = Column(String(50), default='READY')
    confidence = Column(Float)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyMember(Base):
    """회사 멤버 테이블"""
    __tablename__ = "company_members"
    
    member_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id"), nullable=False)
    role = Column(String(20), nullable=False)
    member_name = Column(String(100), nullable=False)
    department = Column(String(100))
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Account(Base):
    """계정 테이블"""
    __tablename__ = "accounts"
    
    account_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    account_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminVideoPost(Base):
    """Admin 영상 게시 테이블"""
    __tablename__ = "admin_video_posts"
    
    post_id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.video_id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("admin_youtube_channels.channel_id"), nullable=False)
    
    yt_video_id = Column(String(255), unique=True)
    yt_title = Column(String(255))
    yt_description = Column(Text)
    
    post_status = Column(String(20), nullable=False, default='pending')
    
    scheduled_at = Column(TIMESTAMP)
    published_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    """Admin 영상 게시 테이블"""
    __tablename__ = "admin_video_posts"
    
    post_id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.video_id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("admin_youtube_channels.channel_id"), nullable=False)
    
    yt_video_id = Column(String(255), unique=True)
    yt_title = Column(String(255))
    yt_description = Column(Text)
    
    post_status = Column(String(20), nullable=False, default='pending')
    
    scheduled_at = Column(TIMESTAMP)
    published_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)


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
# 1. 전체 영상 목록 관리
# ============================================
def get_all_videos_filtered(
    db: Session,
    company_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Video], int]:
    """
    전체 영상 목록 조회 (Admin 전용)
    
    Returns:
        (videos, total_count)
    """
    query = db.query(Video, Company).join(
        Company, Video.company_id == Company.company_id
    )
    
    # 회사별 필터링
    if company_id:
        query = query.filter(Video.company_id == company_id)
    
    # 상태별 필터링
    if status:
        query = query.filter(Video.status == status)
    
    # 검색 (회사명 또는 제품명)
    if search:
        query = query.filter(
            or_(
                Company.company_name.ilike(f'%{search}%'),
                Video.title.ilike(f'%{search}%')
            )
        )
    
    # 날짜 범위 필터링
    if date_from:
        query = query.filter(Video.created_at >= date_from)
    if date_to:
        query = query.filter(Video.created_at <= date_to)
    
    # 총 개수
    total_count = query.count()
    
    # 정렬
    if sort_by == 'created_at':
        sort_column = Video.created_at
    elif sort_by == 'completed_at':
        sort_column = Video.completed_at
    elif sort_by == 'company_name':
        sort_column = Company.company_name
    else:
        sort_column = Video.created_at
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 페이지네이션
    results = query.offset(offset).limit(limit).all()
    
    # Video 객체만 추출
    videos = [result[0] for result in results]
    
    return videos, total_count


def get_video_with_company(db: Session, video_id: int) -> Optional[Dict]:
    """
    영상 정보와 회사 정보 함께 조회
    
    Returns:
        {
            'video': Video,
            'company': Company,
            'project': VideoProject
        }
    """
    result = db.query(Video, Company, VideoProject).join(
        Company, Video.company_id == Company.company_id
    ).outerjoin(
        VideoProject, Video.ad_id == VideoProject.ad_id
    ).filter(Video.video_id == video_id).first()
    
    if not result:
        return None
    
    return {
        'video': result[0],
        'company': result[1],
        'project': result[2]
    }


# ============================================
# 2. 영상 게시 관리
# ============================================
def get_pending_videos(db: Session, offset: int = 0, limit: int = 20) -> Tuple[List[Video], int]:
    """
    게시 대기 영상 목록 조회 (client_approved 상태)
    """
    query = db.query(Video, Company).join(
        Company, Video.company_id == Company.company_id
    ).filter(Video.status == 'client_approved')
    
    total_count = query.count()
    
    results = query.order_by(Video.completed_at.desc()).offset(offset).limit(limit).all()
    videos = [result[0] for result in results]
    
    return videos, total_count


def create_video_post(
    db: Session,
    video_id: int,
    channel_id: int,
    yt_title: Optional[str] = None,
    yt_description: Optional[str] = None,
    scheduled_at: Optional[datetime] = None
) -> AdminVideoPost:
    """
    영상 게시 레코드 생성
    """
    post = AdminVideoPost(
        video_id=video_id,
        channel_id=channel_id,
        yt_title=yt_title,
        yt_description=yt_description,
        scheduled_at=scheduled_at,
        post_status='pending'
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return post


def update_video_post_status(
    db: Session,
    post_id: int,
    status: str,
    yt_video_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> AdminVideoPost:
    """
    영상 게시 상태 업데이트
    """
    post = db.query(AdminVideoPost).filter(AdminVideoPost.post_id == post_id).first()
    if not post:
        return None
    
    post.post_status = status
    
    if yt_video_id:
        post.yt_video_id = yt_video_id
    
    if status == 'published':
        post.published_at = datetime.utcnow()
    
    if error_message:
        post.error_message = error_message
        post.retry_count += 1
    
    db.commit()
    db.refresh(post)
    
    return post


# ============================================
# 3. 시스템 모니터링
# ============================================
def get_active_workflows(db: Session, offset: int = 0, limit: int = 20) -> Tuple[List[WorkflowExecution], int]:
    """
    진행 중인 워크플로우 목록 조회
    """
    query = db.query(WorkflowExecution).filter(
        WorkflowExecution.status.in_(['created', 'generating_character', 'pending_approval', 'processing'])
    )
    
    total_count = query.count()
    
    workflows = query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(limit).all()
    
    return workflows, total_count


def get_failed_workflows(db: Session, offset: int = 0, limit: int = 20) -> Tuple[List[WorkflowExecution], int]:
    """
    실패한 워크플로우 목록 조회
    """
    query = db.query(WorkflowExecution).filter(WorkflowExecution.status == 'failed')
    
    total_count = query.count()
    
    workflows = query.order_by(WorkflowExecution.created_at.desc()).offset(offset).limit(limit).all()
    
    return workflows, total_count


def get_workflow_with_stages(db: Session, execution_id: str) -> Optional[Dict]:
    """
    워크플로우와 단계 정보 함께 조회
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if not workflow:
        return None
    
    stages = db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == execution_id
    ).order_by(WorkflowStage.stage_order).all()
    
    return {
        'workflow': workflow,
        'stages': stages
    }


def retry_workflow(db: Session, execution_id: str) -> WorkflowExecution:
    """
    워크플로우 재시도
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if not workflow:
        return None
    
    workflow.status = 'created'
    workflow.retry_count += 1
    workflow.error_message = None
    workflow.progress_percentage = 0
    
    db.commit()
    db.refresh(workflow)
    
    return workflow


def cancel_workflow(db: Session, execution_id: str) -> WorkflowExecution:
    """
    워크플로우 취소
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if not workflow:
        return None
    
    workflow.status = 'cancelled'
    workflow.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workflow)
    
    return workflow



# ============================================
# 4. 밈 데이터 관리
# ============================================
def get_all_memes_filtered(
    db: Session,
    status: Optional[str] = None,
    meme_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Meme], int]:
    """
    밈 목록 조회 (필터링, 검색)
    """
    query = db.query(Meme)
    
    # 상태 필터링
    if status:
        query = query.filter(Meme.status == status)
    
    # 타입 필터링
    if meme_type:
        query = query.filter(Meme.meme_type == meme_type)
    
    # 검색 (밈 이름 또는 정의)
    if search:
        query = query.filter(
            or_(
                Meme.meme_name.ilike(f'%{search}%'),
                Meme.definition.ilike(f'%{search}%')
            )
        )
    
    # 총 개수
    total_count = query.count()
    
    # 정렬
    if sort_by == 'created_at':
        sort_column = Meme.created_at
    elif sort_by == 'updated_at':
        sort_column = Meme.updated_at
    elif sort_by == 'meme_name':
        sort_column = Meme.meme_name
    elif sort_by == 'confidence':
        sort_column = Meme.confidence
    else:
        sort_column = Meme.created_at
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 페이지네이션
    memes = query.offset(offset).limit(limit).all()
    
    return memes, total_count


def get_meme_by_id(db: Session, meme_id: int) -> Optional[Meme]:
    """밈 상세 조회"""
    return db.query(Meme).filter(Meme.meme_id == meme_id).first()


def create_meme(
    db: Session,
    meme_name: str,
    definition: Optional[str] = None,
    origin: Optional[str] = None,
    key_phrase: Optional[str] = None,
    meme_type: Optional[str] = None,
    risk_info: Optional[str] = None
) -> Meme:
    """밈 수동 추가"""
    meme = Meme(
        meme_name=meme_name,
        definition=definition,
        origin=origin,
        key_phrase=key_phrase,
        meme_type=meme_type,
        risk_info=risk_info,
        status='READY'
    )
    
    db.add(meme)
    db.commit()
    db.refresh(meme)
    
    return meme


def update_meme(
    db: Session,
    meme_id: int,
    meme_name: Optional[str] = None,
    definition: Optional[str] = None,
    origin: Optional[str] = None,
    key_phrase: Optional[str] = None,
    meme_type: Optional[str] = None,
    risk_info: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[Meme]:
    """밈 정보 수정"""
    meme = db.query(Meme).filter(Meme.meme_id == meme_id).first()
    if not meme:
        return None
    
    if meme_name is not None:
        meme.meme_name = meme_name
    if definition is not None:
        meme.definition = definition
    if origin is not None:
        meme.origin = origin
    if key_phrase is not None:
        meme.key_phrase = key_phrase
    if meme_type is not None:
        meme.meme_type = meme_type
    if risk_info is not None:
        meme.risk_info = risk_info
    if status is not None:
        meme.status = status
    
    meme.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(meme)
    
    return meme


def delete_meme(db: Session, meme_id: int) -> bool:
    """밈 삭제 (소프트 삭제 - 상태를 DELETED로 변경)"""
    meme = db.query(Meme).filter(Meme.meme_id == meme_id).first()
    if not meme:
        return False
    
    meme.status = 'DELETED'
    meme.updated_at = datetime.utcnow()
    
    db.commit()
    
    return True


def get_meme_quality_stats(db: Session) -> Dict:
    """밈 품질 통계"""
    total_count = db.query(Meme).count()
    ready_count = db.query(Meme).filter(Meme.status == 'READY').count()
    processing_count = db.query(Meme).filter(Meme.status == 'PROCESSING').count()
    
    avg_confidence = db.query(func.avg(Meme.confidence)).filter(
        Meme.confidence.isnot(None)
    ).scalar()
    
    return {
        'total_count': total_count,
        'ready_count': ready_count,
        'processing_count': processing_count,
        'avg_confidence': float(avg_confidence) if avg_confidence else 0.0
    }


# ============================================
# 5. 회사 관리
# ============================================
def get_all_companies_filtered(
    db: Session,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 20
) -> Tuple[List[Company], int]:
    """
    전체 회사 목록 조회
    """
    query = db.query(Company)
    
    # 활성화 상태 필터링
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    
    # 검색 (회사명)
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    
    # 총 개수
    total_count = query.count()
    
    # 정렬
    if sort_by == 'created_at':
        sort_column = Company.created_at
    elif sort_by == 'company_name':
        sort_column = Company.company_name
    else:
        sort_column = Company.created_at
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 페이지네이션
    companies = query.offset(offset).limit(limit).all()
    
    return companies, total_count


def get_company_detail(db: Session, company_id: int) -> Optional[Dict]:
    """
    회사 상세 정보 조회 (멤버 수, 영상 수 포함)
    """
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        return None
    
    # 멤버 수
    member_count = db.query(CompanyMember).filter(
        CompanyMember.company_id == company_id
    ).count()
    
    # 영상 수
    video_count = db.query(Video).filter(Video.company_id == company_id).count()
    
    # 완료된 영상 수
    completed_video_count = db.query(Video).filter(
        Video.company_id == company_id,
        Video.status.in_(['completed', 'client_approved', 'admin_approved', 'published'])
    ).count()
    
    return {
        'company': company,
        'member_count': member_count,
        'video_count': video_count,
        'completed_video_count': completed_video_count
    }


def toggle_company_active(db: Session, company_id: int, is_active: bool) -> Optional[Company]:
    """
    회사 활성화/비활성화
    """
    company = db.query(Company).filter(Company.company_id == company_id).first()
    if not company:
        return None
    
    company.is_active = is_active
    company.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(company)
    
    return company


def get_company_video_stats(db: Session, company_id: int) -> Dict:
    """
    회사별 영상 제작 통계
    """
    # 상태별 영상 수
    status_counts = db.query(
        Video.status,
        func.count(Video.video_id).label('count')
    ).filter(
        Video.company_id == company_id
    ).group_by(Video.status).all()
    
    status_dict = {status: count for status, count in status_counts}
    
    # 총 영상 수
    total_videos = sum(status_dict.values())
    
    # 평균 제작 시간
    avg_processing_time = db.query(
        func.avg(VideoProject.processing_time)
    ).join(
        Video, Video.ad_id == VideoProject.ad_id
    ).filter(
        Video.company_id == company_id,
        VideoProject.processing_time.isnot(None)
    ).scalar()
    
    return {
        'total_videos': total_videos,
        'status_counts': status_dict,
        'avg_processing_time_minutes': int(avg_processing_time) if avg_processing_time else 0
    }


def get_company_cost_stats(db: Session, company_id: int) -> Dict:
    """
    회사별 비용 집계
    """
    # 총 비용
    total_cost = db.query(
        func.sum(VideoProject.cost_estimate)
    ).join(
        Video, Video.ad_id == VideoProject.ad_id
    ).filter(
        Video.company_id == company_id,
        VideoProject.cost_estimate.isnot(None)
    ).scalar()
    
    # 평균 비용
    avg_cost = db.query(
        func.avg(VideoProject.cost_estimate)
    ).join(
        Video, Video.ad_id == VideoProject.ad_id
    ).filter(
        Video.company_id == company_id,
        VideoProject.cost_estimate.isnot(None)
    ).scalar()
    
    # 영상 수
    video_count = db.query(Video).filter(Video.company_id == company_id).count()
    
    return {
        'total_cost_usd': float(total_cost) if total_cost else 0.0,
        'avg_cost_usd': float(avg_cost) if avg_cost else 0.0,
        'video_count': video_count
    }


def get_company_members(db: Session, company_id: int) -> List[Dict]:
    """
    회사 멤버 목록 조회
    """
    members = db.query(CompanyMember, Account).join(
        Account, CompanyMember.account_id == Account.account_id
    ).filter(
        CompanyMember.company_id == company_id
    ).all()
    
    result = []
    for member, account in members:
        result.append({
            'member_id': member.member_id,
            'account_id': member.account_id,
            'email': account.email,
            'member_name': member.member_name,
            'role': member.role,
            'department': member.department,
            'is_primary': member.is_primary,
            'is_active': account.is_active,
            'created_at': member.created_at
        })
    
    return result
