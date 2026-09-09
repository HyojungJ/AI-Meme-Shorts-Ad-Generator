const REVIEW_STATUSES = ['character_review', 'voice_review', 'scenario_review', 'video_review', 'asset_pending']
const GENERATING_STATUSES = ['character_generating', 'voice_generating', 'scenario_generating', 'video_generating', 'content_generating', 'asset_generating', 'asset_approved', 'processing']
const PENDING_STATUSES = ['pending', 'draft']

export function isReviewStatus(status: string): boolean {
  return REVIEW_STATUSES.includes(status)
}

export function isGeneratingStatus(status: string): boolean {
  return GENERATING_STATUSES.includes(status)
}

export function isPendingStatus(status: string): boolean {
  return PENDING_STATUSES.includes(status)
}
