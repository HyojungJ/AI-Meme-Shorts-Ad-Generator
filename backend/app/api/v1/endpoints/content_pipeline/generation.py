"""
Content Pipeline API - generation + preview endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import AdStatus
from . import helpers
from .helpers import (
    get_current_user, get_db,
    _get_ad_request_with_auth, _check_not_generating,
    PROGRESS,
    AdCharacterGenerateRequest,
    AdVoiceGenerateRequest,
    ScenarioGenerateRequest,
    CharacterPreviewByAdResponse,
    VoicePreviewByAdResponse,
    ScenarioResponse,
    SceneResponse,
    VideoPreviewByAdResponse,
)
from .tasks import (
    _bg_generate_character,
    _bg_generate_voice,
    _bg_generate_scenario,
    _bg_generate_video,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# === 생성 API ===

@router.post("/{ad_id}/character/generate")
async def generate_ad_character(
    ad_id: int,
    request: Request,
    char_request: AdCharacterGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 캐릭터 이미지 생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_CHARACTER, 'character_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["character_start"], 'character_generation')

    background_tasks.add_task(
        _bg_generate_character,
        ad_id=ad_id,
        char_prompt=char_request.character_prompt,
        aspect_ratio=char_request.aspect_ratio or "9:16",
        company_id=ad_request.company_id,
        original_status=original_status,
        force_new_character=bool(char_request.force_new_character),
    )

    return {"ad_id": ad_id, "status": AdStatus.GENERATING_CHARACTER}


@router.post("/{ad_id}/voice/generate")
async def generate_ad_voice(
    ad_id: int,
    request: Request,
    voice_request: AdVoiceGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 음성 생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    if not ad_request.character_id:
        raise HTTPException(status_code=400, detail="캐릭터를 먼저 생성해주세요")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    voice_description = (
        voice_request.voice_description
        or character.voice_design_prompt
        or "neutral voice"
    )

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_VOICE, 'character_generation')

    background_tasks.add_task(
        _bg_generate_voice,
        ad_id=ad_id,
        character_id=character.character_id,
        company_id=ad_request.company_id,
        voice_description=voice_description,
        sample_text=voice_request.sample_text,
        original_status=original_status,
    )

    return {"ad_id": ad_id, "character_id": character.character_id, "status": AdStatus.GENERATING_VOICE}


@router.post("/{ad_id}/scenario/generate")
async def generate_ad_scenario(
    ad_id: int,
    request: Request,
    scenario_request: ScenarioGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 시나리오 생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    if ad_request.status == AdStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="이미 완료된 광고입니다")

    char_approved, voice_approved = helpers.video_crud.check_assets_approval(db, ad_id)
    if not (char_approved and voice_approved):
        raise HTTPException(status_code=400, detail="캐릭터와 음성이 먼저 승인되어야 합니다")

    meme_id = scenario_request.meme_id or ad_request.meme_id
    if not meme_id:
        raise HTTPException(status_code=400, detail="밈을 선택해주세요")

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_SCENARIO, 'scenario_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_start"], 'scenario_generation')

    background_tasks.add_task(
        _bg_generate_scenario,
        ad_id=ad_id,
        meme_id=meme_id,
        product_name=ad_request.item_name or "Unknown Product",
        product_category=ad_request.item_category or "기타",
        product_highlight=ad_request.item_description or "",  # item_keymessage → item_description
        original_status=original_status,
    )

    return {"ad_id": ad_id, "status": AdStatus.GENERATING_SCENARIO}


@router.post("/{ad_id}/video/generate")
async def generate_ad_video(
    ad_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """광고용 영상 생성 (백그라운드)"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)
    _check_not_generating(ad_request)

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="시나리오를 먼저 생성해주세요")

    if not ad_request.character_id:
        raise HTTPException(status_code=400, detail="캐릭터를 먼저 생성해주세요")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if not character.elevenlabs_voice_id:
        raise HTTPException(status_code=400, detail="음성을 먼저 생성해주세요")

    original_status = ad_request.status
    helpers.video_crud.update_ad_status(db, ad_id, AdStatus.GENERATING_VIDEO, 'video_generation')
    helpers.video_crud.update_workflow_progress(db, ad_id, PROGRESS["video_start"], 'video_generation')

    video = helpers.video_crud.create_video_for_ad(
        db=db,
        ad_id=ad_id,
        company_id=ad_request.company_id,
        account_id=user_info["account_id"],
        title=scenario.title,
        script_id=scenario.script_id
    )

    product_image_url = helpers.get_presigned_url(ad_request.item_images[0]) if ad_request.item_images else None
    character_image_presigned = helpers.get_presigned_url(character.image_url) if character.image_url else None

    background_tasks.add_task(
        _bg_generate_video,
        ad_id=ad_id,
        video_id=video.video_id,
        script_id=scenario.script_id,
        company_id=ad_request.company_id,
        character_id=ad_request.character_id,
        scenes=scenario.scenes,
        character_image_url=character_image_presigned,
        voice_id=character.elevenlabs_voice_id,
        title=scenario.title,
        original_status=original_status,
        product_image_url=product_image_url,
    )

    return {"ad_id": ad_id, "video_id": video.video_id, "status": AdStatus.GENERATING_VIDEO}


