import { api, MOCK_MODE } from '../client'

export const finalApi = {
  async downloadVideo(videoId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { download_url: '/mock-video.mp4' }
    }

    return api.get<{ download_url: string }>(`/api/v1/videos/${videoId}/download`)
  },

  async approveVideo(videoId: number, feedback?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '영상이 최종 승인되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/videos/${videoId}/approve`, { feedback })
  },

  async rejectVideo(videoId: number, reason: string, feedback?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '영상이 거부되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/videos/${videoId}/reject`, { reason, feedback })
  },

  async previewVideo(videoId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { preview_url: 'https://placehold.co/1280x720/1a1a1a/c8ff00?text=Preview+Video' }
    }

    return api.get<{ preview_url: string }>(`/api/v1/videos/${videoId}/preview`)
  },

  async reviseVideo(videoId: number, feedback?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '영상 재생성이 요청되었습니다', execution_id: 'exec_new_123' }
    }

    return api.post<{ message: string; execution_id?: string }>(`/api/v1/videos/${videoId}/revise`, {
      feedback,
    })
  },
}
