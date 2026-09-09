from pathlib import Path
from typing import Dict, Any

from PIL import Image
from langchain_core.messages import AIMessage

from backend.video.state import VideoState
from backend.video.sora import SoraClient
from backend.video.prompt_builder import SoraPromptBuilder
from backend.video.config import config
from backend.db.video_repository import VideoRepository


def sora_node(state: VideoState) -> Dict[str, Any]:
    scene_clips = state["scene_clips"]
    sora_model = state.get("sora_model", config.sora_model)
    output_dir = Path(state.get("output_dir", config.output_dir))

    clips_dir = output_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    sora = SoraClient(model=sora_model)
    prompt_builder = SoraPromptBuilder(use_llm=True)
    repo = VideoRepository()

    character_infos = {}
    for char_name in ["부장", "사원"]:
        char_info = repo.get_character_info(char_name)
        if char_info:
            character_infos[char_name] = char_info

    sora_results = {}
    total_cost = 0
    base_dir = output_dir.parent.parent  # content-generator 루트

    for clip in scene_clips:
        scene_number = clip["scene_number"]
        scene_data = clip.get("scene_data", {})

        sora_prompt = prompt_builder.build_scene_prompt(
            scene_data=scene_data,
            character_infos=character_infos
        )

        image_path = _get_reference_image(clip, character_infos, repo, base_dir)

        scene_duration = clip.get("duration_seconds", 4)
        sora_options = [4, 8, 12]
        sora_duration = next((d for d in sora_options if d >= scene_duration), 12)

        if image_path:
            image_path = _resize_image_for_sora(image_path, output_dir)
            result = sora.generate_from_image(
                image_path=image_path,
                prompt=sora_prompt,
                duration=sora_duration
            )
        else:
            result = sora.generate(
                prompt=sora_prompt,
                duration=sora_duration
            )

        if result.status == "completed" and result.video_id:
            output_path = clips_dir / f"scene_{scene_number}_sora.mp4"
            downloaded = sora.download(result.video_id, str(output_path))

            cost = result.cost_usd or (sora.COSTS.get(sora_model, 0.1) * sora_duration)
            clip["clip_video_path"] = downloaded
            clip["sora_cost"] = cost
            clip["sora_prompt_used"] = sora_prompt
            total_cost += cost

            sora_results[scene_number] = {
                "video_path": downloaded,
                "prompt": sora_prompt,
                "duration": sora_duration,
                "cost": cost,
            }

            repo.update_clip_status(
                clip_id=clip["clip_id"],
                clip_video_url=downloaded,
                status="generated"
            )
        else:
            clip["error"] = result.error

    return {
        "messages": [AIMessage(content=f"[sora] {len(sora_results)}개 영상 생성 완료")],
        "phase": "compose",
        "scene_clips": scene_clips,
        "sora_results": sora_results,
        "total_cost": state.get("total_cost", 0) + total_cost,
    }


def _get_reference_image(clip: Dict, character_infos: Dict, repo: VideoRepository, base_dir: Path):
    characters = clip.get("characters", [])
    if len(characters) >= 2:
        combined_path = base_dir / config.combined_image
        if combined_path.exists():
            return str(combined_path)

    main_char = clip.get("character", "부장")
    image_path = repo.get_character_image(main_char)
    if image_path and not Path(image_path).is_absolute():
        image_path = str(base_dir / image_path)

    return image_path


def _resize_image_for_sora(image_path: str, output_dir: Path) -> str:
    target_size = (config.video_width, config.video_height)
    try:
        img = Image.open(image_path)
        if img.size == target_size:
            return image_path

        target_w, target_h = target_size
        target_ratio = target_w / target_h
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_height = target_h
            new_width = int(img.width * (target_h / img.height))
        else:
            new_width = target_w
            new_height = int(img.height * (target_w / img.width))

        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        left = (new_width - target_w) // 2
        top = (new_height - target_h) // 2
        img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))

        temp_dir = output_dir / "temp"
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / f"resized_{Path(image_path).name}"
        img_cropped.save(str(temp_path), "PNG")

        return str(temp_path)

    except Exception:
        return image_path
