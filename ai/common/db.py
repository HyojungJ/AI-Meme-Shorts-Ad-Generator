import json
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from common.config import config


@contextmanager
def get_connection():
    conn = psycopg2.connect(
        host=config.db.host,
        port=config.db.port,
        dbname=config.db.name,
        user=config.db.user,
        password=config.db.password,
    )
    try:
        yield conn
    finally:
        conn.close()


class MemeRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, meme_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM memes WHERE meme_id = %s", (meme_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_name(self, name: str) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM memes WHERE meme_name = %s", (name,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_all_names(self) -> set[str]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT meme_name FROM memes")
            return {row[0] for row in cur.fetchall()}

    def get_unprocessed(self, limit: int = 10) -> list[dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM memes
                WHERE status = 'READY'
                ORDER BY created_at
                LIMIT %s
            """, (limit,))
            return [dict(row) for row in cur.fetchall()]

    def insert_name_only(self, name: str) -> int | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memes (meme_name, status)
                VALUES (%s, 'READY')
                ON CONFLICT (meme_name) DO NOTHING
                RETURNING meme_id
            """, (name,))
            self.conn.commit()
            result = cur.fetchone()
            return result[0] if result else None

    def upsert(self, meme: dict, commit: bool = True) -> int:
        """Insert or update meme, returns meme_id."""
        # Build source_video from reference_videos (최대 5개 전체 저장)
        ref_videos = meme.get("reference_videos", [])
        source_video = ref_videos[:5]

        # Build video_analysis (motion_prompt, style_keywords, prosody, emotion)
        video_analysis = {
            "motion_prompt": meme.get("motion_prompt"),
            "style_keywords": meme.get("style_keywords", []),
            "prosody": meme.get("prosody"),
            "emotion": meme.get("emotion"),
        }

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memes (
                    meme_name, definition, meme_type, key_phrase,
                    sources, origin, risk_info,
                    source_video, video_analysis,
                    confidence, status
                )
                VALUES (
                    %(name)s, %(definition)s, %(meme_type)s, %(key_phrase)s,
                    %(sources)s, %(origin)s, %(risk_info)s,
                    %(source_video)s, %(video_analysis)s,
                    %(confidence)s, 'PROCESSED'
                )
                ON CONFLICT (meme_name) DO UPDATE SET
                    definition = EXCLUDED.definition,
                    meme_type = EXCLUDED.meme_type,
                    key_phrase = EXCLUDED.key_phrase,
                    sources = EXCLUDED.sources,
                    origin = EXCLUDED.origin,
                    risk_info = EXCLUDED.risk_info,
                    source_video = EXCLUDED.source_video,
                    video_analysis = EXCLUDED.video_analysis,
                    confidence = EXCLUDED.confidence,
                    status = 'PROCESSED',
                    updated_at = CURRENT_TIMESTAMP
                RETURNING meme_id
            """, {
                "name": meme["name"],
                "definition": meme.get("definition"),
                "meme_type": meme.get("meme_type"),
                "key_phrase": meme.get("key_phrase"),
                "sources": json.dumps(meme.get("sources", [])),
                "origin": json.dumps(meme.get("origin") or {}),
                "risk_info": meme.get("risk_level", "low"),
                "source_video": json.dumps(source_video),
                "video_analysis": json.dumps(video_analysis),
                "confidence": meme.get("confidence"),
            })
            meme_id = cur.fetchone()[0]
            if commit:
                self.conn.commit()
            return meme_id


class MemeExampleRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_all(self, meme_id: int, examples: list, commit: bool = True):
        """Delete existing and insert new usage examples."""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM meme_examples WHERE meme_id = %s", (meme_id,))
            for ex in examples:
                cur.execute("""
                    INSERT INTO meme_examples (meme_id, situation, dialogue_example, example_type, tone, note, source_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    meme_id,
                    ex.get("context", ""),
                    ex.get("usage", ""),
                    ex.get("example_type", "good"),
                    ex.get("tone"),
                    ex.get("note"),
                    ex.get("source_url"),
                ))
            if commit:
                self.conn.commit()

    def get_by_meme(self, meme_id: int) -> list[dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM meme_examples
                WHERE meme_id = %s
                ORDER BY example_type, created_at
            """, (meme_id,))
            return [dict(row) for row in cur.fetchall()]


def save_meme_output(meme_output: dict) -> int:
    """Save complete MemeOutput to DB. Returns meme_id."""
    with get_connection() as conn:
        meme_repo = MemeRepository(conn)
        example_repo = MemeExampleRepository(conn)

        try:
            # 1. Save meme (deferred commit)
            meme_id = meme_repo.upsert(meme_output, commit=False)

            # 2. Save usage examples (deferred commit)
            usage_examples = meme_output.get("usage_examples", [])
            if usage_examples:
                example_repo.save_all(meme_id, usage_examples, commit=False)

            # 3. Commit all changes atomically
            conn.commit()
            return meme_id
        except Exception:
            conn.rollback()
            raise


class ScriptRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, script_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scripts WHERE script_id = %s",
                (script_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            result = dict(row)
            return result

    def save(self, script: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scripts (meme_id, title, description, total_duration, scenes, hashtags)
                VALUES (%(meme_id)s, %(title)s, %(description)s, %(total_duration)s, %(scenes)s, %(hashtags)s)
                RETURNING script_id
            """, {
                "meme_id": script["meme_id"],
                "title": script["title"],
                "description": script.get("description"),
                "total_duration": script["total_duration"],
                "scenes": json.dumps(script["scenes"]),
                "hashtags": json.dumps(script.get("hashtags", [])),
            })
            self.conn.commit()
            return cur.fetchone()[0]


class PromptVersionRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_active(self, prompt_name: str) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT version_id, prompt_name, version, prompt_content, is_active, metrics, created_at
                FROM prompt_versions
                WHERE prompt_name = %s AND is_active = true
            """, (prompt_name,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_version(self, prompt_name: str, version: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT version_id, prompt_name, version, prompt_content, is_active, metrics, created_at
                FROM prompt_versions
                WHERE prompt_name = %s AND version = %s
            """, (prompt_name, version))
            row = cur.fetchone()
            return dict(row) if row else None

    def save(self, prompt_name: str, version: int, content: str, activate: bool = False) -> int:
        with self.conn.cursor() as cur:
            if activate:
                cur.execute(
                    "UPDATE prompt_versions SET is_active = false WHERE prompt_name = %s AND is_active = true",
                    (prompt_name,)
                )
            cur.execute("""
                INSERT INTO prompt_versions (prompt_name, version, prompt_content, is_active, metrics)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING version_id
            """, (prompt_name, version, content, activate, json.dumps({})))
            self.conn.commit()
            return cur.fetchone()[0]

    def activate(self, prompt_name: str, version: int):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE prompt_versions SET is_active = false WHERE prompt_name = %s AND is_active = true",
                (prompt_name,)
            )
            cur.execute(
                "UPDATE prompt_versions SET is_active = true WHERE prompt_name = %s AND version = %s",
                (prompt_name, version)
            )
            self.conn.commit()


