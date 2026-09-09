"""
Content Pipeline - individual step functions.
"""
import json
import logging
import os
import time

logger = logging.getLogger(__name__)
from pathlib import Path

from content_pipeline.pipeline_helpers import (
    VOICE_DESIGN_SAMPLE_TEXT,
    _build_product_context,
    _save_voice_sample,
    convert_to_scenes,
    design_voice_node,
    generate_voice_node,
    get_voice_service,
    generate_character_image_node,
    generate_scene_image_node,
    load_video_config,
    generate_video_node,
    merge_video_node,
    Scene,
    ScenarioOutput,
    GENERATE_SCENARIO_TEMPLATE_V4,
    REVIEW_SCENARIO_TEMPLATE_V3,
    REGENERATE_SCENARIO_TEMPLATE_V3,
    MEME_EXAMPLE_TEMPLATE_V1,
)
from content_pipeline.video.nodes import verify_video_node


def run_scenario_step(ad_id: int, meme_id: int = None) -> dict:
    """시나리오만 생성 (검수용). meme_id는 DB에서 ad_id로 조회."""
    from scenario_agent import run_scenario_agent

    result = run_scenario_agent(
        ad_id=ad_id,
        generate_template=GENERATE_SCENARIO_TEMPLATE_V4,
        review_template=REVIEW_SCENARIO_TEMPLATE_V3,
        regenerate_template=REGENERATE_SCENARIO_TEMPLATE_V3,
        meme_example_template=MEME_EXAMPLE_TEMPLATE_V1,
        used_templates=["GENERATE_V4", "REVIEW_V3", "REGENERATE_V3", "MEME_EXAMPLE_V1"],
    )

    if result["status"] == "failed":
        return {"status": "failed", "error": result.get("error")}

    scenario = result["scenario"]
    company = result.get("company_data", {})
    meme = result.get("meme_data", {})

    return {
        "status": "ok",
        "scenes": convert_to_scenes(scenario),
        "title": scenario.title,
        "total_duration": getattr(scenario, "total_duration", None),
        "meme_name": meme.get("meme_name", "Unknown"),
        "script_id": result.get("script_id"),
        "company_data": company,
        "meme_data": meme,
    }


def run_character_step(
    prompt: str,
    aspect_ratio: str = "9:16",
    # DB 저장용 (optional)
    character_id: int = None,
) -> dict:
    """캐릭터 이미지만 생성 (검수용). script_id 없음 — 캐릭터는 시나리오 전에 생성."""
    result = generate_character_image_node({
        "character_prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "character_id": character_id,
    })

    if result.get("status") != "ok":
        return {"status": "failed", "error": result.get("error")}

    return {
        "status": "ok",
        "image_url": result.get("character_image_url"),
        "image_path": result.get("character_image_path"),
        "db_image_id": result.get("db_image_id"),
    }


def run_voice_design_step(
    voice_name: str,
    voice_description: str,
    sample_text: str = None,
    # DB 저장용 (optional)
    character_id: int = None,
) -> dict:
    """
    Voice Design 수행 후 샘플 음성 저장 (검수용).
    provider 라우팅은 design_voice_node()에서 처리 (VOICE_PROVIDER 환경변수).

    Returns:
        {
            "status": "ok",
            "voice_id": "...",
            "voice_sample_url": "..."  # 검수용 샘플 음성 URL
        }
    """
    text = sample_text or VOICE_DESIGN_SAMPLE_TEXT

    if not voice_name or not voice_name.strip():
        return {"status": "failed", "error": "voice_name is required"}
    if not voice_description or not voice_description.strip():
        return {"status": "failed", "error": "voice_description is required"}

    # 기본값은 "qwen"
    provider = (os.getenv("VOICE_PROVIDER", "qwen") or "qwen").strip().lower()
    if provider != "elevenlabs":
        # 자체 음성 디자인 노드 사용
        result = design_voice_node({
            "text": text,
            "voice_name": voice_name,
            "voice_description": voice_description,
            "character_id": character_id,
        })

        if result.get("status") == "failed":
            return {"status": "failed", "error": result.get("error")}

        return {
            "status": "ok",
            "voice_id": result.get("voice_id"),
            "voice_sample_url": result.get("voice_sample_url"),
        }

    max_retries = 2
    last_frame_path: Path | None = None
    for attempt in range(max_retries + 1):
        try:
            service = get_voice_service()

            design_response = service.design_voice(
                voice_description=voice_description,
                text=text,
            )

            if not design_response.previews:
                return {"status": "failed", "error": "No voice previews generated"}

            preview = design_response.previews[0]
            voice_sample_url = _save_voice_sample(
                audio_base64=preview.audio_base_64,
                voice_name=voice_name,
            )

            create_response = service.create_voice(
                voice_name=voice_name,
                voice_description=voice_description,
                generated_voice_id=preview.generated_voice_id,
            )

            if character_id and create_response.voice_id:
                from content_pipeline.db import update_elevenlabs_voice_id
                update_elevenlabs_voice_id(character_id, create_response.voice_id)

            return {
                "status": "ok",
                "voice_id": create_response.voice_id,
                "voice_sample_url": voice_sample_url,
            }
        except Exception as e:
            if attempt < max_retries and "timed out" in str(e).lower():
                time.sleep(2 ** attempt)
                continue
            return {"status": "failed", "error": str(e)}


