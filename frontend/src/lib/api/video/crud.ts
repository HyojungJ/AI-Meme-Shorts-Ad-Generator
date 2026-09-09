import { api, MOCK_MODE } from '../client'
import { getVideos, getVideoById, addVideo, deleteVideo as mockDeleteVideo } from '../mock'
import { transformWorkflowToVideo, transformProjectToVideo } from './transforms'
import type { Video, MyProjectWorkflowResponse, CharacterResponse, ProjectResponse } from '@/types'

export const videoApi = {
  async generateVideo(formData: FormData) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      const productName = formData.get('product_name') as string
      const companyName = formData.get('company_name') as string
      return addVideo({
        companyName: companyName || '테스트 회사',
        productName: productName || '새 제품',
        productCategory: formData.get('product_category') as string || '기타',
        productHighlight: formData.get('product_highlight') as string || '',
      })
    }

    return api.postFormData<{ ad_id: number; execution_id: string }>('/api/v1/videos/generate', formData)
  },

  async getCharacters() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return [
        { character_id: 1, image_url: 'https://placehold.co/200x200', is_active: true, created_at: new Date().toISOString(), image_prompt: '밝고 친근한 느낌' },
        { character_id: 2, image_url: 'https://placehold.co/200x200', is_active: true, created_at: new Date().toISOString(), image_prompt: '신뢰감 있는 차분한 느낌' },
      ]
    }

    return api.get<CharacterResponse[]>('/api/v1/videos/characters')
  },

  async getCharacterPreview(characterId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { id: characterId, name: '캐릭터', description: '설명', image_url: 'https://placehold.co/400x400', voice_id: null }
    }

    return api.get<CharacterResponse>(`/api/v1/videos/character/${characterId}`)
  },

  async getMyProjects(page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const videos = getVideos()
      return {
        items: videos,
        total: videos.length,
        page,
        per_page: perPage,
        total_pages: Math.ceil(videos.length / perPage),
      }
    }

    const offset = (page - 1) * perPage
    const response = await api.get<{ workflows: MyProjectWorkflowResponse[]; total_count: number }>(`/api/v1/status/my-projects?offset=${offset}&limit=${perPage}`)

    const items = response.workflows.map(transformWorkflowToVideo)
    return {
      items,
      total: response.total_count,
      page,
      per_page: perPage,
      total_pages: Math.ceil(response.total_count / perPage),
    }
  },

  async getProjectById(id: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return getVideoById(id)
    }

    const response = await api.get<ProjectResponse & {
      character_id?: number
      item_name?: string
      item_category?: string
      item_description?: string
      company_name?: string
      character_image_prompt?: string
      character_voice_prompt?: string
      character_revision_history?: Array<{ feedback_type: string; revision_notes: string; requested_at: string }>
      workflow?: { status: string; current_stage?: string; progress_percentage?: number }
      video?: { video_id?: number; s3_url?: string; thumbnail_url?: string; duration_seconds?: number; status?: string }
      item_images?: string[]
      product_image_url?: string | null
    }>(`/api/v1/videos/${id}`)

    if (response.item_name) {
      // ad_request.status를 우선 사용 (백엔드에서 정확한 상태 관리)
      let mappedStatus: Video['status'] = 'character_generating'
      const adStatus = response.status // ad_request.status
      const stage = response.workflow?.current_stage?.toLowerCase() || ''

      // ad_request.status 기반 매핑
      if (adStatus === 'draft' || adStatus === 'created') {
        mappedStatus = 'pending'  // 정보 입력 대기
      } else if (adStatus === 'generating_character') {
        // current_stage로 구분
        if (stage.includes('voice')) {
          mappedStatus = 'voice_generating'  // 음성 생성
        } else {
          mappedStatus = 'character_generating'  // 캐릭터 이미지 생성
        }
      } else if (adStatus === 'pending_approval') {
        // current_stage로 구분
        if (stage.includes('video') || stage.includes('scenario')) {
          mappedStatus = 'video_review'  // 영상 검수
        } else {
          mappedStatus = 'character_review'  // 캐릭터 검수
        }
      } else if (adStatus === 'generating_scenario' || adStatus === 'content_generating') {
        mappedStatus = 'scenario_generating'  // 시나리오 생성
      } else if (adStatus === 'generating_video') {
        mappedStatus = 'video_generating'  // 영상 생성
      } else if (adStatus === 'completed') {
        mappedStatus = 'completed'
      } else if (adStatus === 'failed') {
        mappedStatus = 'failed'
      }

      return {
        id: String(response.ad_id),
        title: response.item_name,
        status: mappedStatus,
        views: 0,
        createdAt: response.created_at.split('T')[0],
        companyName: response.company_name || undefined,
        productCategory: response.item_category || undefined,
        productHighlight: response.item_description || undefined,
        productImageUrl: response.item_images?.[0] || response.product_image_url || undefined,
        characterImagePrompt: response.character_image_prompt || undefined,
        characterVoicePrompt: response.character_voice_prompt || undefined,
        characterRevisionHistory: response.character_revision_history || undefined,
        characterImageUrl: response.character_image_url || undefined,
        voiceSampleUrl: response.voice_sample_url || undefined,
        videoId: response.video?.video_id,
        videoUrl: response.video?.s3_url || undefined,
        characterId: response.character_id,
        progressPercentage: response.workflow?.progress_percentage,
      }
    }

    return transformProjectToVideo(response)
  },

  async generateCharacter(adId: number, data: {
    character_style: string
    reference_image_url?: string
    additional_prompts?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return { character_id: 1, status: 'generating' }
    }

    return api.post<{ character_id: number; status: string }>('/api/v1/videos/characters/generate', {
      ad_id: adId,
      ...data,
    })
  },

  async generateVoice(characterId: number, data: {
    voice_style: string
    sample_text?: string
    reference_audio_url?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return { voice_id: 'voice_123', status: 'generating' }
    }

    return api.post<{ voice_id: string; status: string }>(
      `/api/v1/videos/characters/${characterId}/voice/generate`,
      data
    )
  },

  async getVoicePreview(characterId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { voice_id: 'voice_123', preview_url: '/mock-voice-sample.mp3', status: 'ready' }
    }

    return api.get<{ voice_id: string; preview_url: string; status: string }>(
      `/api/v1/videos/characters/${characterId}/voice`
    )
  },

  async reviseCharacterImage(characterId: number, data: {
    revision_notes: string
    character_prompt?: string
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return {
        character_id: characterId,
        character_name: '캐릭터',
        image_url: 'https://placehold.co/400x400/1a1a1a/c8ff00?text=Revised',
        size_bytes: 150000,
        created_at: new Date().toISOString(),
        message: '캐릭터 이미지를 재생성합니다',
      }
    }

    return api.post<{
      character_id: number
      character_name: string
      image_url: string
      size_bytes: number
      created_at: string
      message: string
    }>(`/api/v1/videos/character/${characterId}/revise`, data)
  },

  async deleteProject(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      mockDeleteVideo(adId)
      return { message: '영상이 삭제되었습니다' }
    }

    return api.delete<{ message: string }>(`/api/v1/videos/${adId}`)
  },

  async reviseVoice(characterId: number, data: {
    revision_notes?: string
    rejection_reason?: string
    sample_text?: string
    approved?: boolean
  }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return {
        character_id: characterId,
        voice_url: '/mock-voice-revised.mp3',
        voice_id: 'voice_revised_' + Date.now(),
        duration_seconds: 3.5,
        size_bytes: 50000,
        created_at: new Date().toISOString(),
        message: '음성을 재생성합니다',
      }
    }

    return api.post<{
      character_id: number
      voice_url: string
      voice_id: string | null
      duration_seconds: number | null
      size_bytes: number
      created_at: string
      message: string
    }>(`/api/v1/videos/characters/${characterId}/voice/revise`, data)
  },

}
