import { api, MOCK_MODE } from '../client'
import { mockData, memePerformanceData, categoryPerformanceData, trendData, analyticsSummary, getVideos } from '../mock'
import { generateInsights } from './insights'
import type {
  MemePerformanceResponse,
  PaginatedResponse,
  MemePerformance,
  CategoryPerformance,
  PaginatedMemePerformance,
  PaginatedCategoryPerformance,
  MemeSortBy,
  CategorySortBy,
  SortOrder,
} from '@/types'

export const analyticsApi = {
  async getDashboard() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return analyticsSummary
    }

    const response = await api.get<{
      period: { from: string; to: string }
      summary: {
        total_videos: number
        total_views: number
        average_engagement_rate: number
        total_companies: number
      }
      trends: {
        views_growth: number
        engagement_growth: number
      }
      top_category: string | null
      top_meme_type: string | null
    }>('/api/v1/admin/analytics/dashboard')
    return {
      totalVideos: response.summary?.total_videos || 0,
      totalViews: response.summary?.total_views || 0,
      avgEngagement: response.summary?.average_engagement_rate || 0,
      topCategory: response.top_category || '-',
      topMemeType: response.top_meme_type || 'unknown',
      viewsChange: response.trends?.views_growth || 0,
      engagementChange: response.trends?.engagement_growth || 0,
    }
  },

  async getMemePerformance(params?: {
    page?: number
    limit?: number
    sortBy?: MemeSortBy
    sortOrder?: SortOrder
    search?: string
  }): Promise<PaginatedMemePerformance> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      let data = [...memePerformanceData]

      // 검색
      if (params?.search) {
        const searchLower = params.search.toLowerCase()
        data = data.filter(m => m.label.toLowerCase().includes(searchLower))
      }

      // 정렬
      if (params?.sortBy) {
        data.sort((a, b) => {
          const aVal = a[params.sortBy!]
          const bVal = b[params.sortBy!]
          return params.sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        })
      }

      // 페이지네이션
      const page = params?.page || 1
      const limit = params?.limit || 10
      const start = (page - 1) * limit
      const total = data.length

      return {
        items: data.slice(start, start + limit),
        total,
        page,
        totalPages: Math.ceil(total / limit),
      }
    }

    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.limit) queryParams.append('limit', String(params.limit))
    if (params?.sortBy) {
      const sortByMap: Record<string, string> = {
        'avgViews': 'views',
        'avgCompletionRate': 'completion_rate',
        'avgEngagementRate': 'engagement_rate',
        'videoCount': 'video_count',
        'totalViews': 'total_views',
      }
      queryParams.append('sort_by', sortByMap[params.sortBy] || params.sortBy)
    }
    if (params?.sortOrder) queryParams.append('sort_order', params.sortOrder)
    if (params?.search) queryParams.append('search', params.search)
    const query = queryParams.toString() ? `?${queryParams}` : ''

    const response = await api.get<{
      items: Array<{
        meme_id: number
        meme_name: string
        category: string
        usage_count: number
        total_views: number
        average_views_per_video: number
        average_engagement_rate: number
        average_view_duration: number
        top_performing_video: unknown
      }>
      total: number
      page: number
      total_pages: number
    }>(`/api/v1/admin/analytics/memes${query}`)

    return {
      items: (response.items || []).map(m => ({
        memeType: (m.category || 'quotable') as MemePerformance['memeType'],
        label: m.meme_name || '',
        videoCount: m.usage_count || 0,
        totalViews: m.total_views || 0,
        avgViews: m.average_views_per_video || 0,
        avgCompletionRate: 0,
        avgEngagementRate: m.average_engagement_rate || 0,
      })),
      total: response.total || response.items?.length || 0,
      page: response.page || 1,
      totalPages: response.total_pages || 1,
    }
  },

  // Top N 밈 가져오기 (차트용)
  async getTopMemes(limit = 10, sortBy: MemeSortBy = 'avgViews'): Promise<MemePerformance[]> {
    const result = await this.getMemePerformance({
      page: 1,
      limit,
      sortBy,
      sortOrder: 'desc',
    })
    return result.items
  },

  async getCategoryPerformance(params?: {
    page?: number
    limit?: number
    sortBy?: CategorySortBy
    sortOrder?: SortOrder
    search?: string
  }): Promise<PaginatedCategoryPerformance> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      let data = [...categoryPerformanceData]

      // 검색
      if (params?.search) {
        const searchLower = params.search.toLowerCase()
        data = data.filter(c => c.category.toLowerCase().includes(searchLower))
      }

      // 정렬
      if (params?.sortBy) {
        data.sort((a, b) => {
          const aVal = a[params.sortBy!]
          const bVal = b[params.sortBy!]
          return params.sortOrder === 'asc' ? aVal - bVal : bVal - aVal
        })
      }

      // 페이지네이션
      const page = params?.page || 1
      const limit = params?.limit || 10
      const start = (page - 1) * limit
      const total = data.length

      return {
        items: data.slice(start, start + limit),
        total,
        page,
        totalPages: Math.ceil(total / limit),
      }
    }

    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', String(params.page))
    if (params?.limit) queryParams.append('limit', String(params.limit))
    if (params?.sortBy) {
      const sortByMap: Record<string, string> = {
        'avgViews': 'views',
        'avgCompletionRate': 'completion_rate',
        'avgEngagementRate': 'engagement_rate',
        'videoCount': 'video_count',
        'totalViews': 'total_views',
      }
      queryParams.append('sort_by', sortByMap[params.sortBy] || params.sortBy)
    }
    if (params?.sortOrder) queryParams.append('sort_order', params.sortOrder)
    if (params?.search) queryParams.append('search', params.search)
    const query = queryParams.toString() ? `?${queryParams}` : ''

    const response = await api.get<{
      period: { from: string; to: string }
      categories: Array<{
        category: string
        video_count: number
        total_views: number
        average_engagement_rate: number
        top_memes: Array<{ meme_name: string; usage_count: number; average_engagement_rate: number }>
      }>
      total: number
      page: number
      total_pages: number
    }>(`/api/v1/admin/analytics/categories${query}`)

    return {
      items: (response.categories || []).map(c => ({
        category: c.category || '',
        videoCount: c.video_count || 0,
        totalViews: c.total_views || 0,
        avgViews: Math.round((c.total_views || 0) / Math.max(c.video_count || 1, 1)),
        avgEngagementRate: c.average_engagement_rate || 0,
        topMemeType: (c.top_memes?.[0]?.meme_name || 'unknown') as CategoryPerformance['topMemeType'],
        trend: 'stable' as const,
      })),
      total: response.total || response.categories?.length || 0,
      page: response.page || 1,
      totalPages: response.total_pages || 1,
    }
  },

  // Top N 카테고리 가져오기 (차트용)
  async getTopCategories(limit = 10, sortBy: CategorySortBy = 'avgViews'): Promise<CategoryPerformance[]> {
    const result = await this.getCategoryPerformance({
      page: 1,
      limit,
      sortBy,
      sortOrder: 'desc',
    })
    return result.items
  },

  async getTrends(period: 'week' | 'month' | 'quarter' = 'month') {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      // 동적 인사이트 생성
      const insights = generateInsights(
        memePerformanceData,
        categoryPerformanceData,
        trendData,
        { viewsChange: analyticsSummary.viewsChange, totalViews: analyticsSummary.totalViews }
      )
      return { data: trendData, insights }
    }

    const response = await api.get<{
      period: { from: string; to: string }
      granularity: string
      metric: string
      data_points: Array<{ date: string; value: number; predicted?: boolean }>
      summary: { total: number; average: number }
      insights?: Array<{ type: string; title: string; description: string }>
    }>(`/api/v1/admin/analytics/trends?period=${period}`)

    return {
      data: (response.data_points || []).map(t => ({
        date: t.date,
        views: t.value || 0,
        engagement: 0,
        predicted: t.predicted || false,
      })),
      insights: (response.insights || []).map(i => ({
        type: i.type as 'positive' | 'negative' | 'neutral',
        title: i.title,
        description: i.description,
      })),
    }
  },

  async exportData(params: {
    report_type: 'dashboard' | 'memes' | 'categories' | 'companies' | 'videos'
    date_from: string
    date_to: string
    format: 'csv' | 'excel'
    include_details?: boolean
    filters?: {
      company_ids?: number[]
      meme_categories?: string[]
    }
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return {
        export_id: 'export_' + Date.now(),
        status: 'processing',
        estimated_completion: new Date(Date.now() + 60000).toISOString(),
        message: '내보내기가 시작되었습니다',
      }
    }

    return api.post<{
      export_id: string
      status: string
      estimated_completion: string
      message: string
    }>('/api/v1/admin/analytics/export', params)
  },

  async getExportStatus(exportId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        export_id: exportId,
        status: 'completed',
        download_url: '/mock-export.csv',
        file_size_mb: 1.5,
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        created_at: new Date(Date.now() - 60000).toISOString(),
        completed_at: new Date().toISOString(),
      }
    }

    return api.get<{
      export_id: string
      status: string
      download_url?: string
      file_size_mb?: number
      expires_at?: string
      created_at: string
      completed_at?: string
    }>(`/api/v1/admin/analytics/export/${exportId}`)
  },

  async getCompanyPerformance(params?: {
    date_from?: string
    date_to?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        period: {
          from_date: params?.date_from || '2026-01-01',
          to: params?.date_to || '2026-01-28',
        },
        companies: [
          {
            company_id: 1,
            company_name: '회사A',
            total_videos: 15,
            total_views: 45000,
            total_engagement: 2500,
            average_engagement_rate: 5.2,
            average_views_per_video: 3000,
            most_used_meme: '두둥탁',
            best_performing_video: { video_id: 1, title: '신제품 홍보', views: 8500, engagement_rate: 6.2 },
          },
          {
            company_id: 2,
            company_name: '회사B',
            total_videos: 10,
            total_views: 32000,
            total_engagement: 1800,
            average_engagement_rate: 4.8,
            average_views_per_video: 3200,
            most_used_meme: '어머 이건 사야해',
            best_performing_video: { video_id: 5, title: '할인 이벤트', views: 6200, engagement_rate: 5.5 },
          },
          {
            company_id: 3,
            company_name: '회사C',
            total_videos: 8,
            total_views: 28000,
            total_engagement: 1600,
            average_engagement_rate: 5.5,
            average_views_per_video: 3500,
            most_used_meme: '비포애프터',
            best_performing_video: { video_id: 10, title: '제품 리뷰', views: 5800, engagement_rate: 5.8 },
          },
        ],
        total_companies: 3,
      }
    }

    const queryParams = new URLSearchParams()
    if (params?.date_from) queryParams.append('date_from', params.date_from)
    if (params?.date_to) queryParams.append('date_to', params.date_to)
    const query = queryParams.toString() ? `?${queryParams}` : ''

    return api.get<{
      period: { from_date: string; to: string }
      companies: Array<{
        company_id: number
        company_name: string
        total_videos: number
        total_views: number
        total_engagement: number
        average_engagement_rate: number
        average_views_per_video: number
        most_used_meme: string
        best_performing_video: {
          video_id: number
          title: string
          views: number
          engagement_rate: number
        }
      }>
      total_companies: number
    }>(`/api/v1/admin/analytics/companies${query}`)
  },
}