def run_tts_step(
    text: str,
    voice_id: str,
    # DB 저장용 (optional)
    character_id: int = None,
    script_id: int = None,
    scene_key: str = None,
    voice_description: str = None,
    clone_prompt_url: str = None,
) -> dict:
    """TTS 생성 (voice_id 필수)."""
    if not voice_id:
        return {"status": "failed", "error": "voice_id is required"}

    state = {
        "text": text,
        "voice_id": voice_id,
        "character_id": character_id,
        "script_id": script_id,
        "scene_key": scene_key,
    }
    if voice_description:
        state["voice_description"] = voice_description
    if clone_prompt_url:
        state["clone_prompt_url"] = clone_prompt_url

    result = generate_voice_node(state)

    if result.get("status") == "failed":
        return {"status": "failed", "error": result.get("error")}

    return {
        "status": "ok",
        "audio_url": result.get("audio_url"),
        "duration_seconds": result.get("duration_seconds"),
        "db_voice_gen_id": result.get("db_voice_gen_id"),
    }


def run_scene_image_step(
    scenario_prompt: str,
    character_image_url: str = None,
    character_image_path: str = None,
    product_image_url: str = None,
    product_image_path: str = None,
    # DB 저장용 (optional)
    script_id: int = None,
    scene_key: str = None,
    character_id: int = None,
) -> dict:
    """씬 이미지만 생성 (검수용). URL 또는 path 중 하나 필요."""
    result = generate_scene_image_node({
        "scenario_prompt": scenario_prompt,
        "character_image_url": character_image_url,
        "character_image_path": character_image_path,
        "product_image_url": product_image_url,
        "product_image_path": product_image_path,
        "aspect_ratio": "9:16",
        "script_id": script_id,
        "scene_key": scene_key,
        "character_id": character_id,
    })

    if result.get("status") != "ok":
        return {"status": "failed", "error": result.get("error")}

    return {
        "status": "ok",
        "image_url": result.get("image_url"),
        "image_path": result.get("output_path"),
        "db_image_id": result.get("db_image_id"),
    }


def run_video_step(
    scenes: list[dict],
    scene_assets: list[dict],
    character_image_url: str = None,
    character_image_path: str = None,
    # DB 저장용 (optional)
    script_id: int = None,
    company_id: int = None,
    ad_id: int = None,
    title: str = None,
    product_context: str = None,
    character_description: str = None,
) -> dict:
    """영상 생성 (검수용). generate_video_node + merge_video_node에 위임."""
    config = load_video_config()

    # scenes + scene_assets → scene_inputs 변환
    scene_inputs = []
    for i, (scene, asset) in enumerate(zip(scenes, scene_assets)):
        prompt = scene.get("scenario_prompt", "")
        audio_url = asset.get("audio_url")
        audio_path = asset.get("audio_path")
        if not prompt or (not audio_url and not audio_path):
            continue
        visual_desc = prompt
        if character_description:
            # visual_description 앞에 캐릭터 정보 주입 — GPT가 무시하지 못하도록
            visual_desc = f"[Main character: {character_description}] {prompt}"
        scene_data = {
            "action": scene.get("action", ""),
            "dialogue": scene.get("dialogue", ""),
            "scene_type": scene.get("structure_type", ""),
            "visual_description": visual_desc,
        }
        if character_description:
            scene_data["character_appearance"] = character_description
        if product_context:
            scene_data["context"] = product_context
        scene_inputs.append({
            "prompt": json.dumps(scene_data, ensure_ascii=False),
            "audio_url": audio_url,
            "audio_path": audio_path,
            "duration_seconds": asset.get("duration_seconds"),
            "reference_image_url": asset.get("image_url") or character_image_url,
            "reference_image_path": asset.get("image_path") or character_image_path,
            "output_path": str(config.output_dir / f"scene_{i + 1:02d}.mp4"),
            "scene_key": scene.get("scene_key", f"scene_{i+1}"),
            "voice_gen_id": asset.get("db_voice_gen_id"),
            "image_id": asset.get("db_image_id"),
        })

    if not scene_inputs:
        return {"status": "failed", "error": "No valid scenes to generate"}

    scenario = ScenarioOutput(
        script_id=script_id,
        meme_id=0,
        title=title or "Generated Video",
        description="",
        total_duration=sum(float(s.get("duration_seconds") or 5.0) for s in scene_inputs),
        scenes=[Scene(scene_number=i + 1, scene_type="setup") for i in range(len(scene_inputs))],
    )

    state = {
        "scenario": scenario,
        "scene_inputs": scene_inputs,
        "company_id": company_id,
        "ad_id": ad_id,
        "title": title,
        "max_retries": 2,
    }

    gen_result = generate_video_node(state)
    if gen_result.get("status") == "failed":
        return gen_result

    state.update(gen_result)
    state["merged_output_path"] = str(config.output_dir / f"merged_{int(time.time())}.mp4")
    merge_result = merge_video_node(state)
    if merge_result.get("status") == "failed":
        return merge_result

    # 영상 검증 (Gemini 2.5 Pro)
    state.update(merge_result)
    try:
        verify_result = verify_video_node(state)
        verification_score = verify_result.get("score")
        verification_decision = verify_result.get("decision", "present_to_user")
        verification_message = verify_result.get("message", "")
        logger.info(
            "영상 검증 완료: ad_id=%s, score=%s, decision=%s",
            ad_id, verification_score, verification_decision,
        )
    except Exception as exc:
        logger.warning("영상 검증 실패 (무시하고 진행): %s", exc)
        verification_score = None
        verification_decision = "skipped"
        verification_message = str(exc)

    return {
        "status": "ok",
        "video_url": merge_result.get("merged_video_url"),
        "video_path": str(merge_result.get("merged_output_path", "")),
        "scene_videos": gen_result.get("scene_outputs", []),
        "db_video_id": merge_result.get("db_video_id"),
        "verification_score": verification_score,
        "verification_decision": verification_decision,
        "verification_message": verification_message,
    }
