from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import AIMessage

from backend.video.state import VideoState
from backend.video.tts import TTSGenerator
from backend.video.config import config
from backend.db.video_repository import VideoRepository


def tts_node(state: VideoState) -> Dict[str, Any]:
    scene_clips = state["scene_clips"]
    tts_model = state.get("tts_model", config.tts_model)
    output_dir = Path(state.get("output_dir", config.output_dir))

    audio_dir = output_dir / "audio"
    temp_dir = output_dir / "temp" / "tts"
    audio_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    tts = TTSGenerator(model=tts_model)
    repo = VideoRepository()

    dialogue_clips = [c for c in scene_clips if c.get("tts_items") or c.get("tts_text")]

    tts_results = {}
    total_cost = 0

    for clip in dialogue_clips:
        scene_number = clip["scene_number"]
        output_path = audio_dir / f"scene_{scene_number}.mp3"
        scene_temp_dir = temp_dir / f"scene_{scene_number}"

        tts_items = clip.get("tts_items", [])

        if tts_items:
            result = tts.generate_and_concat(
                items=tts_items,
                output_path=str(output_path),
                temp_dir=str(scene_temp_dir)
            )
        else:
            character = "부장" if clip.get("is_meme_scene") else clip.get("character", "부장")
            result = tts.generate(
                text=clip["tts_text"],
                output_path=str(output_path),
                character=character
            )

        if not result.error:
            clip["tts_audio_path"] = result.audio_path
            clip["tts_cost"] = result.cost_usd
            clip["tts_duration"] = result.duration_seconds
            total_cost += result.cost_usd

            tts_results[scene_number] = {
                "audio_path": result.audio_path,
                "duration": result.duration_seconds,
                "cost": result.cost_usd,
            }

            repo.update_clip_status(
                clip_id=clip["clip_id"],
                tts_audio_url=result.audio_path
            )

    return {
        "messages": [AIMessage(content=f"[tts] {len(tts_results)}개 TTS 생성 완료")],
        "phase": "sora",
        "scene_clips": scene_clips,
        "tts_results": tts_results,
        "total_cost": state.get("total_cost", 0) + total_cost,
    }
