"""
영상 생성 관련 데이터베이스 모델 및 함수 (단계별 추적 기능 포함)
작업 내용 3번: 워크플로우 실행 관리 + 단계별 상태 추적
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

# auth/v2의 Base와 모델들을 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v2'))
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
    
    # 단계별 정보 (JSONB) ✨ 추가됨
    stages_info = Column(JSONB)
    
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


# ============================================
# 단계별 정보 관리 함수 ✨ 새로 추가
# ============================================
def initialize_workflow_stages(db, execution_id: uuid.UUID):
    """
    워크플로우 초기 단계 설정
    영상 생성 요청 시 호출
    """
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        stages = [
            {"name": "파일 업로드", "status": "completed", "order": 1},
            {"name": "시나리오 생성", "status": "pending", "order": 2},
            {"name": "음성 합성", "status": "pending", "order": 3},
            {"name": "영상 렌더링", "status": "pending", "order": 4},
            {"name": "품질 검증", "status": "pending", "order": 5},
            {"name": "S3 업로드", "status": "pending", "order": 6}
        ]
        
        workflow.stages_info = {
            "stages": [
                {
                    **stage,
                    "started_at": None,
                    "completed_at": None,
                    "duration_seconds": None,
                    "error_message": None
                }
                for stage in stages
            ],
            "estimated_completion": None
        }
        
        db.commit()
        db.refresh(workflow)
        print(f"워크플로우 단계 초기화: {execution_id}")
        return workflow
    return None


def update_stage_status(db, execution_id: uuid.UUID, stage_name: str, 
                       status: str, duration_seconds: int = None, 
                       error_message: str = None):
    """
    특정 단계의 상태 업데이트
    파이프라인 팀이 호출하는 함수
    
    Args:
        execution_id: 워크플로우 ID
        stage_name: 단계명 (예: "시나리오 생성")
        status: 상태 (pending/processing/completed/failed)
        duration_seconds: 소요 시간 (completed 시)
        error_message: 에러 메시지 (failed 시)
    """
    workflow = get_workflow_by_id(db, execution_id)
    if not workflow or not workflow.stages_info:
        return None
    
    stages = workflow.stages_info.get("stages", [])
    
    for stage in stages:
        if stage["name"] == stage_name:
            stage["status"] = status
            
            if status == "processing":
                stage["started_at"] = datetime.utcnow().isoformat()
            elif status == "completed":
                stage["completed_at"] = datetime.utcnow().isoformat()
                if duration_seconds:
                    stage["duration_seconds"] = duration_seconds
            elif status == "failed":
                stage["error_message"] = error_message
            
            break
    
    workflow.stages_info = {"stages": stages, "estimated_completion": workflow.stages_info.get("estimated_completion")}
    db.commit()
    db.refresh(workflow)
    print(f"단계 상태 업데이트: {stage_name} -> {status}")
    return workflow


def get_stage_summary(workflow):
    """
    단계 정보 요약
    API 응답용
    
    Returns:
        completed_stages: 완료된 단계 목록
        current_stage: 현재 진행 중인 단계
        pending_stages: 대기 중인 단계 목록
    """
    if not workflow or not workflow.stages_info:
        return [], None, []
    
    stages = workflow.stages_info.get("stages", [])
    
    completed = [s for s in stages if s["status"] == "completed"]
    current = next((s for s in stages if s["status"] == "processing"), None)
    pending = [s["name"] for s in stages if s["status"] == "pending"]
    
    return completed, current, pending


def calculate_estimated_completion(workflow):
    """
    예상 완료 시간 계산
    완료된 단계들의 평균 소요 시간 기반
    
    Returns:
        estimated_completion: 예상 완료 시각 (ISO format)
        estimated_remaining_seconds: 남은 예상 시간 (초)
    """
    if not workflow or not workflow.stages_info:
        return None, None
    
    stages = workflow.stages_info.get("stages", [])
    
    # 완료된 단계들의 평균 소요 시간 계산
    completed_stages = [s for s in stages if s["status"] == "completed" and s.get("duration_seconds")]
    if not completed_stages:
        return None, None
    
    avg_duration = sum(s["duration_seconds"] for s in completed_stages) / len(completed_stages)
    
    # 남은 단계 수
    remaining_stages = len([s for s in stages if s["status"] in ["pending", "processing"]])
    
    # 예상 남은 시간
    estimated_remaining = int(avg_duration * remaining_stages)
    
    # 예상 완료 시각
    estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_remaining)
    
    return estimated_completion.isoformat(), estimated_remaining
