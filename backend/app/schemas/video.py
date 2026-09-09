"""
영상 관련 Pydantic 스키마
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class AdRequestStatus(str, Enum):
    """광고 요청 상태 (프론트/백엔드 공유)"""
    DRAFT = "draft"
    GENERATING_CHARACTER = "generating_character"
    GENERATING_VOICE = "generating_voice"
    GENERATING_SCENARIO = "generating_scenario"
    GENERATING_VIDEO = "generating_video"
    CONTENT_GENERATING = "content_generating"
    PENDING_APPROVAL = "pending_approval"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoStatus(str, Enum):
    """영상 상태"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    CLIENT_APPROVED = "client_approved"
    CLIENT_REJECTED = "client_rejected"
    ADMIN_APPROVED = "admin_approved"
    ADMIN_REJECTED = "admin_rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class ScenarioApprovalStatus(str, Enum):
    """시나리오 승인 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class VideoGenerateResponse(BaseModel):
    execution_id: str
    ad_id: int
    status: str
    message: str


class CharacterPromptSuggestRequest(BaseModel):
    """제품 정보 기반 캐릭터 프롬프트 추천 요청"""
    product_name: str = Field(..., min_length=1, description="제품명")
    product_category: Optional[str] = Field(None, description="제품 카테고리")
    product_description: Optional[str] = Field(None, description="제품 설명/강조점")


class CharacterPromptSuggestResponse(BaseModel):
    """제품 정보 기반 캐릭터 프롬프트 추천 응답"""
    character_image_prompt: str
    character_voice_prompt: str


class CharacterPreviewResponse(BaseModel):
    character_id: int
    image_url: Optional[str]
    voice_url: Optional[str]
    is_active: bool
    created_at: str
    image_prompt: Optional[str] = None
    voice_design_prompt: Optional[str] = None


class CharacterListResponse(BaseModel):
    character_id: int
    image_url: str
    is_active: bool
    created_at: str
    image_prompt: Optional[str] = None


class ApprovalRequest(BaseModel):
    approved: bool
    rejection_reason: Optional[str] = None
    feedback: Optional[str] = None


class ApprovalResponse(BaseModel):
    character_id: int
    status: str
    message: str


class WorkflowStatusResponse(BaseModel):
    execution_id: str
    ad_id: int
    character_id: Optional[int] = None
    item_name: Optional[str] = None
    scene_image_url: Optional[str] = None
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class ProjectListResponse(BaseModel):
    total_count: int
    offset: int
    limit: int
    workflows: List[WorkflowStatusResponse]


class VideoDownloadResponse(BaseModel):
    video_id: int
    download_url: str
    expires_at: str
    file_size_bytes: Optional[int] = None
    format: Optional[str] = None


class VideoApprovalRequest(BaseModel):
    feedback: Optional[str] = None


class VideoRejectionRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="거부 사유")
    feedback: Optional[str] = None


class VideoApprovalResponse(BaseModel):
    video_id: int
    status: str
    message: str


class VideoPreviewResponse(BaseModel):
    video_id: int
    preview_url: str
    expires_at: str
    duration_seconds: Optional[float] = None
    thumbnail_url: Optional[str] = None


class VideoReviseRequest(BaseModel):
    """영상 수정 요청"""
    revision_notes: str = Field(..., min_length=1, description="수정 요청 내용")
    feedback: Optional[str] = Field(None, description="추가 피드백")


class VideoReviseResponse(BaseModel):
    """영상 수정 요청 응답"""
    video_id: int
    status: str
    message: str


class CharacterGenerateRequest(BaseModel):
    """캐릭터 생성 요청"""
    character_style_raw: str = Field(..., min_length=1, description="캐릭터 전체 설명 (외형, 음성 스타일 포함)")
    character_prompt: str = Field(..., description="이미지 생성 프롬프트")
    aspect_ratio: Optional[str] = Field("1:1", description="이미지 비율 (1:1, 16:9, 9:16)")


class CharacterGenerateResponse(BaseModel):
    """캐릭터 생성 응답"""
    character_id: int
    image_url: str
    image_path: str
    size_bytes: int
    created_at: str
    message: str


class VoiceGenerateRequest(BaseModel):
    """음성 생성 요청"""
    sample_text: str = Field(..., min_length=1, description="음성 샘플 텍스트")
    voice_description: Optional[str] = Field(None, description="음성 설명 (예: 밝고 경쾌한 목소리)")


class VoiceGenerateResponse(BaseModel):
    """음성 생성 응답"""
    character_id: int
    voice_url: str
    voice_id: Optional[str] = None
    duration_seconds: Optional[float] = None
    size_bytes: int
    created_at: str
    message: str


class VoicePreviewResponse(BaseModel):
    """음성 미리듣기 응답"""
    character_id: int
    voice_url: str
    voice_design_prompt: Optional[str] = None
    duration_seconds: Optional[float] = None
    created_at: str


class VoiceApprovalRequest(BaseModel):
    """음성 승인 요청"""
    approved: bool
    feedback: Optional[str] = None


class VoiceReviseRequest(BaseModel):
    """음성 수정 요청"""
    revision_notes: Optional[str] = Field(None, description="수정 요청 내용")
    rejection_reason: Optional[str] = Field(None, description="거부 사유 (프론트엔드 호환)")
    sample_text: Optional[str] = Field(None, description="새로운 샘플 텍스트")
    approved: Optional[bool] = Field(None, description="승인 여부 (프론트엔드 호환)")

    def get_revision_notes(self) -> str:
        """revision_notes 또는 rejection_reason 반환"""
        return self.revision_notes or self.rejection_reason or ""


class CharacterReviseRequest(BaseModel):
    """캐릭터 이미지 수정 요청"""
    revision_notes: str = Field(..., min_length=1, description="수정 요청 내용")
    character_prompt: Optional[str] = Field(None, description="새로운 이미지 생성 프롬프트")


class CharacterRegenerateResponse(BaseModel):
    """캐릭터 이미지 재생성 응답"""
    character_id: int
    image_url: str
    size_bytes: int
    created_at: str
    message: str


# ============================================
# Content Pipeline API 스키마
# ============================================

class AdCharacterGenerateRequest(BaseModel):
    """광고용 캐릭터 생성 요청"""
    character_prompt: str = Field(..., min_length=1, max_length=2000, description="캐릭터 이미지 생성 프롬프트")
    aspect_ratio: Optional[str] = Field("9:16", pattern=r"^\d+:\d+$", description="이미지 비율")
    force_new_character: Optional[bool] = Field(False, description="새 캐릭터 강제 생성")


class AdCharacterGenerateResponse(BaseModel):
    """광고용 캐릭터 생성 응답"""
    character_id: int
    image_url: str
    status: str


class AdVoiceGenerateRequest(BaseModel):
    """광고용 음성 생성 요청"""
    sample_text: str = Field(..., min_length=1, max_length=1000, description="음성 샘플 텍스트")
    voice_description: Optional[str] = Field(None, max_length=500, description="음성 설명")


class AdVoiceGenerateResponse(BaseModel):
    """광고용 음성 생성 응답"""
    character_id: int
    voice_url: str
    voice_id: Optional[str] = None
    status: str


class ScenarioGenerateRequest(BaseModel):
    """시나리오 생성 요청"""
    meme_id: Optional[int] = None


class SceneResponse(BaseModel):
    """씬 응답"""
    scene_number: int
    content: str
    timestamp: Optional[str] = None


class ScenarioGenerateResponse(BaseModel):
    """시나리오 생성 응답"""
    script_id: int
    title: str
    scenes: List[SceneResponse]
    status: str


class AdVideoGenerateResponse(BaseModel):
    """광고용 영상 생성 응답"""
    video_id: int
    status: str
    estimated_duration: Optional[int] = None


class CharacterPreviewByAdResponse(BaseModel):
    """광고별 캐릭터 미리보기"""
    character_id: int
    image_url: Optional[str]
    is_approved: bool
    created_at: str


class VoicePreviewByAdResponse(BaseModel):
    """광고별 음성 미리보기"""
    character_id: int
    voice_url: Optional[str]
    is_approved: bool
    created_at: str


class ScenarioResponse(BaseModel):
    """시나리오 조회 응답"""
    script_id: int
    title: str
    description: Optional[str] = None
    scenes: List[SceneResponse]
    approval_status: str


class VideoPreviewByAdResponse(BaseModel):
    """광고별 영상 미리보기"""
    video_id: int
    preview_url: Optional[str]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[int] = None
    status: str


class ItemApprovalRequest(BaseModel):
    """개별 항목 승인 요청"""
    approved: bool
    feedback: Optional[str] = None


class ItemApprovalResponse(BaseModel):
    """개별 항목 승인 응답"""
    status: str
    message: str


class CharacterRevisionRequest(BaseModel):
    """캐릭터 수정 요청"""
    revision_notes: str = Field(..., min_length=1, max_length=2000, description="수정 요청 내용")
    character_prompt: Optional[str] = Field(None, max_length=2000, description="새로운 프롬프트")


class VoiceRevisionRequest(BaseModel):
    """음성 수정 요청"""
    revision_notes: str = Field(..., min_length=1, max_length=2000, description="수정 요청 내용")
    sample_text: Optional[str] = Field(None, max_length=1000, description="새로운 샘플 텍스트")


class SceneScenarioRevision(BaseModel):
    """씬별 시나리오 수정"""
    scene_number: int = Field(..., gt=0, description="씬 번호 (1부터 시작)")
    scenario_notes: str = Field(..., min_length=1, max_length=2000, description="시나리오 수정 내용")


class ScenarioReviseRequest(BaseModel):
    """시나리오 수정 요청"""
    scene_revisions: List[SceneScenarioRevision] = Field(..., min_length=1)
    general_notes: Optional[str] = Field(None, max_length=2000, description="전체 수정 피드백")


class SceneVideoRevision(BaseModel):
    """씬별 영상 수정"""
    scene_number: int = Field(..., gt=0, description="씬 번호 (1부터 시작)")
    video_notes: str = Field(..., min_length=1, max_length=2000, description="영상 수정 내용")


class VideoSceneReviseRequest(BaseModel):
    """영상 씬별 수정 요청"""
    scene_revisions: List[SceneVideoRevision] = Field(..., min_length=1)


class ContentGenerateRequest(BaseModel):
    """콘텐츠 통합 생성 요청"""
    meme_id: Optional[int] = None


class SceneContentRevision(BaseModel):
    """씬별 통합 수정"""
    scene_number: int = Field(..., gt=0, description="씬 번호 (1부터 시작)")
    scenario_notes: Optional[str] = Field(None, max_length=2000, description="시나리오 수정 내용")
    video_notes: Optional[str] = Field(None, max_length=2000, description="영상 수정 내용")


class ContentReviseRequest(BaseModel):
    """콘텐츠 통합 수정 요청"""
    scene_revisions: List[SceneContentRevision] = Field(..., min_length=1)
    general_notes: Optional[str] = Field(None, max_length=2000, description="전체 수정 피드백")


class ContentGenerateResponse(BaseModel):
    """콘텐츠 통합 생성/수정 응답"""
    ad_id: int
    status: str
    message: Optional[str] = None


class AssetsApproveResponse(BaseModel):
    """에셋 통합 승인 응답"""
    status: str
    message: str
    can_proceed: bool


class ContentApproveResponse(BaseModel):
    """컨텐츠 통합 승인 응답"""
    status: str
    message: str
    is_completed: bool


