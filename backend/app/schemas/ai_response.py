"""
AI 파이프라인 응답 스키마
3개 클라이언트(Mock, Direct, HTTP) 응답 형식 통일
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class CharacterImageResponse(BaseModel):
    image_url: str
    image_path: Optional[str] = None
    model: Optional[str] = None
    voice_design_prompt: Optional[str] = None
    image_prompt: Optional[str] = None
    size_bytes: Optional[int] = None


class VoiceDesignResponse(BaseModel):
    voice_url: str
    voice_id: Optional[str] = None
    duration_seconds: Optional[float] = None
    size_bytes: Optional[int] = None


class ScenarioResponse(BaseModel):
    scenes: List[Dict[str, Any]]
    title: Optional[str] = None
    script_id: Optional[int] = None


class VideoGenerationResponse(BaseModel):
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    status: str = "ok"
    estimated_duration: Optional[int] = None
    db_video_id: Optional[int] = None


class CharacterRegenerationResponse(BaseModel):
    image_url: str
    image_path: Optional[str] = None
    model: Optional[str] = None
    verification_score: Optional[float] = None
    verification_decision: Optional[str] = None
    retry_count: int = 0


class ScenarioRevisionResponse(BaseModel):
    script_id: int
    scenes: List[Dict[str, Any]]
    title: Optional[str] = None
    status: str = "revised"


class VideoRevisionResponse(BaseModel):
    video_id: int
    status: str
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    estimated_duration: Optional[int] = None
    verification_score: Optional[float] = None
    verification_decision: Optional[str] = None
