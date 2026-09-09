export type VideoStatus =
  | 'pending'
  | 'pending_approval'
  | 'generating_character'
  | 'character_generating'
  | 'character_review'
  | 'voice_generating'
  | 'voice_review'
  | 'asset_generating'
  | 'asset_pending'
  | 'asset_approved'
  | 'scenario_generating'
  | 'scenario_review'
  | 'content_generating'
  | 'content_pending'
  | 'video_generating'
  | 'video_review'
  | 'completed'
  | 'client_approved'
  | 'client_rejected'
  | 'admin_approved'
  | 'admin_rejected'
  | 'published'
  | 'processing'
  | 'failed'

export type AdminRequestStatus = 'pending' | 'character' | 'voice' | 'scenario' | 'review' | 'video' | 'completed' | 'error'

// 밈 타입
export type MemeType = 'dudungtak' | 'must-buy' | 'real-review' | 'mz-flex' | 'asmr-unboxing' | 'before-after'

export interface SceneData {
  scene_number: number
  content: string
  timestamp?: string
}

export interface ScenarioVersion {
  script_id: number
  ad_id: number
  title: string
  generation_type: 'initial' | 'regenerated' | 'revised'
  approval_status: 'pending' | 'approved' | 'rejected'
  quality_check_passed: boolean
  quality_issues: string[]
  review_result: Record<string, unknown> | null
  revision_notes?: string
  created_at: string
  scenes?: SceneData[]
}

export interface Video {
  id: string
  title: string
  status: VideoStatus
  views: number
  createdAt: string
  companyName?: string
  productCategory?: string
  productHighlight?: string
  productImageUrl?: string
  memeType?: MemeType
  characterImagePrompt?: string
  characterVoicePrompt?: string
  characterRevisionHistory?: Array<{ feedback_type: string; revision_notes: string; requested_at: string }>
  characterImageUrl?: string
  sceneImageUrl?: string
  voiceSampleUrl?: string
  scenario?: string
  characterId?: number
  videoId?: number
  scriptId?: number
  videoUrl?: string
  progressPercentage?: number
  scenes?: SceneData[]
}

export interface AdminRequest {
  id: string
  adId?: number
  companyName: string
  productName: string
  status: AdminRequestStatus
  createdAt: string
  updatedAt: string
  error?: string
}

export interface VideoRequestFormData {
  companyName: string
  productName: string
  productCategory: string
  productHighlight: string
}

export interface User {
  user_id: number
  email: string
  name: string
  companyName?: string
  department?: string
  role?: 'manager' | 'member'
  profile_img?: string | null
  is_admin?: boolean
  access_token?: string
  createdAt?: string
}

// 영상 성과 지표
export interface VideoMetrics {
  views: number
  likes: number
  comments: number
  shares: number
  watchTime: number // 평균 시청 시간 (초)
  completionRate: number // 시청 완료율 (%)
  engagementRate: number // 참여율 (%)
  dailyViews: { date: string; views: number }[]
  hourlyViews: { hour: number; views: number }[]
}

// 확장된 영상 타입 (성과 포함)
export interface VideoWithMetrics extends Video {
  memeType?: MemeType
  metrics?: VideoMetrics
}

// 밈별 성과
export interface MemePerformance {
  memeType: MemeType
  label: string
  videoCount: number
  totalViews: number
  avgViews: number
  avgCompletionRate: number
  avgEngagementRate: number
}

// 카테고리별 성과
export interface CategoryPerformance {
  category: string
  videoCount: number
  totalViews: number
  avgViews: number
  avgEngagementRate: number
  topMemeType: MemeType
  trend: 'up' | 'down' | 'stable'
}

// 트렌드 데이터
export interface TrendDataPoint {
  date: string
  views: number
  engagement: number
  predicted?: boolean
}

export interface TrendInsight {
  type: 'positive' | 'negative' | 'neutral'
  title: string
  description: string
}

// 분석 요약
export interface AnalyticsSummary {
  totalVideos: number
  totalViews: number
  avgEngagement: number
  topCategory: string
  topMemeType: string
  viewsChange: number // 전주 대비 변화율 (%)
  engagementChange: number
}

// ============================================
// Backend API Response Types
// ============================================

// Auth
export interface TokenResponse {
  access_token: string
  refresh_token: string
  account_id: number
  email: string
  account_type: 'client' | 'admin'
  company_id: number | null
  role: string | null
}

export interface BackendUser {
  account_id: number
  email: string
  member_name?: string
  company_name?: string
  department?: string
  role?: 'manager' | 'member'
  account_type: 'client' | 'admin'
  created_at: string
  profile_img?: string | null
}

// Video/Workflow
export interface MyProjectWorkflowResponse {
  ad_id: number
  item_name?: string
  status: string
  current_stage?: string
  created_at: string
  character_id?: number
  scene_image_url?: string
}

export interface WorkflowStatusResponse {
  execution_id: string
  ad_id: number
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current_stage: string
  progress_percentage: number
  created_at: string
  completed_at: string | null
  error_message: string | null
  retry_count: number
}

