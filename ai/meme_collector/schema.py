from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OriginInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str | None = Field(None, description="원본 콘텐츠/프로그램명")
    creator: str | None = Field(None, description="메인 아티스트/원작자만 (feat./피처링 제외)")
    date: str | None = Field(None, description="유행 시기 (YYYY or YYYY-MM)")
    platform: str | None = Field(None, description="확산 플랫폼 (YouTube, TikTok 등)")


class Prosody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pitch: Literal["low", "medium", "high"] = "medium"
    speed: Literal["slow", "medium", "fast"] = "medium"
    emotion: str = "neutral"
    ssml: str | None = None


class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    url: str | None = None


class ReferenceVideo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    video_id: str
    url: str
    title: str
    view_count: int = 0


class UsageExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: str = Field(..., description="상황/맥락 (예: 친구가 황당한 말 할 때)")
    usage: str = Field(..., description="사용 방법 (예: '어쩔티비~' 하고 무시한다)")
    tone: Literal["playful", "sarcastic", "aggressive", "friendly", "neutral"] = "playful"
    example_type: Literal["good", "bad"] = "good"
    note: str | None = None
    source_url: str | None = Field(None, description="출처 URL (블로그, 유튜브 등)")


class MemeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    definition: str = Field(..., description="Rich definition in Korean (150+ chars)")
    meme_type: Literal["quotable", "performable", "hybrid"]
    key_phrase: str | None = Field(None, description="Exact catchphrase in Korean")
    emotion: str | None = Field(None, description="Emotion hint for TTS (e.g., excited, sarcastic)")
    prosody: Prosody | None = Field(None, description="TTS prosody settings")
    motion_prompt: str = Field(..., description="Detailed Sora-compatible prompt in English")
    style_keywords: list[str] = Field(default_factory=list)
    usage_examples: list[UsageExample] = Field(default_factory=list, description="활용 예시 목록")
    reference_videos: list[ReferenceVideo] = Field(default_factory=list)
    sources: list[SourceInfo] = Field(default_factory=list)
    origin: OriginInfo | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class AnalyzerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meme_type: Literal["quotable", "performable", "hybrid"]
    key_phrase: str | None = Field(None, description="Exact catchphrase extracted from context")
    definition: str = Field(..., description="Rich 5-8 sentence definition in Korean (200+ chars), including meaning, origin, context, popularity reason, variation patterns, and usage examples for scenarios")
    emotion: str | None = Field(None, description="Emotion hint for TTS (e.g., excited, sarcastic)")
    prosody: Prosody | None = Field(None, description="TTS prosody settings")
    motion_prompt: str = Field(..., description="Detailed English prompt for Sora video generation")
    style_keywords: list[str] = Field(default_factory=list)
    usage_examples: list[UsageExample] = Field(default_factory=list, description="활용 예시 목록")
    origin: OriginInfo | None = None
    risk_level: Literal["low", "medium", "high"] = "low"
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(..., ge=0.0, le=100.0)
    feedback: str = ""
    decision: Literal["PASS", "RETRY", "FAIL"]
