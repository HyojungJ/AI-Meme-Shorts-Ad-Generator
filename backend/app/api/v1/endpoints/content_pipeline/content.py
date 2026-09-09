"""
Content Pipeline API - content unified endpoints + status + versions
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import AdStatus, VideoStatus, ApprovalStatus, WorkflowStatus
from . import helpers
from .helpers import (
    get_current_user, get_db,
    _get_ad_request_with_auth, _check_not_generating, _lock_ad_request,
    SCENE_KEY_MAP, PROGRESS,
    ContentGenerateRequest,
    ContentReviseRequest,
    ContentGenerateResponse,
    ContentApproveResponse,
)
from .tasks import (
    _bg_generate_content,
    _bg_revise_content,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{ad_id}/content/generate", response_model=ContentGenerateResponse)
async def generate_ad_content(
    ad_id: int,
    request: Request,
    content_request: ContentGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """시나리오+TTS+영상 통합 생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    if ad_request.status == AdStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="이미 완료된 광고입니다")

    char_approved, voice_approved = helpers.video_crud.check_assets_approval(db, ad_id)
    if not (char_approved and voice_approved):
        raise HTTPException(status_code=400, detail="캐릭터와 음성이 먼저 승인되어야 합니다")

    meme_id = content_request.meme_id or ad_request.meme_id
    if not meme_id:
        raise HTTPException(status_code=400, detail="밈을 선택해주세요")

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.CONTENT_GENERATING, 'scenario_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_start"], 'scenario_generation')

    background_tasks.add_task(
        _bg_generate_content,
        ad_id=ad_id,
        meme_id=meme_id,
        product_name=ad_request.item_name or "Unknown Product",
        product_category=ad_request.item_category or "기타",
        product_highlight=ad_request.item_description or "",  # item_keymessage → item_description
        original_status=original_status,
    )

    return ContentGenerateResponse(ad_id=ad_id, status=AdStatus.CONTENT_GENERATING)


@router.post("/{ad_id}/content/revise", response_model=ContentGenerateResponse)
async def revise_ad_content(
    ad_id: int,
    request: Request,
    revision: ContentReviseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """시나리오+TTS+영상 통합 재생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오가 아직 생성되지 않았습니다")

    # scene_number → scene_key 변환 후 피드백 DB 저장
    scene_key_map = SCENE_KEY_MAP
    scene_feedback = {}
    for rev in revision.scene_revisions:
        key = scene_key_map.get(rev.scene_number, f"scene_{rev.scene_number}")
        notes = []
        if rev.scenario_notes:
            notes.append(f"시나리오: {rev.scenario_notes}")
        if rev.video_notes:
            notes.append(f"영상: {rev.video_notes}")
        if notes:
            scene_feedback[key] = " / ".join(notes)

    helpers.video_crud.update_scenario_scenes(
        db,
        scenario.script_id,
        scenario.scenes,
        {
            "feedback_type": "human_feedback",
            "scene_feedback": scene_feedback,
            "overall_comment": revision.general_notes or "",
        }
    )

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.CONTENT_GENERATING, 'scenario_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_start"], 'scenario_generation')

    background_tasks.add_task(
        _bg_revise_content,
        ad_id=ad_id,
        original_status=original_status,
    )

    return ContentGenerateResponse(
        ad_id=ad_id,
        status=AdStatus.CONTENT_GENERATING,
        message='시나리오+영상 재생성을 시작합니다'
    )


@router.post("/{ad_id}/content/approve", response_model=ContentApproveResponse)
async def approve_ad_content(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """시나리오+영상 통합 승인 -> 완료 (유일한 콘텐츠 완료 경로)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    # 동시 승인 요청 방지 (행 잠금)
    _lock_ad_request(db, ad_id)
    db.refresh(ad_request)

    if ad_request.status != AdStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail=f"현재 상태에서는 승인할 수 없습니다 (현재: {ad_request.status})")

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="시나리오가 아직 생성되지 않았습니다")

    video = helpers.video_crud.get_video_by_ad(db, ad_id)
    if not video:
        raise HTTPException(status_code=400, detail="영상이 아직 생성되지 않았습니다")

    if video.status != VideoStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="영상 생성이 완료되지 않았습니다")

    # 단일 트랜잭션으로 모든 승인 처리 (FOR UPDATE 잠금 유지)
    scenario.approval_status = ApprovalStatus.APPROVED
    scenario.approved_at = datetime.utcnow()
    scenario.approved_by_account_id = user_info["account_id"]
    scenario.updated_at = datetime.utcnow()

    video.status = VideoStatus.CLIENT_APPROVED
    video.updated_at = datetime.utcnow()

    ad_request.status = AdStatus.COMPLETED
    ad_request.updated_at = datetime.utcnow()

    workflow = helpers.video_crud.get_workflow_by_ad(db, ad_id)
    if workflow:
        workflow.status = WorkflowStatus.COMPLETED
        workflow.current_stage = 'completed'
        workflow.progress_percentage = 100

    db.commit()

    return ContentApproveResponse(
        status=AdStatus.COMPLETED,
        message="시나리오와 영상이 최종 승인되었습니다.",
        is_completed=True
    )


