"""
Content Pipeline - orchestration functions (asset + content generation).
"""
import logging

logger = logging.getLogger(__name__)
from concurrent.futures import ThreadPoolExecutor, as_completed

from content_pipeline.pipeline_helpers import _build_product_context
from content_pipeline.pipeline_steps import (
    run_scenario_step,
    run_character_step,
    run_voice_design_step,
    run_tts_step,
    run_scene_image_step,
    run_video_step,
)


# === 1단계: 캐릭터 + 음성 동시 생성 ===


def run_asset_generation_step(
    character_prompt: str,
    voice_description: str,
    voice_name: str,
    aspect_ratio: str = "9:16",
    character_id: int = None,
) -> dict:
    """
    캐릭터 이미지 + 음성 디자인 동시 생성 (1단계 검수용).

    1. 캐릭터 이미지 생성 (병렬)
    2. 음성 디자인 생성 (병렬)
    3. 결과 통합 반환

    Args:
        character_prompt: 이미지 생성 프롬프트
        voice_description: 보이스 디자인 프롬프트
        voice_name: 보이스 이름 (ElevenLabs에 등록될 이름)
        aspect_ratio: 이미지 비율 (기본 9:16 세로형)

    Returns:
        {
            "status": "ok",
            "character_image_url": "...",
            "character_image_path": "...",
            "voice_id": "...",
            "voice_sample_url": "...",
        }
    """
    if not character_prompt or not character_prompt.strip():
        return {"status": "failed", "error": "character_prompt is required"}
    if not voice_description or not voice_description.strip():
        return {"status": "failed", "error": "voice_description is required"}

    # 1. 캐릭터 이미지 + 음성 디자인 병렬 생성
    results = {}
    errors = []

    def generate_character():
        return run_character_step(character_prompt, aspect_ratio, character_id=character_id)

    def generate_voice():
        return run_voice_design_step(voice_name, voice_description, character_id=character_id)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(generate_character): "character",
            executor.submit(generate_voice): "voice",
        }

        for future in as_completed(futures):
            task_name = futures[future]
            try:
                result = future.result()
                results[task_name] = result
                if result.get("status") == "failed":
                    errors.append(f"{task_name}: {result.get('error')}")
            except Exception as e:
                errors.append(f"{task_name}: {e}")

    if errors:
        return {"status": "failed", "error": "; ".join(errors)}

    character_result = results.get("character", {})
    voice_result = results.get("voice", {})

    return {
        "status": "ok",
        "character_image_url": character_result.get("image_url"),
        "character_image_path": character_result.get("image_path"),
        "voice_id": voice_result.get("voice_id"),
        "voice_sample_url": voice_result.get("voice_sample_url"),
        "character_prompt": character_prompt,
        "voice_description": voice_description,
    }


# === 2단계: 시나리오 → TTS → 영상 통합 생성 ===


def run_content_generation_step(
    ad_id: int,
    meme_id: int,
    voice_id: str,
    character_image_url: str = None,
    character_image_path: str = None,
    product_image_url: str = None,
    company_id: int = None,
    character_id: int = None,
    voice_description: str = None,
    clone_prompt_url: str = None,
    character_description: str = None,
) -> dict:
    """
    검수 완료된 asset으로 콘텐츠 생성 (2단계).

    1. 시나리오 생성
    2. TTS 생성 (씬별)
    3. 영상 생성 (씬별) + 병합

    Args:
        ad_id: 광고 요청 ID
        meme_id: 밈 ID
        voice_id: 승인된 보이스 ID (필수)
        character_image_url: 승인된 캐릭터 이미지 URL
        character_image_path: 승인된 캐릭터 이미지 경로
        product_image_url: 제품 이미지 URL

    Returns:
        {
            "status": "ok",
            "scenes": [...],
            "scene_assets": [...],
            "video_url": "...",
            "video_path": "...",
            "title": "...",
            "meme_name": "...",
            "script_id": ...,
        }
    """
    if not voice_id:
        return {"status": "failed", "error": "voice_id is required"}

    # 1. 시나리오 생성
    scenario_result = run_scenario_step(ad_id, meme_id)
    if scenario_result.get("status") == "failed":
        return scenario_result

    scenes = scenario_result["scenes"]
    company_data = scenario_result.get("company_data", {})
    meme_data = scenario_result.get("meme_data", {})
    product_context = _build_product_context(company_data, meme_data)

    # 2. TTS 생성 (씬별 병렬)
    scene_assets = [{"scene_key": scene["scene_key"]} for scene in scenes]

    def _generate_tts(idx, scene):
        dialogue = scene.get("dialogue", "")
        if not dialogue:
            return idx, None
        tts_result = run_tts_step(
            text=dialogue,
            voice_id=voice_id,
            character_id=character_id,
            script_id=scenario_result.get("script_id"),
            scene_key=scene["scene_key"],
            voice_description=voice_description,
            clone_prompt_url=clone_prompt_url,
        )
        return idx, tts_result

    with ThreadPoolExecutor(max_workers=len(scenes)) as executor:
        futures = [executor.submit(_generate_tts, i, scene) for i, scene in enumerate(scenes)]
        for future in as_completed(futures):
            idx, tts_result = future.result()
            if tts_result and tts_result.get("status") == "ok":
                scene_assets[idx]["audio_url"] = tts_result.get("audio_url")
                scene_assets[idx]["duration_seconds"] = tts_result.get("duration_seconds")
                scene_assets[idx]["db_voice_gen_id"] = tts_result.get("db_voice_gen_id")

    # 3. 첫 씬 이미지 생성 (캐릭터 + 제품 합성, 이후 씬은 ComfyUI가 이전 프레임 사용)
    if character_image_url and scenes:
        scene = scenes[0]
        scenario_prompt = scene.get("scenario_prompt", "") or scene.get("visual_description", "")
        if scenario_prompt:
            img_result = run_scene_image_step(
                scenario_prompt=scenario_prompt,
                character_image_url=character_image_url,
                product_image_url=product_image_url,
                script_id=scenario_result.get("script_id"),
                scene_key=scene["scene_key"],
                character_id=character_id,
            )
            if img_result.get("status") != "ok" or not img_result.get("image_url"):
                error_msg = img_result.get("error", "unknown error")
                return {"status": "failed", "error": f"Scene 1 image generation failed: {error_msg}"}
            scene_assets[0]["image_url"] = img_result["image_url"]
            if img_result.get("image_path"):
                scene_assets[0]["image_path"] = img_result["image_path"]
            scene_assets[0]["db_image_id"] = img_result.get("db_image_id")

    # 4. 영상 생성 + 병합
    video_result = run_video_step(
        scenes=scenes,
        scene_assets=scene_assets,
        character_image_url=character_image_url,
        character_image_path=character_image_path,
        script_id=scenario_result.get("script_id"),
        company_id=company_id,
        ad_id=ad_id,
        title=scenario_result.get("title"),
        product_context=product_context,
        character_description=character_description,
    )

    if video_result.get("status") == "failed":
        return video_result

    return {
        "status": "ok",
        "scenes": scenes,
        "scene_assets": scene_assets,
        "video_url": video_result.get("video_url"),
        "video_path": video_result.get("video_path"),
        "scene_videos": video_result.get("scene_videos"),
        "title": scenario_result.get("title"),
        "meme_name": scenario_result.get("meme_name"),
        "total_duration": scenario_result.get("total_duration"),
        "script_id": scenario_result.get("script_id"),
    }
