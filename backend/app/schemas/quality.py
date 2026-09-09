"""
품질 관리 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


# ============= 품질 점수 낮은 영상 =============

class QualityIssue(BaseModel):
    """품질 이슈"""
    category: str
    issue: str
    severity: str
    details: str


class LowQualityVideo(BaseModel):
    """품질 점수 낮은 영상"""
    video_id: int
    title: str
    company_id: int
    company_name: str
    quality_score: int
    quality_issues: List[QualityIssue]
    status: str
    created_at: str
    client_approved: bool
    views: int
    engagement_rate: float


class LowQualityIssueSummary(BaseModel):
    """이슈 요약"""
    category: str
    count: int


class LowQualityVideoSummary(BaseModel):
    """품질 요약"""
    average_quality_score: float
    most_common_issues: List[LowQualityIssueSummary]


class LowQualityVideoResponse(BaseModel):
    """품질 점수 낮은 영상 응답"""
    threshold: int
    total_count: int
    offset: int
    limit: int
    videos: List[LowQualityVideo]
    summary: LowQualityVideoSummary


# ============= 품질 검증 실패 =============

class ValidationDetails(BaseModel):
    """검증 상세"""
    pass


class ValidationFailure(BaseModel):
    """검증 실패"""
    validation_id: int
    video_id: int
    title: str
    company_id: int
    company_name: str
    failure_type: str
    failure_reason: str
    severity: str
    validation_details: Dict
    status: str
    retry_count: int
    created_at: str
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]
    review_note: Optional[str]
    resolved_at: Optional[str]


class ValidationFailureSummary(BaseModel):
    """검증 실패 요약"""
    by_failure_type: Dict[str, int]
    by_status: Dict[str, int]
    by_severity: Dict[str, int]


class ValidationFailureResponse(BaseModel):
    """검증 실패 응답"""
    total_count: int
    offset: int
    limit: int
    failures: List[ValidationFailure]
    summary: ValidationFailureSummary


# ============= 품질 검증 재시도 =============

class RetryValidationRequest(BaseModel):
    """검증 재시도 요청"""
    force_reprocess: bool = True
    skip_checks: Optional[List[str]] = None
    note: Optional[str] = None


class RetryValidationResponse(BaseModel):
    """검증 재시도 응답"""
    validation_id: int
    video_id: int
    status: str
    retry_count: int
    message: str
    estimated_completion: str


# ============= 품질 검증 승인 =============

class ApproveValidationRequest(BaseModel):
    """검증 승인 요청"""
    reason: str
    override_checks: List[str]


class ApproveValidationResponse(BaseModel):
    """검증 승인 응답"""
    validation_id: int
    video_id: int
    status: str
    approved_by: str
    approved_at: str
    message: str


# ============= 품질 트렌드 =============

class QualityTrendPeriod(BaseModel):
    """품질 트렌드 기간"""
    period: str
    average_quality_score: float
    total_videos: int
    validation_failures: int
    failure_rate: float
    most_common_issue: str


class QualityTrendSummary(BaseModel):
    """품질 트렌드 요약"""
    average_quality_score: float
    quality_improvement: float
    average_failure_rate: float
    failure_rate_improvement: float


class QualityTrendResponse(BaseModel):
    """품질 트렌드 응답"""
    period: Dict[str, str]
    granularity: str
    trends: List[QualityTrendPeriod]
    summary: QualityTrendSummary
