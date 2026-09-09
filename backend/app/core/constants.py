"""애플리케이션 상수"""
from enum import StrEnum


class AdStatus(StrEnum):
    DRAFT = "draft"
    GENERATING_CHARACTER = "generating_character"
    GENERATING_SCENARIO = "generating_scenario"
    GENERATING_VIDEO = "generating_video"
    GENERATING_VOICE = "generating_voice"
    CONTENT_GENERATING = "content_generating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    COMPLETED = "completed"


class VideoStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CLIENT_APPROVED = "client_approved"
    ADMIN_APPROVED = "admin_approved"
    ADMIN_REJECTED = "admin_rejected"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


# 워크플로우 단계별 진행률
WORKFLOW_PROGRESS = {
    "character_start": 10,
    "voice_start": 20,
    "character_review": 30,
    "assets_approved": 40,
    "scenario_start": 50,
    "scenario_done": 60,
    "video_start": 70,
    "content_review": 85,
    "video_approved": 90,
    "completed": 100,
}

# 생성 중 상태 (중복 요청 방지용)
GENERATING_STATUSES = frozenset({
    AdStatus.GENERATING_CHARACTER,
    AdStatus.GENERATING_SCENARIO,
    AdStatus.GENERATING_VIDEO,
    AdStatus.GENERATING_VOICE,
    AdStatus.CONTENT_GENERATING,
})
