from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import AIMessage

from backend.video.state import VideoState
from backend.video.composer import VideoComposer
from backend.video.config import config
from backend.db.video_repository import VideoRepository


def finalize_node(state: VideoState) -> Dict[str, Any]:
    script_id = state["script_id"]
    script = state["script"]
    scene_clips = state["scene_clips"]
    composed_clips = state["composed_clips"]
    output_dir = Path(state.get("output_dir", config.output_dir))

    composer = VideoComposer(output_dir=str(output_dir))
    repo = VideoRepository()

    valid_clips = [c for c in composed_clips if c]

    if not valid_clips:
        return {
            "messages": [AIMessage(content="[finalize] 합성할 클립이 없습니다")],
            "phase": "done",
            "status": "failed",
            "errors": state.get("errors", []) + ["합성할 클립 없음"],
        }

    output_path = output_dir / f"script_{script_id}_final.mp4"
    result = composer.concat(
        clips=valid_clips,
        output_path=str(output_path)
    )

    if not result.success:
        return {
            "messages": [AIMessage(content=f"[finalize] 최종 합성 실패: {result.error}")],
            "phase": "done",
            "status": "failed",
            "errors": state.get("errors", []) + [f"최종 합성 실패: {result.error}"],
        }

    total_cost = _calculate_total_cost(scene_clips, state.get("total_cost", 0))

    gen_id = repo.save_generated_video(
        script_id=script_id,
        meme_id=script.get("meme_id"),
        final_url=result.output_path,
        cost=total_cost,
        status="completed"
    )

    return {
        "messages": [AIMessage(content=f"[finalize] 완료: gen_id={gen_id}")],
        "phase": "done",
        "status": "completed",
        "gen_id": gen_id,
        "final_video_path": result.output_path,
        "total_duration": result.duration_seconds,
        "total_cost": total_cost,
    }


def _calculate_total_cost(scene_clips: list, base_cost: float) -> float:
    clip_cost = sum(
        clip.get("tts_cost", 0) +
        clip.get("sora_cost", 0)
        for clip in scene_clips
    )
    return max(clip_cost, base_cost)
