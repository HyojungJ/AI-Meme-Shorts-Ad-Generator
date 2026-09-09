import hashlib
from typing import Any

from psycopg2.extras import Json

from content_pipeline.db.connection import db_cursor


def update_generation_metadata(character_id: int, updates: dict) -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE company_characters
            SET generation_metadata = COALESCE(generation_metadata, '{}'::jsonb) || %s::jsonb,
                updated_at = now()
            WHERE character_id = %s
            """,
            (Json(updates), character_id),
        )


def update_elevenlabs_voice_id(character_id: int, voice_id: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE company_characters
            SET elevenlabs_voice_id = %s,
                updated_at = now()
            WHERE character_id = %s
            """,
            (voice_id, character_id),
        )


def update_company_character_image_url(character_id: int, image_url: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE company_characters
            SET image_url = %s,
                updated_at = now()
            WHERE character_id = %s
            """,
            (image_url, character_id),
        )


def upsert_voice_generation(
    *,
    character_id: int,
    script_id: int | None,
    scene_key: str,
    text_content: str,
    text_hash: str | None,
    audio_url: str | None,
    duration_seconds: float | None,
    size_bytes: int | None,
    settings: dict[str, Any] | None,
) -> int:
    if text_hash:
        text_hash = hashlib.sha256(f"{scene_key}|{text_hash}".encode("utf-8")).hexdigest()[:12]
    else:
        text_hash = hashlib.sha256(f"{scene_key}|{text_content}".encode("utf-8")).hexdigest()[:12]

    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO voice_generations (
                character_id, script_id, scene_key, text_content, text_hash,
                audio_url, duration_seconds, size_bytes, settings_json
            )
            VALUES (
                %(character_id)s, %(script_id)s, %(scene_key)s, %(text_content)s, %(text_hash)s,
                %(audio_url)s, %(duration_seconds)s, %(size_bytes)s, %(settings_json)s
            )
            ON CONFLICT (character_id, text_hash)
            DO UPDATE SET
                script_id = EXCLUDED.script_id,
                scene_key = EXCLUDED.scene_key,
                text_content = EXCLUDED.text_content,
                audio_url = EXCLUDED.audio_url,
                duration_seconds = EXCLUDED.duration_seconds,
                size_bytes = EXCLUDED.size_bytes,
                settings_json = EXCLUDED.settings_json,
                created_at = now()
            RETURNING voice_gen_id
            """,
            {
                "character_id": character_id,
                "script_id": script_id,
                "scene_key": scene_key,
                "text_content": text_content,
                "text_hash": text_hash,
                "audio_url": audio_url,
                "duration_seconds": duration_seconds,
                "size_bytes": size_bytes,
                "settings_json": Json(settings or {}),
            },
        )
        return cur.fetchone()[0]


def upsert_image_generation(
    *,
    character_id: int,
    script_id: int,
    prompt: str | None,
    model: str | None,
    image_url: str | None,
    size_bytes: int | None,
    metadata: dict[str, Any] | None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO image_generations (
                character_id, script_id, prompt, model, image_url, size_bytes, metadata_json
            )
            VALUES (
                %(character_id)s, %(script_id)s, %(prompt)s, %(model)s,
                %(image_url)s, %(size_bytes)s, %(metadata_json)s
            )
            ON CONFLICT (script_id)
            DO UPDATE SET
                character_id = EXCLUDED.character_id,
                prompt = EXCLUDED.prompt,
                model = EXCLUDED.model,
                image_url = EXCLUDED.image_url,
                size_bytes = EXCLUDED.size_bytes,
                metadata_json = EXCLUDED.metadata_json,
                created_at = now()
            RETURNING image_id
            """,
            {
                "character_id": character_id,
                "script_id": script_id,
                "prompt": prompt,
                "model": model,
                "image_url": image_url,
                "size_bytes": size_bytes,
                "metadata_json": Json(metadata or {}),
            },
        )
        return cur.fetchone()[0]


def upsert_scene_video(
    *,
    script_id: int,
    scene_key: str,
    voice_gen_id: int | None,
    image_id: int | None,
    video_url: str | None,
    duration_seconds: float | None,
    size_bytes: int | None,
    generation_model: str | None,
    generation_metadata: dict[str, Any] | None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO scene_videos (
                script_id, scene_key, voice_gen_id, image_id, video_url,
                duration_seconds, size_bytes, generation_model, generation_metadata
            )
            VALUES (
                %(script_id)s, %(scene_key)s, %(voice_gen_id)s, %(image_id)s, %(video_url)s,
                %(duration_seconds)s, %(size_bytes)s, %(generation_model)s, %(generation_metadata)s
            )
            ON CONFLICT (script_id, scene_key)
            DO UPDATE SET
                voice_gen_id = EXCLUDED.voice_gen_id,
                image_id = EXCLUDED.image_id,
                video_url = EXCLUDED.video_url,
                duration_seconds = EXCLUDED.duration_seconds,
                size_bytes = EXCLUDED.size_bytes,
                generation_model = EXCLUDED.generation_model,
                generation_metadata = EXCLUDED.generation_metadata,
                created_at = now()
            RETURNING scene_video_id
            """,
            {
                "script_id": script_id,
                "scene_key": scene_key,
                "voice_gen_id": voice_gen_id,
                "image_id": image_id,
                "video_url": video_url,
                "duration_seconds": duration_seconds,
                "size_bytes": size_bytes,
                "generation_model": generation_model,
                "generation_metadata": Json(generation_metadata or {}),
            },
        )
        return cur.fetchone()[0]


