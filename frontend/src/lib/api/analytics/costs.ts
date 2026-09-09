import { api, MOCK_MODE } from '../client'
import type {
  CostStatisticsResponse,
  CompanyCostResponse,
  PaginatedResponse,
} from '@/types'

export const costsApi = {
  async getCompanyCosts(year: number, month: number, page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        items: [
          { company_id: 1, company_name: '회사A', total_videos: 10, total_cost: 150000, avg_cost_per_video: 15000 },
          { company_id: 2, company_name: '회사B', total_videos: 5, total_cost: 80000, avg_cost_per_video: 16000 },
        ],
        total: 2,
        page,
        per_page: perPage,
        total_pages: 1,
      }
    }

    const offset = (page - 1) * perPage
    return api.get<PaginatedResponse<CompanyCostResponse>>(
      `/api/v1/admin/costs/companies?year=${year}&month=${month}&offset=${offset}&limit=${perPage}`
    )
  },

  async getStatistics() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        total_cost: 500000,
        avg_cost_per_video: 15000,
        cost_by_stage: { character: 3000, voice: 2000, scenario: 5000, video: 5000 },
        monthly_costs: [
          { month: '2026-01', cost: 500000 },
        ],
      }
    }

    return api.get<CostStatisticsResponse>('/api/v1/admin/costs/statistics')
  },

  async getOptimizationSuggestions() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return [
        { type: 'cost', title: '비용 최적화', description: '캐릭터 생성 단계에서 배치 처리를 활용하면 20% 비용 절감 가능' },
      ]
    }

    return api.get<{ type: string; title: string; description: string }[]>('/api/v1/admin/costs/optimization-suggestions')
  },

  async getCostDetails(params?: {
    offset?: number
    limit?: number
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        total_count: 5,
        offset: params?.offset || 0,
        limit: params?.limit || 20,
        details: [
          { cost_id: 1, company_id: 1, company_name: '회사A', video_id: 1, video_title: '신제품 홍보 영상', cost_type: 'character', amount: 3000, details: { model: 'sd-xl' }, created_at: '2026-01-15T10:00:00' },
          { cost_id: 2, company_id: 1, company_name: '회사A', video_id: 1, video_title: '신제품 홍보 영상', cost_type: 'voice', amount: 2000, details: { model: 'elevenlabs' }, created_at: '2026-01-15T11:00:00' },
          { cost_id: 3, company_id: 1, company_name: '회사A', video_id: 1, video_title: '신제품 홍보 영상', cost_type: 'scenario', amount: 5000, details: { model: 'gpt-4' }, created_at: '2026-01-16T09:00:00' },
          { cost_id: 4, company_id: 1, company_name: '회사A', video_id: 1, video_title: '신제품 홍보 영상', cost_type: 'video', amount: 5000, details: { model: 'sora' }, created_at: '2026-01-17T14:00:00' },
          { cost_id: 5, company_id: 2, company_name: '회사B', video_id: 2, video_title: '이벤트 안내', cost_type: 'character', amount: 3000, details: { model: 'sd-xl' }, created_at: '2026-01-18T10:00:00' },
        ],
      }
    }

    const queryParams = new URLSearchParams()
    if (params?.offset !== undefined) queryParams.append('offset', String(params.offset))
    if (params?.limit !== undefined) queryParams.append('limit', String(params.limit))
    const query = queryParams.toString() ? `?${queryParams}` : ''

    return api.get<{
      total_count: number
      offset: number
      limit: number
      details: Array<{
        cost_id: number
        company_id: number
        company_name: string
        video_id: number
        video_title: string
        cost_type: string
        amount: number
        details: Record<string, unknown>
        created_at: string
      }>
    }>(`/api/v1/admin/costs/details${query}`)
  },
}
