from dataclasses import dataclass


@dataclass
class VideoConfig:
    sora_model: str = "sora-2"
    sora_timeout: int = 300
    sora_poll_interval: int = 5
    tts_model: str = "tts-1-hd"
    tts_default_voice: str = "alloy"
    output_dir: str = "data/output"
    video_width: int = 720
    video_height: int = 1280
    character_images_dir: str = "data/images"
    combined_image: str = "data/images/azae_newbie_with_bg.png"
    scene_builder_model: str = "gpt-4o-mini-2024-07-18"
    scene_builder_temperature: float = 0.4
    translator_temperature: float = 0.3
    default_background: str = "Modern Korean corporate office with desks, monitors, office chairs, and indoor plants"


config = VideoConfig()
