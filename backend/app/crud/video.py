"""
영상 관련 CRUD 로직
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uuid

from app.models.ad_request import AdRequest
from app.models.company import CompanyCharacter
from app.models.workflow import WorkflowExecution, WorkflowStage
from app.models.video import Video
from app.models.company import Company


# ============================================
# AdRequest CRUD
# ============================================
def create_ad_request(
    db: Session,
    company_id: int,
    account_id: int,
    item_name: str,
    item_category: Optional[str],
    item_description: Optional[str],  # item_keymessage → item_description
    item_url: Optional[str],
    item_images: List[str],
    character_id: Optional[int],
    character_image_prompt: Optional[str],
    meme_id: Optional[int],
    character_voice_prompt: Optional[str]
):
    """광고 요청 생성"""
    ad_request = AdRequest(
        company_id=company_id,
        account_id=account_id,
        item_name=item_name,
        item_category=item_category,
        item_description=item_description,  # item_keymessage → item_description
        item_url=item_url,
        item_images=item_images,
        character_id=character_id,
        character_image_prompt=character_image_prompt,
        meme_id=meme_id,
        character_voice_prompt=character_voice_prompt
    )
    db.add(ad_request)
    db.commit()
    db.refresh(ad_request)
    return ad_request


def get_ad_request_by_id(db: Session, ad_id: int):
    """광고 요청 조회"""
    return db.query(AdRequest).filter(AdRequest.ad_id == ad_id).first()


def get_ad_requests_by_company(db: Session, company_id: int, offset: int = 0, limit: int = 10):
    """회사별 광고 요청 목록"""
    return db.query(AdRequest).filter(
        AdRequest.company_id == company_id
    ).offset(offset).limit(limit).all()


def delete_ad_request(db: Session, ad_id: int):
    """광고 요청 및 관련 데이터 삭제 (FK RESTRICT 테이블 수동 삭제)"""
    from sqlalchemy import text

    # script_id 목록 조회
    rows = db.execute(
        text("SELECT script_id FROM scenario_scripts WHERE ad_id = :ad_id"),
        {"ad_id": ad_id},
    ).fetchall()
    script_ids = [r[0] for r in rows]

    if script_ids:
        # scene_videos → voice_generations / image_generations → scene_assets 순서
        db.execute(
            text("DELETE FROM scene_videos WHERE script_id = ANY(:ids)"),
            {"ids": script_ids},
        )
        db.execute(
            text("DELETE FROM voice_generations WHERE script_id = ANY(:ids)"),
            {"ids": script_ids},
        )
        db.execute(
            text("DELETE FROM image_generations WHERE script_id = ANY(:ids)"),
            {"ids": script_ids},
        )
        db.execute(
            text("DELETE FROM scene_assets WHERE script_id = ANY(:ids)"),
            {"ids": script_ids},
        )

    # 나머지는 CASCADE로 처리됨 (scenario_scripts, videos, workflow_execution 등)
    result = db.execute(text("DELETE FROM ad_requests WHERE ad_id = :ad_id"), {"ad_id": ad_id})
    db.commit()
    return result.rowcount > 0


# ============================================
# CompanyCharacter CRUD
# ============================================
def create_company_character(
    db: Session,
    company_id: int,
    image_url: str,
    image_prompt: Optional[str] = None,
    image_model: Optional[str] = None,
    elevenlabs_voice_id: Optional[str] = None,
    voice_design_prompt: Optional[str] = None
):
    """회사 캐릭터 생성"""
    character = CompanyCharacter(
        company_id=company_id,
        image_url=image_url,
        image_prompt=image_prompt,
        image_model=image_model,
        elevenlabs_voice_id=elevenlabs_voice_id,
        voice_design_prompt=voice_design_prompt,
        is_active=False
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


def get_character_by_id(db: Session, character_id: int):
    """캐릭터 조회"""
    return db.query(CompanyCharacter).filter(
        CompanyCharacter.character_id == character_id
    ).first()


def get_characters_by_company(db: Session, company_id: int, active_only: bool = True):
    """회사 캐릭터 목록"""
    query = db.query(CompanyCharacter).filter(CompanyCharacter.company_id == company_id)
    if active_only:
        query = query.filter(CompanyCharacter.is_active == True)
    return query.all()


def enforce_character_slot_limit(db: Session, company_id: int, max_active: int = 5):
    """활성 캐릭터 슬롯 제한(soft delete) 적용."""
    active_chars = (
        db.query(CompanyCharacter)
        .filter(CompanyCharacter.company_id == company_id)
        .filter(CompanyCharacter.is_active == True)
        .order_by(CompanyCharacter.updated_at.asc())
        .all()
    )
    if len(active_chars) <= max_active:
        return []

    excess = len(active_chars) - max_active
    to_deactivate = active_chars[:excess]
    now = datetime.utcnow().isoformat()
    for char in to_deactivate:
        char.is_active = False
        metadata = dict(char.generation_metadata or {})
        metadata["deactivated"] = {
            "reason": "slot_limit_exceeded",
            "at": now,
        }
        char.generation_metadata = metadata
    db.commit()
    return [c.character_id for c in to_deactivate]

def activate_character(db: Session, character_id: int):
    """캐릭터 활성화"""
    character = get_character_by_id(db, character_id)
    if character:
        character.is_active = True
        db.commit()
        db.refresh(character)
    return character


def deactivate_character(db: Session, character_id: int):
    """캐릭터 비활성화"""
    character = get_character_by_id(db, character_id)
    if character:
        character.is_active = False
        db.commit()
        db.refresh(character)
    return character


# ============================================
# WorkflowExecution CRUD
# ============================================
def create_workflow(
    db: Session,
    ad_id: int,
    company_id: int,
    account_id: int,
    meme_id: Optional[int] = None
):
    """워크플로우 생성"""
    workflow = WorkflowExecution(
        execution_id=uuid.uuid4(),
        ad_id=ad_id,
        company_id=company_id,
        account_id=account_id,
        meme_id=meme_id,
        status='created'
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def get_workflow_by_id(db: Session, execution_id: uuid.UUID):
    """워크플로우 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == execution_id
    ).first()


