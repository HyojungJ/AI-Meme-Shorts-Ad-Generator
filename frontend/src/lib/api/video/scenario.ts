import { api, MOCK_MODE } from '../client'
import { getVideoById, approveScenario as mockApproveScenario, approveCharacter as mockApproveCharacter, requestCharacterRevision, approveVoice as mockApproveVoice, requestVoiceRevision } from '../mock'
import type { ScenarioResponse, ScenarioVersion } from '@/types'

export const scenarioApi = {
  async getScenarioByAd(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return {
        script_id: 1,
        title: '테스트 시나리오',
        scenes: [
          { scene_number: 1, content: 'Hook 씬', timestamp: '0:00' },
          { scene_number: 2, content: 'Body 씬 1', timestamp: '0:05' },
          { scene_number: 3, content: 'Body 씬 2', timestamp: '0:10' },
          { scene_number: 4, content: 'Close 씬', timestamp: '0:15' },
        ],
        approval_status: 'pending',
      }
    }

    return api.get<{
      script_id: number
      title: string
      description?: string
      scenes: Array<{ scene_number: number; content: string; timestamp?: string }>
      approval_status: string
    }>(`/api/v1/video/${adId}/scenario`)
  },

  async generateScenario(adId: string, memeId?: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return {
        script_id: 1,
        title: '테스트 시나리오',
        scenes: [
          { scene_number: 1, content: 'Hook 씬', timestamp: '0:00' },
          { scene_number: 2, content: 'Body 씬 1', timestamp: '0:05' },
          { scene_number: 3, content: 'Body 씬 2', timestamp: '0:10' },
          { scene_number: 4, content: 'Close 씬', timestamp: '0:15' },
        ],
        status: 'generated',
      }
    }

    return api.post<{
      script_id: number
      title: string
      scenes: Array<{ scene_number: number; content: string; timestamp?: string }>
      status: string
    }>(`/api/v1/video/${adId}/scenario/generate`, {
      meme_id: memeId,
    })
  },

  async getScenarios(videoId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const video = getVideoById(videoId)
      if (!video?.scenario) return []
      return [{
        scenario_id: 1,
        ad_id: parseInt(videoId),
        content: video.scenario,
        version: 1,
        status: 'pending' as const,
        created_at: new Date().toISOString(),
        feedback: null,
      }]
    }

    return api.get<ScenarioResponse[]>(`/api/v1/video/${videoId}/scenarios`)
  },

  async approveScenario(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return mockApproveScenario(adId)
    }

    return api.post<{ message: string }>(`/api/v1/video/${adId}/scenario/approve`, { approved: true })
  },

  async reviseScenario(
    videoId: string,
    scenarioId: number,
    sceneRevisions: Array<{ scene_number: number; scenario_notes: string; video_notes: string }>,
    generalNotes?: string
  ) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return {
        script_id: scenarioId,
        title: '수정된 시나리오',
        scenes: sceneRevisions.map(r => ({
          scene_number: r.scene_number,
          content: `수정됨: ${r.scenario_notes}`,
          timestamp: `0:${((r.scene_number - 1) * 5).toString().padStart(2, '0')}`,
        })),
        status: 'revised',
      }
    }

    return api.post<{
      script_id: number
      title: string
      scenes: Array<{ scene_number: number; content: string; timestamp?: string }>
      status: string
    }>(`/api/v1/video/${videoId}/scenario/revise`, {
      scene_revisions: sceneRevisions,
      general_notes: generalNotes,
    })
  },

  async approveCharacter(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return mockApproveCharacter(adId)
    }

    return api.post<{ message: string }>(`/api/v1/video/${adId}/character/approve`, { approved: true })
  },

  async reviseCharacter(adId: string, rejectionReason: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return requestCharacterRevision(adId)
    }

    return api.post<{ message: string }>(`/api/v1/video/${adId}/character/revise`, { revision_notes: rejectionReason })
  },

  async approveVoice(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return mockApproveVoice(adId)
    }

    return api.post<{ message: string }>(`/api/v1/video/${adId}/voice/approve`, { approved: true })
  },

  async reviseVoice(adId: string, rejectionReason: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return requestVoiceRevision(adId)
    }

    return api.post<{ message: string }>(`/api/v1/video/${adId}/voice/revise`, { revision_notes: rejectionReason })
  },

  async generateVideo(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return { video_id: 1, status: 'completed', estimated_duration: 120 }
    }

    return api.post<{ video_id: number; status: string; estimated_duration: number }>(
      `/api/v1/video/${adId}/video/generate`, {}
    )
  },

  async reviseVideo(adId: string, sceneRevisions: Array<{ scene_number: number; video_notes: string }>) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return { video_id: 1, status: 'processing', estimated_duration: 120 }
    }

    return api.post<{ video_id: number; status: string; estimated_duration: number }>(
      `/api/v1/video/${adId}/video/revise`, { scene_revisions: sceneRevisions }
    )
  },

  // === 통합 콘텐츠 API ===

  async generateContent(adId: string, memeId?: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return { ad_id: parseInt(adId), status: 'content_generating' }
    }

    return api.post<{ ad_id: number; status: string }>(
      `/api/v1/video/${adId}/content/generate`, { meme_id: memeId }
    )
  },

  async reviseContent(
    adId: string,
    sceneRevisions: Array<{ scene_number: number; scenario_notes?: string; video_notes?: string }>,
    generalNotes?: string
  ) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 2000))
      return { ad_id: parseInt(adId), status: 'content_generating' }
    }

    return api.post<{ ad_id: number; status: string }>(
      `/api/v1/video/${adId}/content/revise`, {
        scene_revisions: sceneRevisions,
        general_notes: generalNotes,
      }
    )
  },

  async approveContent(adId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { status: 'completed', message: '최종 승인 완료', is_completed: true }
    }

    return api.post<{ status: string; message: string; is_completed: boolean }>(
      `/api/v1/video/${adId}/content/approve`, {}
    )
  },

  // === 시나리오 버전 관리 ===

  async getScenarioVersions(adId: string): Promise<ScenarioVersion[]> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return [
        {
          script_id: 2,
          ad_id: parseInt(adId),
          title: '수정된 시나리오',
          generation_type: 'revised',
          approval_status: 'pending',
          quality_check_passed: true,
          quality_issues: [],
          review_result: null,
          revision_notes: '대사를 더 자연스럽게 수정해주세요',
          created_at: new Date().toISOString(),
          scenes: [
            { scene_number: 1, content: '수정된 Hook 씬' },
            { scene_number: 2, content: '수정된 Body 씬 1' },
            { scene_number: 3, content: '수정된 Body 씬 2' },
            { scene_number: 4, content: '수정된 Close 씬' },
          ],
        },
        {
          script_id: 1,
          ad_id: parseInt(adId),
          title: '초기 시나리오',
          generation_type: 'initial',
          approval_status: 'rejected',
          quality_check_passed: true,
          quality_issues: [],
          review_result: null,
          created_at: new Date(Date.now() - 86400000).toISOString(),
          scenes: [
            { scene_number: 1, content: '원본 Hook 씬' },
            { scene_number: 2, content: '원본 Body 씬 1' },
            { scene_number: 3, content: '원본 Body 씬 2' },
            { scene_number: 4, content: '원본 Close 씬' },
          ],
        },
      ]
    }

    const response = await api.get<{
      versions: Array<{
        version: number
        script_id: number
        title: string
        description?: string
        generation_type: string
        approval_status: string
        created_at: string
        is_latest: boolean
        scenes_count: number
        revision_notes?: string
        scenes?: Array<{ scene_number: number; dialogue: string; scene_type: string }>
      }>
      total: number
    }>(`/api/v1/video/${adId}/scenarios/versions`)

    // API 응답을 ScenarioVersion 타입으로 변환
    return response.versions.map(v => ({
      script_id: v.script_id,
      ad_id: parseInt(adId),
      title: v.title,
      generation_type: v.generation_type as 'initial' | 'regenerated' | 'revised',
      approval_status: v.approval_status as 'pending' | 'approved' | 'rejected',
      quality_check_passed: (v as Record<string, unknown>).quality_check_passed as boolean ?? true,
      quality_issues: (v as Record<string, unknown>).quality_issues as string[] ?? [],
      review_result: (v as Record<string, unknown>).review_result as Record<string, unknown> ?? null,
      revision_notes: v.revision_notes,
      created_at: v.created_at,
      scenes: v.scenes?.map(s => ({
        scene_number: s.scene_number,
        content: s.dialogue,
      })),
    }))
  },

  async getScenarioByVersion(adId: string, scriptId: number): Promise<ScenarioVersion> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        script_id: scriptId,
        ad_id: parseInt(adId),
        title: '시나리오 제목',
        generation_type: 'initial',
        approval_status: 'approved',
        quality_check_passed: true,
        quality_issues: [],
        review_result: null,
        created_at: new Date().toISOString(),
        scenes: [
          { scene_number: 1, content: '대사 1' },
          { scene_number: 2, content: '대사 2' },
          { scene_number: 3, content: '대사 3' },
          { scene_number: 4, content: '대사 4' },
        ],
      }
    }

    const response = await api.get<{
      script_id: number
      ad_id: number
      meme_id: number
      title: string
      description?: string
      hashtags: string[]
      scenes: Array<{
        scene_key: string
        scene_number: number
        dialogue: string
        emotion: string
        action: string
        visual_description: string
        scene_type: string
        duration_seconds: number
      }>
      generation_type: string
      approval_status: string
      status: string
      created_at: string
      updated_at: string
      review_result?: Record<string, unknown>
      revision_notes?: string
    }>(`/api/v1/video/${adId}/scenarios/${scriptId}`)

    return {
      script_id: response.script_id,
      ad_id: response.ad_id,
      title: response.title,
      generation_type: response.generation_type as 'initial' | 'regenerated' | 'revised',
      approval_status: response.approval_status as 'pending' | 'approved' | 'rejected',
      quality_check_passed: (response as Record<string, unknown>).quality_check_passed as boolean ?? true,
      quality_issues: (response as Record<string, unknown>).quality_issues as string[] ?? [],
      review_result: response.review_result || null,
      revision_notes: response.revision_notes,
      created_at: response.created_at,
      scenes: response.scenes.map(s => ({
        scene_number: s.scene_number,
        content: s.dialogue,
      })),
    }
  },

  async retryGeneration(adId: string, characterImagePrompt: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return { ad_id: parseInt(adId), status: 'generating_character' }
    }

    return api.post<{ ad_id: number; status: string }>(
      `/api/v1/video/${adId}/character/generate`, { character_prompt: characterImagePrompt }
    )
  },
}
