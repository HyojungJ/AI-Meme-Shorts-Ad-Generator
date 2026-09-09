"""
사용자 관리 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ============= 사용자 목록 =============

class UserListItem(BaseModel):
    """사용자 목록 항목"""
    account_id: int
    email: str
    member_name: Optional[str]
    account_type: str
    status: str
    company_id: Optional[int]
    company_name: Optional[str]
    department: Optional[str]
    role: Optional[str]
    created_at: str
    last_login_at: Optional[str]
    video_count: int


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    total_count: int
    offset: int
    limit: int
    users: List[UserListItem]


# ============= 사용자 상세 =============

class UserCompanyInfo(BaseModel):
    """사용자 회사 정보"""
    company_id: int
    company_name: str
    role: str
    joined_at: str


class UserProfile(BaseModel):
    """사용자 프로필"""
    phone: Optional[str]
    department: Optional[str]
    position: Optional[str]


class UserStatistics(BaseModel):
    """사용자 통계"""
    total_videos: int
    total_views: int
    total_projects: int
    active_projects: int
    average_engagement_rate: float


class UserActivity(BaseModel):
    """사용자 활동"""
    created_at: str
    last_login_at: Optional[str]
    last_video_created_at: Optional[str]
    login_count: int


class UserVerification(BaseModel):
    """사용자 인증 정보"""
    is_email_verified: bool
    email_verified_at: Optional[str]
    is_phone_verified: bool


class RecentVideo(BaseModel):
    """최근 영상"""
    video_id: int
    title: str
    status: str
    views: int
    created_at: str


class UserDetailResponse(BaseModel):
    """사용자 상세 정보 응답"""
    account_id: int
    email: str
    name: str
    account_type: str
    company: Optional[UserCompanyInfo]
    profile: UserProfile
    statistics: UserStatistics
    activity: UserActivity
    recent_videos: List[RecentVideo]


# ============= 사용자 상태 변경 =============

class UpdateStatusRequest(BaseModel):
    """상태 변경 요청"""
    status: str = Field(..., description="active, inactive, suspended")
    reason: Optional[str] = None
    notify_user: bool = False


class UpdateStatusResponse(BaseModel):
    """상태 변경 응답"""
    account_id: int
    status: str
    previous_status: str
    is_active: bool
    changed_at: str
    changed_by: str
    reason: Optional[str]
    message: str


# ============= 사용자 권한 변경 =============

class UpdateRoleRequest(BaseModel):
    """권한 변경 요청"""
    company_id: int
    role: str = Field(..., description="manager, member")
    reason: Optional[str] = None


class UpdateRoleResponse(BaseModel):
    """권한 변경 응답"""
    account_id: int
    company_id: int
    role: str
    previous_role: str
    changed_at: str
    changed_by: str
    reason: Optional[str]
    message: str


# ============= 활동 로그 =============

class ActivityLogItem(BaseModel):
    """활동 로그 항목"""
    log_id: int
    action_type: str
    action_description: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: dict
    ip_address: str
    user_agent: str
    created_at: str


class ActivityLogResponse(BaseModel):
    """활동 로그 응답"""
    account_id: int
    total_count: int
    offset: int
    limit: int
    logs: List[ActivityLogItem]


# ============= 사용자 삭제 =============

class DeleteUserRequest(BaseModel):
    """사용자 삭제 요청"""
    confirmation: str = Field(..., description="반드시 'DELETE' 입력")
    reason: str
    delete_videos: bool = False


class DeleteUserResponse(BaseModel):
    """사용자 삭제 응답"""
    account_id: int
    status: str
    deleted_at: str
    deleted_by: str
    videos_deleted: bool
    message: str


# ============= 사용자 통계 =============

class UserStatisticsByType(BaseModel):
    """계정 유형별 통계"""
    client: int
    admin: int


class UserStatisticsByRole(BaseModel):
    """권한별 통계"""
    manager: int
    member: int


class UserEngagement(BaseModel):
    """사용자 참여도"""
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    average_videos_per_user: float


class TopActiveUser(BaseModel):
    """상위 활성 사용자"""
    account_id: int
    name: str
    company_name: str
    total_videos: int
    total_views: int


class UserStatisticsResponse(BaseModel):
    """사용자 통계 응답"""
    period: dict
    total_users: int
    active_users: int
    inactive_users: int
    new_users_this_period: int
    user_growth_rate: float
    by_account_type: UserStatisticsByType
    by_role: UserStatisticsByRole
    engagement: UserEngagement
    top_active_users: List[TopActiveUser]


# ============= 대량 작업 =============

class BulkActionRequest(BaseModel):
    """대량 작업 요청"""
    action: str = Field(..., description="activate, deactivate, send_notification")
    account_ids: List[int]
    reason: Optional[str] = None
    notify_users: bool = False


class BulkActionResponse(BaseModel):
    """대량 작업 응답"""
    action: str
    total_requested: int
    success_count: int
    failed_count: int
    errors: List[str]
    changed_by: str
    reason: Optional[str]
    message: str