export interface WorkflowDetailResponse extends WorkflowStatusResponse {
  stages: WorkflowStage[]
}

export interface WorkflowStage {
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export interface CharacterResponse {
  character_id: number
  image_url: string
  is_active: boolean
  created_at: string
  image_prompt?: string | null
}

export interface ProjectResponse {
  ad_id: number
  title: string
  status: string
  company_name: string
  product_category: string
  product_highlight: string
  product_image_url: string | null
  character_style: string
  meme_type: string
  created_at: string
  updated_at: string
  views: number
  character_image_url: string | null
  voice_sample_url: string | null
  video_url: string | null
}

export interface ScenarioResponse {
  scenario_id: number
  ad_id: number
  content: string
  version: number
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  feedback: string | null
}

// Admin
export interface AdminVideoResponse {
  ad_id: number
  title: string
  company_name: string
  status: string
  created_at: string
  published_at: string | null
  youtube_url: string | null
  views: number
}

export interface AdminWorkflowResponse {
  execution_id: string
  ad_id: number
  title: string
  company_id: number
  company_name: string
  status: string
  current_stage: string
  progress_percentage: number
  created_at: string
  error_message: string | null
  retry_count: number
}

export interface AdminUserResponse {
  account_id: number
  email: string
  account_type: 'client' | 'admin'
  // flat structure (from list API)
  member_name?: string
  company_name?: string
  department?: string
  status?: 'active' | 'inactive' | 'suspended'
  created_at?: string
  last_login_at?: string | null
  video_count?: number
  // nested structure (from detail API)
  name?: string
  is_active?: boolean
  company?: {
    company_id: number
    company_name: string
    role: string
    joined_at: string
  }
  profile?: {
    phone: string | null
    department: string | null
    position: string | null
  }
  statistics?: {
    total_videos: number
    total_views: number
    total_projects: number
    active_projects: number
    average_engagement_rate: number
  }
  activity?: {
    created_at: string
    last_login_at: string | null
    last_video_created_at: string | null
    login_count: number
  }
  recent_videos?: Array<{
    video_id: number
    title: string
    status: string
    views: number
    created_at: string
  }>
}

// Analytics
export interface AnalyticsDashboardResponse {
  total_videos: number
  total_views: number
  avg_engagement_rate: number
  active_users: number
  videos_this_week: number
  views_change_percent: number
  engagement_change_percent: number
}

export interface MemePerformanceResponse {
  meme_type: string
  label: string
  video_count: number
  total_views: number
  avg_views: number
  avg_completion_rate: number
  avg_engagement_rate: number
}

export interface CategoryPerformanceResponse {
  category: string
  video_count: number
  total_views: number
  avg_views: number
  avg_engagement_rate: number
  top_meme_type: string
  trend: 'up' | 'down' | 'stable'
}

export interface TrendResponse {
  date: string
  views: number
  engagement: number
  predicted?: boolean
}

// Costs
export interface CostStatisticsResponse {
  total_cost: number
  avg_cost_per_video: number
  cost_by_stage: Record<string, number>
  monthly_costs: { month: string; cost: number }[]
}

export interface CompanyCostResponse {
  company_id: number
  company_name: string
  total_videos: number
  total_cost: number
  avg_cost_per_video: number
}

// Quality
export interface LowQualityVideoResponse {
  ad_id: number
  title: string
  company_name: string
  quality_score: number
  issues: string[]
  created_at: string
}

export interface ValidationFailureResponse {
  validation_id: number
  ad_id: number
  title: string
  stage: string
  failure_reason: string
  created_at: string
  retry_count: number
}

// Pagination wrapper
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

// Paginated Meme Performance (for analytics)
export interface PaginatedMemePerformance {
  items: MemePerformance[]
  total: number
  page: number
  totalPages: number
}

// Paginated Category Performance (for analytics)
export interface PaginatedCategoryPerformance {
  items: CategoryPerformance[]
  total: number
  page: number
  totalPages: number
}

// Sort options for analytics
export type MemeSortBy = 'avgViews' | 'avgCompletionRate' | 'avgEngagementRate' | 'videoCount' | 'totalViews'
export type CategorySortBy = 'avgViews' | 'avgEngagementRate' | 'videoCount' | 'totalViews'
export type SortOrder = 'asc' | 'desc'

// Workflow Detail (신청 내용 + 수정 이력)
export interface WorkflowDetailData {
  ad_request: {
    ad_id: number
    item_name: string
    item_category: string | null
    item_url: string | null
    item_images: string[]
    item_description: string | null
    character_image_prompt: string | null
    character_voice_prompt: string | null
    meme_name: string | null
    status: string
    created_at: string | null
  } | null
  revision_history: {
    scenarios: Array<{
      script_id: number
      title: string
      generation_type: string
      approval_status: string
      quality_check_passed: boolean
      quality_issues: string[]
      review_result: Record<string, unknown> | null
      created_at: string | null
    }>
    videos: Array<{
      video_id: number
      title: string
      status: string
      rejection_reason: string | null
      rejected_at: string | null
      review_result: Record<string, unknown> | null
      created_at: string | null
    }>
  }
}
