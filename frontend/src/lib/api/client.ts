import { API_URL } from '@/lib/config'

// ============================================
// Token Management
// ============================================

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('refresh_token')
}

export function setTokens(accessToken: string, refreshToken?: string) {
  localStorage.setItem('access_token', accessToken)
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken)
  }
}

export function setToken(token: string) {
  setTokens(token)
}

export function removeTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function removeToken() {
  removeTokens()
}

// ============================================
// API Client
// ============================================

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  try {
    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      removeTokens()
      return null
    }

    const data = await response.json()
    setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    removeTokens()
    return null
  }
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = getAccessToken()
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }

  // Only set Content-Type if not FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  })

  // Handle token refresh on 401
  if (response.status === 401 && getRefreshToken()) {
    if (!isRefreshing) {
      isRefreshing = true
      const newToken = await refreshAccessToken()
      isRefreshing = false

      if (newToken) {
        onTokenRefreshed(newToken)
        headers['Authorization'] = `Bearer ${newToken}`
        response = await fetch(`${API_URL}${endpoint}`, {
          ...options,
          headers,
        })
      } else {
        onTokenRefreshed('')
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        throw new Error('인증이 만료되었습니다')
      }
    } else {
      // Wait for token refresh
      const newToken = await new Promise<string>((resolve) => {
        subscribeTokenRefresh(resolve)
      })
      if (!newToken) {
        throw new Error('인증이 만료되었습니다')
      }
      headers['Authorization'] = `Bearer ${newToken}`
      response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
      })
    }
  }

  if (response.status === 401) {
    removeTokens()
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
    throw new Error('인증이 만료되었습니다')
  }

  return response
}

async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetchWithAuth(endpoint, options)

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'API Error' }))
    const detail = (error as { detail?: unknown }).detail
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    throw new Error(message || `API Error: ${response.status}`)
  }

  // Handle empty responses
  const text = await response.text()
  if (!text) return null as T
  return JSON.parse(text)
}

export const api = {
  get: <T>(endpoint: string) => apiRequest<T>(endpoint),
  post: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'DELETE' }),
  postFormData: <T>(endpoint: string, formData: FormData) =>
    apiRequest<T>(endpoint, { method: 'POST', body: formData }),
}

export const API_URL_EXPORT = API_URL
export const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK_MODE === 'true'

// Mock 모드 관리자 계정 (환경변수로 설정, 프로덕션에서는 사용 안함)
export const MOCK_ADMIN_EMAIL = process.env.NEXT_PUBLIC_MOCK_ADMIN_EMAIL || ''
export const MOCK_ADMIN_PASSWORD = process.env.NEXT_PUBLIC_MOCK_ADMIN_PASSWORD || ''
