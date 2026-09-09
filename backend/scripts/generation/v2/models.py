"""
데이터베이스 모델 정의
새로운 테이블 구조에 맞춰 재작성
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float, ARRAY, Numeric, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from dotenv import load_dotenv
import uuid

load_dotenv()

# Base 생성
Base = declarative_base()

# 데이터베이스 연결
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================
# 1. 사용자 인증 및 권한
# ============================================

class Account(Base):
    """계정 공통 테이블"""
    __tablename__ = "accounts"
    
    account_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    account_type = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("account_type IN ('client', 'admin')", name='chk_account_type'),
    )


class Client(Base):
    """클라이언트 (일반 사용자)"""
    __tablename__ = "clients"
    
    client_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime)
    reset_token = Column(Text)
    reset_expires_at = Column(DateTime)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Admin(Base):
    """어드민 (비밀번호 로그인)"""
    __tablename__ = "admins"
    
    admin_id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    refresh_token = Column(Text)
    rt_expires_at = Column(DateTime)
    last_login_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Company(Base):
    """회사"""
    __tablename__ = "companies"
    
    company_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyMember(Base):
    """회사 멤버"""
    __tablename__ = "company_members"
    
    member_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    member_name = Column(String(100), nullable=False)
    department = Column(String(100))
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("role IN ('manager', 'member')", name='chk_member_role'),
    )


# ============================================
# 2. 콘텐츠 생성
# ============================================

class Meme(Base):
    """밈 데이터"""
    __tablename__ = "memes"
    
    meme_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    meme_name = Column(String(255), unique=True, nullable=False)
    definition = Column(Text)
    origin = Column(JSONB)
    key_phrase = Column(Text)
    sources = Column(JSONB, default=[])
    risk_info = Column(String(20))
    meme_type = Column(String(50))
    status = Column(String(50), default='READY')
    source_video = Column(JSONB, default={})
    video_analysis = Column(JSONB, default={})
    confidence = Column(Float)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("status IN ('READY', 'PROCESSING', 'COMPLETED', 'FAILED')", name='chk_meme_status'),
        CheckConstraint("meme_type IN ('Dialogue', 'Motion', 'Hybrid')", name='chk_meme_type'),
    )


class MemeExample(Base):
    """밈 사용 예시"""
    __tablename__ = "meme_examples"
    
    example_id = Column(Integer, primary_key=True, index=True)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="CASCADE"), nullable=False)
    situation = Column(String(255), nullable=False)
    dialogue_example = Column(Text)
    source_url = Column(String(500))
    example_type = Column(String(20))
    note = Column(Text)
    tone = Column(String(20))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class CompanyCharacter(Base):
    """회사별 캐릭터 자산"""
    __tablename__ = "company_characters"
    
    character_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    character_name = Column(String(255), nullable=False)
    character_mood = Column(String(255), nullable=False)
    character_style = Column(String(255), nullable=False)
    voice_tone = Column(String(255), nullable=False)
    image_url = Column(Text, nullable=False)
    voice_url = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    approval_status = Column(String(20), default='approved')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected')", name='chk_approval_status'),
    )


class VideoProject(Base):
    """영상 제작 프로젝트"""
    __tablename__ = "video_projects"
    
    project_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("company_characters.character_id", ondelete="SET NULL"))
    
    # 제품 정보
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(100))
    item_highlight = Column(Text)
    item_url = Column(String(500))
    item_images = Column(ARRAY(Text), default=[])
    
    # 캐릭터 입력값 (새로 생성할 때)
    character_mood = Column(String(255))
    character_style = Column(String(255))
    voice_tone = Column(String(255))
    voice_description = Column(Text)
    
    # 밈 정보
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    
    # 최종 결과물
    final_video_url = Column(Text)
    
    # 상태 및 관리
    status = Column(String(50), default='draft')
    reference_notes = Column(Text)
    
    # 비용 및 시간
    cost_estimate = Column(Numeric(10, 4), default=0)
    processing_time = Column(Integer)
    
    # 시간 정보
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("cardinality(item_images) <= 3", name='chk_item_images_count'),
    )


# ============================================
# 3. 생성/결과물
# ============================================

class PromptVersion(Base):
    """프롬프트 버전 관리"""
    __tablename__ = "prompt_versions"
    
    version_id = Column(Integer, primary_key=True, index=True)
    prompt_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSONB, default=[])
    model_config = Column(JSONB)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('prompt_name', 'version', name='uq_prompt_name_version'),
    )


class ScenarioScript(Base):
    """시나리오 스크립트"""
    __tablename__ = "scenario_scripts"
    
    script_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("video_projects.project_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="RESTRICT"), nullable=False)
    
    # 시나리오 메타데이터
    title = Column(String(255), nullable=False)
    description = Column(Text)
    hashtags = Column(ARRAY(Text))
    
    # 3단 구조 시나리오
    scenes = Column(JSONB, nullable=False)
    total_duration = Column(Float)
    
    # AI 생성 정보
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.version_id", ondelete="SET NULL"))
    used_model = Column(String(50))
    generation_cost = Column(Numeric(10, 4))
    processing_time_seconds = Column(Integer)
    
    # 품질 검증
    quality_check_passed = Column(Boolean, default=False)
    quality_issues = Column(ARRAY(Text))
    
    # 고객 승인
    approval_status = Column(String(20), default='pending')
    approval_requested_at = Column(DateTime)
    approved_at = Column(DateTime)
    approved_by_account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="SET NULL"))
    
    # 상태 관리
    status = Column(String(50), default='draft')
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("total_duration > 0 AND total_duration BETWEEN 15 AND 20", name='chk_total_duration'),
        CheckConstraint("approval_status IN ('pending', 'approved', 'rejected', 'auto_approved')", name='chk_approval_status'),
        CheckConstraint("status IN ('draft', 'validated', 'approved', 'rejected')", name='chk_status'),
    )


class SceneAsset(Base):
    """장면별 자산"""
    __tablename__ = "scene_assets"
    
    asset_id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id", ondelete="CASCADE"), nullable=False)
    scene_key = Column(String(50), nullable=False)
    
    # 음성 파일
    audio_url = Column(Text)
    audio_duration_seconds = Column(Float)
    audio_storage_path = Column(String(500))
    
    # 캐릭터 이미지
    character_image_url = Column(Text)
    character_image_storage_path = Column(String(500))
    
    # 씬 영상
    scene_video_url = Column(Text)
    scene_video_storage_path = Column(String(500))
    scene_video_duration = Column(Float)
    
    # 캐릭터 일관성 점수
    character_similarity_score = Column(Float)
    
    # 생성 정보
    generation_model = Column(String(50))
    generation_cost = Column(Numeric(10, 4))
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('script_id', 'scene_key', name='uq_script_scene'),
    )


class Video(Base):
    """최종 영상"""
    __tablename__ = "videos"
    
    video_id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("video_projects.project_id", ondelete="CASCADE"))
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="SET NULL"))
    
    # 메타데이터
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 파일 접근 정보
    s3_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text)
    presigned_url = Column(Text)
    presigned_expires_at = Column(DateTime)
    
    # 파일 상세 정보
    file_size_bytes = Column(Integer)
    duration_seconds = Column(Integer)
    resolution = Column(String(20))
    format = Column(String(20))
    download_count = Column(Integer, default=0)
    
    # 상태 및 로그
    status = Column(String(20), nullable=False, default='processing')
    error_message = Column(Text)
    
    # 시간 정보
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        CheckConstraint("status IN ('processing', 'completed', 'failed')", name='chk_status'),
    )


# ============================================
# 5. 운영/자동화
# ============================================

class WorkflowExecution(Base):
    """워크플로우 실행 (진행 상태 관리)"""
    __tablename__ = "workflow_execution"
    
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("video_projects.project_id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    
    workflow_type = Column(String(50), nullable=False, default="video")
    status = Column(String(50), nullable=False, default="created")
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    approval_status = Column(String(50))
    
    total_cost_usd = Column(Numeric(10, 4), default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    completed_at = Column(TIMESTAMP(timezone=True))
    
    __table_args__ = (
        CheckConstraint("status IN ('created', 'generating_character', 'pending_approval', 'approved', 'rejected', 'processing', 'completed', 'failed', 'cancelled')", name='chk_workflow_status'),
        CheckConstraint("progress_percentage BETWEEN 0 AND 100", name='chk_progress_range'),
        CheckConstraint("retry_count BETWEEN 0 AND 10", name='chk_retry_limit'),
    )


class WorkflowStage(Base):
    """워크플로우 단계별 로그"""
    __tablename__ = "workflow_stages"
    
    stage_id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_execution.execution_id", ondelete="CASCADE"), nullable=False)
    
    stage_name = Column(String(100), nullable=False)
    stage_order = Column(Integer, nullable=False)
    status = Column(String(50), default='pending', nullable=False)
    
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    duration_seconds = Column(Integer)
    
    error_message = Column(Text)
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'skipped')", name='chk_stage_status'),
        UniqueConstraint('execution_id', 'stage_order', name='uq_execution_stage'),
    )


# ============================================
# 데이터베이스 세션
# ============================================

def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
