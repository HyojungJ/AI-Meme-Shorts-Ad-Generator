from __future__ import annotations

from typing import Any

from content_pipeline.db import load_elevenlabs_voice_id, load_voice_description, load_voice_text
from content_pipeline.voice import get_initial_state
from content_pipeline.voice.nodes import design_voice_node, generate_voice_node
from content_pipeline.voice.state import DEFAULT_DESIGN_TEXT


def run_voice_generation(
    *,
    text: str | None,
    voice_id: str | None,
    voice_description: str | None,
    voice_name: str | None,
    design_text: str | None,
    preview_index: int,
    ttv_model_id: str | None,
    user_id: str,
    settings: dict[str, Any],
    script_id: int | None,
    character_id: int | None,
    scene_number: int | None,
    scene_key: str | None,
    use_db_text: bool,
    prefer_existing_voice: bool = True,
) -> dict:
    if use_db_text and not text and script_id:
        scene_index = (scene_number - 1) if scene_number else 0
        text = load_voice_text(script_id, scene_index)
    if not text:
        raise ValueError("--text is required (or use DB text with valid script_id).")

    if not voice_description and character_id:
        voice_description = load_voice_description(character_id)

    resolved_voice_id = (voice_id or "").strip() or None
    if not resolved_voice_id and character_id:
        existing = load_elevenlabs_voice_id(character_id)
        if existing and prefer_existing_voice:
            resolved_voice_id = existing

    if not resolved_voice_id:
        if not voice_description or not voice_name:
            raise ValueError("voice_description/voice_name are required to create a new voice.")
        design_state = get_initial_state(
            text=text,
            voice_id=None,
            voice_name=voice_name,
            voice_description=voice_description,
            preview_index=preview_index,
            user_id=user_id,
            settings=settings,
            script_id=script_id,
            scene_number=scene_number,
            scene_key=scene_key,
            character_id=character_id,
        )
        design_state["design_text"] = design_text or DEFAULT_DESIGN_TEXT
        if ttv_model_id:
            design_state["ttv_model_id"] = ttv_model_id
        design_result = design_voice_node(design_state)
        if design_result.get("status") == "failed":
            return design_result
        resolved_voice_id = design_result.get("voice_id")

    tts_state = get_initial_state(
        text=text,
        voice_id=resolved_voice_id,
        voice_name=None,
        voice_description=None,
        preview_index=preview_index,
        user_id=user_id,
        settings=settings,
        script_id=script_id,
        scene_number=scene_number,
        scene_key=scene_key,
        character_id=character_id,
    )
    return generate_voice_node(tts_state)
