// Re-export from split modules for backward compatibility
export { generateInsights } from './analytics/insights'
export { analyticsApi } from './analytics/dashboard'
export { clientAnalyticsApi } from './analytics/client-analytics'
export type { ClientDashboardResponse, VideoPerformanceResponse } from './analytics/client-analytics'
export { costsApi } from './analytics/costs'
export { qualityApi } from './analytics/quality'
export { finalApi } from './analytics/final'
