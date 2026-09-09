"""
비용 관리 관련 Pydantic 스키마
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ============= 회사별 비용 =============

class CompanyCosts(BaseModel):
    """회사 비용"""
    character_generation: int
    voice_synthesis: int
    video_rendering: int
    storage: int
    api_calls: int
    total: int


class CompanyUsage(BaseModel):
    """회사 사용량"""
    total_videos: int
    total_characters: int
    total_duration_minutes: int
    storage_gb: float


class CompanyComparison(BaseModel):
    """회사 비교"""
    previous_month_total: int
    growth_rate: float


class CompanyCostItem(BaseModel):
    """회사별 비용 항목"""
    company_id: int
    company_name: str
    costs: CompanyCosts
    usage: CompanyUsage
    average_cost_per_video: int
    comparison: CompanyComparison


class CompanyCostSummary(BaseModel):
    """비용 요약"""
    total_cost_all_companies: int
    average_cost_per_company: int
    highest_cost_company: Dict[str, Any]


class CompanyCostResponse(BaseModel):
    """회사별 비용 응답"""
    period: Dict[str, int]
    total_companies: int
    companies: List[CompanyCostItem]
    summary: CompanyCostSummary


# ============= 전체 비용 통계 =============

class TotalCosts(BaseModel):
    """전체 비용"""
    character_generation: int
    voice_synthesis: int
    video_rendering: int
    storage: int
    api_calls: int
    total: int


class CostBreakdownPercentage(BaseModel):
    """비용 비율"""
    character_generation: float
    voice_synthesis: float
    video_rendering: float
    storage: float
    api_calls: float


class UsageStatistics(BaseModel):
    """사용량 통계"""
    total_videos: int
    total_characters: int
    total_duration_minutes: int
    total_storage_gb: int
    total_api_calls: int


class CostAverages(BaseModel):
    """평균 비용"""
    cost_per_video: int
    cost_per_minute: int
    cost_per_character: int


class CostTrendPoint(BaseModel):
    """비용 트렌드 포인트"""
    date: str
    total_cost: int
    video_count: int


class CostComparison(BaseModel):
    """비용 비교"""
    previous_period_total: int
    growth_rate: float
    cost_efficiency_improvement: float


class CostStatisticsResponse(BaseModel):
    """비용 통계 응답"""
    period: Dict[str, str]
    total_costs: TotalCosts
    cost_breakdown_percentage: CostBreakdownPercentage
    usage_statistics: UsageStatistics
    averages: CostAverages
    trends: List[CostTrendPoint]
    comparison: CostComparison


# ============= 비용 상세 내역 =============

class CostDetailItem(BaseModel):
    """비용 상세 항목"""
    cost_id: int
    company_id: int
    company_name: str
    video_id: int
    video_title: str
    cost_type: str
    amount: int
    details: Dict
    created_at: str


class CostDetailsResponse(BaseModel):
    """비용 상세 응답"""
    total_count: int
    offset: int
    limit: int
    details: List[CostDetailItem]


# ============= 비용 최적화 제안 =============

class OptimizationSuggestion(BaseModel):
    """최적화 제안"""
    suggestion_id: int
    company_id: int
    company_name: str
    category: str
    title: str
    description: str
    current_cost: int
    optimized_cost: int
    potential_savings: int
    savings_percentage: float
    implementation_effort: str
    affected_videos: int


class OptimizationResponse(BaseModel):
    """최적화 제안 응답"""
    total_potential_savings: int
    suggestions: List[OptimizationSuggestion]
