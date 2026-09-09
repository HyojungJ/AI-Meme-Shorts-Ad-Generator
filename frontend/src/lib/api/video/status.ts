import { api, MOCK_MODE } from '../client'
import { getVideoById } from '../mock'
import type { WorkflowStatusResponse, WorkflowDetailResponse } from '@/types'

export const statusApi = {
  async getWorkflowStatus(videoId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      const video = getVideoById(videoId)
      if (!video) return null
      return {
        execution_id: `exec_${videoId}`,
        ad_id: parseInt(videoId),
        status: video.status === 'completed' ? 'completed' : 'running',
        current_stage: video.status,
        progress_percentage: video.status === 'completed' ? 100 : 50,
        created_at: video.createdAt,
        completed_at: video.status === 'completed' ? video.createdAt : null,
        error_message: null,
      } as WorkflowStatusResponse
    }

    return api.get<WorkflowStatusResponse>(`/api/v1/status/${videoId}`)
  },

  async getWorkflowDetail(videoId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      const video = getVideoById(videoId)
      if (!video) return null
      return {
        execution_id: `exec_${videoId}`,
        ad_id: parseInt(videoId),
        status: video.status === 'completed' ? 'completed' : 'running',
        current_stage: video.status,
        progress_percentage: video.status === 'completed' ? 100 : 50,
        created_at: video.createdAt,
        completed_at: video.status === 'completed' ? video.createdAt : null,
        error_message: null,
        stages: [
          { name: 'character_generating', status: 'completed', started_at: null, completed_at: null, error_message: null },
          { name: 'character_review', status: 'completed', started_at: null, completed_at: null, error_message: null },
          { name: 'voice_generating', status: 'running', started_at: null, completed_at: null, error_message: null },
        ],
      } as WorkflowDetailResponse
    }

    return api.get<WorkflowDetailResponse>(`/api/v1/status/${videoId}/detail`)
  },
}
