"""
Content Pipeline API - background task functions
"""
import logging
from datetime import datetime

from .helpers import (
    _run_async, _bg_safe_rollback, _bg_run_video_generation,
    PROGRESS, video_crud, SessionLocal, AIPipelineClient,
)

logger = logging.getLogger(__name__)


def _bg_generate_character(
    ad_id: int,
    char_prompt: str,
    aspect_ratio: str,
    company_id: int,
    original_status: str,
    force_new_character: bool = False,
):
    """백그라운드에서 캐릭터 이미지 + 음성 생성"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()

        # 1. 캐릭터 이미지 생성
        result = _run_async(ai_client.generate_character_image(
            character_prompt=char_prompt,
            character_name=f"Ad_{ad_id}_Character",
            company_id=company_id,
            aspect_ratio=aspect_ratio,
        ))

        image_url = result.get('image_url')
        if not image_url:
            error_msg = result.get('error', 'image_url 없음')
            video_crud.update_ad_status(db, ad_id, 'failed')
            logger.error(f"캐릭터 이미지 생성 실패 (ad_id={ad_id}): {error_msg}")
            return

        voice_design_prompt = result.get('voice_design_prompt')
        image_prompt = result.get('image_prompt') or char_prompt

        video_crud.enforce_character_slot_limit(db, company_id, max_active=5)
        character = video_crud.create_company_character(
            db=db,
            company_id=company_id,
            image_url=image_url,
            image_prompt=image_prompt,
            image_model=result.get('model', 'imagen-3.0'),
            voice_design_prompt=voice_design_prompt,
        )

        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        if ad_request:
            ad_request.character_id = character.character_id
            ad_request.character_image_prompt = image_prompt
            ad_request.character_voice_prompt = voice_design_prompt
            db.commit()

        logger.info(f"캐릭터 이미지 생성 완료 (ad_id={ad_id}, character_id={character.character_id})")

        # 2. 음성 생성
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["voice_start"], 'voice_generation')

        sample_text = (
            "안녕하세요, 저는 이 광고의 캐릭터입니다. "
            "오늘 여러분께 정말 좋은 제품을 소개해 드리려고 해요. "
            "이 제품은 여러분의 일상을 더욱 편리하고 즐겁게 만들어 줄 거예요. 지금 바로 확인해 보세요!"
        )

        if not voice_design_prompt or len(voice_design_prompt) < 20:
            voice_design_prompt = (voice_design_prompt or char_prompt) + ", 자연스럽고 친근한 목소리"

        voice_result = _run_async(ai_client.generate_voice(
            text=sample_text,
            voice_description=voice_design_prompt,
            character_id=character.character_id,
            company_id=company_id
        ))

        voice_id = voice_result.get('voice_id')
        voice_sample_url = voice_result.get('voice_url')

        if not voice_id:
            error_msg = voice_result.get('error', 'voice_id 없음')
            video_crud.update_ad_status(db, ad_id, 'failed')
            logger.error(f"음성 생성 실패 (ad_id={ad_id}): {error_msg}")
            return

        character.elevenlabs_voice_id = voice_id
        if voice_sample_url:
            character.voice_sample_url = voice_sample_url
        db.commit()

        logger.info(f"음성 생성 완료 (ad_id={ad_id}, voice_id={voice_id})")

        # 3. 음성 생성 완료 후 검수 대기로 변경
        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'character_review')
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["character_review"], 'character_review')
        logger.info(f"캐릭터+음성 생성 완료 (ad_id={ad_id}, character_id={character.character_id})")
    except Exception as e:
        logger.error(f"백그라운드 캐릭터+음성 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "character")
    finally:
        db.close()


def _bg_generate_voice(ad_id: int, character_id: int, company_id: int, voice_description: str, sample_text: str, original_status: str):
    """백그라운드에서 음성 생성"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()
        result = _run_async(ai_client.generate_voice(
            text=sample_text,
            voice_description=voice_description,
            character_id=character_id,
            company_id=company_id,
        ))

        voice_id = result.get('voice_id')
        voice_url = result.get('voice_url')

        character = video_crud.get_character_by_id(db, character_id)
        if character:
            character.elevenlabs_voice_id = voice_id
            character.voice_sample_url = voice_url
            character.voice_design_prompt = voice_description
            character.updated_at = datetime.utcnow()
            db.commit()

        video_crud.update_workflow_progress(db, ad_id, PROGRESS["character_review"], 'character_generation')
        video_crud.update_ad_status(db, ad_id, original_status)
        logger.info(f"음성 생성 완료 (ad_id={ad_id}, voice_id={voice_id})")
    except Exception as e:
        logger.error(f"백그라운드 음성 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "voice")
    finally:
        db.close()


def _bg_revise_scenario(ad_id: int, script_id: int, scene_revisions: list, company_id: int, original_status: str):
    """백그라운드에서 시나리오 수정"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()
        result = _run_async(ai_client.revise_scenario(
            script_id=script_id,
            scene_revisions=scene_revisions,
            company_id=company_id,
            ad_id=ad_id,
        ))

        new_scenes = result.get('scenes', [])
        new_script_id = result.get('script_id', script_id)

        if new_script_id != script_id:
            video_crud.update_scenario_approval(db, new_script_id, 'pending')
        else:
            video_crud.update_scenario_scenes(db, script_id, new_scenes)
            video_crud.update_scenario_approval(db, script_id, 'pending')

        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'scenario_review')
        logger.info(f"시나리오 수정 완료 (ad_id={ad_id}, script_id={new_script_id})")
    except Exception as e:
        logger.error(f"백그라운드 시나리오 수정 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "scenario_revise")
    finally:
        db.close()


def _bg_revise_video(ad_id: int, video_id: int, scene_revisions: list, company_id: int, original_status: str):
    """백그라운드에서 영상 수정"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()
        result = _run_async(ai_client.revise_video(
            video_id=video_id,
            scene_revisions=scene_revisions,
            company_id=company_id,
        ))

        video_url = result.get('video_url')
        if video_url:
            video_crud.update_video_status(db, video_id, 'completed', s3_url=video_url)
            video_crud.update_ad_status(db, ad_id, 'pending_approval', 'scenario_review')
            logger.info(f"영상 수정 완료 (ad_id={ad_id}, video_id={video_id})")
        else:
            video_crud.update_video_status(db, video_id, 'failed', error_message="video_url is empty")
            video_crud.update_ad_status(db, ad_id, 'failed')
            logger.error(f"영상 수정 결과에 video_url 없음 (ad_id={ad_id})")
    except Exception as e:
        logger.error(f"백그라운드 영상 수정 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "video_revise")
    finally:
        db.close()


def _bg_generate_scenario(ad_id: int, meme_id: int, product_name: str, product_category: str, product_highlight: str, original_status: str):
    """백그라운드에서 시나리오 생성 -> 영상 생성까지 자동 연결"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()

        # 1. 시나리오 생성
        result = _run_async(ai_client.generate_scenario(
            product_name=product_name,
            product_category=product_category,
            product_highlight=product_highlight,
            meme_id=meme_id,
            ad_id=ad_id,
        ))

        scenes_data = result.get('scenes', [])
        title = result.get('title', f"{product_name} 광고")

        # AI pipeline이 이미 scenario_scripts에 저장했으므로 조회만
        script_id = result.get('script_id')
        scenario = video_crud.get_scenario_by_id(db, script_id) if script_id else None
        if not scenario:
            scenario = video_crud.get_scenario_by_ad(db, ad_id)

        video_crud.update_ad_status(db, ad_id, 'generating_video', 'scenario_generation')
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_done"], 'scenario_generation')
        logger.info(f"시나리오 생성 완료, 영상 생성 시작 (ad_id={ad_id})")

        # 2. 영상 생성 자동 연결
        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        character = video_crud.get_character_by_id(db, ad_request.character_id)
        if not character or not character.elevenlabs_voice_id:
            logger.error(f"영상 생성 불가: 캐릭터/음성 없음 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'pending_approval', 'scenario_generation')
            return

        _bg_run_video_generation(db, ai_client, ad_id, ad_request, character, scenario, scenes_data, title)

    except Exception as e:
        logger.error(f"백그라운드 시나리오+영상 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "scenario")
    finally:
        db.close()


def _bg_generate_video(
    ad_id: int, video_id: int, script_id: int, company_id: int,
    character_id: int, scenes: list, character_image_url: str, voice_id: str, title: str, original_status: str,
    product_image_url: str = None,
):
    """백그라운드에서 영상 생성 (단독)"""
    db = SessionLocal()
    try:
        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        character = video_crud.get_character_by_id(db, character_id)
        scenario = video_crud.get_scenario_by_ad(db, ad_id)
        if not ad_request or not character or not scenario:
            logger.error(f"영상 생성 불가: 데이터 누락 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'failed')
            return

        ai_client = AIPipelineClient()
        _bg_run_video_generation(db, ai_client, ad_id, ad_request, character, scenario, scenes, title)
    except Exception as e:
        logger.error(f"백그라운드 영상 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "video")
    finally:
        db.close()


def _bg_generate_content(ad_id: int, meme_id: int, product_name: str, product_category: str, product_highlight: str, original_status: str):
    """백그라운드에서 시나리오+TTS+영상 통합 생성"""
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()

        # 1. 시나리오 생성
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_start"], 'scenario_generation')
        result = _run_async(ai_client.generate_scenario(
            product_name=product_name,
            product_category=product_category,
            product_highlight=product_highlight,
            meme_id=meme_id,
            ad_id=ad_id,
        ))

        scenes_data = result.get('scenes', [])
        title = result.get('title', f"{product_name} 광고")

        # AI pipeline이 이미 scenario_scripts에 저장했으므로 조회만
        script_id = result.get('script_id')
        scenario = video_crud.get_scenario_by_id(db, script_id) if script_id else None
        if not scenario:
            scenario = video_crud.get_scenario_by_ad(db, ad_id)

        video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_done"], 'scenario_generation')
        logger.info(f"[content/generate] 시나리오 생성 완료 (ad_id={ad_id})")

        # 2. 영상 생성
        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        character = video_crud.get_character_by_id(db, ad_request.character_id)
        if not character or not character.elevenlabs_voice_id:
            logger.error(f"영상 생성 불가: 캐릭터/음성 없음 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'failed')
            return

        _bg_run_video_generation(db, ai_client, ad_id, ad_request, character, scenario, scenes_data, title)

    except Exception as e:
        logger.error(f"[content/generate] 통합 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "content_generate")
    finally:
        db.close()


def _bg_revise_content(ad_id: int, original_status: str):
    """백그라운드에서 시나리오+TTS+영상 통합 재생성"""
    logger.info(f"[_bg_revise_content] 시작 (ad_id={ad_id})")
    db = SessionLocal()
    try:
        ai_client = AIPipelineClient()

        # 1. 시나리오 재생성 (DB에 저장된 피드백 기반)
        video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_start"], 'scenario_generation')
        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        scenario = video_crud.get_scenario_by_ad(db, ad_id)
        if not scenario:
            logger.error(f"[content/revise] 시나리오 없음 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'failed')
            return

        logger.info(f"[_bg_revise_content] 시나리오 재생성 시작 (ad_id={ad_id}, script_id={scenario.script_id})")

        # scene_revisions는 이미 DB(scenario_scripts.review_result)에 저장됨
        # Direct 모드: run_scenario_regenerate_step(ad_id)가 DB에서 직접 읽음
        # HTTP 모드: ad_id를 전달하여 서버 측에서 DB 읽기
        result = _run_async(ai_client.revise_scenario(
            script_id=scenario.script_id,
            scene_revisions=[],
            company_id=ad_request.company_id,
            ad_id=ad_id
        ))

        logger.info(f"[_bg_revise_content] 시나리오 재생성 완료 (ad_id={ad_id}, result={result})")

        new_scenes = result.get('scenes', scenario.scenes)
        new_script_id = result.get('script_id', scenario.script_id)

        if new_script_id != scenario.script_id:
            video_crud.update_scenario_approval(db, new_script_id, 'pending')
        else:
            video_crud.update_scenario_scenes(db, scenario.script_id, new_scenes)
            video_crud.update_scenario_approval(db, scenario.script_id, 'pending')

        video_crud.update_workflow_progress(db, ad_id, PROGRESS["scenario_done"], 'scenario_generation')
        logger.info(f"[content/revise] 시나리오 재생성 완료 (ad_id={ad_id})")

        # 2. 영상 재생성
        logger.info(f"[_bg_revise_content] 영상 재생성 시작 (ad_id={ad_id})")
        character = video_crud.get_character_by_id(db, ad_request.character_id)
        if not character or not character.elevenlabs_voice_id:
            logger.error(f"[content/revise] 캐릭터/음성 없음 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'failed')
            return

        # script_id가 바뀌었으면 시나리오 다시 조회
        revised_scenario = scenario
        if new_script_id != scenario.script_id:
            revised_scenario = video_crud.get_scenario_by_id(db, new_script_id) or scenario

        api_scenes = new_scenes if isinstance(new_scenes, list) else []
        logger.info(f"[_bg_revise_content] _bg_run_video_generation 호출 (ad_id={ad_id}, scenes_count={len(api_scenes)})")
        _bg_run_video_generation(
            db, ai_client, ad_id, ad_request, character, revised_scenario,
            api_scenes, result.get('title', scenario.title)
        )
        logger.info(f"[_bg_revise_content] 영상 재생성 완료 (ad_id={ad_id})")

    except Exception as e:
        logger.error(f"[content/revise] 통합 재생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
        _bg_safe_rollback(db, ad_id, original_status, "content_revise")
    finally:
        db.close()


def _bg_revise_character(ad_id: int, character_id: int, revision_notes: str, character_prompt: str, company_id: int):
    """백그라운드에서 캐릭터 이미지 재생성 + AI 검수"""
    db = SessionLocal()
    try:
        character = video_crud.get_character_by_id(db, character_id)
        if not character:
            logger.error(f"캐릭터를 찾을 수 없음 (character_id={character_id})")
            video_crud.update_ad_status(db, ad_id, 'failed', 'character_generation')
            return

        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        if not ad_request:
            logger.error(f"광고 요청을 찾을 수 없음 (ad_id={ad_id})")
            video_crud.update_ad_status(db, ad_id, 'failed', 'character_generation')
            return

        base_prompt = character_prompt or character.image_prompt or ""
        original_image_url = character.image_url or ""

        logger.info(f"[캐릭터 재생성] ad_id={ad_id}, character_id={character_id}")
        logger.info(f"[캐릭터 재생성] 기존 프롬프트: {base_prompt}")
        logger.info(f"[캐릭터 재생성] 수정 요청: {revision_notes}")

        ai_client = AIPipelineClient()
        result = _run_async(ai_client.regenerate_character_image(
            character_id=character_id,
            original_image_url=original_image_url,
            revision_notes=revision_notes or "",
            character_prompt=base_prompt,
            company_id=company_id,
            aspect_ratio="9:16",
        ))

        logger.info(f"[캐릭터 재생성] AI 파이프라인 전체 응답: {result}")

        image_url = result.get('image_url')
        image_path = result.get('image_path')

        logger.info(f"[캐릭터 재생성] image_url: {image_url}")
        logger.info(f"[캐릭터 재생성] image_path: {image_path}")

        if not image_url:
            logger.error(f"[캐릭터 재생성] 이미지 URL이 없음. 전체 응답: {result}")
            raise Exception(f"No image returned from model response. Result: {result}")

        # 프롬프트 업데이트
        if character_prompt:
            character.image_prompt = character_prompt
        elif revision_notes:
            character.image_prompt = f"{base_prompt}. Modification: {revision_notes}"

        character.image_url = image_url
        character.is_active = False
        character.updated_at = datetime.utcnow()

        # 검증 결과 저장 (GPT-4o Vision)
        verification_score = result.get('verification_score')
        if verification_score is not None:
            character.generation_metadata = {
                **(character.generation_metadata or {}),
                "auto_review": {
                    "score": verification_score,
                    "decision": result.get('verification_decision'),
                    "retry_count": result.get('retry_count', 0),
                }
            }
            logger.info(f"[캐릭터 재생성] 검증 결과 저장: score={verification_score}, decision={result.get('verification_decision')}")

        db.commit()

        # 상태를 '캐릭터 검수 대기'로 변경
        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'character_approval')
        logger.info(f"[캐릭터 재생성] 완료 - ad_id={ad_id}, character_id={character_id}, image_url={image_url}")

    except Exception as e:
        logger.error(f"[캐릭터 재생성] 오류 (ad_id={ad_id}): {str(e)}", exc_info=True)
        video_crud.update_ad_status(db, ad_id, 'failed', 'character_generation')
    finally:
        db.close()


def _bg_revise_voice(ad_id: int, character_id: int, revision_notes: str, sample_text: str, company_id: int):
    """백그라운드에서 음성 재생성"""
    db = SessionLocal()
    try:
        character = video_crud.get_character_by_id(db, character_id)
        if not character:
            logger.error(f"캐릭터를 찾을 수 없음 (character_id={character_id})")
            video_crud.update_ad_status(db, ad_id, 'failed', 'voice_generation')
            return

        ai_client = AIPipelineClient()
        result = _run_async(ai_client.generate_voice(
            text=sample_text,
            voice_description=revision_notes,
            character_id=character_id,
            company_id=company_id
        ))

        voice_url = result.get('voice_url')
        voice_id = result.get('voice_id')

        character.elevenlabs_voice_id = voice_id
        character.voice_sample_url = voice_url
        character.voice_design_prompt = revision_notes
        character.updated_at = datetime.utcnow()
        db.commit()

        # 상태를 '캐릭터 검수 대기'로 변경
        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'character_approval')
        logger.info(f"음성 재생성 완료 (ad_id={ad_id}, character_id={character_id})")

    except Exception as e:
        logger.error(f"음성 재생성 오류 (ad_id={ad_id}): {str(e)}")
        video_crud.update_ad_status(db, ad_id, 'failed', 'voice_generation')
    finally:
        db.close()
