"""
영상 생성 관련 데이터베이스 모델 및 함수
작업 내용 3번: 워크플로우 실행 관리
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import uuid

# auth/v2의 Base와 모델들을 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'auth', 'v2'))
from database_v2 import Base, engine, SessionLocal, User, Company

load_dotenv()


# ============================================
# 모델 정의
# ============================================
class Meme(Base):
    """
    밈 데이터 테이블
    DMG 관련 요구사항
    """
    __tablename__ = "memes"
    
    meme_id = Column(Integer, primary_key=True, index=True)
    meme_name = Column(String(255), unique=True, nullable=False)
    definition = Column(Text)
    key_phrase = Column(String(255))
    risk_level = Column(String(50))
    motion_prompt = Column(Text)
    quality_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class WorkflowExecution(Base):
    """
    영상 제작 워크플로우 실행 테이블
    작업 내용 3번: 워크플로우 실행 관리
    
    상태(status) 값:
    - created: 요청 접수됨
    - generating_character: 캐릭터 이미지/음성 생성 중
    - pending_approval: 사용자 승인 대기 중
    - approved: 사용자가 승인함
    - rejected: 사용자가 거부함
    - processing: 영상 생성 중
    - completed: 완료
    - failed: 실패
    - cancelled: 취소됨
    """
    __tablename__ = "workflow_execution"
    
    # 기본 정보
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    
    # 워크플로우 타입 및 상태
    workflow_type = Column(String(50), nullable=False, default="video")
    status = Column(String(50), nullable=False, default="created")
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    scenario_status = Column(String(50))
    
    # 입력/출력 데이터 (JSONB)
    input_params = Column(JSONB, nullable=False)
    output_result = Column(JSONB)
    
    # 비용 및 에러
    total_cost_usd = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # 시간 정보
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))


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
# WorkflowExecution 관련 함수
# ============================================
def create_workflow(db, user_id: int, company_id: int, input_params: dict,
                   meme_id: int = None, workflow_type: str = "video"):
    """
    새 워크플로우 생성
    작업 내용 3번: workflow_execution 테이블에 작업 기록 생성
    """
    new_workflow = WorkflowExecution(
        user_id=user_id,
        company_id=company_id,
        meme_id=meme_id,
        workflow_type=workflow_type,
        input_params=input_params,
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


def get_workflows_by_user(db, user_id: int, limit: int = 10):
    """사용자의 워크플로우 목록 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.user_id == user_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()


def get_workflows_by_company(db, company_id: int, limit: int = 10):
    """회사의 워크플로우 목록 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()


def update_workflow_status(db, execution_id: uuid.UUID, status: str, 
                          current_stage: str = None, progress: int = None,
                          error_message: str = None):
    """
    워크플로우 상태 업데이트
    """
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


def update_workflow_output(db, execution_id: uuid.UUID, output_result: dict):
    """
    워크플로우 출력 결과 업데이트
    """
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.output_result = output_result
        db.commit()
        db.refresh(workflow)
        print(f"워크플로우 출력 업데이트: {execution_id}")
        return workflow
    return None


def check_duplicate_workflow(db, company_id: int, product_name: str, meme_id: int):
    """
    중복 워크플로우 확인 (DMG-AUTO-07)
    동일한 제품명과 밈으로 진행 중인 작업이 있는지 확인
    """
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.input_params['product_name'].astext == product_name,
        WorkflowExecution.meme_id == meme_id,
        WorkflowExecution.status.in_(['created', 'processing'])
    ).first()


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
