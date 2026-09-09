import { api, MOCK_MODE } from './client'

export type MemeStatus = 'READY' | 'COMPLETED' | 'PROCESSING'
export type MemeType = 'quotable' | 'performable' | 'hybrid'

// 백엔드 스키마와 일치하는 Meme 인터페이스
export interface Meme {
  meme_id: number
  meme_name: string
  description: string | null
  meme_type: MemeType | null
  thumbnail_url: string | null
  status: string
  usage_count: number
  avg_engagement_rate: number
  created_at: string
}

export interface MemeDetail extends Meme {
  origin: Record<string, unknown> | null
  key_phrase: string | null
  sources: string[] | null
  risk_info: string | null
  confidence: number | null
  created_at: string
}

export interface MemeListResponse {
  memes: Meme[]
  total_count: number
}

export interface MemeSortItem {
  meme_id: number
  meme_name: string
  situation: string
  example_id: number
  similarity: number
}

export interface MemeSortResponse {
  results: MemeSortItem[]
}

const mockMemes: MemeDetail[] = [
  {
    meme_id: 1,
    meme_name: '두둥탁',
    description: '극적인 반전이나 충격적인 정보를 전달할 때 사용하는 효과음 밈',
    meme_type: 'quotable',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: { source: '드럼 효과음', year: 2020 },
    key_phrase: null,
    sources: ['https://example.com/dudungtak'],
    risk_info: null,
    confidence: 0.95,
    created_at: '2026-01-01T00:00:00',
  },
  {
    meme_id: 2,
    meme_name: '어머 이건 사야해',
    description: '충동구매를 유발하는 제품 소개에 적합한 밈',
    meme_type: 'quotable',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: { source: '홈쇼핑', year: 2019 },
    key_phrase: null,
    sources: null,
    risk_info: null,
    confidence: 0.88,
    created_at: '2026-01-02T00:00:00',
  },
  {
    meme_id: 3,
    meme_name: '이게 실화냐',
    description: '놀라운 성능이나 가격을 강조할 때 사용',
    meme_type: 'quotable',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: null,
    key_phrase: null,
    sources: null,
    risk_info: null,
    confidence: 0.92,
    created_at: '2026-01-03T00:00:00',
  },
  {
    meme_id: 4,
    meme_name: 'MZ 플렉스',
    description: 'MZ세대 트렌드에 맞는 과시형 콘텐츠',
    meme_type: 'performable',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: null,
    key_phrase: null,
    sources: null,
    risk_info: '과도한 과시 주의',
    confidence: 0.85,
    created_at: '2026-01-04T00:00:00',
  },
  {
    meme_id: 5,
    meme_name: 'ASMR 언박싱',
    description: '제품 개봉 시 소리를 강조한 ASMR 스타일',
    meme_type: 'performable',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: null,
    key_phrase: null,
    sources: null,
    risk_info: null,
    confidence: 0.90,
    created_at: '2026-01-05T00:00:00',
  },
  {
    meme_id: 6,
    meme_name: '비포애프터',
    description: '사용 전/후를 극적으로 비교하는 포맷',
    meme_type: 'hybrid',
    thumbnail_url: null,
    status: 'READY',
    usage_count: 0,
    avg_engagement_rate: 0.0,
    origin: null,
    key_phrase: null,
    sources: null,
    risk_info: null,
    confidence: 0.93,
    created_at: '2026-01-06T00:00:00',
  },
]

export const memeApi = {
  async getMemes(params?: {
    status?: MemeStatus
    meme_type?: MemeType
    search?: string
    offset?: number
    limit?: number
  }): Promise<MemeListResponse> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      let filtered = [...mockMemes]

      if (params?.status) {
        filtered = filtered.filter((m) => m.status === params.status)
      }
      if (params?.meme_type) {
        filtered = filtered.filter((m) => m.meme_type === params.meme_type)
      }
      if (params?.search) {
        const searchLower = params.search.toLowerCase()
        filtered = filtered.filter(
          (m) =>
            m.meme_name.toLowerCase().includes(searchLower) ||
            (m.description && m.description.toLowerCase().includes(searchLower))
        )
      }

      const offset = params?.offset || 0
      const limit = params?.limit || 10
      const paginated = filtered.slice(offset, offset + limit)

      return {
        memes: paginated.map((m) => ({
          meme_id: m.meme_id,
          meme_name: m.meme_name,
          description: m.description,
          meme_type: m.meme_type,
          thumbnail_url: m.thumbnail_url,
          status: m.status,
          usage_count: m.usage_count,
          avg_engagement_rate: m.avg_engagement_rate,
          created_at: m.created_at,
        })),
        total_count: filtered.length,
      }
    }

    const queryParams = new URLSearchParams()
    if (params?.status) queryParams.append('status', params.status)
    if (params?.meme_type) queryParams.append('meme_type', params.meme_type)
    if (params?.search) queryParams.append('search', params.search)
    if (params?.offset !== undefined) queryParams.append('offset', String(params.offset))
    if (params?.limit !== undefined) queryParams.append('limit', String(params.limit))
    const query = queryParams.toString() ? `?${queryParams}` : ''

    return api.get<MemeListResponse>(`/api/v1/memes${query}`)
  },

  async getMemeDetail(memeId: number): Promise<MemeDetail> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      const meme = mockMemes.find((m) => m.meme_id === memeId)
      if (!meme) throw new Error('밈을 찾을 수 없습니다')
      return meme
    }

    return api.get<MemeDetail>(`/api/v1/memes/${memeId}`)
  },

  async sortMemes(itemDescription: string, topN: number = 30): Promise<MemeSortResponse> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return {
        results: mockMemes.map((m, i) => ({
          meme_id: m.meme_id,
          meme_name: m.meme_name,
          situation: m.description || '',
          example_id: i + 1,
          similarity: +(0.9 - i * 0.1).toFixed(4),
        })),
      }
    }

    return api.post<MemeSortResponse>('/api/v1/memes/sort', {
      item_description: itemDescription,
      top_n: topN,
    })
  },
}
