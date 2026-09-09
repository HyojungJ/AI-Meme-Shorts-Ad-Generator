"""
영상 상태 추적 관련 CRUD 로직
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import uuid

logger = logging.getLogger(__name__)

from app.models.workflow import WorkflowExecution, WorkflowStage


def get_workflow_by_id(db: Session, execution_id: uuid.UUID) -> Optional[WorkflowExecution]:
    """워크플로우 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()


def get_workflow_stages(db: Session, execution_id: uuid.UUID) -> List[WorkflowStage]:
    """워크플로우의 모든 단계 조회"""
    return db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == execution_id
    ).order_by(WorkflowStage.stage_order).all()


def initialize_workflow_stages(db: Session, execution_id: uuid.UUID):
    """워크플로우 초기 단계 설정"""
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
    logger.info("워크플로우 단계 초기화: %s", execution_id)


def update_stage_status(
    db: Session,
    execution_id: uuid.UUID,
    stage_name: str,
    status: str,
    error_message: Optional[str] = None
) -> Optional[WorkflowStage]:
    """특정 단계의 상태 업데이트"""
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
        logger.info("단계 상태 업데이트: %s -> %s", stage_name, status)
    
    return stage



def get_workflow_status(db: Session, execution_id: str) -> Optional[WorkflowExecution]:
    """워크플로우 상태 조회 (문자열 execution_id)"""
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        return None
    
    return get_workflow_by_id(db, exec_uuid)


def get_workflow_detail(db: Session, execution_id: str) -> Optional[dict]:
    """워크플로우 상세 정보 조회 (단계 포함)"""
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        return None
    
    workflow = get_workflow_by_id(db, exec_uuid)
    if not workflow:
        return None
    
    stages = get_workflow_stages(db, exec_uuid)
    
    return {
        'workflow': workflow,
        'stages': stages
    }
