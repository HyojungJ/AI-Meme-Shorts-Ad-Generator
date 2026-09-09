import { api, MOCK_MODE } from '../client'
import type {
  LowQualityVideoResponse,
  ValidationFailureResponse,
  PaginatedResponse,
} from '@/types'

export const qualityApi = {
  async getLowQualityVideos(threshold: number, page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { items: [], total: 0, page, per_page: perPage, total_pages: 0 }
    }

    const offset = (page - 1) * perPage
    return api.get<PaginatedResponse<LowQualityVideoResponse>>(
      `/api/v1/admin/quality/low-score-videos?threshold=${threshold}&offset=${offset}&limit=${perPage}`
    )
  },

  async getValidationFailures(page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { items: [], total: 0, page, per_page: perPage, total_pages: 0 }
    }

    const offset = (page - 1) * perPage
    return api.get<PaginatedResponse<ValidationFailureResponse>>(`/api/v1/admin/quality/validation-failures?offset=${offset}&limit=${perPage}`)
  },

  async retryValidation(validationId: number, params?: {
    force_reprocess?: boolean
    skip_checks?: string[]
    note?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return {
        validation_id: validationId,
        video_id: 1,
        status: 'processing',
        retry_count: 1,
        message: '검증이 재시작되었습니다',
        estimated_completion: new Date(Date.now() + 300000).toISOString(),
      }
    }

    return api.post<{
      validation_id: number
      video_id: number
      status: string
      retry_count: number
      message: string
      estimated_completion: string
    }>(`/api/v1/admin/quality/validation/${validationId}/retry`, {
      force_reprocess: params?.force_reprocess ?? false,
      skip_checks: params?.skip_checks,
      note: params?.note,
    })
  },

  async getQualityTrends() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return [
        { date: '2026-01-15', avg_quality_score: 85 },
        { date: '2026-01-16', avg_quality_score: 87 },
        { date: '2026-01-17', avg_quality_score: 86 },
      ]
    }

    return api.get<{ date: string; avg_quality_score: number }[]>('/api/v1/admin/quality/trends')
  },

  async approveValidation(validationId: number, params: {
    reason: string
    override_checks: string[]
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return {
        validation_id: validationId,
        video_id: 1,
        status: 'approved',
        approved_by: 'admin',
        approved_at: new Date().toISOString(),
        message: '검증이 수동 승인되었습니다',
      }
    }

    return api.post<{
      validation_id: number
      video_id: number
      status: string
      approved_by: string
      approved_at: string
      message: string
    }>(`/api/v1/admin/quality/validation/${validationId}/approve`, params)
  },
}
