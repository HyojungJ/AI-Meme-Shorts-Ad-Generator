"""
Admin 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class VideoListItem(BaseModel):
    video_id: int
    title: str
    company_id: int
    company_name: str
    status: str
    duration_seconds: Optional[int]
    file_size_mb: Optional[float]
    created_at: str
    completed_at: Optional[str]


class VideoListResponse(BaseModel):
    total_count: int
    offset: int
    limit: int
    videos: List[VideoListItem]


class PublishVideoRequest(BaseModel):
    channel_id: int = Field(..., description="YouTube 채널 ID")
    yt_title: Optional[str] = Field(None, description="YouTube 제목")
    yt_description: Optional[str] = Field(None, description="YouTube 설명")
    scheduled_at: Optional[str] = Field(None, description="예약 게시 시간")
    privacy_status: Optional[str] = Field("public", description="공개 설정 (public, private, unlisted)")


class PublishVideoResponse(BaseModel):
    post_id: int
    video_id: int
    status: str
    message: str


class WorkflowListItem(BaseModel):
    execution_id: str
    ad_id: int
    company_id: int
    title: Optional[str] = None
    company_name: Optional[str] = None
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    retry_count: int
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str] = None


class WorkflowListResponse(BaseModel):
    total_count: int
    offset: int
    limit: int
    workflows: List[WorkflowListItem]


class WorkflowActionResponse(BaseModel):
    execution_id: str
    status: str
    message: str
