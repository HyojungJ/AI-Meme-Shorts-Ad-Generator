from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class Beat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str = Field(..., description="비트 ID")
    type: Literal["dialogue", "action", "reaction"] = Field(...)
    character: Literal["부장", "사원"] = Field(...)
    text: Optional[str] = None
    emotion: Optional[str] = None
    motion_prompt: Optional[str] = None
    duration: float = Field(default=3.0)


class MemeReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meme_id: int
    meme_name: str
    meme_type: Literal["quotable", "performable"]
    key_phrase: Optional[str] = None


class Scene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_number: int
    scene_type: Literal["hook", "setup", "buildup", "meme", "punchline"]
    purpose: Optional[str] = None
    comedy_beat: Optional[str] = None
    scene_motion_prompt: Optional[str] = None
    meme_reference: Optional[MemeReference] = None
    beats: List[Beat] = Field(default_factory=list)


class VideoData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    video_id: Optional[str] = None
    time_stamp: Optional[dict] = None
    motion_prompt_hint: Optional[str] = None
    motion_sequence: Optional[List[dict]] = None
    body_parts: Optional[dict] = None
    style_keywords: Optional[List[str]] = None
    duration_seconds: Optional[float] = None


class AudioData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    video_id: Optional[str] = None
    audio_file: Optional[str] = None
    prosody: Optional[dict] = None
    ssml: Optional[str] = None
    detected_text: Optional[str] = None


class ScenarioInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meme_id: int
    meme_name: str
    definition: str
    meme_type: Literal["quotable", "performable"]
    key_phrase: Optional[str] = None
    video_data: Optional[VideoData] = None
    audio_data: Optional[AudioData] = None
    characters: List[dict] = Field(default_factory=list)


class ScenarioOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    script_id: Optional[int] = None
    meme_id: int
    title: str
    description: Optional[str] = None
    total_duration: float
    scenes: List[Scene]
    hashtags: List[str] = Field(default_factory=list)

    def to_db_format(self) -> dict:
        return {
            "meme_id": self.meme_id,
            "title": self.title,
            "description": self.description,
            "total_duration": self.total_duration,
            "scenes": [scene.model_dump() for scene in self.scenes],
            "hashtags": self.hashtags,
        }


class SkeletonBeat(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    type: Literal["dialogue", "action", "reaction"]
    character: Literal["부장", "사원"]
    text: Optional[str] = None
    emotion: Optional[str] = None
    motion_prompt: Optional[str] = None
    duration: float = Field(default=3.0)


class SkeletonScene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_number: int
    scene_type: Literal["hook", "setup", "buildup", "meme", "punchline"]
    purpose: Optional[str] = None
    comedy_beat: Optional[str] = None
    beats: List[SkeletonBeat] = Field(default_factory=list)


class SkeletonOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    scenes: List[SkeletonScene]
    total_duration: float
    hashtags: List[str] = Field(default_factory=list)


class DialogueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    beat_id: str
    text: str


class DialogueOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    character: str
    dialogues: List[DialogueItem]


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")
    character_id: Optional[int] = None
    name: Literal["부장", "사원"]
    description: str
    style: str
    style_tags: List[str] = Field(default_factory=list)
    is_active: bool = True


class LLMEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    score: int = Field(..., ge=0, le=20)
    reasoning: str
    suggestions: List[str] = Field(default_factory=list)


class EvaluationBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    structure: float = Field(default=0, ge=0, le=20)
    character: float = Field(default=0, ge=0, le=20)
    meme_accuracy: float = Field(default=0, ge=0, le=20)
    motion_quality: float = Field(default=0, ge=0, le=20)
    naturalness: float = Field(default=0, ge=0, le=20)


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_score: float = Field(..., ge=0, le=100)
    breakdown: EvaluationBreakdown
    feedback: str
    suggestions: List[str] = Field(default_factory=list)
