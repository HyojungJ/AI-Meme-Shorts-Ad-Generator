"""
영상 생성 상태 추적 데이터베이스 V2
새로운 스키마: video_projects, workflow_execution, workflow_stages
"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

# generation/v3의 모델들을 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'generation', 'v3'))
from generation.v3.database_v3 import (
    Base, engine, SessionLocal,
    WorkflowExecution, WorkflowStage, VideoProject,
    get_workflow_by_id
)

load_dotenv()


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
# WorkflowStage 관련 함수
# ============================================
def initialize_workflow_stages(db, execution_id: uuid.UUID):
    """
    워크플로우 초기 단계 설정
    영상 생성 요청 시 호출
    """
    stages = [
        {"name": "프로젝트 생성", "order": 1},
        {"name": "캐릭터 생성", "order": 2},
        {"name": "시나리오 생성", "order": 3},
        {"name": "음성 합성", "order": 4},
        {"name": "영상 렌더링", "order": 5},
        {"name": "품질 검증", "order": 6},
        {"name": "S3 업로드", "order": 7}
    ]
    
    for stage_info in stages:
        stage = WorkflowStage(
            execution_id=execution_id,
            stage_name=stage_info["name"],
            stage_order=stage_info["order"],
            status='pending'
        )
        db.add(stage)
    
    db.commit()
    print(f"워크플로우 단계 초기화: {execution_id}")


def get_workflow_stages(db, execution_id: uuid.UUID):
    """워크플로우의 모든 단계 조회"""
    return db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == execution_id
    ).order_by(WorkflowStage.stage_order).all()


def update_stage_status(db, execution_id: uuid.UUID, stage_name: str, 
                       status: str, error_message: str = None):
    """
    특정 단계의 상태 업데이트
    
    Args:
        execution_id: 워크플로우 ID
        stage_name: 단계명 (예: "시나리오 생성")
        status: 상태 (pending/processing/completed/failed/skipped)
        error_message: 에러 메시지 (failed 시)
    """
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
        print(f"단계 상태 업데이트: {stage_name} -> {status}")
        return stage
    return None


def get_stage_summary(workflow, stages):
    """
    단계 정보 요약
    
    Returns:
        completed_stages: 완료된 단계 목록
        current_stage: 현재 진행 중인 단계
        pending_stages: 대기 중인 단계 목록
    """
    if not stages:
        return [], None, []
    
    completed = [s for s in stages if s.status == "completed"]
    current = next((s for s in stages if s.status == "processing"), None)
    pending = [s.stage_name for s in stages if s.status == "pending"]
    
    return completed, current, pending


def calculate_estimated_completion(db, workflow, stages):
    """
    예상 완료 시간 계산
    완료된 단계들의 평균 소요 시간 기반
    
    Returns:
        estimated_completion: 예상 완료 시각 (ISO format)
        estimated_remaining_seconds: 남은 예상 시간 (초)
    """
    if not stages:
        return None, None
    
    # 완료된 단계들의 평균 소요 시간 계산
    completed_stages = [s for s in stages if s.status == "completed" and s.duration_seconds]
    if not completed_stages:
        # 완료된 단계가 없으면 회사 평균 사용
        avg_time = get_average_processing_time(db, workflow.company_id)
        elapsed = (datetime.utcnow() - workflow.created_at).total_seconds()
        remaining = max(0, avg_time - elapsed)
        estimated_completion = datetime.utcnow() + timedelta(seconds=remaining)
        return estimated_completion.isoformat(), int(remaining)
    
    avg_duration = sum(s.duration_seconds for s in completed_stages) / len(completed_stages)
    
    # 남은 단계 수
    remaining_stages = len([s for s in stages if s.status in ["pending", "processing"]])
    
    # 예상 남은 시간
    estimated_remaining = int(avg_duration * remaining_stages)
    
    # 예상 완료 시각
    estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_remaining)
    
    return estimated_completion.isoformat(), estimated_remaining


def get_average_processing_time(db, company_id: int = None):
    """
    평균 처리 시간 계산 (완료된 워크플로우 기준)
    """
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