def get_workflow_by_ad(db: Session, ad_id: int):
    """광고 요청의 워크플로우 조회"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.ad_id == ad_id
    ).first()


def update_workflow_status(
    db: Session,
    execution_id: uuid.UUID,
    status: str,
    current_stage: Optional[str] = None,
    progress_percentage: int = 0
):
    """워크플로우 상태 업데이트"""
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.status = status
        if current_stage:
            workflow.current_stage = current_stage
        workflow.progress_percentage = progress_percentage
        db.commit()
        db.refresh(workflow)
    return workflow


def get_workflows_by_company_filtered(
    db: Session,
    company_id: int,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'created_at',
    order: str = 'desc',
    offset: int = 0,
    limit: int = 10
):
    """회사별 워크플로우 목록 (필터링)"""
    query = db.query(WorkflowExecution).filter(WorkflowExecution.company_id == company_id)
    
    if status:
        query = query.filter(WorkflowExecution.status == status)
    if date_from:
        query = query.filter(WorkflowExecution.created_at >= date_from)
    if date_to:
        query = query.filter(WorkflowExecution.created_at <= date_to)
    
    # 정렬
    if sort_by == 'created_at':
        query = query.order_by(
            WorkflowExecution.created_at.desc() if order == 'desc' else WorkflowExecution.created_at.asc()
        )
    elif sort_by == 'completed_at':
        query = query.order_by(
            WorkflowExecution.completed_at.desc() if order == 'desc' else WorkflowExecution.completed_at.asc()
        )
    
    total_count = query.count()
    workflows = query.offset(offset).limit(limit).all()
    
    return workflows, total_count


def check_duplicate_ad_request(db: Session, company_id: int, item_name: str, meme_id: Optional[int]):
    """중복 광고 요청 확인"""
    query = db.query(AdRequest).filter(
        AdRequest.company_id == company_id,
        AdRequest.item_name == item_name,
        AdRequest.status.in_(['draft', 'processing'])
    )
    if meme_id:
        query = query.filter(AdRequest.meme_id == meme_id)
    return query.first()


def initialize_workflow_stages(db: Session, execution_id: uuid.UUID):
    """워크플로우 단계 초기화"""
    stages = [
        {"stage_name": "character_generation", "stage_order": 1},
        {"stage_name": "scenario_generation", "stage_order": 2},
        {"stage_name": "audio_generation", "stage_order": 3},
        {"stage_name": "video_generation", "stage_order": 4},
        {"stage_name": "final_processing", "stage_order": 5}
    ]
    
    for stage_data in stages:
        stage = WorkflowStage(
            execution_id=execution_id,
            stage_name=stage_data["stage_name"],
            stage_order=stage_data["stage_order"],
            status='pending'
        )
        db.add(stage)
    
    db.commit()


def increment_retry_count(db: Session, execution_id: uuid.UUID):
    """재시도 횟수 증가"""
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.retry_count += 1
        db.commit()
        db.refresh(workflow)
    return workflow


def get_video_by_id(db: Session, video_id: int):
    """영상 조회"""
    return db.query(Video).filter(Video.video_id == video_id).first()


def approve_video(db: Session, video_id: int, approval_type: str, approved_by: int):
    """영상 승인"""
    video = get_video_by_id(db, video_id)
    if video:
        if approval_type == 'client':
            video.status = 'client_approved'
        elif approval_type == 'admin':
            video.status = 'admin_approved'
        
        video.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(video)
    return video


def reject_video(db: Session, video_id: int, rejection_type: str, rejection_reason: str, rejected_by: int):
    """영상 거부"""
    video = get_video_by_id(db, video_id)
    if video:
        if rejection_type == 'client':
            video.status = 'client_rejected'
        elif rejection_type == 'admin':
            video.status = 'admin_rejected'

        video.rejection_reason = rejection_reason
        video.rejected_by_account_id = rejected_by
        video.rejected_at = datetime.utcnow()
        video.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(video)
    return video


# ============================================
# Content Pipeline CRUD
# ============================================

_WORKFLOW_VALID_STATUSES = {
    'created', 'generating_character', 'generating_voice', 'generating_scenario', 'generating_video',
    'content_generating',
    'pending_approval', 'approved', 'rejected', 'processing', 'completed', 'failed', 'cancelled',
}


def update_ad_status(db: Session, ad_id: int, status: str, current_stage: Optional[str] = None):
    """광고 요청 + 워크플로우 상태를 단일 트랜잭션으로 업데이트"""
    ad_request = get_ad_request_by_id(db, ad_id)
    if ad_request:
        ad_request.status = status
        ad_request.updated_at = datetime.utcnow()

    workflow = get_workflow_by_ad(db, ad_id)
    if workflow:
        wf_status = status if status in _WORKFLOW_VALID_STATUSES else 'processing'
        workflow.status = wf_status
        if current_stage:
            workflow.current_stage = current_stage

    db.commit()
    if ad_request:
        db.refresh(ad_request)

    return ad_request


def update_workflow_progress(db: Session, ad_id: int, progress: int, stage: Optional[str] = None):
    """워크플로우 진행률 업데이트"""
    workflow = get_workflow_by_ad(db, ad_id)
    if workflow:
        workflow.progress_percentage = progress
        if stage:
            workflow.current_stage = stage
        db.commit()
        db.refresh(workflow)
    return workflow


def get_scenario_by_ad(db: Session, ad_id: int):
    """광고별 최신 시나리오 조회"""
    from app.models.scenario import ScenarioScript
    return db.query(ScenarioScript).filter(
        ScenarioScript.ad_id == ad_id
    ).order_by(ScenarioScript.script_id.desc()).first()


def get_all_scenarios_by_ad(db: Session, ad_id: int):
    """광고별 모든 시나리오 버전 조회 (최신순)"""
    from app.models.scenario import ScenarioScript
    return db.query(ScenarioScript).filter(
        ScenarioScript.ad_id == ad_id
    ).order_by(ScenarioScript.created_at.desc()).all()


def get_scenario_by_id(db: Session, script_id: int):
    """시나리오 ID로 조회"""
    from app.models.scenario import ScenarioScript
    return db.query(ScenarioScript).filter(
        ScenarioScript.script_id == script_id
    ).first()


def create_scenario(
    db: Session,
    ad_id: int,
    meme_id: int,
    title: str,
    scenes: dict
):
    """시나리오 생성"""
    from app.models.scenario import ScenarioScript

    scenario = ScenarioScript(
        ad_id=ad_id,
        meme_id=meme_id,
        title=title,
        scenes=scenes,
        status='draft',
        approval_status='pending'
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def update_scenario_approval(db: Session, script_id: int, status: str, approved_by: Optional[int] = None):
    """시나리오 승인 상태 업데이트"""
    from app.models.scenario import ScenarioScript

    scenario = db.query(ScenarioScript).filter(
        ScenarioScript.script_id == script_id
    ).first()

    if scenario:
        scenario.approval_status = status
        if status == 'approved' and approved_by:
            scenario.approved_at = datetime.utcnow()
            scenario.approved_by_account_id = approved_by
        scenario.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(scenario)
    return scenario


def update_scenario_scenes(db: Session, script_id: int, scenes: dict, revision_notes: Optional[dict] = None):
    """시나리오 씬 업데이트"""
    from app.models.scenario import ScenarioScript

    scenario = db.query(ScenarioScript).filter(
        ScenarioScript.script_id == script_id
    ).first()

    if scenario:
        scenario.scenes = scenes
        if revision_notes:
            scenario.review_result = revision_notes
        scenario.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(scenario)
    return scenario


def create_video_for_ad(
    db: Session,
    ad_id: int,
    company_id: int,
    account_id: int,
    title: str,
    script_id: Optional[int] = None
):
    """광고용 영상 생성"""
    # idx_videos_script unique constraint 대응:
    # 이전 실패/처리 중인 video가 같은 script_id를 가지고 있으면 NULL로 해제
    if script_id:
        old_videos = db.query(Video).filter(
            Video.script_id == script_id,
            Video.status.in_(['failed', 'processing']),
        ).all()
        for v in old_videos:
            v.script_id = None
        if old_videos:
            db.flush()

    video = Video(
        ad_id=ad_id,
        company_id=company_id,
        account_id=account_id,
        title=title,
        script_id=script_id,
        s3_url="",  # 생성 후 업데이트
        status='processing'
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_video_by_ad(db: Session, ad_id: int):
    """광고별 영상 조회"""
    return db.query(Video).filter(
        Video.ad_id == ad_id
    ).order_by(Video.created_at.desc()).first()


def update_video_status(db: Session, video_id: int, status: str, s3_url: Optional[str] = None, error_message: Optional[str] = None):
    """영상 상태 업데이트"""
    video = get_video_by_id(db, video_id)
    if video:
        video.status = status
        if s3_url:
            video.s3_url = s3_url
        if error_message is not None:
            video.error_message = error_message
        video.updated_at = datetime.utcnow()
        if status == 'completed':
            video.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(video)
    return video


def update_video_revision(db: Session, video_id: int, revision_notes: dict):
    """영상 수정 요청 저장"""
    video = get_video_by_id(db, video_id)
    if video:
        video.review_result = revision_notes
        video.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(video)
    return video


def check_assets_approval(db: Session, ad_id: int) -> tuple:
    """캐릭터+음성 승인 상태 확인"""
    ad_request = get_ad_request_by_id(db, ad_id)
    if not ad_request or not ad_request.character_id:
        return False, False

    character = get_character_by_id(db, ad_request.character_id)
    if not character:
        return False, False

    # 캐릭터 이미지 승인 여부 (is_active로 판단)
    character_approved = character.is_active

    # 음성 승인 여부 (elevenlabs_voice_id가 있으면 승인된 것으로 간주)
    voice_approved = bool(character.elevenlabs_voice_id)

    return character_approved, voice_approved


def check_content_approval(db: Session, ad_id: int) -> tuple:
    """시나리오+영상 승인 상태 확인"""
    scenario = get_scenario_by_ad(db, ad_id)
    video = get_video_by_ad(db, ad_id)

    scenario_approved = scenario and scenario.approval_status == 'approved'
    video_approved = video and video.status == 'client_approved'

    return scenario_approved, video_approved
