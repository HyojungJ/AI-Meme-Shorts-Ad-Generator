import { api, MOCK_MODE } from '../client'
import { mockData, memePerformanceData, categoryPerformanceData, trendData, getVideos } from '../mock'
import type {
  MemePerformance,
  CategoryPerformance,
} from '@/types'

export interface ClientDashboardResponse {
  period: { from: string; to: string }
  summary: {
    total_projects: number
    completed_projects: number
    processing_projects: number
    total_videos: number
    published_videos: number
    total_views: number
    total_likes: number
    total_comments: number
    avg_engagement_rate: number
    total_cost_usd: number
    completion_rate: number
  }
  status_distribution: Record<string, number>
  views_timeline: { date: string; views: number }[]
  engagement_timeline: { date: string; engagement_rate: number }[]
  recent_videos: {
    video_id: number
    title: string
    status: string
    created_at: string
    views: number
    likes: number
    engagement_rate: number
  }[]
}

export interface VideoPerformanceResponse {
  video_id: number
  title: string
  status: string
  created_at: string
  duration_seconds: number | null
  latest_performance: {
    views: number
    likes: number
    dislikes: number
    comments: number
    shares: number
    engagement_rate: number
    watch_time_seconds: number
    average_view_duration: number
    captured_at: string | null
  }
  timeline: {
    captured_at: string
    views: number
    likes: number
    comments: number
    shares: number
    engagement_rate: number
  }[]
  hourly_views: {
    hour: number
    views: number
  }[]
}

export const clientAnalyticsApi = {
  async getDashboard(dateFrom?: string, dateTo?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const videos = getVideos()
      const completedCount = videos.filter(v => v.status === 'completed').length
      const processingStatuses = ['character_generating', 'voice_generating', 'scenario_generating', 'video_generating', 'content_generating', 'asset_generating']
      const processingCount = videos.filter(v => processingStatuses.includes(v.status)).length
      const reviewStatuses = ['character_review', 'voice_review', 'scenario_review', 'video_review']
      const reviewCount = videos.filter(v => reviewStatuses.includes(v.status)).length
      const pendingCount = videos.filter(v => v.status === 'pending').length
      const failedCount = videos.filter(v => v.status === 'failed').length
      return {
        period: { from: '2026-01-01', to: '2026-01-26' },
        summary: {
          total_projects: videos.length,
          completed_projects: completedCount,
          processing_projects: processingCount,
          total_videos: completedCount,
          published_videos: completedCount,
          total_views: 125000,
          total_likes: 8500,
          total_comments: 1200,
          avg_engagement_rate: 4.2,
          total_cost_usd: 450.0,
          completion_rate: videos.length > 0 ? Math.round((completedCount / videos.length) * 100) : 0,
        },
        status_distribution: {
          completed: completedCount,
          processing: processingCount,
          review: reviewCount,
          pending: pendingCount,
          failed: failedCount,
        },
        views_timeline: mockData.dailyStats.map((d) => ({ date: d.date, views: d.views })),
        engagement_timeline: mockData.dailyStats.map((d) => ({ date: d.date, engagement_rate: d.engagement })),
        recent_videos: videos.slice(0, 5).map((v) => ({
          video_id: parseInt(v.id),
          title: v.title,
          status: v.status,
          created_at: v.createdAt,
          views: v.views,
          likes: Math.floor(v.views * 0.05),
          engagement_rate: 4.2,
        })),
      } as ClientDashboardResponse
    }

    const params = new URLSearchParams()
    if (dateFrom) params.append('date_from', dateFrom)
    if (dateTo) params.append('date_to', dateTo)
    const query = params.toString() ? `?${params}` : ''
    return api.get<ClientDashboardResponse>(`/api/v1/analytics/dashboard${query}`)
  },

  async getVideoPerformance(videoId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        video_id: videoId,
        title: '테스트 영상',
        status: 'completed',
        created_at: '2026-01-15T00:00:00',
        duration_seconds: 60,
        latest_performance: {
          views: 5000,
          likes: 250,
          dislikes: 10,
          comments: 80,
          shares: 30,
          engagement_rate: 4.5,
          watch_time_seconds: 45,
          average_view_duration: 45,
          captured_at: '2026-01-26T00:00:00',
        },
        timeline: [],
        hourly_views: Array.from({ length: 24 }, (_, hour) => ({
          hour,
          views: Math.floor(Math.random() * 500)
        }))
      } as VideoPerformanceResponse
    }

    return api.get<VideoPerformanceResponse>(`/api/v1/analytics/videos/${videoId}`)
  },

  async getSummary() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      const videos = getVideos()
      const completedCount = videos.filter(v => v.status === 'completed').length
      return {
        total_projects: videos.length,
        completed_projects: completedCount,
        total_videos: completedCount,
        total_cost_usd: 450.0,
      }
    }

    return api.get<{ total_projects: number; completed_projects: number; total_videos: number; total_cost_usd: number }>('/api/v1/analytics/summary')
  },

  // 사용자용 밈별 분석
  async getMyMemes() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return memePerformanceData
    }

    const response = await api.get<Array<{
      meme_id: number
      meme_name: string
      meme_type: string
      video_count: number
      total_views: number
      avg_views: number
    }>>('/api/v1/analytics/memes')

    return response.map(m => ({
      memeType: m.meme_type as MemePerformance['memeType'],
      label: m.meme_name,
      videoCount: m.video_count,
      totalViews: m.total_views,
      avgViews: m.avg_views,
      avgCompletionRate: 0,
      avgEngagementRate: 0,
    }))
  },

  // 사용자용 카테고리별 분석
  async getMyCategories() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return categoryPerformanceData
    }

    const response = await api.get<Array<{
      category: string
      video_count: number
      total_views: number
      avg_views: number
    }>>('/api/v1/analytics/categories')

    return response.map(c => ({
      category: c.category,
      videoCount: c.video_count,
      totalViews: c.total_views,
      avgViews: c.avg_views,
      avgEngagementRate: 0,
      topMemeType: 'unknown' as CategoryPerformance['topMemeType'],
      trend: 'stable' as const,
    }))
  },

  // 사용자용 트렌드 분석
  async getMyTrends() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { data: trendData, insights: [] }
    }

    const response = await api.get<{
      data: Array<{ date: string; views: number }>
      insights: Array<{ type: string; title: string; description: string }>
    }>('/api/v1/analytics/trends')

    return {
      data: response.data.map(t => ({
        date: t.date,
        views: t.views,
        engagement: 0,
        predicted: false,
      })),
      insights: response.insights.map(i => ({
        type: i.type as 'positive' | 'negative' | 'neutral',
        title: i.title,
        description: i.description,
      })),
    }
  },
}
