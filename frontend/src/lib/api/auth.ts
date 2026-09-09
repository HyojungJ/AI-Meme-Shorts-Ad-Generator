import { api, setTokens, removeTokens, MOCK_MODE, MOCK_ADMIN_EMAIL, MOCK_ADMIN_PASSWORD, API_URL_EXPORT } from './client'
import type { TokenResponse, BackendUser } from '@/types'

// ============================================
// Mock Data
// ============================================

const mockUser = {
  user_id: 1,
  email: 'test@example.com',
  name: '테스트유저',
  companyName: '테스트회사',
  department: '개발팀',
  role: 'member' as const,
  profile_img: null,
  is_admin: false,
  access_token: 'mock_token_12345',
  createdAt: '2026-01-15',
}

// Mock 모드에서 현재 로그인한 사용자 정보 저장
let mockCurrentUser: typeof mockUser | null = null

// ============================================
// Helper Functions
// ============================================

function transformUserResponse(data: BackendUser) {
  return {
    user_id: data.account_id,
    email: data.email,
    name: data.member_name || '',
    companyName: data.company_name || '',
    department: data.department || '',
    role: (data.role || 'member') as 'manager' | 'member',
    profile_img: data.profile_img || null,
    is_admin: data.account_type === 'admin',
    access_token: '',
    createdAt: data.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
  }
}

// ============================================
// Auth API
// ============================================

export const authApi = {
  async login(email: string, password: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      if (MOCK_ADMIN_EMAIL && email === MOCK_ADMIN_EMAIL && password === MOCK_ADMIN_PASSWORD) {
        mockCurrentUser = { ...mockUser, user_id: 0, email: MOCK_ADMIN_EMAIL, name: '관리자', is_admin: true }
        return mockCurrentUser
      }
      mockCurrentUser = { ...mockUser, email, name: email.split('@')[0], is_admin: false }
      return mockCurrentUser
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '로그인 실패' }))
      throw new Error(error.detail || '이메일 또는 비밀번호가 올바르지 않습니다')
    }

    const data: TokenResponse = await response.json()
    setTokens(data.access_token, data.refresh_token)
    return {
      access_token: data.access_token,
      user_id: data.account_id,
      email: data.email,
      is_admin: data.account_type === 'admin',
    }
  },

  async register(email: string, password: string, name: string, companyName: string, department: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return {
        ...mockUser,
        email,
        name,
        companyName,
        department,
        role: 'member',
        createdAt: new Date().toISOString().split('T')[0],
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        member_name: name,
        company_name: companyName,
        department,
        role: 'member',
      }),
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: '회원가입 실패' }))
      throw new Error(error.detail || '회원가입에 실패했습니다')
    }

    const data = await response.json()
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token)
    }
    return transformUserResponse(data)
  },

  async logout() {
    if (MOCK_MODE) {
      mockCurrentUser = null
      removeTokens()
      return
    }

    try {
      await api.post('/api/v1/auth/logout', {})
    } finally {
      removeTokens()
    }
  },

  async getCurrentUser() {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return mockCurrentUser || mockUser
    }

    const data = await api.get<BackendUser>('/api/v1/auth/me')
    return transformUserResponse(data)
  },

  async updateProfile(data: { member_name?: string; company_name?: string; department?: string }) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { ...mockUser, name: data.member_name || mockUser.name }
    }

    const response = await api.patch<BackendUser>('/api/v1/auth/me', data)
    return transformUserResponse(response)
  },

  async requestPasswordReset(email: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '비밀번호 재설정 이메일이 발송되었습니다' }
    }

    return api.post<{ message: string }>('/api/v1/auth/password-reset/request', { email })
  },

  async confirmPasswordReset(token: string, newPassword: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 500))
      return { message: '비밀번호가 변경되었습니다' }
    }

    return api.post<{ message: string }>('/api/v1/auth/password-reset/confirm', {
      token,
      new_password: newPassword,
    })
  },

  async refreshToken(refreshToken: string) {
    if (MOCK_MODE) {
      await new Promise((r) => setTimeout(r, 200))
      return {
        access_token: 'mock_refreshed_token_' + Date.now(),
        refresh_token: refreshToken,
        token_type: 'bearer' as const,
        account_id: 1,
        email: 'test@example.com',
        account_type: 'client',
        company_id: 1,
        role: 'member',
      }
    }

    const response = await fetch(`${API_URL_EXPORT}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      removeTokens()
      throw new Error('토큰 갱신에 실패했습니다')
    }

    const data: {
      access_token: string
      refresh_token: string
      token_type: 'bearer'
      account_id: number
      email: string
      account_type: string
      company_id?: number
      role?: string
    } = await response.json()
    setTokens(data.access_token, data.refresh_token)
    return data
  },
}

// Legacy exports
export const loginWithEmail = authApi.login
export const registerWithEmail = authApi.register
export const getCurrentUser = authApi.getCurrentUser
