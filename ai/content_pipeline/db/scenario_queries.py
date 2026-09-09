from typing import Any

from content_pipeline.db.connection import db_cursor, get_db_connection
from content_pipeline.db.s3_helpers import _maybe_presign_s3_url


def load_scenario_prompts(script_id: int, *, prompt_kind: str = "visual") -> list[str]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT scenes FROM scenario_scripts WHERE script_id = %s",
            (script_id,),
        )
        row = cur.fetchone()
        scenes = row[0] if row else None

    scenes_list = _normalize_scenes_payload(scenes)

    prompts: list[str] = []
    for scene in scenes_list:
        if not isinstance(scene, dict):
            prompts.append("")
            continue
        if prompt_kind == "action":
            prompt = scene.get("action") or scene.get("scene_motion_prompt") or ""
        else:
            prompt = scene.get("visual_description") or scene.get("scene_motion_prompt") or ""
        if not prompt:
            parts = []
            if prompt_kind == "action":
                parts.extend([scene.get("emotion") or "", scene.get("purpose") or ""])
            else:
                parts.extend([scene.get("action") or "", scene.get("emotion") or ""])
            prompt = " ".join([p for p in parts if p]).strip()
        if not prompt:
            beat_texts = []
            for beat in scene.get("beats", []) or []:
                if isinstance(beat, dict) and beat.get("text"):
                    beat_texts.append(beat["text"])
            prompt = " ".join(beat_texts).strip()
        prompts.append(str(prompt).strip())
    return prompts


def load_scene_prompt(script_id: int, scene_index: int) -> str:
    prompts = load_scenario_prompts(script_id)
    if 0 <= scene_index < len(prompts):
        return prompts[scene_index]
    return ""


def load_character_prompt(character_id: int) -> str:
    with db_cursor() as cur:
        cur.execute(
            "SELECT image_prompt FROM company_characters WHERE character_id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if not row:
        return ""
    return str(row[0]).strip() if row[0] else ""


def load_voice_description(character_id: int) -> str:
    with db_cursor() as cur:
        cur.execute(
            "SELECT voice_design_prompt FROM company_characters WHERE character_id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if not row:
        return ""
    return str(row[0]).strip() if row[0] else ""


def load_elevenlabs_voice_id(character_id: int) -> str:
    with db_cursor() as cur:
        cur.execute(
            "SELECT elevenlabs_voice_id FROM company_characters WHERE character_id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if not row:
        return ""
    return str(row[0]).strip() if row[0] else ""


def load_character_image_url(character_id: int) -> str:
    with db_cursor() as cur:
        cur.execute(
            "SELECT image_url FROM company_characters WHERE character_id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if not row:
        return ""
    return _maybe_presign_s3_url(str(row[0]).strip()) if row[0] else ""


def load_ad_request_item_images(ad_id: int) -> list[str]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT item_images FROM ad_requests WHERE ad_id = %s",
            (ad_id,),
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return []
    if isinstance(row[0], list):
        items = [_maybe_presign_s3_url(str(item)) for item in row[0] if item]
        items = [i for i in items if "placeholder.com" not in i] + [i for i in items if "placeholder.com" in i]
        return items
    return [_maybe_presign_s3_url(str(row[0]))]


def load_latest_script_id_by_ad_id(ad_id: int) -> int | None:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT script_id
            FROM scenario_scripts
            WHERE ad_id = %s
            ORDER BY created_at DESC, script_id DESC
            LIMIT 1
            """,
            (ad_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def load_clone_prompt_url(character_id: int) -> str:
    with db_cursor() as cur:
        cur.execute(
            "SELECT generation_metadata->>'clone_prompt_url' FROM company_characters WHERE character_id = %s",
            (character_id,),
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return ""
    return str(row[0]).strip()


def load_voice_text(script_id: int, scene_index: int) -> str:
    # 음성 합성용 텍스트를 씬 대사/비트/제품설명 순으로 조회
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT scenes, ad_id FROM scenario_scripts WHERE script_id = %s",
                (script_id,),
            )
            row = cur.fetchone()
            scenes = row[0] if row else None
            ad_id = row[1] if row else None

            if scenes is not None:
                scenes_list = _normalize_scenes_payload(scenes)
                if 0 <= scene_index < len(scenes_list):
                    scene = scenes_list[scene_index]
                    if isinstance(scene, dict):
                        dialogue = scene.get("dialogue")
                        if dialogue:
                            return str(dialogue).strip()
                        beat_texts = []
                        for beat in scene.get("beats", []) or []:
                            if isinstance(beat, dict) and beat.get("text"):
                                beat_texts.append(beat["text"])
                        text = " ".join(beat_texts).strip()
                        if text:
                            return text

            if ad_id:
                cur.execute(
                    "SELECT item_description FROM ad_requests WHERE ad_id = %s",
                    (ad_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    return str(row[0]).strip()
    finally:
        conn.close()
    return ""


def load_video_by_id(video_id: int) -> dict | None:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT video_id, s3_url, script_id, company_id, ad_id, account_id, title
            FROM videos
            WHERE video_id = %s
            """,
            (video_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "video_id": row[0],
            "s3_url": row[1],
            "script_id": row[2],
            "company_id": row[3],
            "ad_id": row[4],
            "account_id": row[5],
            "title": row[6],
        }


def _normalize_scenes_payload(scenes: Any) -> list[dict]:
    # scenes가 list 또는 scene1~ 형태 dict여도 동일한 리스트로 정규화
    if isinstance(scenes, list):
        return scenes
    if isinstance(scenes, dict):
        if isinstance(scenes.get("scenes"), list):
            return scenes.get("scenes") or []
        scene_items: list[tuple[int, dict]] = []
        for key, value in scenes.items():
            if not isinstance(key, str) or not key.startswith("scene"):
                continue
            suffix = key.replace("scene", "", 1)
            if not suffix.isdigit():
                continue
            if isinstance(value, dict):
                scene_items.append((int(suffix), value))
        scene_items.sort(key=lambda item: item[0])
        return [item[1] for item in scene_items]
    return []
