"""
성과 분석 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============= 대시보드 =============

class PeriodInfo(BaseModel):
    """기간 정보"""
    from_date: str = Field(..., alias="from")
    to: str


class DashboardSummary(BaseModel):
    """대시보드 요약 정보"""
    total_videos: int
    total_views: int
    total_likes: int
    total_comments: int
    total_shares: int
    average_engagement_rate: float
    average_view_duration_seconds: float
    total_companies: int
    active_companies: int


class DashboardTrends(BaseModel):
    """대시보드 트렌드"""
    views_growth: float
    engagement_growth: float
    video_count_growth: float


class TopPerformingVideo(BaseModel):
    """상위 성과 영상"""
    video_id: int
    title: str
    company_name: Optional[str] = None
    views: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    published_at: Optional[str] = None


class TopCompany(BaseModel):
    """상위 성과 회사"""
    company_id: int
    company_name: str
    total_videos: int
    total_views: int
    average_engagement_rate: float


class DashboardResponse(BaseModel):
    """대시보드 응답"""
    period: PeriodInfo
    summary: DashboardSummary
    trends: DashboardTrends
    top_performing_videos: List[TopPerformingVideo]
    top_companies: List[TopCompany]
    top_category: Optional[str] = None
    top_meme_type: Optional[str] = None


# ============= 밈별 성과 =============

class TopPerformingVideoInMeme(BaseModel):
    """밈 내 최고 성과 영상"""
    video_id: int
    title: str
    views: int
    engagement_rate: float


class MemePerformance(BaseModel):
    """밈 성과"""
    meme_id: int
    meme_name: str
    category: str
    usage_count: int
    total_views: int
    average_views_per_video: int
    average_engagement_rate: float
    average_view_duration: float
    top_performing_video: TopPerformingVideoInMeme


class MemePerformanceResponse(BaseModel):
    """밈별 성과 응답"""
    period: PeriodInfo
    memes: List[MemePerformance]
    total_memes_used: int


# ============= 카테고리별 성과 =============

class TopMemeInCategory(BaseModel):
    """카테고리 내 상위 밈"""
    meme_name: str
    usage_count: int
    average_engagement_rate: float


class CategoryPerformance(BaseModel):
    """카테고리 성과"""
    category: str
    video_count: int
    total_views: int
    average_engagement_rate: float
    top_memes: List[TopMemeInCategory]


class CategoryPerformanceResponse(BaseModel):
    """카테고리별 성과 응답"""
    period: PeriodInfo
    categories: List[CategoryPerformance]


# ============= 시계열 트렌드 =============

class TrendDataPoint(BaseModel):
    """트렌드 데이터 포인트"""
    date: str
    value: float
    video_count: int


class TrendPeak(BaseModel):
    """트렌드 최고/최저점"""
    date: str
    value: float


class TrendSummary(BaseModel):
    """트렌드 요약"""
    total: float
    average: float
    peak: TrendPeak
    lowest: TrendPeak


class TrendInsight(BaseModel):
    """트렌드 인사이트"""
    type: str  # 'positive', 'negative', 'neutral'
    title: str
    description: str


class TrendResponse(BaseModel):
    """시계열 트렌드 응답"""
    period: PeriodInfo
    granularity: str
    metric: str
    data_points: List[TrendDataPoint]
    summary: TrendSummary
    insights: List[TrendInsight] = []


# ============= 데이터 내보내기 =============

class ExportFilters(BaseModel):
    """내보내기 필터"""
    company_ids: Optional[List[int]] = None
    meme_categories: Optional[List[str]] = None


class ExportRequest(BaseModel):
    """데이터 내보내기 요청"""
    report_type: str = Field(..., description="리포트 유형")
    date_from: str
    date_to: str
    format: str = Field(..., description="파일 형식 (csv, excel)")
    include_details: bool = True
    filters: Optional[ExportFilters] = None


class ExportResponse(BaseModel):
    """데이터 내보내기 응답"""
    export_id: str
    status: str
    estimated_completion: str
    message: str


class ExportStatusResponse(BaseModel):
    """내보내기 상태 응답"""
    export_id: str
    status: str
    download_url: Optional[str] = None
    file_size_mb: Optional[float] = None
    expires_at: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# ============= 회사별 성과 =============

class BestPerformingVideo(BaseModel):
    """최고 성과 영상"""
    video_id: int
    title: str
    views: int
    engagement_rate: float


class CompanyPerformance(BaseModel):
    """회사 성과"""
    company_id: int
    company_name: str
    total_videos: int
    total_views: int
    total_engagement: int
    average_engagement_rate: float
    average_views_per_video: int
    most_used_meme: str
    best_performing_video: BestPerformingVideo


class CompanyPerformanceResponse(BaseModel):
    """회사별 성과 응답"""
    period: PeriodInfo
    companies: List[CompanyPerformance]
    total_companies: int
