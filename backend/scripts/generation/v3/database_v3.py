"""
영상 생성 관련 데이터베이스 모델 및 함수 V3
새로운 스키마: video_projects, company_characters, workflow_execution
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, ARRAY, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import uuid

# auth/v3의 Base와 모델들을 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))
from database_v3 import Base, engine, SessionLocal, Account, Company

load_dotenv()


# ============================================
# 모델 정의
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
        CheckConstraint("status IN ('READY', 'PROCESSING', 'PROCESSED', 'COMPLETED', 'FAILED')", name='chk_meme_status'),
        CheckConstraint("meme_type IN ('quotable', 'performable', 'hybrid')", name='chk_meme_type'),
    )


class CompanyCharacter(Base):
    """회사별 캐릭터 자산"""
    __tablename__ = "company_characters"
    
    character_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    character_name = Column(String(255), nullable=False)
    character_mood = Column(String(255), nullable=False)
    character_style = Column(String(255), nullable=False)
    voice_tone = Column(String(255), nullable=False)
    image_url = Column(Text, nullable=False)
    voice_url = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoProject(Base):
    """영상 제작 프로젝트"""
    __tablename__ = "ad_requests"
    
    project_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    character_id = Column(Integer, ForeignKey("company_characters.character_id", ondelete="SET NULL"), index=True)
    
    # 제품 정보
    item_name = Column(String(255), nullable=False)
    item_category = Column(String(20))
    item_description = Column(Text)  # item_highlight -> item_description
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


class WorkflowExecution(Base):
    """워크플로우 실행 (진행 상태 관리)"""
    __tablename__ = "workflow_execution"
    
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Integer, ForeignKey("ad_requests.project_id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    
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


# ============================================
# VideoProject 관련 함수
# ============================================
def create_video_project(db, company_id: int, user_id: int, item_name: str,
                        item_category: str = None, item_description: str = None,
                        item_url: str = None, item_images: list = None,
                        character_id: int = None,
                        character_mood: str = None, character_style: str = None,
                        voice_tone: str = None, voice_description: str = None,
                        meme_id: int = None, reference_notes: str = None):
    """
    새 영상 프로젝트 생성
    """
    new_project = VideoProject(
        company_id=company_id,
        account_id=user_id,  # user_id -> account_id
        item_name=item_name,
        item_category=item_category,
        item_description=item_description,  # item_highlight -> item_description
        item_url=item_url,
        item_images=item_images or [],
        character_id=character_id,
        character_mood=character_mood,
        character_style=character_style,
        voice_tone=voice_tone,
        voice_description=voice_description,
        meme_id=meme_id,
        reference_notes=reference_notes,
        status='draft'
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    print(f"새 프로젝트 생성: Project ID {new_project.project_id}")
    return new_project


def get_project_by_id(db, project_id: int):
    """프로젝트 ID로 조회"""
    return db.query(VideoProject).filter(VideoProject.project_id == project_id).first()


def get_projects_by_company(db, company_id: int, limit: int = 10):
    """회사의 프로젝트 목록 조회"""
    return db.query(VideoProject).filter(
        VideoProject.company_id == company_id
    ).order_by(VideoProject.created_at.desc()).limit(limit).all()


def update_project_character(db, project_id: int, character_id: int):
    """프로젝트에 캐릭터 연결"""
    project = get_project_by_id(db, project_id)
    if project:
        project.character_id = character_id
        db.commit()
        db.refresh(project)
        print(f"프로젝트 {project_id}에 캐릭터 {character_id} 연결")
        return project
    return None


def update_project_status(db, project_id: int, status: str):
    """프로젝트 상태 업데이트"""
    project = get_project_by_id(db, project_id)
    if project:
        project.status = status
        if status == 'completed':
            project.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return project
    return None


# ============================================
# CompanyCharacter 관련 함수
# ============================================
def create_company_character(db, company_id: int, character_name: str,
                            character_mood: str, character_style: str,
                            voice_tone: str, image_url: str, voice_url: str,
                            is_active: bool = True):
    """
    새 캐릭터 생성
    """
    new_character = CompanyCharacter(
        company_id=company_id,
        character_name=character_name,
        character_mood=character_mood,
        character_style=character_style,
        voice_tone=voice_tone,
        image_url=image_url,
        voice_url=voice_url,
        is_active=is_active
    )
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    print(f"새 캐릭터 생성: Character ID {new_character.character_id}")
    return new_character


def get_character_by_id(db, character_id: int):
    """캐릭터 ID로 조회"""
    return db.query(CompanyCharacter).filter(CompanyCharacter.character_id == character_id).first()


def get_characters_by_company(db, company_id: int, active_only: bool = True):
    """회사의 캐릭터 목록 조회"""
    query = db.query(CompanyCharacter).filter(CompanyCharacter.company_id == company_id)
    if active_only:
        query = query.filter(CompanyCharacter.is_active == True)
    return query.order_by(CompanyCharacter.created_at.desc()).all()


def activate_character(db, character_id: int):
    """캐릭터 활성화"""
    character = get_character_by_id(db, character_id)
    if character:
        character.is_active = True
        db.commit()
        db.refresh(character)
        print(f"캐릭터 {character_id} 활성화 완료")
        return character
    return None


def deactivate_character(db, character_id: int):
    """캐릭터 비활성화"""
    character = get_character_by_id(db, character_id)
    if character:
        character.is_active = False
        db.commit()
        db.refresh(character)
        print(f"캐릭터 {character_id} 비활성화")
        return character
    return None


# ============================================
# WorkflowExecution 관련 함수
# ============================================
def create_workflow(db, project_id: int, company_id: int, account_id: int,
                   meme_id: int = None):
    """
    새 워크플로우 생성 (영상 생성 전용)
    """
    new_workflow = WorkflowExecution(
        project_id=project_id,
        company_id=company_id,
        account_id=account_id,
        meme_id=meme_id,
        status="created"
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    print(f"새 워크플로우 생성: Execution ID {new_workflow.execution_id}")
    return new_workflow


def get_workflow_by_id(db, execution_id: uuid.UUID):
    """Execution ID로 워크플로우 조회"""
    return db.query(WorkflowExecution).filter(WorkflowExecution.execution_id == execution_id).first()


def get_workflow_by_project(db, project_id: int):
    """프로젝트 ID로 워크플로우 조회"""
    return db.query(WorkflowExecution).filter(WorkflowExecution.project_id == project_id).first()


def get_workflows_by_company(db, company_id: int, limit: int = 10):
    """회사의 워크플로우 목록 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()


