"""
시나리오 관련 CRUD 로직
"""
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import uuid

logger = logging.getLogger(__name__)

from app.models.scenario import ScenarioScript
from app.models.workflow import WorkflowExecution


def get_scenario_by_job(db: Session, job_id: str) -> Tuple[Optional[WorkflowExecution], Optional[ScenarioScript]]:
    """작업 ID로 최신 시나리오 1개 조회"""
    try:
        execution_id = uuid.UUID(job_id)
    except ValueError:
        return None, None
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if not workflow:
        return None, None
    
    # 최신 시나리오 1개만 조회
    scenario = db.query(ScenarioScript).filter(
        ScenarioScript.ad_id == workflow.ad_id,
        ScenarioScript.approval_status.in_(['pending', 'approved'])
    ).order_by(ScenarioScript.created_at.desc()).first()
    
    return workflow, scenario


def get_scenario_by_id(db: Session, script_id: int) -> Optional[ScenarioScript]:
    """시나리오 조회"""
    return db.query(ScenarioScript).filter(ScenarioScript.script_id == script_id).first()


def approve_scenario_by_id(db: Session, script_id: int, approved_by: int) -> Optional[ScenarioScript]:
    """시나리오 승인"""
    scenario = get_scenario_by_id(db, script_id)
    if scenario:
        scenario.approval_status = 'approved'
        scenario.approved_at = datetime.utcnow()
        scenario.approved_by_account_id = approved_by
        db.commit()
        db.refresh(scenario)
        logger.info("시나리오 승인: script_id=%d", script_id)
    return scenario


def reject_other_scenarios(db: Session, ad_id: int, approved_script_id: int):
    """다른 시나리오 거부"""
    db.query(ScenarioScript).filter(
        ScenarioScript.ad_id == ad_id,
        ScenarioScript.script_id != approved_script_id,
        ScenarioScript.approval_status == 'pending'
    ).update({
        'approval_status': 'rejected',
        'updated_at': datetime.utcnow()
    })
    db.commit()
    logger.info("다른 시나리오 거부: ad_id=%d", ad_id)


def update_workflow_after_approval(db: Session, job_id: str, next_stage: str) -> Optional[WorkflowExecution]:
    """시나리오 승인 후 워크플로우 업데이트"""
    try:
        execution_id = uuid.UUID(job_id)
    except ValueError:
        return None
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if workflow:
        workflow.status = 'processing'
        workflow.current_stage = next_stage
        workflow.progress_percentage = 30
        db.commit()
        db.refresh(workflow)
        logger.info("워크플로우 업데이트: %s -> %s", job_id, next_stage)
    
    return workflow


def increment_revision_count(db: Session, job_id: str) -> Tuple[Optional[WorkflowExecution], int]:
    """수정 요청 횟수 증가"""
    try:
        execution_id = uuid.UUID(job_id)
    except ValueError:
        return None, 0
    
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()
    
    if workflow:
        workflow.retry_count += 1
        db.commit()
        db.refresh(workflow)
        logger.info("수정 요청 횟수 증가: %s -> %d", job_id, workflow.retry_count)
        return workflow, workflow.retry_count
    
    return None, 0


def get_pending_scenarios_for_auto_approval(db: Session) -> List[ScenarioScript]:
    """24시간 경과한 미승인 시나리오 조회"""
    deadline = datetime.utcnow() - timedelta(hours=24)
    return db.query(ScenarioScript).filter(
        ScenarioScript.approval_status == 'pending',
        ScenarioScript.approval_requested_at < deadline
    ).all()


def auto_approve_scenario(db: Session, script_id: int) -> Optional[ScenarioScript]:
    """시나리오 자동 승인"""
    scenario = get_scenario_by_id(db, script_id)
    if scenario:
        scenario.approval_status = 'auto_approved'
        scenario.approved_at = datetime.utcnow()
        scenario.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(scenario)
        logger.info("시나리오 자동 승인: script_id=%d", script_id)
    return scenario


def create_scenario(
    db: Session,
    ad_id: int,
    meme_id: int,
    title: str,
    scenes: dict,
    generation_type: str = 'initial',
    used_templates: list = None,
    **kwargs
) -> ScenarioScript:
    """시나리오 생성 (초안 또는 재생성)"""
    scenario = ScenarioScript(
        ad_id=ad_id,
        meme_id=meme_id,
        title=title,
        scenes=scenes,
        generation_type=generation_type,  # 'initial' 또는 'regenerated'
        used_templates=used_templates,
        **kwargs
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    logger.info("시나리오 생성: script_id=%d, type=%s", scenario.script_id, generation_type)
    return scenario



def get_scenario_candidates(db: Session, job_id: str) -> Optional[ScenarioScript]:
    """시나리오 조회 (단일)"""
    workflow, scenario = get_scenario_by_job(db, job_id)
    return scenario


def approve_scenario(db: Session, script_id: int) -> Optional[ScenarioScript]:
    """시나리오 승인 (간단 버전)"""
    scenario = get_scenario_by_id(db, script_id)
    if scenario:
        scenario.approval_status = 'approved'
        scenario.approved_at = datetime.utcnow()
        scenario.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(scenario)
        logger.info("시나리오 승인: script_id=%d", script_id)
    return scenario


def request_scenario_revision(
    db: Session,
    script_id: int,
    scene_revisions: list
) -> Optional[ScenarioScript]:
    """시나리오 수정 요청 (씬별)"""
    scenario = get_scenario_by_id(db, script_id)
    if scenario:
        # approval_status는 pending으로 유지 (revision_requested는 허용되지 않음)
        scenario.updated_at = datetime.utcnow()
        
        # scene_revisions 배열을 scene_feedback dict로 변환
        scene_feedback = {
            f"scene{rev['scene_number']}": rev['revision_notes']
            for rev in scene_revisions
        }
        
        revision_data = {
            'feedback_type': 'human_feedback',
            'scene_feedback': scene_feedback,
            'requested_at': datetime.utcnow().isoformat()
        }
        
        # 기존 review_result 덮어쓰기
        scenario.review_result = revision_data
        
        db.commit()
        db.refresh(scenario)
        logger.info("시나리오 수정 요청: script_id=%d, 씬 개수=%d", script_id, len(scene_revisions))
    return scenario
