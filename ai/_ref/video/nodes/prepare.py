from typing import Dict, Any, List
from langchain_core.messages import AIMessage

from backend.video.state import VideoState
from backend.db.video_repository import VideoRepository


def prepare_node(state: VideoState) -> Dict[str, Any]:
    script_id = state["script_id"]
    repo = VideoRepository()

    try:
        script = repo.get_script(script_id)
        if not script:
            return {
                "messages": [AIMessage(content=f"[prepare] Script not found: {script_id}")],
                "status": "failed",
                "errors": state.get("errors", []) + [f"Script not found: {script_id}"],
                "phase": "done",
            }

        scene_clips = _create_scene_clips(script, repo)

        return {
            "messages": [AIMessage(content=f"[prepare] {len(scene_clips)}개 씬 클립 생성 완료")],
            "phase": "tts",
            "script": script,
            "scene_clips": scene_clips,
            "status": "processing",
        }

    except Exception as e:
        error_msg = f"[prepare] 실패: {str(e)}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "errors": state.get("errors", []) + [error_msg],
            "status": "failed",
            "phase": "done",
        }


def _create_scene_clips(script: Dict[str, Any], repo: VideoRepository) -> List[Dict]:
    scene_clips = []
    scenes = script.get("scenes", [])

    for scene in scenes:
        scene_number = scene.get("scene_number", 0)
        scene_type = scene.get("scene_type", "")
        beats = scene.get("beats", [])

        tts_items = []
        motion_prompt = None
        total_duration = 0
        characters_in_scene = set()

        for beat in beats:
            beat_type = beat.get("type")
            text = beat.get("text")
            character = beat.get("character", "부장")

            if beat_type == "dialogue" and text:
                tts_items.append({
                    "text": text,
                    "character": character,
                    "beat_id": beat.get("beat_id"),
                })
            elif beat_type == "action" and scene_type == "meme" and text:
                tts_items.append({
                    "text": text,
                    "character": character,
                    "beat_id": beat.get("beat_id"),
                })

            if character:
                characters_in_scene.add(character)

            if beat.get("motion_prompt"):
                motion_prompt = beat.get("motion_prompt")

            total_duration += beat.get("duration", 2.0)

        main_character = list(characters_in_scene)[0] if characters_in_scene else "부장"

        clip = {
            "script_id": script.get("script_id"),
            "scene_number": scene_number,
            "beat_id": f"scene-{scene_number}",
            "character": main_character,
            "characters": list(characters_in_scene),
            "clip_type": scene_type,
            "motion_prompt": motion_prompt,
            "tts_items": tts_items,
            "tts_text": " ".join([item["text"] for item in tts_items]) if tts_items else None,
            "duration_seconds": min(total_duration, 8),
            "is_meme_scene": scene_type == "meme",
            "status": "pending",
            "scene_data": scene,
            "tts_audio_path": None,
            "clip_video_path": None,
            "final_clip_path": None,
            "tts_cost": 0,
            "sora_cost": 0,
        }
        scene_clips.append(clip)

        clip_id = repo.create_scene_clip(clip)
        clip["clip_id"] = clip_id

    return scene_clips
