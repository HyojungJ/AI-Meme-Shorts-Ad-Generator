from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from content_pipeline.db import (
    _maybe_presign_s3_url,
    _normalize_scenes_payload,
    get_db_connection,
    load_scenario_prompts,
)


def build_scene_inputs_from_db(
    *,
    script_id: int,
    output_dir: str | Path,
    scene_key_map: dict[str, str] | None = None,
    product_context: str | None = None,
) -> list[dict]:
    # DB의 scenario_scripts.scenes에서 scene_inputs를 구성한다.
    # - scene_inputs: 씬별 prompt/audio/reference/output_path 묶음
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT scenes FROM scenario_scripts WHERE script_id = %s",
                (script_id,),
            )
            row = cur.fetchone()
            scenes_payload = row[0] if row else None
    finally:
        conn.close()

    scenes = _normalize_scenes_payload(scenes_payload)
    if not scenes:
        raise ValueError(f"No scenes found for script_id={script_id}")

    scene_key_map = scene_key_map or {}
    assets = _load_scene_generation_assets(script_id)

    output_dir = Path(output_dir)
    inputs: list[dict] = []
    for idx, scene in enumerate(scenes, start=1):
        # scene_type을 scene_key로 매핑하고, 없으면 scene_XX로 생성
        scene_type = scene.get("scene_type") if isinstance(scene, dict) else None
        scene_key = scene_key_map.get(scene_type) if scene_type else None
        if not scene_key:
            scene_key = f"scene_{idx:02d}"
        # DB의 scenario_scripts.scenes 전체 정보를 프롬프트로 전달
        scene_payload = scene if isinstance(scene, dict) else {}
        if scene_payload:
            if product_context:
                scene_payload = {**scene_payload, "context": product_context}
            prompt = json.dumps(scene_payload, ensure_ascii=False)
        else:
            action_prompts = load_scenario_prompts(script_id, prompt_kind="action")
            visual_prompts = load_scenario_prompts(script_id, prompt_kind="visual")
            action_prompt = action_prompts[idx - 1] if idx - 1 < len(action_prompts) else ""
            visual_prompt = visual_prompts[idx - 1] if idx - 1 < len(visual_prompts) else ""
            if action_prompt and visual_prompt:
                prompt = f"Action: {action_prompt}\nVisual: {visual_prompt}"
            else:
                prompt = action_prompt or visual_prompt
        # duration은 음성 길이를 우선 사용하고, 없으면 4초로 기본값 적용
        duration = None
        payload = {
            "scene_key": scene_key,
            "prompt": prompt,
            "duration_seconds": duration,
            "output_path": str(output_dir / f"scene_{idx:02d}.mp4"),
        }
        asset = assets.get(scene_key)
        if asset:
            # voice_generations/image_generations에서 가져온 audio/image 반영
            if asset.get("reference_image_url"):
                payload["reference_image_url"] = asset["reference_image_url"]
            if asset.get("audio_url"):
                payload["audio_url"] = asset["audio_url"]
            if asset.get("audio_duration_seconds") is not None:
                duration = asset.get("audio_duration_seconds")
                payload["duration_seconds"] = duration
        if payload.get("duration_seconds") is None:
            logger.warning(
                "No TTS duration for scene_key=%s (script_id=%s), using 4.0s fallback",
                scene_key, script_id,
            )
            payload["duration_seconds"] = 4.0
        inputs.append(payload)
    return inputs


def _load_scene_generation_assets(script_id: int) -> dict[str, dict]:
    # voice_generations/image_generations에서 씬별 audio/image 결과를 모은다.
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT ON (scene_key)
                    scene_key,
                    audio_url,
                    duration_seconds
                FROM voice_generations
                WHERE script_id = %s AND audio_url IS NOT NULL
                ORDER BY scene_key, created_at DESC
                """,
                (script_id,),
            )
            voice_rows = cur.fetchall()
            cur.execute(
                """
                SELECT DISTINCT ON ((metadata_json->>'scene_key'))
                    (metadata_json->>'scene_key') AS scene_key,
                    image_url
                FROM image_generations
                WHERE script_id = %s
                  AND metadata_json ? 'scene_key'
                ORDER BY (metadata_json->>'scene_key'), created_at DESC
                """,
                (script_id,),
            )
            image_rows = cur.fetchall()
    finally:
        conn.close()

    assets: dict[str, dict] = {}
    for scene_key, audio_url, duration_seconds in voice_rows:
        assets[str(scene_key)] = {
            "audio_url": _maybe_presign_s3_url(audio_url),
            "audio_duration_seconds": duration_seconds,
        }
    for scene_key, image_url in image_rows:
        entry = assets.setdefault(str(scene_key), {})
        entry["reference_image_url"] = _maybe_presign_s3_url(image_url)
    return assets
