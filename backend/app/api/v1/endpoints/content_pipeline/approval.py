"""
Content Pipeline API - approval + revision endpoints
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import AdStatus, VideoStatus, ApprovalStatus
from . import helpers
from .helpers import (
    get_current_user, get_db,
    _get_ad_request_with_auth, _check_not_generating,
    GENERATING_STATUSES, SCENE_KEY_MAP, PROGRESS,
    ItemApprovalRequest,
    ItemApprovalResponse,
    AdCharacterGenerateResponse,
    AdVoiceGenerateResponse,
    CharacterRevisionRequest,
    VoiceRevisionRequest,
    ScenarioReviseRequest,
    VideoSceneReviseRequest,
    AssetsApproveResponse,
)
from .tasks import (
    _bg_revise_character,
    _bg_revise_voice,
    _bg_revise_scenario,
    _bg_revise_video,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# === 승인/거부 API ===

@router.post("/{ad_id}/character/approve", response_model=ItemApprovalResponse)
async def approve_ad_character(
    ad_id: int,
    request: Request,
    approval: ItemApprovalRequest,
    db: Session = Depends(get_db)
):
    """광고용 캐릭터 개별 승인"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    if not ad_request.character_id:
        raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if approval.approved:
        helpers.video_crud.activate_character(db, character.character_id)
        return ItemApprovalResponse(status=ApprovalStatus.APPROVED, message="캐릭터가 승인되었습니다")
    else:
        helpers.video_crud.deactivate_character(db, character.character_id)
        return ItemApprovalResponse(status=ApprovalStatus.REJECTED, message="캐릭터가 거부되었습니다")


@router.post("/{ad_id}/character/revise", response_model=AdCharacterGenerateResponse)
async def revise_ad_character(
    ad_id: int,
    request: Request,
    revision: CharacterRevisionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 캐릭터 수정 요청"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    if not ad_request.character_id:
        raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    # 상태를 '이미지 생성 중'으로 변경
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_CHARACTER, 'character_generation')

    # 백그라운드에서 재생성 실행
    background_tasks.add_task(
        _bg_revise_character,
        ad_id,
        character.character_id,
        revision.revision_notes,
        revision.character_prompt,
        ad_request.company_id
    )

    return AdCharacterGenerateResponse(
        character_id=character.character_id,
        image_url=character.image_url,
        status="regenerating"
    )


