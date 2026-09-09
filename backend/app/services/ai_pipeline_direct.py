"""
AI 파이프라인 Direct 클라이언트
HTTP 대신 AI 함수를 직접 호출 (프로토타입/테스트용)

요구사항:
- AI 패키지의 모든 의존성이 설치되어 있어야 함
- backend와 AI 폴더가 같은 부모 디렉토리에 있어야 함

사용법:
    1. AI 폴더의 uv 환경에서 backend 실행:
       cd AI && uv run -- uvicorn backend.app.main:app

    2. 또는 backend의 pyproject.toml에 AI 의존성 추가 후 실행
"""
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# AI 패키지 경로 추가
_ai_path = Path(__file__).parent.parent.parent.parent / "AI"
if str(_ai_path) not in sys.path:
    sys.path.insert(0, str(_ai_path))

# Lazy import: AI 함수들은 실제 호출 시점에 import
_ai_functions = None


def _load_ai_functions():
    """AI 함수들을 lazy import (의존성 에러 시점 지연)"""
    global _ai_functions
    if _ai_functions is not None:
        return _ai_functions

    try:
        from content_pipeline.pipeline import (
            suggest_character_prompts_from_product,
            run_character_step,
            run_voice_design_step,
            run_tts_step,
            run_scenario_step,
            run_scene_image_step,
            run_video_step,
            run_image_regeneration_step,
            run_video_regeneration_step,
            run_scenario_regenerate_step,
            run_asset_generation_step,
            run_content_generation_step,
            run_content_regenerate_step,
        )
        _ai_functions = {
            "suggest_character_prompts_from_product": suggest_character_prompts_from_product,
            "run_character_step": run_character_step,
            "run_voice_design_step": run_voice_design_step,
            "run_tts_step": run_tts_step,
            "run_scenario_step": run_scenario_step,
            "run_scene_image_step": run_scene_image_step,
            "run_video_step": run_video_step,
            "run_image_regeneration_step": run_image_regeneration_step,
            "run_video_regeneration_step": run_video_regeneration_step,
            "run_scenario_regenerate_step": run_scenario_regenerate_step,
            "run_asset_generation_step": run_asset_generation_step,
            "run_content_generation_step": run_content_generation_step,
            "run_content_regenerate_step": run_content_regenerate_step,
        }
        logger.info("AI functions loaded successfully")
        return _ai_functions
    except ImportError as e:
        raise ImportError(
            f"AI 패키지 import 실패: {e}\n"
            "AI 패키지의 의존성이 설치되어 있는지 확인하세요.\n"
            "해결 방법: cd AI && uv sync && cd ../backend && uv run -- uvicorn app.main:app"
        ) from e


from app.services.ai_pipeline_base import AIPipelineBase