def update_workflow_status(db, execution_id: uuid.UUID, status: str,
                          current_stage: str = None, progress: int = None,
                          error_message: str = None):
    """워크플로우 상태 업데이트"""
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.status = status
        if current_stage:
            workflow.current_stage = current_stage
        if progress is not None:
            workflow.progress_percentage = progress
        if error_message:
            workflow.error_message = error_message
        
        # 완료 시간 업데이트
        if status in ["completed", "failed", "cancelled"]:
            workflow.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        print(f"워크플로우 상태 업데이트: {execution_id} -> {status}")
        return workflow
    return None


def increment_retry_count(db, execution_id: uuid.UUID):
    """재시도 횟수 증가"""
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.retry_count += 1
        db.commit()
        return workflow
    return None


# ============================================
# Meme 관련 함수
# ============================================
def get_meme_by_id(db, meme_id: int):
    """밈 ID로 조회"""
    return db.query(Meme).filter(Meme.meme_id == meme_id).first()


def get_meme_by_name(db, meme_name: str):
    """밈 이름으로 조회"""
    return db.query(Meme).filter(Meme.meme_name == meme_name).first()


# ============================================
# 중복 확인
# ============================================
def check_duplicate_project(db, company_id: int, item_name: str, meme_id: int):
    """
    중복 프로젝트 확인
    동일한 제품명과 밈으로 진행 중인 프로젝트가 있는지 확인
    """
    return db.query(VideoProject).filter(
        VideoProject.company_id == company_id,
        VideoProject.item_name == item_name,
        VideoProject.meme_id == meme_id,
        VideoProject.status.in_(['draft', 'processing'])
    ).first()


# ============================================
# WorkflowStage 관련 함수 (단계별 상세 정보)
# ============================================
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
    )