# === 미리보기 API ===

@router.get("/{ad_id}/character/preview", response_model=CharacterPreviewByAdResponse)
async def preview_ad_character(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고별 캐릭터 미리보기"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    if not ad_request.character_id:
        raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    image_url = helpers.get_presigned_url(character.image_url) or character.image_url

    return CharacterPreviewByAdResponse(
        character_id=character.character_id,
        image_url=image_url,
        is_approved=character.is_active,
        created_at=character.created_at.isoformat()
    )


@router.get("/{ad_id}/voice/preview", response_model=VoicePreviewByAdResponse)
async def preview_ad_voice(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고별 음성 미리보기"""
    user_info = await get_current_user(request)
    ad_request = _get_ad_request_with_auth(db, ad_id, user_info)

    if not ad_request.character_id:
        raise HTTPException(status_code=404, detail="캐릭터가 아직 생성되지 않았습니다")

    character = helpers.video_crud.get_character_by_id(db, ad_request.character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    voice_url = helpers.get_presigned_url(character.voice_sample_url) or character.voice_sample_url
    is_approved = bool(character.elevenlabs_voice_id)

    return VoicePreviewByAdResponse(
        character_id=character.character_id,
        voice_url=voice_url,
        is_approved=is_approved,
        created_at=character.updated_at.isoformat() if character.updated_at else character.created_at.isoformat()
    )


@router.get("/{ad_id}/scenario", response_model=ScenarioResponse)
async def get_ad_scenario(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고별 시나리오 조회"""
    user_info = await get_current_user(request)
    _get_ad_request_with_auth(db, ad_id, user_info)

    scenario = helpers.video_crud.get_scenario_by_ad(db, ad_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오가 아직 생성되지 않았습니다")

    scenes_data = scenario.scenes or []

    # scenes_data가 딕셔너리인 경우 리스트로 변환
    if isinstance(scenes_data, dict):
        scenes_list = []
        for key in sorted(scenes_data.keys()):
            if key.startswith('scene'):
                scenes_list.append(scenes_data[key])
        scenes_data = scenes_list

    scenes = []
    for i, scene in enumerate(scenes_data):
        # scene이 딕셔너리인지 확인
        if isinstance(scene, dict):
            scenes.append(SceneResponse(
                scene_number=i + 1,
                content=scene.get('content', '') or scene.get('dialogue', ''),
                timestamp=scene.get('timestamp')
            ))
        else:
            # scene이 문자열이거나 다른 타입인 경우 스킵
            continue

    return ScenarioResponse(
        script_id=scenario.script_id,
        title=scenario.title,
        description=scenario.description,
        scenes=scenes,
        approval_status=scenario.approval_status
    )


@router.get("/{ad_id}/video/preview", response_model=VideoPreviewByAdResponse)
async def preview_ad_video(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """광고별 영상 미리보기"""
    user_info = await get_current_user(request)
    _get_ad_request_with_auth(db, ad_id, user_info)

    video = helpers.video_crud.get_video_by_ad(db, ad_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상이 아직 생성되지 않았습니다")

    return VideoPreviewByAdResponse(
        video_id=video.video_id,
        preview_url=helpers.get_presigned_url(video.s3_url) if video.s3_url else None,
        thumbnail_url=video.thumbnail_url,
        duration_seconds=video.duration_seconds,
        status=video.status
    )