@router.post("/{ad_id}/voice/approve", response_model=ItemApprovalResponse)
async def approve_ad_voice(
    ad_id: int,
    request: Request,
    approval: ItemApprovalRequest,
    db: Session = Depends(get_db)
):
    """광고용 음성 개별 승인"""
    try:
        user_info = await get_current_user(request)
        ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

        if not ad_request.character_id:
            raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

        character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

        if not character.elevenlabs_voice_id:
            raise HTTPException(status_code=400, detail="음성이 아직 생성되지 않았습니다")

        if approval.approved:
            return ItemApprovalResponse(status=ApprovalStatus.APPROVED, message="음성이 승인되었습니다")
        else:
            character.elevenlabs_voice_id = None
            character.voice_sample_url = None
            character.updated_at = datetime.utcnow()
            db.commit()
            return ItemApprovalResponse(status=ApprovalStatus.REJECTED, message="음성이 거부되었습니다. 재생성이 필요합니다.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 승인 실패 (ad_id={ad_id}): {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"음성 승인 중 오류 발생: {str(e)}")


@router.post("/{ad_id}/voice/revise", response_model=AdVoiceGenerateResponse)
async def revise_ad_voice(
    ad_id: int,
    request: Request,
    revision: VoiceRevisionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 음성 수정 요청"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    if not ad_request.character_id:
        raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    # 상태를 '음성 생성 중'으로 변경
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_VOICE, 'voice_generation')

    sample_text = revision.sample_text or "안녕하세요, 저는 활기차고 밝은 캐릭터입니다. 오늘도 좋은 하루 보내세요! 여러분과 함께하는 이 시간이 정말 즐겁습니다. 매일매일 새로운 이야기를 들려드릴게요. 앞으로도 많은 응원 부탁드립니다. 감사합니다!"

    # 백그라운드에서 재생성 실행
    background_tasks.add_task(
        _bg_revise_voice,
        ad_id,
        character.character_id,
        revision.revision_notes,
        sample_text,
        ad_request.company_id
    )

    return AdVoiceGenerateResponse(
        character_id=character.character_id,
        voice_url=character.voice_sample_url,
        voice_id=character.elevenlabs_voice_id,
        status="regenerating"
    )


@router.post("/{ad_id}/assets/approve", response_model=AssetsApproveResponse)
async def approve_ad_assets(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """캐릭터+음성 통합 승인 -> 다음 단계 진행"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    # 이미 진행 중이거나 완료된 상태에서 호출 방지
    blocked_statuses = GENERATING_STATUSES | {AdStatus.COMPLETED, AdStatus.CONTENT_GENERATING}
    if ad_request.status in blocked_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"현재 상태에서는 에셋 승인을 할 수 없습니다 (현재: {ad_request.status})"
        )

    char_approved, voice_approved = helpers.video_crud.check_assets_approval(db, ad_id)

    if not char_approved:
        return AssetsApproveResponse(
            status=ApprovalStatus.PENDING,
            message="캐릭터가 아직 승인되지 않았습니다",
            can_proceed=False
        )

    if not voice_approved:
        return AssetsApproveResponse(
            status=ApprovalStatus.PENDING,
            message="음성이 아직 승인되지 않았습니다",
            can_proceed=False
        )

    helpers.video_crud.update_ad_status(db, ad_id, 'processing', 'scenario_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["assets_approved"], 'scenario_generation')

    return AssetsApproveResponse(
        status=ApprovalStatus.APPROVED,
        message="에셋이 모두 승인되었습니다. 시나리오 생성을 진행할 수 있습니다.",
        can_proceed=True
    )


@router.post("/{ad_id}/scenario/approve", response_model=ItemApprovalResponse)
async def approve_ad_scenario(
    ad_id: int,
    request: Request,
    approval: ItemApprovalRequest,
    db: Session = Depends(get_db)
):
    """광고용 시나리오 승인"""
    user_info = await get_current_user(request)
    _get_ad_request_with_auth(db, ad_id, user_info)

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오가 아직 생성되지 않았습니다")

    if approval.approved:
        helpers.video_crud.update_scenario_approval(db, scenario.script_id, ApprovalStatus.APPROVED, user_info["account_id"])
        return ItemApprovalResponse(status=ApprovalStatus.APPROVED, message="시나리오가 승인되었습니다")
    else:
        helpers.video_crud.update_scenario_approval(db, scenario.script_id, ApprovalStatus.REJECTED)
        return ItemApprovalResponse(status=ApprovalStatus.REJECTED, message="시나리오가 거부되었습니다")


@router.post("/{ad_id}/scenario/revise")
async def revise_ad_scenario(
    ad_id: int,
    request: Request,
    revision: ScenarioReviseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 시나리오 씬별 수정 요청 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오가 아직 생성되지 않았습니다")

    scene_revisions = [
        {"scene_number": r.scene_number, "scenario_notes": r.scenario_notes}
        for r in revision.scene_revisions
    ]

    # scene_number → scene_key 변환 (AI pipeline과 동일한 네이밍)
    scene_feedback = {}
    for rev in scene_revisions:
        key = SCENE_KEY_MAP.get(rev["scene_number"], f"scene_{rev['scene_number']}")
        if rev.get("scenario_notes"):
            scene_feedback[key] = rev["scenario_notes"]

    # 피드백을 DB에 먼저 저장 (run_scenario_regenerate_step이 DB에서 읽음)
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
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_SCENARIO, 'scenario_generation')

    background_tasks.add_task(
        _bg_revise_scenario,
        ad_id=ad_id,
        script_id=scenario.script_id,
        scene_revisions=scene_revisions,
        company_id=ad_request.company_id,
        original_status=original_status,
    )

    return {"ad_id": ad_id, "script_id": scenario.script_id, "status": AdStatus.GENERATING_SCENARIO}


@router.post("/{ad_id}/video/approve", response_model=ItemApprovalResponse)
async def approve_ad_video(
    ad_id: int,
    request: Request,
    approval: ItemApprovalRequest,
    db: Session = Depends(get_db)
):
    """광고용 영상 승인"""
    user_info = await get_current_user(request)
    _get_ad_request_with_auth(db, ad_id, user_info)

    video = helpers.video_crud.get_video_by_ad(db, ad_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상이 아직 생성되지 않았습니다")

    if video.status == VideoStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="영상 생성이 아직 진행 중입니다")

    if approval.approved:
        helpers.video_crud.update_video_status(db, video.video_id, VideoStatus.CLIENT_APPROVED)
        helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["video_approved"], 'video_generation')
        return ItemApprovalResponse(status=ApprovalStatus.APPROVED, message="영상이 승인되었습니다")
    else:
        helpers.video_crud.update_video_status(db, video.video_id, 'client_rejected')
        return ItemApprovalResponse(status=ApprovalStatus.REJECTED, message="영상이 거부되었습니다")


@router.post("/{ad_id}/video/revise")
async def revise_ad_video(
    ad_id: int,
    request: Request,
    revision: VideoSceneReviseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 영상 씬별 수정 요청 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    video = helpers.video_crud.get_video_by_ad(db, ad_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상이 아직 생성되지 않았습니다")

    scene_revisions = [
        {"scene_number": r.scene_number, "video_notes": r.video_notes}
        for r in revision.scene_revisions
    ]

    helpers.video_crud.update_video_revision(
        db,
        video.video_id,
        {"scene_revisions": scene_revisions}
    )

    original_status = ad_request.status
    helpers.video_crud.update_video_status(db, video.video_id, VideoStatus.PROCESSING)
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_VIDEO, 'video_generation')

    background_tasks.add_task(
        _bg_revise_video,
        ad_id=ad_id,
        video_id=video.video_id,
        scene_revisions=scene_revisions,
        company_id=ad_request.company_id,
        original_status=original_status,
    )

    return {"ad_id": ad_id, "video_id": video.video_id, "status": AdStatus.GENERATING_VIDEO}
