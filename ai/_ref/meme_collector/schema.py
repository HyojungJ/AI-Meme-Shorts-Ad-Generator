from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class OriginInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: str = None
    creator: str = None
    date: str = None
    platform: str = None


class DefinitionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    definition: str = Field(description="밈의 종합적 정의")
    origin: OriginInfo = Field(default_factory=OriginInfo)
    keywords: list = Field(default_factory=list)
    key_phrase: str = Field(None, description="밈의 핵심 대사/문구")


class RiskInfoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controversies: list = Field(default_factory=list)
    sensitive_topics: list = Field(default_factory=list)
    risk_level: str = Field("low")
    news_summary: str = Field("")


class MemeTypeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meme_type: Literal["quotable", "performable", "hybrid"]
    key_phrase: str = None
    reason: str = ""
    confidence: Literal["high", "medium", "low"] = "medium"