# === 상태 조회 API ===

@router.get("/{ad_id}/status")
async def get_ad_status(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고 생성 상태 경량 조회 (폴링용)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    workflow = helpers.video_crud.get_workflow_by_ad(db, ad_id)

    return {
        "ad_id": ad_id,
        "status": ad_request.status,
        "current_stage": workflow.current_stage if workflow else None,
        "progress": workflow.progress_percentage if workflow else 0,
    }



# === 시나리오 버전 관리 API ===

@router.get("/{ad_id}/scenarios/versions")
async def get_scenario_versions(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고의 모든 시나리오 버전 조회"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    # 모든 시나리오 버전 조회
    scenarios = helpers.video_crud.get_all_scenarios_by_ad(db, ad_id)

    if not scenarios:
        return {"versions": [], "total": 0}

    # 버전 정보 구성
    versions = []
    for idx, scenario in enumerate(scenarios):
        # 최신 버전부터 역순으로 버전 번호 부여
        version_number = len(scenarios) - idx

        # 씬 데이터 변환
        scenes_list = []
        if scenario.scenes:
            # scenes가 리스트인 경우
            if isinstance(scenario.scenes, list):
                for scene_data in scenario.scenes:
                    if isinstance(scene_data, dict):
                        scenes_list.append({
                            "scene_number": scene_data.get("scene_number", 0),
                            "dialogue": scene_data.get("dialogue", ""),
                            "scene_type": scene_data.get("scene_type", ""),
                        })
            # scenes가 딕셔너리인 경우
            elif isinstance(scenario.scenes, dict):
                for scene_key, scene_data in scenario.scenes.items():
                    scene_num = int(scene_key.replace("scene_", "").replace("scene", "")) if "scene" in scene_key else 0
                    scenes_list.append({
                        "scene_number": scene_num,
                        "dialogue": scene_data.get("dialogue", ""),
                        "scene_type": scene_data.get("scene_type", ""),
                    })
            scenes_list.sort(key=lambda x: x["scene_number"])

        versions.append({
            "version": version_number,
            "script_id": scenario.script_id,
            "title": scenario.title,
            "description": scenario.description,
            "generation_type": scenario.generation_type,
            "approval_status": scenario.approval_status,
            "created_at": scenario.created_at.isoformat(),
            "is_latest": idx == 0,
            "scenes_count": len(scenes_list),
            "scenes": scenes_list,
            "revision_notes": getattr(scenario, 'revision_notes', None),
        })

    return {
        "versions": versions,
        "total": len(versions),
        "latest_version": versions[0] if versions else None
    }


@router.get("/{ad_id}/scenarios/{script_id}")
async def get_scenario_by_version(
    ad_id: int,
    script_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """특정 버전의 시나리오 상세 조회"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    # 시나리오 조회
    scenario = helpers.video_crud.get_scenario_by_id(db, script_id)

    if not scenario or scenario.ad_id != ad_id:
        raise HTTPException(status_code=404, detail="시나리오를 찾을 수 없습니다")

    # 씬 정보 구성
    scenes = []
    if scenario.scenes:
        if isinstance(scenario.scenes, dict):
            for scene_key, scene_data in scenario.scenes.items():
                scenes.append({
                    "scene_key": scene_key,
                    "scene_number": int(scene_key.replace("scene", "")) if "scene" in scene_key else 0,
                    "dialogue": scene_data.get("dialogue", ""),
                    "emotion": scene_data.get("emotion", ""),
                    "action": scene_data.get("action", ""),
                    "visual_description": scene_data.get("visual_description", ""),
                    "scene_type": scene_data.get("scene_type", ""),
                    "duration_seconds": scene_data.get("duration_seconds", 0),
                })
        else:
            for i, scene_data in enumerate(scenario.scenes):
                scenes.append({
                    "scene_key": f"scene_{i + 1}",
                    "scene_number": scene_data.get("scene_number", i + 1),
                    "dialogue": scene_data.get("dialogue", "") or scene_data.get("content", ""),
                    "emotion": scene_data.get("emotion", ""),
                    "action": scene_data.get("action", ""),
                    "visual_description": scene_data.get("visual_description", ""),
                    "scene_type": scene_data.get("scene_type", ""),
                    "duration_seconds": scene_data.get("duration_seconds", 0),
                })
        scenes.sort(key=lambda x: x["scene_number"])

    return {
        "script_id": scenario.script_id,
        "ad_id": scenario.ad_id,
        "meme_id": scenario.meme_id,
        "title": scenario.title,
        "description": scenario.description,
        "hashtags": scenario.hashtags or [],
        "scenes": scenes,
        "generation_type": scenario.generation_type,
        "approval_status": scenario.approval_status,
        "status": scenario.status,
        "created_at": scenario.created_at.isoformat(),
        "updated_at": scenario.updated_at.isoformat(),
        "review_result": scenario.review_result,
    }
