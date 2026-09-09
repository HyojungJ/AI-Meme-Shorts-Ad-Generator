from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class Beat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    type: Literal["dialogue", "action", "reaction"]
    character: str
    text: str = None
    emotion: str = None
    motion_prompt: str = None
    duration: float = 3.0


class MemeReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meme_id: int
    meme_name: str
    meme_type: Literal["quotable", "performable"]
    key_phrase: str = None


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_number: int
    scene_type: Literal["hook", "setup", "buildup", "meme", "punchline"]
    purpose: str = None
    comedy_beat: str = None
    scene_motion_prompt: str = None
    meme_reference: MemeReference = None
    beats: list[Beat] = Field(default_factory=list)


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")
    character_id: int = None
    name: str
    description: str
    style: str
    video_gen_prompt: str = None


class VideoData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    motion_prompt_hint: str = None
    motion_sequence: list[dict] = None
    duration_seconds: float = None


class AudioData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ssml: str = None
    prosody: dict = None


# === Pipeline Input ===

class PipelineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meme_id: int
    meme_name: str
    definition: str
    meme_type: Literal["quotable", "performable"]
    key_phrase: str = None
    video_data: VideoData = None
    audio_data: AudioData = None
    characters: list[Character] = Field(default_factory=list)


# === Scenario Output (-> Video Input) ===

class ScenarioOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    script_id: int = None
    meme_id: int
    title: str
    description: str = None
    total_duration: float
    scenes: list[Scene]
    hashtags: list[str] = Field(default_factory=list)

    def to_db_format(self) -> dict:
        return {
            "meme_id": self.meme_id,
            "title": self.title,
            "description": self.description,
            "total_duration": self.total_duration,
            "scenes": [scene.model_dump() for scene in self.scenes],
            "hashtags": self.hashtags,
        }


# === Video Output (Final) ===

class VideoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    video_id: int = None
    script_id: int
    video_url: str
    duration_seconds: float
    total_cost: float = 0.0


# === DB Models (Content Pipeline) ===

class CompanyCharacterDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    character_id: int = None
    company_id: int
    character_name: str = None
    character_mood: str = None
    character_style: str = None
    voice_tone: str = None
    image_url: str = None
    image_prompt: str = None
    image_model: str = None
    elevenlabs_voice_id: str = None
    voice_design_prompt: str = None
    generation_metadata: dict = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None


class VoiceGenerationDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    voice_gen_id: int = None
    character_id: int
    script_id: int = None
    scene_key: str
    text_content: str
    text_hash: str = None
    audio_url: str = None
    duration_seconds: float = None
    size_bytes: int = None
    settings_json: dict = Field(default_factory=dict)
    created_at: datetime = None


class ImageGenerationDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    image_id: int = None
    character_id: int
    script_id: int
    prompt: str = None
    model: str = None
    image_url: str = None
    size_bytes: int = None
    metadata_json: dict = Field(default_factory=dict)
    created_at: datetime = None


class SceneVideoDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    scene_video_id: int = None
    script_id: int
    scene_key: str
    voice_gen_id: int = None
    image_id: int = None
    video_url: str = None
    duration_seconds: float = None
    size_bytes: int = None
    generation_model: str = None
    generation_cost: float = None
    generation_metadata: dict = Field(default_factory=dict)
    created_at: datetime = None


class VideoDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    video_id: int = None
    ad_id: int = None
    company_id: int = None
    script_id: int = None
    title: str = None
    description: str = None
    s3_url: str = None
    thumbnail_url: str = None
    file_size_bytes: int = None
    duration_seconds: int = None
    status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None


class AdRequestDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ad_id: int = None
    company_id: int = None
    account_id: int = None
    character_id: int = None
    item_name: str
    item_category: str
    item_url: str = None
    item_images: list[str] = Field(default_factory=list)
    item_description: str
    voice_description: str = None
    meme_id: int = None
    character_image_prompt: str = Field(default=None, validation_alias="character_style_raw")
    character_voice_prompt: str = Field(default=None, validation_alias="notes")
    status: str = "draft"
    created_at: datetime = None
    updated_at: datetime = None