def get_workflow_stages(db, execution_id: uuid.UUID):
    """워크플로우의 모든 단계 조회"""
    from sqlalchemy import select
    return db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == execution_id
    ).order_by(WorkflowStage.stage_order).all()


def create_workflow_stage(db, execution_id: uuid.UUID, stage_name: str, stage_order: int):
    """새 워크플로우 단계 생성"""
    new_stage = WorkflowStage(
        execution_id=execution_id,
        stage_name=stage_name,
        stage_order=stage_order,
        status='pending'
    )
    db.add(new_stage)
    db.commit()
    db.refresh(new_stage)
    return new_stage


def initialize_workflow_stages(db, execution_id: uuid.UUID):
    """
    워크플로우 초기 단계 설정
    영상 생성 요청 시 호출하여 모든 단계를 초기화
    """
    stages = [
        {"name": "프로젝트 생성", "order": 1},
        {"name": "캐릭터 생성", "order": 2},
        {"name": "시나리오 생성", "order": 3},
        {"name": "음성 합성", "order": 4},
        {"name": "영상 렌더링", "order": 5},
        {"name": "품질 ��증", "order": 6},
        {"name": "S3 업로드", "order": 7}
    ]
    
    for stage_info in stages:
        create_workflow_stage(
            db=db,
            execution_id=execution_id,
            stage_name=stage_info["name"],
            stage_order=stage_info["order"]
        )
    
    print(f"워크플로우 단계 초기화 완료: {execution_id} (총 {len(stages)}개 단계)")


def update_stage_status(db, execution_id: uuid.UUID, stage_name: str, status: str, error_message: str = None):
    """단계 상태 업데이트"""
    stage = db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == execution_id,
        WorkflowStage.stage_name == stage_name
    ).first()
    
    if stage:
        stage.status = status
        
        if status == 'processing' and not stage.started_at:
            stage.started_at = datetime.utcnow()
        
        if status in ['completed', 'failed', 'skipped']:
            stage.completed_at = datetime.utcnow()
            if stage.started_at:
                duration = (stage.completed_at - stage.started_at).total_seconds()
                stage.duration_seconds = int(duration)
        
        if error_message:
            stage.error_message = error_message
        
        db.commit()
        db.refresh(stage)
        return stage
    return None


# ============================================
# 워크플로우 목록 조회 (필터링, 페이지네이션)
# ============================================
def get_workflows_by_company_filtered(db, company_id: int, 
                                     status: str = None,
                                     date_from: datetime = None,
                                     date_to: datetime = None,
                                     sort_by: str = 'created_at',
                                     order: str = 'desc',
                                     offset: int = 0,
                                     limit: int = 10):
    """
    회사의 워크플로우 목록 조회 (필터링, 페이지네이션)
    """
    query = db.query(WorkflowExecution).filter(WorkflowExecution.company_id == company_id)
    
    # 상태 필터링
    if status:
        query = query.filter(WorkflowExecution.status == status)
    
    # 날짜 범위 필터링
    if date_from:
        query = query.filter(WorkflowExecution.created_at >= date_from)
    if date_to:
        query = query.filter(WorkflowExecution.created_at <= date_to)
    
    # 정렬
    if sort_by == 'created_at':
        sort_column = WorkflowExecution.created_at
    elif sort_by == 'completed_at':
        sort_column = WorkflowExecution.completed_at
    else:
        sort_column = WorkflowExecution.created_at
    
    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # 총 개수
    total_count = query.count()
    
    # 페이지네이션
    workflows = query.offset(offset).limit(limit).all()
    
    return workflows, total_count


def get_average_processing_time(db, company_id: int = None):
    """
    평균 처리 시간 계산 (완료된 워크플로우 기준)
    """
    from sqlalchemy import func
    
    query = db.query(
        func.avg(
            func.extract('epoch', WorkflowExecution.completed_at - WorkflowExecution.created_at)
        ).label('avg_seconds')
    ).filter(
        WorkflowExecution.status == 'completed',
        WorkflowExecution.completed_at.isnot(None)
    )
    
    if company_id:
        query = query.filter(WorkflowExecution.company_id == company_id)
    
    result = query.first()
    return int(result.avg_seconds) if result and result.avg_seconds else 3600  # 기본값 1시간