class AIPipelineDirectClient(AIPipelineBase):
    """AI 파이프라인 Direct 클라이언트 (AI 함수 직접 호출)"""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url)

    async def generate_character_image(
        self,
        character_prompt: str,
        character_name: str,
        company_id: int,
        aspect_ratio: str = "9:16",
        product_name: Optional[str] = None,
        product_category: Optional[str] = None,
        product_description: Optional[str] = None,
        character_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        캐릭터 이미지 생성.

        character_prompt가 있으면 이미지 프롬프트로 그대로 사용하고,
        product_* 정보가 있으면 보이스 프롬프트 추천에 활용한다.
        """
        funcs = _load_ai_functions()

        has_prompt = bool((character_prompt or "").strip())
        has_product = bool(product_name or product_category or product_description)

        image_prompt = None
        voice_description = None

        if has_prompt:
            image_prompt = (character_prompt or "").strip()
            if has_product:
                prompts = funcs["suggest_character_prompts_from_product"](
                    item_name=product_name or "",
                    item_category=product_category or "",
                    item_description=product_description or "",
                )
                voice_description = prompts.get("voice_description")
        else:
            prompts = funcs["suggest_character_prompts_from_product"](
                item_name=product_name or "",
                item_category=product_category or "",
                item_description=product_description or "",
            )
            image_prompt = prompts.get("character_prompt")
            voice_description = prompts.get("voice_description")

        if not image_prompt:
            image_prompt = (
                "A friendly adult with bright eyes and a warm, welcoming smile. "
                "Soft, even lighting and a clean, cheerful atmosphere. Full body shot."
            )
        if isinstance(voice_description, str):
            voice_description = voice_description.strip() or None

        # character_id 추출 (파라미터 우선, 없으면 character_name에서 파싱)
        char_id = character_id
        if not char_id and character_name and character_name.startswith("Character_"):
            try:
                char_id = int(character_name.split("_")[1])
            except (IndexError, ValueError):
                pass

        result = funcs["run_character_step"](
            prompt=image_prompt,
            aspect_ratio=aspect_ratio,
            character_id=char_id,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Character generation failed"))

        # run_character_step은 character_image_url을 반환함
        return {
            "image_url": result.get("image_url") or result.get("character_image_url"),
            "image_path": result.get("image_path") or result.get("character_image_path"),
            "model": "nanobanana",
            "voice_design_prompt": voice_description,
            "image_prompt": image_prompt,
        }

    async def suggest_character_prompts_from_product(
        self,
        item_name: str,
        item_category: Optional[str] = None,
        item_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """제품 정보 기반 캐릭터 프롬프트 추천"""
        funcs = _load_ai_functions()
        result = funcs["suggest_character_prompts_from_product"](
            item_name=item_name,
            item_category=item_category or "",
            item_description=item_description or ""
        )
        return {
            "character_image_prompt": result.get("character_prompt"),
            "character_voice_prompt": result.get("voice_description"),
        }

    async def generate_voice(
        self,
        text: str,
        voice_description: str,
        character_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        """
        음성 디자인 + 샘플 생성

        ElevenLabs Voice Design API를 사용하여 voice_id 발급
        """
        funcs = _load_ai_functions()

        result = funcs["run_voice_design_step"](
            voice_name=f"character_{character_id}",
            voice_description=voice_description,
            sample_text=text or None,
            character_id=character_id,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Voice generation failed"))

        return {
            "voice_url": result.get("voice_sample_url"),
            "voice_id": result.get("voice_id"),
        }

    async def generate_scenario(
        self,
        product_name: str,
        product_category: str,
        product_highlight: str,
        meme_id: Optional[int] = None,
        ad_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        시나리오 생성

        Direct 모드: AI pipeline이 ad_id로 DB에서 product 정보를 직접 로드.
        product_name/category/highlight는 HTTP 클라이언트 호환용 파라미터.
        """
        funcs = _load_ai_functions()

        if not ad_id:
            raise Exception("ad_id is required for scenario generation in direct mode")
        if not meme_id:
            raise Exception("meme_id is required for scenario generation")

        result = funcs["run_scenario_step"](
            ad_id=ad_id,
            meme_id=meme_id,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Scenario generation failed"))

        # scenes를 API 응답 형식으로 변환 — AI 키를 그대로 전달하되 content/visual_description도 추가 (하위호환)
        scenes = result.get("scenes", [])
        api_scenes = [
            {
                "scene_number": i + 1,
                "dialogue": scene.get("dialogue", ""),
                "content": scene.get("dialogue", ""),
                "scenario_prompt": scene.get("scenario_prompt", ""),
                "visual_description": scene.get("scenario_prompt", ""),
                "action": scene.get("action", ""),
                "duration": scene.get("duration", 5),
                "scene_key": scene.get("scene_key", f"scene_{i+1}"),
                "structure_type": scene.get("structure_type", ""),
            }
            for i, scene in enumerate(scenes)
        ]

        return {
            "scenes": api_scenes,
            "title": result.get("title"),
            "script_id": result.get("script_id"),
        }

    async def generate_scene_image(
        self,
        product_image_url: str,
        character_image_url: str,
        scenario_prompt: str,
        scene_key: str,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """
        씬 이미지 생성
        """
        funcs = _load_ai_functions()

        result = funcs["run_scene_image_step"](
            scenario_prompt=scenario_prompt,
            character_image_url=character_image_url,
            product_image_url=product_image_url,
            scene_key=scene_key,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Scene image generation failed"))

        return {
            "image_url": result.get("image_url"),
            "image_path": result.get("image_path"),
        }

    async def generate_video(
        self,
        ad_id: int,
        script_id: int,
        company_id: int,
        character_id: int = None,
        scenes: list = None,
        character_image_url: str = None,
        voice_id: str = None,
        title: str = None,
        product_image_url: str = None,
        clone_prompt_url: str = None,
        voice_description: str = None,
        character_description: str = None,
    ) -> Dict[str, Any]:
        """
        영상 생성

        1. 각 씬별 TTS 생성
        2. 씬 이미지 합성 (캐릭터 + 제품 이미지)
        3. run_video_step() 호출하여 영상 생성 + 병합
        """
        funcs = _load_ai_functions()

        if not scenes:
            return {"status": "failed", "error": "scenes is required"}
        if not voice_id:
            return {"status": "failed", "error": "voice_id is required"}

        # 1. TTS 생성 (각 씬별)
        scene_assets = []
        for i, scene in enumerate(scenes):
            dialogue = scene.get("content", "") or scene.get("dialogue", "")
            scene_key = f"scene_{i + 1}"
            asset = {"scene_key": scene_key}

            if dialogue:
                tts_result = funcs["run_tts_step"](
                    text=dialogue,
                    voice_id=voice_id,
                    character_id=character_id,
                    script_id=script_id,
                    scene_key=scene_key,
                    clone_prompt_url=clone_prompt_url,
                    voice_description=voice_description,
                )
                if tts_result.get("status") == "ok":
                    asset["audio_url"] = tts_result.get("audio_url")
                    asset["duration_seconds"] = tts_result.get("duration_seconds")
                else:
                    logger.warning(f"TTS failed for scene {i + 1}: {tts_result.get('error')}")

            scene_assets.append(asset)

        # 2. 씬 이미지 생성 (캐릭터 + 제품 이미지 합성)
        if character_image_url and product_image_url:
            for i, scene in enumerate(scenes):
                scene_key = f"scene_{i + 1}"
                scenario_prompt = scene.get("visual_description", "") or scene.get("scenario_prompt", "")
                if not scenario_prompt:
                    continue
                try:
                    img_result = funcs["run_scene_image_step"](
                        scenario_prompt=scenario_prompt,
                        character_image_url=character_image_url,
                        product_image_url=product_image_url,
                        script_id=script_id,
                        scene_key=scene_key,
                        character_id=character_id,
                    )
                    if img_result.get("status") == "ok" and img_result.get("image_url"):
                        scene_assets[i]["image_url"] = img_result["image_url"]
                        if img_result.get("image_path"):
                            scene_assets[i]["image_path"] = img_result["image_path"]
                except Exception as exc:
                    logger.warning(f"Scene image generation failed for scene {i+1}: {exc}")

        # 3. scenes 형식 변환 (API 형식 → pipeline 형식)
        pipeline_scenes = []
        for i, scene in enumerate(scenes):
            pipeline_scenes.append({
                "scene_key": f"scene_{i + 1}",
                "scene_number": i + 1,
                "dialogue": scene.get("content", "") or scene.get("dialogue", ""),
                "scenario_prompt": scene.get("visual_description", "") or scene.get("scenario_prompt", ""),
                "duration": scene.get("duration", 5),
            })

        # 4. 영상 생성
        # NOTE: company_id 의도적 생략 — Backend가 create_video_for_ad()로 video row를 관리.
        # AI pipeline의 insert_final_video() 중복 실행 방지.
        result = funcs["run_video_step"](
            scenes=pipeline_scenes,
            scene_assets=scene_assets,
            character_image_url=character_image_url,
            script_id=script_id,
            ad_id=ad_id,
            title=title,
            character_description=character_description,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Video generation failed"))

        return {
            "status": "ok",
            "video_url": result.get("video_url"),
            "video_path": result.get("video_path"),
            "scene_videos": result.get("scene_videos"),
            "db_video_id": result.get("db_video_id"),
            "estimated_duration": sum(
                sv.get("duration_seconds", 0) for sv in result.get("scene_videos", [])
            ) or 15,
        }

    async def regenerate_video(
        self,
        video_id: int,
        ad_id: int,
        revision_notes: str,
        feedback: Optional[str],
        company_id: int
    ) -> Dict[str, Any]:
        """영상 재생성 + Gemini 검수."""
        funcs = _load_ai_functions()

        from content_pipeline.db import load_video_by_id

        video = load_video_by_id(video_id)
        if not video:
            raise Exception(f"Video not found: video_id={video_id}")

        original_video_url = video["s3_url"]
        script_id = video.get("script_id")
        modification_request = revision_notes
        if feedback:
            modification_request = f"{revision_notes}\n피드백: {feedback}"

        result = funcs["run_video_regeneration_step"](
            modification_request=modification_request,
            original_video_url=original_video_url,
            script_id=script_id,
            company_id=company_id,
            ad_id=ad_id,
            account_id=video.get("account_id"),
            title=video.get("title") or "Regenerated Video",
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Video regeneration failed"))

        return {
            "video_id": video_id,
            "status": "ok",
            "video_url": result.get("merged_video_url"),
            "video_path": result.get("merged_output_path"),
            "db_video_id": result.get("db_video_id"),
            "verification_score": result.get("verification_score"),
            "verification_decision": result.get("verification_decision"),
            "verification_message": result.get("verification_message"),
            "retry_count": result.get("retry_count", 0),
        }

    async def regenerate_character_image(
        self,
        character_id: int,
        original_image_url: str,
        revision_notes: str,
        character_prompt: str,
        company_id: int,
        product_image_url: str = None,
        character_image_url: str = None,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """캐릭터 이미지 재생성 + AI 검수."""
        funcs = _load_ai_functions()

        result = funcs["run_image_regeneration_step"](
            modification_request=revision_notes,
            original_image_url=original_image_url,
            character_id=character_id,
            scenario_prompt=character_prompt,
            product_image_url=product_image_url,
            character_image_url=character_image_url,
            aspect_ratio=aspect_ratio,
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Character regeneration failed"))

        return {
            "image_url": result.get("image_url"),
            "image_path": result.get("image_path"),
            "model": "nanobanana",
            "verification_score": result.get("verification_score"),
            "verification_decision": result.get("verification_decision"),
            "retry_count": result.get("retry_count", 0),
        }

    async def revise_scenario(
        self,
        script_id: int,
        scene_revisions: list,
        company_id: int,
        ad_id: int = None
    ) -> Dict[str, Any]:
        """피드백 기반 시나리오 재생성.

        Direct 모드에서는 피드백을 DB scenario_scripts.review_result에서 읽음.
        사전조건: 호출자가 review_result에 human_feedback을 먼저 저장해야 함.
        """
        funcs = _load_ai_functions()

        if not ad_id:
            raise Exception("ad_id is required for scenario revision in direct mode")

        if scene_revisions:
            logger.info(
                f"revise_scenario: scene_revisions 파라미터 무시됨 "
                f"(Direct 모드에서는 DB review_result 사용, ad_id={ad_id})"
            )

        result = funcs["run_scenario_regenerate_step"](ad_id=ad_id)

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Scenario revision failed"))

        return {
            "script_id": result.get("script_id", script_id),
            "scenes": result.get("scenes", []),
            "title": result.get("title"),
            "status": "revised",
        }

    async def revise_video(
        self,
        video_id: int,
        scene_revisions: list,
        company_id: int
    ) -> Dict[str, Any]:
        """씬별 영상 수정 + Gemini 검수."""
        funcs = _load_ai_functions()

        from content_pipeline.db import load_video_by_id

        video = load_video_by_id(video_id)
        if not video:
            raise Exception(f"Video not found: video_id={video_id}")

        revision_text = "\n".join(
            f"씬 {r['scene_number']}: {r['video_notes']}"
            for r in scene_revisions
        )

        result = funcs["run_video_regeneration_step"](
            modification_request=revision_text,
            original_video_url=video["s3_url"],
            script_id=video.get("script_id"),
            company_id=company_id,
            ad_id=video.get("ad_id"),
            account_id=video.get("account_id"),
            title=video.get("title") or "Revised Video",
        )

        if result.get("status") == "failed":
            raise Exception(result.get("error", "Video revision failed"))

        return {
            "video_id": video_id,
            "status": "ok",
            "video_url": result.get("merged_video_url"),
            "video_path": result.get("merged_output_path"),
            "db_video_id": result.get("db_video_id"),
            "verification_score": result.get("verification_score"),
            "verification_decision": result.get("verification_decision"),
            "estimated_duration": result.get("duration_seconds") or 30,
        }
