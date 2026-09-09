"""
시나리오 검수 데이터베이스 함수
"""
import os
import sys
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, ARRAY, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'generation', 'v3'))

from generation.v3.database_v3 import Base, engine, SessionLocal
from generation.v3.database_v3 import WorkflowExecution, Meme


# ============================================
# 모델 정의
# ============================================
class ScenarioScript(Base):
    """시나리오 스크립트 테이블"""
    __tablename__ = "scenario_scripts"
    
    script_id = Column(Integer, primary_key=True, index=True)
    
    # 연결 정보
    project_id = Column(Integer, ForeignKey("ad_requests.project_id"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id"), nullable=False)
    
    # 시나리오 메타데이터
    title = Column(String(255), nullable=False)
    description = Column(Text)
    hashtags = Column(ARRAY(Text))
    
    # 3단 구조 시나리오
    scenes = Column(JSONB, nullable=False)
    total_duration = Column(Float, nullable=False)
    
    # AI 생성 정보
    prompt_version_id = Column(Integer)
    used_model = Column(String(50))
    generation_cost = Column(Numeric(10, 4))
    processing_time_seconds = Column(Integer)
    
    # 품질 검증
    quality_check_passed = Column(Boolean, default=False)
    quality_issues = Column(ARRAY(Text))
    
    # 고객 승인
    approval_status = Column(String(20), default='pending')  # pending, approved, rejected, auto_approved
    approval_requested_at = Column(TIMESTAMP(timezone=True))
    approved_at = Column(TIMESTAMP(timezone=True))
    approved_by_account_id = Column(Integer)
    
    # 상태 관리
    status = Column(String(50), default='draft')  # draft, validated, approved, rejected
    
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    meme = relationship("Meme", foreign_keys=[meme_id])


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
# 시나리오 조회 함수
# ============================================
def get_scenarios_by_job(db, execution_id: str) -> tuple:
    """
    job_id(execution_id)로 연결된 시나리오 후보 조회
    
    Returns:
        (workflow, scenarios) 튜플
    """
    # 워크플로우 조회
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == uuid.UUID(execution_id)
    ).first()
    
    if not workflow:
        return None, []
    
    # 해당 프로젝트의 시나리오 조회 (최대 2개)
    scenarios = db.query(ScenarioScript).filter(
        ScenarioScript.project_id == workflow.project_id,
        ScenarioScript.approval_status.in_(['pending', 'approved', 'rejected'])
    ).order_by(ScenarioScript.created_at.desc()).limit(2).all()
    
    return workflow, scenarios


def get_scenario_by_id(db, script_id: int) -> Optional[ScenarioScript]:
    """시나리오 ID로 조회"""
    return db.query(ScenarioScript).filter(
        ScenarioScript.script_id == script_id
    ).first()


# ============================================
# 시나리오 승인 함수
# ============================================
def approve_scenario_by_id(db, script_id: int, account_id: int) -> ScenarioScript:
    """
    시나리오 승인 처리
    
    Args:
        script_id: 승인할 시나리오 ID
        account_id: 승인자 계정 ID
    
    Returns:
        승인된 시나리오 객체
    """
    scenario = get_scenario_by_id(db, script_id)
    
    if not scenario:
        return None
    
    # 승인 처리
    scenario.approval_status = 'approved'
    scenario.status = 'approved'
    scenario.approved_at = datetime.utcnow()
    scenario.approved_by_account_id = account_id
    scenario.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(scenario)
    
    print(f"시나리오 승인: script_id={script_id}, account_id={account_id}")
    return scenario


def reject_other_scenarios(db, project_id: int, approved_script_id: int):
    """
    같은 프로젝트의 다른 시나리오들을 거부 처리
    
    Args:
        project_id: 프로젝트 ID
        approved_script_id: 승인된 시나리오 ID (제외)
    """
    db.query(ScenarioScript).filter(
        ScenarioScript.project_id == project_id,
        ScenarioScript.script_id != approved_script_id,
        ScenarioScript.approval_status == 'pending'
    ).update({
        'approval_status': 'rejected',
        'status': 'rejected',
        'updated_at': datetime.utcnow()
    })
    
    db.commit()
    print(f"다른 시나리오 거부 처리: project_id={project_id}")


# ============================================
# 워크플로우 상태 업데이트
# ============================================
def update_workflow_after_approval(db, execution_id: str, next_stage: str = 'audio_generation'):
    """
    시나리오 승인 후 워크플로우 상태 업데이트
    
    Args:
        execution_id: 워크플로우 실행 ID
        next_stage: 다음 단계 이름
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == uuid.UUID(execution_id)
    ).first()
    
    if workflow:
        workflow.status = 'processing'
        workflow.current_stage = next_stage
        workflow.progress_percentage = 30
        
        db.commit()
        db.refresh(workflow)
        
        print(f"워크플로우 상태 업데이트: {execution_id} -> {next_stage}")
        return workflow
    
    return None


# ============================================
# 수정 요청 함수
# ============================================
def increment_revision_count(db, execution_id: str) -> tuple:
    """
    수정 요청 횟수 증가
    
    Returns:
        (workflow, current_count) 튜플
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == uuid.UUID(execution_id)
    ).first()
    
    if workflow:
        workflow.retry_count += 1
        db.commit()
        db.refresh(workflow)
        
        print(f"수정 요청 횟수 증가: {execution_id} -> {workflow.retry_count}")
        return workflow, workflow.retry_count
    
    return None, 0


def save_revision_feedback(db, script_id: int, feedback: str, change_meme: bool):
    """
    수정 요청 피드백 저장
    
    Args:
        script_id: 시나리오 ID
        feedback: 피드백 내용
        change_meme: 밈 변경 희망 여부
    """
    scenario = get_scenario_by_id(db, script_id)
    
    if scenario:
        # quality_issues에 피드백 추가
        issues = scenario.quality_issues or []
        issues.append(f"[수정 요청] {feedback}")
        
        if change_meme:
            issues.append("[밈 변경 요청]")
        
        scenario.quality_issues = issues
        scenario.approval_status = 'rejected'
        scenario.status = 'rejected'
        scenario.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(scenario)
        
        print(f"수정 피드백 저장: script_id={script_id}")
        return scenario
    
    return None


# ============================================
# 자동 승인 함수
# ============================================
def get_pending_scenarios_for_auto_approval(db) -> List[ScenarioScript]:
    """
    24시간 경과한 미승인 시나리오 조회
    
    Returns:
        자동 승인 대상 시나리오 리스트
    """
    deadline = datetime.utcnow() - timedelta(hours=24)
    
    scenarios = db.query(ScenarioScript).filter(
        ScenarioScript.approval_status == 'pending',
        ScenarioScript.approval_requested_at < deadline
    ).all()
    
    return scenarios


def auto_approve_scenario(db, script_id: int) -> ScenarioScript:
    """
    시나리오 자동 승인 처리
    
    Args:
        script_id: 자동 승인할 시나리오 ID
    
    Returns:
        자동 승인된 시나리오 객체
    """
    scenario = get_scenario_by_id(db, script_id)
    
    if not scenario:
        return None
    
    # 자동 승인 처리
    scenario.approval_status = 'auto_approved'
    scenario.status = 'approved'
    scenario.approved_at = datetime.utcnow()
    scenario.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(scenario)
    
    print(f"시나리오 자동 승인: script_id={script_id}")
    return scenario
