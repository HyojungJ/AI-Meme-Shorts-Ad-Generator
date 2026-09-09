"""
content_pipeline.db -- backward-compatible re-export hub.

All public functions are imported from sub-modules so that existing
``from content_pipeline.db import ...`` statements continue to work.
"""

from content_pipeline.db.connection import (
    db_cursor,
    get_db_connection,
    test_db_connection,
)
from content_pipeline.db.s3_helpers import (
    _get_s3_client,
    _maybe_presign_s3_url,
    _parse_s3_location,
)
from content_pipeline.db.scenario_queries import (
    _normalize_scenes_payload,
    load_ad_request_item_images,
    load_character_image_url,
    load_character_prompt,
    load_clone_prompt_url,
    load_elevenlabs_voice_id,
    load_latest_script_id_by_ad_id,
    load_scenario_prompts,
    load_scene_prompt,
    load_video_by_id,
    load_voice_description,
    load_voice_text,
)
from content_pipeline.db.asset_queries import (
    insert_final_video,
    save_verification_result,
    update_company_character_image_url,
    update_elevenlabs_voice_id,
    update_generation_metadata,
    upsert_image_generation,
    upsert_scene_assets,
    upsert_scene_video,
    upsert_voice_generation,
)

__all__ = [
    # connection
    "db_cursor",
    "get_db_connection",
    "test_db_connection",
    # s3
    "_get_s3_client",
    "_maybe_presign_s3_url",
    "_parse_s3_location",
    # scenario queries
    "_normalize_scenes_payload",
    "load_ad_request_item_images",
    "load_character_image_url",
    "load_character_prompt",
    "load_clone_prompt_url",
    "load_elevenlabs_voice_id",
    "load_latest_script_id_by_ad_id",
    "load_scenario_prompts",
    "load_scene_prompt",
    "load_video_by_id",
    "load_voice_description",
    "load_voice_text",
    # asset queries
    "insert_final_video",
    "save_verification_result",
    "update_company_character_image_url",
    "update_elevenlabs_voice_id",
    "update_generation_metadata",
    "upsert_image_generation",
    "upsert_scene_assets",
    "upsert_scene_video",
    "upsert_voice_generation",
]