class CompanyCharacterRepository:
    ALLOWED_COLUMNS = frozenset({
        "character_name", "character_mood", "character_style",
        "voice_tone", "image_url", "image_prompt", "image_model",
        "elevenlabs_voice_id", "voice_design_prompt", "generation_metadata",
        "is_active",
    })

    def __init__(self, conn):
        self.conn = conn

    def get(self, character_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM company_characters WHERE character_id = %s",
                (character_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_company(self, company_id: int) -> list[dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM company_characters WHERE company_id = %s AND is_active = true",
                (company_id,)
            )
            return [dict(row) for row in cur.fetchall()]

    def create(self, character: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO company_characters (
                    company_id, character_name, character_mood, character_style,
                    voice_tone, image_url, image_prompt, image_model,
                    elevenlabs_voice_id, voice_design_prompt, generation_metadata
                )
                VALUES (
                    %(company_id)s, %(character_name)s, %(character_mood)s, %(character_style)s,
                    %(voice_tone)s, %(image_url)s, %(image_prompt)s, %(image_model)s,
                    %(elevenlabs_voice_id)s, %(voice_design_prompt)s, %(generation_metadata)s
                )
                RETURNING character_id
            """, {
                "company_id": character["company_id"],
                "character_name": character.get("character_name"),
                "character_mood": character.get("character_mood"),
                "character_style": character.get("character_style"),
                "voice_tone": character.get("voice_tone"),
                "image_url": character.get("image_url"),
                "image_prompt": character.get("image_prompt"),
                "image_model": character.get("image_model"),
                "elevenlabs_voice_id": character.get("elevenlabs_voice_id"),
                "voice_design_prompt": character.get("voice_design_prompt"),
                "generation_metadata": json.dumps(character.get("generation_metadata", {})),
            })
            self.conn.commit()
            return cur.fetchone()[0]

    def update(self, character_id: int, updates: dict) -> bool:
        if not updates:
            return False

        # 허용된 컬럼만 필터링 (SQL Injection 방지)
        safe_updates = {k: v for k, v in updates.items() if k in self.ALLOWED_COLUMNS}
        if not safe_updates:
            return False

        set_parts = []
        params = {"character_id": character_id}
        for key, value in safe_updates.items():
            if key == "generation_metadata":
                value = json.dumps(value)
            set_parts.append(f"{key} = %({key})s")
            params[key] = value
        set_parts.append("updated_at = NOW()")

        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE company_characters
                SET {', '.join(set_parts)}
                WHERE character_id = %(character_id)s
            """, params)
            self.conn.commit()
            return cur.rowcount > 0


class VoiceGenerationRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, voice_gen_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM voice_generations WHERE voice_gen_id = %s",
                (voice_gen_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_script(self, script_id: int) -> list[dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM voice_generations WHERE script_id = %s ORDER BY scene_key",
                (script_id,)
            )
            return [dict(row) for row in cur.fetchall()]

    def find_by_hash(self, character_id: int, text_hash: str) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM voice_generations WHERE character_id = %s AND text_hash = %s",
                (character_id, text_hash)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create(self, voice_gen: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO voice_generations (
                    character_id, script_id, scene_key, text_content, text_hash,
                    audio_url, duration_seconds, size_bytes, settings_json
                )
                VALUES (
                    %(character_id)s, %(script_id)s, %(scene_key)s, %(text_content)s, %(text_hash)s,
                    %(audio_url)s, %(duration_seconds)s, %(size_bytes)s, %(settings_json)s
                )
                ON CONFLICT (character_id, text_hash) DO UPDATE SET
                    script_id = EXCLUDED.script_id,
                    scene_key = EXCLUDED.scene_key,
                    audio_url = COALESCE(EXCLUDED.audio_url, voice_generations.audio_url),
                    duration_seconds = COALESCE(EXCLUDED.duration_seconds, voice_generations.duration_seconds),
                    size_bytes = COALESCE(EXCLUDED.size_bytes, voice_generations.size_bytes)
                RETURNING voice_gen_id
            """, {
                "character_id": voice_gen["character_id"],
                "script_id": voice_gen.get("script_id"),
                "scene_key": voice_gen["scene_key"],
                "text_content": voice_gen["text_content"],
                "text_hash": voice_gen.get("text_hash"),
                "audio_url": voice_gen.get("audio_url"),
                "duration_seconds": voice_gen.get("duration_seconds"),
                "size_bytes": voice_gen.get("size_bytes"),
                "settings_json": json.dumps(voice_gen.get("settings_json", {})),
            })
            self.conn.commit()
            return cur.fetchone()[0]


class ImageGenerationRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, image_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM image_generations WHERE image_id = %s",
                (image_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_script(self, script_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM image_generations WHERE script_id = %s",
                (script_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def create(self, image_gen: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO image_generations (
                    character_id, script_id, prompt, model,
                    image_url, size_bytes, metadata_json
                )
                VALUES (
                    %(character_id)s, %(script_id)s, %(prompt)s, %(model)s,
                    %(image_url)s, %(size_bytes)s, %(metadata_json)s
                )
                ON CONFLICT (script_id) DO UPDATE SET
                    prompt = EXCLUDED.prompt,
                    model = EXCLUDED.model,
                    image_url = EXCLUDED.image_url,
                    size_bytes = EXCLUDED.size_bytes,
                    metadata_json = EXCLUDED.metadata_json
                RETURNING image_id
            """, {
                "character_id": image_gen["character_id"],
                "script_id": image_gen["script_id"],
                "prompt": image_gen.get("prompt"),
                "model": image_gen.get("model"),
                "image_url": image_gen.get("image_url"),
                "size_bytes": image_gen.get("size_bytes"),
                "metadata_json": json.dumps(image_gen.get("metadata_json", {})),
            })
            self.conn.commit()
            return cur.fetchone()[0]


class SceneVideoRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, scene_video_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scene_videos WHERE scene_video_id = %s",
                (scene_video_id,)
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_script(self, script_id: int) -> list[dict]:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM scene_videos WHERE script_id = %s ORDER BY scene_key",
                (script_id,)
            )
            return [dict(row) for row in cur.fetchall()]

    def create(self, scene_video: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scene_videos (
                    script_id, scene_key, voice_gen_id, image_id,
                    video_url, duration_seconds, size_bytes,
                    generation_model, generation_cost, generation_metadata
                )
                VALUES (
                    %(script_id)s, %(scene_key)s, %(voice_gen_id)s, %(image_id)s,
                    %(video_url)s, %(duration_seconds)s, %(size_bytes)s,
                    %(generation_model)s, %(generation_cost)s, %(generation_metadata)s
                )
                ON CONFLICT (script_id, scene_key) DO UPDATE SET
                    voice_gen_id = EXCLUDED.voice_gen_id,
                    image_id = EXCLUDED.image_id,
                    video_url = EXCLUDED.video_url,
                    duration_seconds = EXCLUDED.duration_seconds,
                    size_bytes = EXCLUDED.size_bytes,
                    generation_model = EXCLUDED.generation_model,
                    generation_cost = EXCLUDED.generation_cost,
                    generation_metadata = EXCLUDED.generation_metadata
                RETURNING scene_video_id
            """, {
                "script_id": scene_video["script_id"],
                "scene_key": scene_video["scene_key"],
                "voice_gen_id": scene_video.get("voice_gen_id"),
                "image_id": scene_video.get("image_id"),
                "video_url": scene_video.get("video_url"),
                "duration_seconds": scene_video.get("duration_seconds"),
                "size_bytes": scene_video.get("size_bytes"),
                "generation_model": scene_video.get("generation_model"),
                "generation_cost": scene_video.get("generation_cost"),
                "generation_metadata": json.dumps(scene_video.get("generation_metadata", {})),
            })
            self.conn.commit()
            return cur.fetchone()[0]


class VideoRepository:
    def __init__(self, conn):
        self.conn = conn

    def get(self, video_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM videos WHERE video_id = %s", (video_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_script(self, script_id: int) -> dict | None:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM videos WHERE script_id = %s", (script_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def create(self, video: dict) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO videos (
                    ad_id, company_id, script_id, title, description,
                    s3_url, thumbnail_url, file_size_bytes, duration_seconds, status
                )
                VALUES (
                    %(ad_id)s, %(company_id)s, %(script_id)s, %(title)s, %(description)s,
                    %(s3_url)s, %(thumbnail_url)s, %(file_size_bytes)s, %(duration_seconds)s, %(status)s
                )
                RETURNING video_id
            """, {
                "ad_id": video.get("ad_id"),
                "company_id": video.get("company_id"),
                "script_id": video.get("script_id"),
                "title": video.get("title"),
                "description": video.get("description"),
                "s3_url": video.get("s3_url"),
                "thumbnail_url": video.get("thumbnail_url"),
                "file_size_bytes": video.get("file_size_bytes"),
                "duration_seconds": video.get("duration_seconds"),
                "status": video.get("status", "pending"),
            })
            self.conn.commit()
            return cur.fetchone()[0]

    def update_status(self, video_id: int, status: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE videos SET status = %s, updated_at = NOW() WHERE video_id = %s",
                (status, video_id)
            )
            self.conn.commit()
            return cur.rowcount > 0