def upsert_scene_assets(
    *,
    script_id: int,
    scene_key: str,
    audio_url: str | None,
    audio_duration_seconds: float | None,
    audio_storage_path: str | None,
    character_image_url: str | None,
    character_image_storage_path: str | None,
    scene_video_url: str | None,
    scene_video_storage_path: str | None,
    scene_video_duration: float | None,
    generation_model: str | None,
    generation_cost: float | None,
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO scene_assets (
                script_id, scene_key, audio_url, audio_duration_seconds, audio_storage_path,
                character_image_url, character_image_storage_path,
                scene_video_url, scene_video_storage_path, scene_video_duration,
                generation_model, generation_cost
            )
            VALUES (
                %(script_id)s, %(scene_key)s, %(audio_url)s, %(audio_duration_seconds)s, %(audio_storage_path)s,
                %(character_image_url)s, %(character_image_storage_path)s,
                %(scene_video_url)s, %(scene_video_storage_path)s, %(scene_video_duration)s,
                %(generation_model)s, %(generation_cost)s
            )
            ON CONFLICT (script_id, scene_key)
            DO UPDATE SET
                audio_url = EXCLUDED.audio_url,
                audio_duration_seconds = EXCLUDED.audio_duration_seconds,
                audio_storage_path = EXCLUDED.audio_storage_path,
                character_image_url = EXCLUDED.character_image_url,
                character_image_storage_path = EXCLUDED.character_image_storage_path,
                scene_video_url = EXCLUDED.scene_video_url,
                scene_video_storage_path = EXCLUDED.scene_video_storage_path,
                scene_video_duration = EXCLUDED.scene_video_duration,
                generation_model = EXCLUDED.generation_model,
                generation_cost = EXCLUDED.generation_cost,
                created_at = now()
            RETURNING asset_id
            """,
            {
                "script_id": script_id,
                "scene_key": scene_key,
                "audio_url": audio_url,
                "audio_duration_seconds": audio_duration_seconds,
                "audio_storage_path": audio_storage_path,
                "character_image_url": character_image_url,
                "character_image_storage_path": character_image_storage_path,
                "scene_video_url": scene_video_url,
                "scene_video_storage_path": scene_video_storage_path,
                "scene_video_duration": scene_video_duration,
                "generation_model": generation_model,
                "generation_cost": generation_cost,
            },
        )
        return cur.fetchone()[0]


def save_verification_result(
    *,
    media_type: str,
    score: int,
    confidence: float,
    decision: str,
    analysis: str,
    missing_elements: list[str],
    retry_count: int,
    modification_request: str,
    character_id: int | None = None,
    script_id: int | None = None,
) -> None:
    """검수 결과를 기존 review_result JSONB 컬럼에 저장."""
    payload = Json({
        "score": score,
        "confidence": confidence,
        "decision": decision,
        "analysis": analysis,
        "missing_elements": missing_elements or [],
        "retry_count": retry_count,
        "modification_request": modification_request,
    })

    with db_cursor() as cur:
        if media_type == "image" and character_id:
            cur.execute(
                """
                UPDATE company_characters
                SET review_result = jsonb_set(
                    COALESCE(review_result, '{}'::jsonb),
                    '{ai_verification_image}',
                    %s
                ),
                updated_at = now()
                WHERE character_id = %s
                """,
                (payload, character_id),
            )
        elif media_type == "video" and script_id:
            cur.execute(
                """
                UPDATE scenario_scripts
                SET review_result = jsonb_set(
                    COALESCE(review_result, '{}'::jsonb),
                    '{ai_verification_video}',
                    %s
                ),
                updated_at = now()
                WHERE script_id = %s
                """,
                (payload, script_id),
            )


def insert_final_video(
    *,
    company_id: int,
    title: str,
    s3_url: str,
    script_id: int | None = None,
    ad_id: int | None = None,
    account_id: int | None = None,
    description: str | None = None,
    file_size_bytes: int | None = None,
    duration_seconds: int | None = None,
    resolution: str | None = None,
    fmt: str | None = None,
    status: str = "completed",
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO videos (
                ad_id, company_id, account_id, title, description, s3_url,
                file_size_bytes, duration_seconds, resolution, format, status, script_id
            )
            VALUES (
                %(ad_id)s, %(company_id)s, %(account_id)s, %(title)s, %(description)s, %(s3_url)s,
                %(file_size_bytes)s, %(duration_seconds)s, %(resolution)s, %(format)s, %(status)s, %(script_id)s
            )
            RETURNING video_id
            """,
            {
                "ad_id": ad_id,
                "company_id": company_id,
                "account_id": account_id,
                "title": title,
                "description": description,
                "s3_url": s3_url,
                "file_size_bytes": file_size_bytes,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
                "format": fmt,
                "status": status,
                "script_id": script_id,
            },
        )
        return cur.fetchone()[0]
