import { api, MOCK_MODE } from './client'
import { getVideos, getVideoById } from './mock'
import type { AdminVideoResponse, AdminWorkflowResponse, AdminUserResponse, Video, WorkflowDetailData } from '@/types'

// ============================================
// Admin API
// ============================================

export const adminApi = {
  // Videos
  async getAllVideos(page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const videos = getVideos()
      return { items: videos, total: videos.length, page, per_page: perPage, total_pages: Math.ceil(videos.length / perPage) }
    }

    const offset = (page - 1) * perPage
    const response = await api.get<{ videos: AdminVideoResponse[]; total_count: number; offset: number; limit: number }>(
      `/api/v1/admin/videos/all?offset=${offset}&limit=${perPage}`
    )
    return {
      items: response.videos || [],
      total: response.total_count,
      page,
      per_page: perPage,
      total_pages: Math.ceil(response.total_count / perPage),
    }
  },

  async getPendingVideos(page = 1, perPage = 10) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const reviewStatuses = ['pending', 'scenario_review', 'character_review', 'voice_review']
      const videos = getVideos().filter(v => reviewStatuses.includes(v.status))
      return { items: videos, total: videos.length, page, per_page: perPage, total_pages: Math.ceil(videos.length / perPage) }
    }

    const offset = (page - 1) * perPage
    const response = await api.get<{ videos: AdminVideoResponse[]; total_count: number; offset: number; limit: number }>(
      `/api/v1/admin/videos/pending?offset=${offset}&limit=${perPage}`
    )
    return {
      items: response.videos || [],
      total: response.total_count,
      page,
      per_page: perPage,
      total_pages: Math.ceil(response.total_count / perPage),
    }
  },

  async getVideoDetail(videoId: string): Promise<Video> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      const video = getVideoById(videoId)
      if (!video) throw new Error('영상을 찾을 수 없습니다')
      return video
    }
    return api.get<Video>(`/api/v1/admin/videos/${videoId}`)
  },

  async publishVideo(
    videoId: string,
    channelId: number,
    ytTitle?: string,
    ytDescription?: string,
    scheduledAt?: string
  ) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 1000))
      return { message: 'YouTube에 게시되었습니다', youtube_url: 'https://youtube.com/watch?v=mock' }
    }

    return api.post<{ message: string; youtube_url: string }>(`/api/v1/admin/videos/${videoId}/publish`, {
      channel_id: channelId,
      yt_title: ytTitle,
      yt_description: ytDescription,
      scheduled_at: scheduledAt,
    })
  },

  // Workflows
  async getWorkflows(page = 1, perPage = 10, status?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return { items: [], total: 0, page, per_page: perPage, total_pages: 0 }
    }

    const offset = (page - 1) * perPage
    const params = new URLSearchParams({ offset: String(offset), limit: String(perPage) })
    if (status) params.append('status_filter', status)
    const response = await api.get<{ workflows: AdminWorkflowResponse[]; total_count: number; offset: number; limit: number }>(
      `/api/v1/admin/workflows?${params}`
    )
    return {
      items: response.workflows || [],
      total: response.total_count,
      page,
      per_page: perPage,
      total_pages: Math.ceil(response.total_count / perPage),
    }
  },

  async retryWorkflow(executionId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '워크플로우가 재시작되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/admin/workflows/${executionId}/retry`, {})
  },

  async cancelWorkflow(executionId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '워크플로우가 취소되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/admin/workflows/${executionId}/cancel`, {})
  },

  async getWorkflowLogs(executionId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        logs: [
          { timestamp: '2026-01-20T10:00:00', level: 'info', message: '워크플로우 시작' },
          { timestamp: '2026-01-20T10:01:00', level: 'info', message: '캐릭터 생성 완료' },
        ],
      }
    }

    return api.get<{ logs: Array<{ timestamp: string; level: string; message: string }> }>(
      `/api/v1/admin/workflows/${executionId}/logs`
    )
  },

  async getWorkflowDetail(executionId: string): Promise<WorkflowDetailData> {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        ad_request: {
          ad_id: 1,
          item_name: '테스트 상품',
          item_category: '뷰티',
          item_url: 'https://example.com',
          item_images: [],
          item_description: '핵심 메시지입니다',
          character_image_prompt: '젊고 활기찬 20대 남성',
          character_voice_prompt: '젊고 활기찬 20대 남성',
          meme_name: '무야호',
          status: 'content_pending',
          created_at: '2026-01-20T10:00:00',
        },
        revision_history: {
          scenarios: [
            { script_id: 1, title: '시나리오 v1', generation_type: 'initial', approval_status: 'approved', quality_check_passed: true, quality_issues: [], review_result: null, created_at: '2026-01-20T10:05:00' },
          ],
          videos: [
            { video_id: 1, title: '영상 v1', status: 'client_rejected', rejection_reason: '음성 싱크 안 맞음', rejected_at: '2026-01-20T13:00:00', review_result: null, created_at: '2026-01-20T12:30:00' },
          ],
        },
      }
    }

    return api.get<WorkflowDetailData>(`/api/v1/admin/workflows/${executionId}/detail`)
  },

  async holdVideo(videoId: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '영상이 보류되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/admin/videos/${videoId}/hold`, {})
  },

  // Users
  async getUsers(page = 1, perPage = 10, search?: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        items: [
          { account_id: 1, email: 'user1@test.com', member_name: '사용자1', company_name: '회사A', department: '개발팀', account_type: 'client' as const, status: 'active' as const, created_at: '2026-01-01', last_login_at: '2026-01-20', video_count: 5 },
          { account_id: 2, email: 'user2@test.com', member_name: '사용자2', company_name: '회사B', department: '마케팅팀', account_type: 'client' as const, status: 'active' as const, created_at: '2026-01-05', last_login_at: '2026-01-19', video_count: 3 },
        ],
        total: 2,
        page,
        per_page: perPage,
        total_pages: 1,
      }
    }

    const offset = (page - 1) * perPage
    const params = new URLSearchParams({ offset: String(offset), limit: String(perPage) })
    if (search) params.append('search', search)
    const response = await api.get<{ users: AdminUserResponse[]; total_count: number; offset: number; limit: number }>(
      `/api/v1/admin/users?${params}`
    )
    return {
      items: response.users || [],
      total: response.total_count,
      page,
      per_page: perPage,
      total_pages: Math.ceil(response.total_count / perPage),
    }
  },

  async getUserDetail(userId: number) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return { account_id: userId, email: 'user@test.com', member_name: '테스트유저', company_name: '테스트회사', department: '개발팀', account_type: 'client' as const, status: 'active' as const, created_at: '2026-01-01', last_login_at: '2026-01-20', video_count: 5 }
    }

    return api.get<AdminUserResponse>(`/api/v1/admin/users/${userId}`)
  },

  async updateUserStatus(userId: number, status: 'active' | 'inactive' | 'suspended') {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '사용자 상태가 변경되었습니다' }
    }

    return api.patch<{ message: string }>(`/api/v1/admin/users/${userId}/status`, { status })
  },

  async updateUserRole(
    userId: number,
    companyId: number,
    role: 'manager' | 'member',
    reason?: string
  ) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '사용자 권한이 변경되었습니다' }
    }

    return api.patch<{ message: string }>(`/api/v1/admin/users/${userId}/role`, {
      company_id: companyId,
      role,
      reason,
    })
  },

  async deleteUser(userId: number, reason: string, deleteVideos: boolean = false) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '사용자가 삭제되었습니다' }
    }

    return api.post<{ message: string }>(`/api/v1/admin/users/${userId}/delete`, {
      confirmation: 'DELETE',
      reason,
      delete_videos: deleteVideos,
    })
  },

  async getUserStatistics() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return { total_users: 50, active_users: 45, new_users_this_week: 5, total_companies: 10 }
    }

    return api.get<{ total_users: number; active_users: number; new_users_this_week: number; total_companies: number }>('/api/v1/admin/users/statistics/summary')
  },

  async getUserActivityLogs(userId: number, page = 1, perPage = 20) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 300))
      return {
        account_id: userId,
        total_count: 5,
        offset: (page - 1) * perPage,
        limit: perPage,
        logs: [
          { log_id: 1, action_type: 'login', action_description: '로그인 성공', resource_type: null, resource_id: null, details: {}, ip_address: '192.168.1.1', user_agent: 'Mozilla/5.0', created_at: '2026-01-20T10:00:00' },
          { log_id: 2, action_type: 'video_create', action_description: '영상 생성 요청', resource_type: 'video', resource_id: 1, details: { ad_id: 1 }, ip_address: '192.168.1.1', user_agent: 'Mozilla/5.0', created_at: '2026-01-20T10:05:00' },
          { log_id: 3, action_type: 'scenario_approve', action_description: '시나리오 승인', resource_type: 'scenario', resource_id: 1, details: {}, ip_address: '192.168.1.1', user_agent: 'Mozilla/5.0', created_at: '2026-01-20T11:00:00' },
          { log_id: 4, action_type: 'profile_update', action_description: '프로필 정보 수정', resource_type: 'profile', resource_id: userId, details: { field: 'name' }, ip_address: '192.168.1.1', user_agent: 'Mozilla/5.0', created_at: '2026-01-19T14:00:00' },
          { log_id: 5, action_type: 'login', action_description: '로그인 성공', resource_type: null, resource_id: null, details: {}, ip_address: '192.168.1.2', user_agent: 'Mozilla/5.0', created_at: '2026-01-18T09:30:00' },
        ],
      }
    }

    const offset = (page - 1) * perPage
    return api.get<{
      account_id: number
      total_count: number
      offset: number
      limit: number
      logs: Array<{
        log_id: number
        action_type: string
        action_description: string
        resource_type: string | null
        resource_id: number | null
        details: Record<string, unknown>
        ip_address: string
        user_agent: string
        created_at: string
      }>
    }>(`/api/v1/admin/users/${userId}/activity-logs?offset=${offset}&limit=${perPage}`)
  },

  async bulkUserAction(
    accountIds: number[],
    action: 'activate' | 'deactivate' | 'suspend' | 'send_notification',
    options?: { reason?: string; notify_users?: boolean }
  ) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      const actionText = action === 'activate' ? '활성화' : action === 'deactivate' ? '비활성화' : action === 'suspend' ? '정지' : '알림 전송'
      return {
        action,
        total_requested: accountIds.length,
        success_count: accountIds.length,
        failed_count: 0,
        errors: [],
        changed_by: 'admin',
        reason: options?.reason || null,
        message: `${accountIds.length}명의 사용자가 ${actionText}되었습니다`,
      }
    }

    return api.post<{
      action: string
      total_requested: number
      success_count: number
      failed_count: number
      errors: string[]
      changed_by: string
      reason: string | null
      message: string
    }>('/api/v1/admin/users/bulk-action', {
      action,
      account_ids: accountIds,
      reason: options?.reason,
      notify_users: options?.notify_users ?? false,
    })
  },
}
