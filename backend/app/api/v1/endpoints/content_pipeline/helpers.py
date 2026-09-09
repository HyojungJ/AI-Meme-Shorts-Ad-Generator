"""
Content Pipeline API - shared helpers and constants
"""
import asyncio
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.video import (
    AdCharacterGenerateRequest,
    AdCharacterGenerateResponse,
    AdVoiceGenerateRequest,
    AdVoiceGenerateResponse,
    ScenarioGenerateRequest,
    ScenarioGenerateResponse,
    SceneResponse,
    AdVideoGenerateResponse,
    CharacterPreviewByAdResponse,
    VoicePreviewByAdResponse,
    ScenarioResponse,
    VideoPreviewByAdResponse,
    ItemApprovalRequest,
    ItemApprovalResponse,
    CharacterRevisionRequest,
    VoiceRevisionRequest,
    ScenarioReviseRequest,
    VideoSceneReviseRequest,
    AssetsApproveResponse,
    ContentApproveResponse,
    ContentGenerateRequest,
    ContentReviseRequest,
    ContentGenerateResponse,
)
from app.crud import video as video_crud
from app.core.security import get_current_user
from app.db.session import get_db, SessionLocal
from app.services.s3_service import get_presigned_url

from app.services.ai_pipeline_factory import AIPipelineClient
from app.core.constants import (
    WORKFLOW_PROGRESS as PROGRESS,
    GENERATING_STATUSES,
)

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async coroutine in sync background task context."""
    return asyncio.run(coro)

SCENE_KEY_MAP = {1: "scene_1", 2: "scene_2", 3: "scene_3", 4: "scene_4"}


def _bg_safe_rollback(db, ad_id: int, fallback_status: str, label: str):
    """백그라운드 에러 시 rollback + 상태 복구"""
    db.rollback()
    try:
        video_crud.update_ad_status(db, ad_id, fallback_status)
    except Exception as inner:
        logger.error(f"상태 복구 실패 ({label}, ad_id={ad_id}): {inner}", exc_info=True)
        db.rollback()
        # 원래 상태 복구도 실패하면 최소한 'failed'로 전환 시도
        try:
            video_crud.update_ad_status(db, ad_id, 'failed')
        except Exception:
            db.rollback()
            logger.critical(f"failed 전환도 실패, 수동 복구 필요 ({label}, ad_id={ad_id})")


def _bg_run_video_generation(db, ai_client, ad_id: int, ad_request, character, scenario, scenes_data: list, title: str):
    """백그라운드 영상 생성 공통 로직. video 객체를 반환."""
    # 영상 생성 시작 - 상태를 video_generating으로 변경
    video_crud.update_ad_status(db, ad_id, 'generating_video', 'video_generation')

    video = video_crud.get_video_by_ad(db, ad_id)
    if not video:
        video = video_crud.create_video_for_ad(
            db=db, ad_id=ad_id, company_id=ad_request.company_id,
            account_id=ad_request.account_id, title=title,
            script_id=scenario.script_id
        )
    else:
        video_crud.update_video_status(db, video.video_id, 'processing')

    video_crud.update_workflow_progress(db, ad_id, PROGRESS["video_start"], 'video_generation')

    product_image_url = get_presigned_url(ad_request.item_images[0]) if ad_request.item_images else None
    character_image_presigned = get_presigned_url(character.image_url) if character.image_url else None
    clone_prompt_url = (character.generation_metadata or {}).get("clone_prompt_url")
    voice_description = character.voice_design_prompt

    video_result = _run_async(ai_client.generate_video(
        ad_id=ad_id, script_id=scenario.script_id,
        company_id=ad_request.company_id,
        character_id=ad_request.character_id,
        scenes=scenes_data, character_image_url=character_image_presigned,
        voice_id=character.elevenlabs_voice_id, title=title,
        product_image_url=product_image_url,
        clone_prompt_url=clone_prompt_url,
        voice_description=voice_description,
        character_description=character.image_prompt,
    ))

    video_url = video_result.get('video_url')
    if video_url:
        video_crud.update_video_status(db, video.video_id, 'completed', s3_url=video_url)

        # 검증 결과 저장 (Gemini 2.5 Pro)
        verification_score = video_result.get('verification_score')
        if verification_score is not None:
            video.review_result = {
                "auto_review": {
                    "score": verification_score,
                    "decision": video_result.get('verification_decision'),
                    "message": video_result.get('verification_message', ''),
                }
            }
            db.commit()
            logger.info(f"영상 검증 결과 저장: ad_id={ad_id}, score={verification_score}")

        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'scenario_review')
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["content_review"], 'scenario_review')
        logger.info(f"영상 생성 완료 (ad_id={ad_id}, video_id={video.video_id})")
    else:
        video_crud.update_video_status(db, video.video_id, 'failed', error_message="video_url is empty")
        video_crud.update_ad_status(db, ad_id, 'failed')
        logger.error(f"영상 생성 결과에 video_url 없음 (ad_id={ad_id})")

    return video


def _check_not_generating(ad_request):
    """이미 생성 중이면 409 반환"""
    if ad_request.status in GENERATING_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"이미 생성이 진행 중입니다 (현재 상태: {ad_request.status})"
        )


def _lock_ad_request(db: Session, ad_id: int):
    """행 잠금으로 동시 상태 변경 방지 (SELECT FOR UPDATE)"""
    db.execute(text("SELECT 1 FROM ad_requests WHERE ad_id = :id FOR UPDATE"), {"id": ad_id})


def _get_ad_request_with_auth(db: Session, ad_id: int, user_info: dict):
    """광고 요청 조회 및 권한 확인"""
    ad_request = video_crud.get_ad_request_by_id(db, ad_id)
    if not ad_request:
        raise HTTPException(status_code=404, detail="광고 요청을 찾을 수 없습니다")

    if user_info.get("account_type") != 'admin':
        if ad_request.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    return ad_request
