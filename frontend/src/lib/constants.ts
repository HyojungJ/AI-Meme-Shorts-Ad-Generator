export const VIDEO_STATUS = {
  PENDING: 'pending',
  CHARACTER_GENERATING: 'character_generating',
  CHARACTER_REVIEW: 'character_review',
  VOICE_GENERATING: 'voice_generating',
  VOICE_REVIEW: 'voice_review',
  SCENARIO_GENERATING: 'scenario_generating',
  SCENARIO_REVIEW: 'scenario_review',
  CONTENT_GENERATING: 'content_generating',
  VIDEO_GENERATING: 'video_generating',
  VIDEO_REVIEW: 'video_review',
  COMPLETED: 'completed',
} as const

export const STATUS_CONFIG: Record<string, { text: string; color: string; bgColor: string }> = {
  pending: { text: '정보 입력', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)]' },
  character_generating: { text: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  character_review: { text: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  voice_generating: { text: '음성 생성중', color: 'text-pink-400', bgColor: 'bg-pink-500/10' },
  voice_review: { text: '음성 검수', color: 'text-pink-400', bgColor: 'bg-pink-500/10' },
  scenario_generating: { text: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  scenario_review: { text: '시나리오 검수', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  content_generating: { text: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  asset_generating: { text: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  asset_pending: { text: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  asset_approved: { text: '캐릭터 승인', color: 'text-green-400', bgColor: 'bg-green-500/10' },
  video_generating: { text: '영상 생성중', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
  video_review: { text: '영상 검수', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
  completed: { text: '완료', color: 'text-green-400', bgColor: 'bg-green-500/10' },
  failed: { text: '실패', color: 'text-red-400', bgColor: 'bg-red-500/10' },
}

export const STATUS_CONFIG_WITH_BORDER: Record<string, { text: string; color: string; bgColor: string }> = {
  draft: { text: '정보 입력', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]' },
  pending: { text: '정보 입력', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]' },
  processing: { text: '처리중', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20' },
  generating_character: { text: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  character_generating: { text: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  character_review: { text: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  pending_approval: { text: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  voice_generating: { text: '음성 생성중', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20' },
  voice_review: { text: '음성 검수', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20' },
  scenario_generating: { text: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20' },
  scenario_review: { text: '시나리오 검수', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20' },
  content_generating: { text: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20' },
  asset_generating: { text: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  asset_pending: { text: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20' },
  asset_approved: { text: '캐릭터 승인', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20' },
  video_generating: { text: '영상 생성중', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20' },
  video_review: { text: '영상 검수', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20' },
  admin_approved: { text: '승인 완료', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20' },
  completed: { text: '완료', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20' },
  failed: { text: '실패', color: 'text-red-400', bgColor: 'bg-red-500/10 border-red-500/20' },
}

const DEFAULT_STATUS = { label: '처리중', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]', step: 0 }

export const ADMIN_STATUS_CONFIG: Record<string, { label: string; color: string; bgColor: string; step: number }> = {
  // 기본 상태
  pending: { label: '정보 입력', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]', step: 0 },
  created: { label: '생성됨', color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]', step: 0 },
  processing: { label: '처리중', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20', step: 1 },
  pending_approval: { label: '승인대기', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20', step: 3 },

  // 캐릭터
  character: { label: '캐릭터', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 1 },
  character_generation: { label: '이미지 생성', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 1 },
  character_generating: { label: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 1 },
  character_review: { label: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 3 },

  // 음성
  voice: { label: '음성', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20', step: 2 },
  voice_generation: { label: '음성 생성', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20', step: 2 },
  voice_generating: { label: '음성 생성중', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20', step: 2 },
  voice_review: { label: '음성 검수', color: 'text-pink-400', bgColor: 'bg-pink-500/10 border-pink-500/20', step: 3 },

  // 에셋
  asset_generating: { label: '이미지 생성중', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 1 },
  asset_pending: { label: '캐릭터 검수', color: 'text-purple-400', bgColor: 'bg-purple-500/10 border-purple-500/20', step: 3 },
  asset_approved: { label: '캐릭터 승인', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20', step: 4 },

  // 시나리오
  scenario: { label: '시나리오', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20', step: 4 },
  scenario_generation: { label: '시나리오 생성', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20', step: 4 },
  scenario_generating: { label: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20', step: 4 },
  scenario_review: { label: '시나리오 검수', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20', step: 6 },
  content_generating: { label: '시나리오 생성중', color: 'text-blue-400', bgColor: 'bg-blue-500/10 border-blue-500/20', step: 4 },

  // 검수
  review: { label: '검수', color: 'text-yellow-400', bgColor: 'bg-yellow-500/10 border-yellow-500/20', step: 6 },

  // 영상
  video: { label: '영상 생성', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20', step: 5 },
  video_generation: { label: '영상 생성', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20', step: 5 },
  video_generating: { label: '영상 생성중', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20', step: 5 },
  video_review: { label: '영상 검수', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10 border-cyan-500/20', step: 6 },

  // 완료/실패
  completed: { label: '완료', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20', step: 7 },
  failed: { label: '실패', color: 'text-red-400', bgColor: 'bg-red-500/10 border-red-500/20', step: -1 },
  error: { label: '오류', color: 'text-red-400', bgColor: 'bg-red-500/10 border-red-500/20', step: -1 },

  // Video 상태 (영상관리 페이지)
  client_approved: { label: '고객 승인', color: 'text-green-400', bgColor: 'bg-green-500/10 border-green-500/20', step: 7 },
  client_rejected: { label: '고객 거절', color: 'text-orange-400', bgColor: 'bg-orange-500/10 border-orange-500/20', step: -1 },
  admin_approved: { label: '게시 대기', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10 border-emerald-500/20', step: 8 },
  admin_rejected: { label: '관리자 보류', color: 'text-orange-400', bgColor: 'bg-orange-500/10 border-orange-500/20', step: -1 },
  published: { label: '게시됨', color: 'text-sky-400', bgColor: 'bg-sky-500/10 border-sky-500/20', step: 8 },
}

export const getAdminStatusConfig = (status: string) => {
  return ADMIN_STATUS_CONFIG[status] || DEFAULT_STATUS
}

export const STATUS_PROGRESS: Record<string, number> = {
  draft: 0,
  pending: 5,
  processing: 10,
  generating_character: 15,
  character_generating: 15,
  voice_generating: 25,
  character_review: 35,
  voice_review: 35,
  pending_approval: 35,
  asset_generating: 20,
  asset_pending: 35,
  asset_review: 35,
  asset_approved: 40,
  scenario_generating: 50,
  content_generating: 60,
  scenario_review: 85,
  video_generating: 75,
  video_review: 90,
  admin_approved: 95,
  completed: 100,
  failed: 0,
}

export const PRODUCT_CATEGORIES = [
  '식품 및 음료',
  '화장품',
  '출판',
  '컴퓨터 및 정보통신',
  '가정용 전기전자',
  '사무기기',
  '가정용품',
  '유통',
  '서비스',
  '패션',
  '그룹 및 기업광고',
  '기타',
] as const

export const MEME_TYPES = {
  'dudungtak': { label: '두둥탁', color: '#c8ff00', description: '극적인 반전/충격 표현' },
  'must-buy': { label: '어머 이건 사야해', color: '#ff6b6b', description: '충동구매 유도' },
  'real-review': { label: '이게 실화냐', color: '#00d4ff', description: '놀라운 효과 강조' },
  'mz-flex': { label: 'MZ 플렉스', color: '#ffd93d', description: 'MZ세대 감성' },
  'asmr-unboxing': { label: 'ASMR 언박싱', color: '#a855f7', description: '감각적 언박싱' },
  'before-after': { label: '비포애프터', color: '#22c55e', description: '변화 강조' },
} as const

const DEFAULT_MEME_TYPE = { label: '기타', color: 'var(--color-text-tertiary)', description: '기타 밈 유형' }

export const getMemeTypeConfig = (memeType: string) => {
  return MEME_TYPES[memeType as keyof typeof MEME_TYPES] || DEFAULT_MEME_TYPE
}
