// ============================================
// API Client & Token Management
// ============================================

export {
  api,
  getAccessToken,
  getRefreshToken,
  setTokens,
  setToken,
  removeTokens,
  removeToken,
  MOCK_MODE,
  MOCK_ADMIN_EMAIL,
  MOCK_ADMIN_PASSWORD,
  API_URL_EXPORT,
} from './client'

// ============================================
// Auth API
// ============================================

export { authApi, loginWithEmail, registerWithEmail, getCurrentUser } from './auth'

// ============================================
// Video, Scenario, Status APIs
// ============================================

export { videoApi, scenarioApi, statusApi } from './video'

// ============================================
// Meme API
// ============================================

export { memeApi } from './meme'
export type { Meme, MemeDetail, MemeStatus, MemeType, MemeListResponse, MemeSortItem, MemeSortResponse } from './meme'

// ============================================
// Character Profiles API
// ============================================

export { characterProfilesApi } from './character-profiles'
export type { CharacterProfile } from './character-profiles'

// ============================================
// Admin API
// ============================================

export { adminApi } from './admin'

// ============================================
// Analytics, Costs, Quality, Final APIs
// ============================================

export {
  analyticsApi,
  clientAnalyticsApi,
  costsApi,
  qualityApi,
  finalApi,
  generateInsights,
} from './analytics'

export type { ClientDashboardResponse, VideoPerformanceResponse } from './analytics'

// ============================================
// Health API
// ============================================

export { healthApi } from './health'
export type { HealthStatus, DatabaseHealthStatus, S3HealthStatus, FullHealthStatus } from './health'

// ============================================
// Mock Data & Helpers
// ============================================

export {
  getVideos,
  addVideo,
  deleteVideo,
  getVideoById,
  updateVideo,
  approveCharacter,
  requestCharacterRevision,
  approveVoice,
  requestVoiceRevision,
  approveScenario,
  requestScenarioRevision,
  mockData,
  getVideoMetrics,
  memePerformanceData,
  categoryPerformanceData,
  trendData,
  trendInsights,
  hourlyViewsDistribution,
  analyticsSummary,
} from './mock'

// ============================================
// Type Re-exports
// ============================================

export type { Video, VideoRequestFormData } from '@/types'
