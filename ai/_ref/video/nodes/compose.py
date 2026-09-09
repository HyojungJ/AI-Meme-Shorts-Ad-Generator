import shutil
from pathlib import Path
from typing import Dict, Any

from langchain_core.messages import AIMessage

from backend.video.state import VideoState
from backend.video.composer import VideoComposer
from backend.video.config import config
from backend.db.video_repository import VideoRepository


def compose_node(state: VideoState) -> Dict[str, Any]:
    scene_clips = state["scene_clips"]
    output_dir = Path(state.get("output_dir", config.output_dir))
    use_sora_audio = state.get("use_sora_audio", False)

    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    composer = VideoComposer(output_dir=str(output_dir))
    repo = VideoRepository()

    composed_clips = []
    base_dir = output_dir.parent.parent

    for clip in scene_clips:
        scene_number = clip["scene_number"]
        video_path = clip.get("clip_video_path")
        audio_path = None if use_sora_audio else clip.get("tts_audio_path")

        final_path = _compose_single_clip(
            scene_number=scene_number,
            video_path=video_path,
            audio_path=audio_path,
            clip=clip,
            clips_dir=clips_dir,
            composer=composer,
            repo=repo,
            base_dir=base_dir
        )

        composed_clips.append(final_path)
        if final_path:
            clip["final_clip_path"] = final_path

    successful = len([c for c in composed_clips if c])

    return {
        "messages": [AIMessage(content=f"[compose] {successful}개 클립 합성 완료")],
        "phase": "finalize",
        "scene_clips": scene_clips,
        "composed_clips": composed_clips,
    }


def _compose_single_clip(
    scene_number: int,
    video_path: str,
    audio_path: str,
    clip: Dict,
    clips_dir: Path,
    composer: VideoComposer,
    repo: VideoRepository,
    base_dir: Path
):
    if video_path and audio_path:
        output_path = clips_dir / f"scene_{scene_number}_final.mp4"
        result = composer.add_audio(
            video_path=video_path,
            audio_path=audio_path,
            output_path=str(output_path)
        )

        if result.success:
            return result.output_path
        return video_path

    elif video_path:
        output_path = clips_dir / f"scene_{scene_number}_final.mp4"
        shutil.copy(video_path, output_path)
        return str(output_path)

    elif audio_path:
        image_path = _get_fallback_image(clip, repo, base_dir)
        if image_path:
            output_path = clips_dir / f"scene_{scene_number}_static.mp4"
            result = composer.image_to_video(
                image_path=image_path,
                audio_path=audio_path,
                output_path=str(output_path)
            )
            if result.success:
                return result.output_path

    return None


def _get_fallback_image(clip: Dict, repo: VideoRepository, base_dir: Path):
    main_char = clip.get("character", "부장")
    image_path = repo.get_character_image(main_char)

    if image_path and not Path(image_path).is_absolute():
        image_path = str(base_dir / image_path)

    return image_path
