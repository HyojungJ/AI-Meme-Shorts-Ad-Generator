import type {
  Video,
  VideoMetrics,
  MemePerformance,
  CategoryPerformance,
  TrendDataPoint,
  TrendInsight,
  AnalyticsSummary,
} from '@/types'

// ============================================
// Mock Default Data
// ============================================

const defaultVideos: Video[] = [
  {
    id: '1',
    title: '신제품 홍보 영상',
    status: 'scenario_review',
    views: 0,
    createdAt: '2026-01-15',
    companyName: 'ABC Corp',
    productCategory: '전자기기',
    productHighlight: '혁신적인 기술, 세련된 디자인',
    productImageUrl: 'https://placehold.co/300x300/1a1a1a/ffffff?text=Product',
    characterImagePrompt: '밝고 친근한 20대 캐릭터, 캐주얼 복장, 3D 스타일',
    characterVoicePrompt: '20대 여성, 밝고 친근한 느낌, 부드러운 목소리',
    characterImageUrl: 'https://placehold.co/400x400/1a1a1a/c8ff00?text=Character',
    voiceSampleUrl: '/mock-voice-sample.mp3',
    scenario: '안녕하세요! 오늘은 ABC Corp의 신제품을 소개해드릴게요.\n\n[장면 1] 제품 클로즈업\n"이 작은 기기가 여러분의 일상을 바꿀 거예요!"\n\n[장면 2] 사용 장면\n"보세요, 이렇게 간단하게!"\n\n[장면 3] 마무리\n"지금 바로 만나보세요!"',
    videoUrl: 'https://placehold.co/1280x720/1a1a1a/c8ff00?text=Preview+Video',
    scenes: [
      { scene_number: 1, content: '인트로 - 캐릭터 등장\n"안녕하세요! 오늘 여러분께 정말 특별한 제품을 소개해드릴게요!"', timestamp: '00:00-00:08' },
      { scene_number: 2, content: '제품 클로즈업\n"이 작은 기기가 여러분의 일상을 완전히 바꿔놓을 거예요. 한번 보세요!"', timestamp: '00:08-00:16' },
      { scene_number: 3, content: '사용 장면 데모\n"보세요, 이렇게 간단하게! 누구나 쉽게 사용할 수 있어요."', timestamp: '00:16-00:24' },
      { scene_number: 4, content: '마무리 CTA\n"지금 바로 만나보세요! 링크는 프로필에 있어요~"', timestamp: '00:24-00:30' },
    ],
  },
  {
    id: '2',
    title: '이벤트 안내',
    status: 'character_review',
    views: 0,
    createdAt: '2026-01-18',
    companyName: 'XYZ Inc',
    productCategory: '식품/음료',
    productHighlight: '특별 할인, 한정 기간',
    productImageUrl: 'https://placehold.co/300x300/1a1a1a/ffffff?text=Product',
    characterImagePrompt: '30대 남성, 전문가 느낌, 신뢰감 있는 차분한 목소리',
    characterVoicePrompt: '30대 남성, 전문가 느낌, 신뢰감 있는 차분한 목소리',
    characterImageUrl: 'https://placehold.co/400x400/1a1a1a/00d4ff?text=Character',
  },
  {
    id: '3',
    title: '브랜드 소개',
    status: 'voice_review',
    views: 0,
    createdAt: '2026-01-19',
    companyName: 'Hello Co',
    productCategory: '뷰티/화장품',
    productHighlight: '천연 성분, 피부에 순한',
    productImageUrl: 'https://placehold.co/300x300/1a1a1a/ffffff?text=Product',
    characterImagePrompt: '20대 여성, 귀여운 말투, 에너지 넘치는 밝은 느낌',
    characterVoicePrompt: '20대 여성, 귀여운 말투, 에너지 넘치는 밝은 느낌',
    characterImageUrl: 'https://placehold.co/400x400/1a1a1a/a855f7?text=Character',
    voiceSampleUrl: '/mock-voice-sample.mp3',
  },
  {
    id: '4',
    title: '신상품 런칭',
    status: 'scenario_review',
    views: 0,
    createdAt: '2026-01-20',
    companyName: 'Fashion Co',
    productCategory: '패션/의류',
    productHighlight: '트렌디한 디자인, 합리적인 가격',
    productImageUrl: 'https://placehold.co/300x300/1a1a1a/ffffff?text=Product',
    characterImagePrompt: '20대 여성, 트렌디하고 세련된 느낌, 빠른 말투',
    characterVoicePrompt: '20대 여성, 트렌디하고 세련된 느낌, 빠른 말투',
    characterImageUrl: 'https://placehold.co/400x400/1a1a1a/ff6b6b?text=Character',
    voiceSampleUrl: '/mock-voice-sample.mp3',
    scenario: '여러분의 스타일을 업그레이드할 시간이에요!\n\n[장면 1] 제품 소개\n"이번 시즌 가장 핫한 아이템!"\n\n[장면 2] 스타일링\n"이렇게 매치하면 완벽해요"\n\n[장면 3] CTA\n"지금 바로 득템하세요!"',
    videoUrl: 'https://placehold.co/1280x720/1a1a1a/ff6b6b?text=Preview+Video',
    scenes: [
      { scene_number: 1, content: '인트로 - 트렌드 소개\n"요즘 가장 핫한 스타일 알려드릴게요!"', timestamp: '00:00-00:07' },
      { scene_number: 2, content: '제품 클로즈업\n"이번 시즌 머스트해브 아이템! 디테일 봐주세요~"', timestamp: '00:07-00:14' },
      { scene_number: 3, content: '스타일링 팁\n"이렇게 매치하면 완벽한 데일리룩 완성!"', timestamp: '00:14-00:21' },
      { scene_number: 4, content: '마무리 CTA\n"지금 바로 득템하세요! 수량 한정이에요!"', timestamp: '00:21-00:28' },
    ],
  },
]

// ============================================
// Video CRUD Functions
// ============================================

export function getVideos(): Video[] {
  if (typeof window === 'undefined') return defaultVideos
  const stored = localStorage.getItem('mock_videos')
  if (stored) {
    return JSON.parse(stored)
  }
  return defaultVideos
}

export function addVideo(data: {
  companyName: string
  productName: string
  productCategory: string
  productHighlight: string
}): Video {
  const videos = getVideos()
  const newVideo: Video = {
    id: String(Date.now()),
    title: `${data.productName} 홍보 영상`,
    status: 'pending',
    views: 0,
    createdAt: new Date().toISOString().split('T')[0],
    companyName: data.companyName,
    productCategory: data.productCategory,
  }
  const updated = [newVideo, ...videos]
  localStorage.setItem('mock_videos', JSON.stringify(updated))
  return newVideo
}

export function deleteVideo(id: string): boolean {
  const videos = getVideos()
  const updated = videos.filter(v => v.id !== id)
  localStorage.setItem('mock_videos', JSON.stringify(updated))
  return true
}

export function getVideoById(id: string): Video | null {
  const videos = getVideos()
  const video = videos.find(v => v.id === id) || null

  // localStorage에 저장된 오래된 데이터에 scenes가 없으면 defaultVideos에서 가져옴
  if (video && video.status === 'scenario_review' && !video.scenes) {
    const defaultVideo = defaultVideos.find(v => v.id === id)
    if (defaultVideo?.scenes) {
      return { ...video, scenes: defaultVideo.scenes, videoUrl: defaultVideo.videoUrl }
    }
  }

  return video
}

export function updateVideo(id: string, data: Partial<Video>): Video | null {
  const videos = getVideos()
  const index = videos.findIndex(v => v.id === id)
  if (index === -1) return null

  videos[index] = { ...videos[index], ...data }
  localStorage.setItem('mock_videos', JSON.stringify(videos))
  return videos[index]
}

// ============================================
// Status Change Functions
// ============================================

export function approveCharacter(id: string): Video | null {
  return updateVideo(id, { status: 'voice_generating' })
}

export function requestCharacterRevision(id: string): Video | null {
  return updateVideo(id, { status: 'character_generating' })
}

export function approveVoice(id: string): Video | null {
  return updateVideo(id, { status: 'scenario_generating' })
}

export function requestVoiceRevision(id: string): Video | null {
  return updateVideo(id, { status: 'voice_generating' })
}

export function approveScenario(id: string): Video | null {
  return updateVideo(id, { status: 'completed' })
}

export function requestScenarioRevision(id: string): Video | null {
  return updateVideo(id, { status: 'scenario_generating' })
}

// ============================================
// Mock Data Object
// ============================================

export const mockData = {
  get videos() {
    return getVideos()
  },
  get stats() {
    const videos = getVideos()
    const processingStatuses = ['character_generating', 'voice_generating', 'scenario_generating', 'video_generating', 'content_generating', 'asset_generating']
    return {
      totalVideos: videos.length,
      totalViews: 125000,
      avgEngagement: 4.2,
      processingCount: videos.filter(v => processingStatuses.includes(v.status)).length,
    }
  },
  dailyStats: [
    { date: '01/14', views: 2400, engagement: 3.8 },
    { date: '01/15', views: 3200, engagement: 4.1 },
    { date: '01/16', views: 2800, engagement: 3.9 },
    { date: '01/17', views: 4100, engagement: 4.5 },
    { date: '01/18', views: 3600, engagement: 4.2 },
    { date: '01/19', views: 3900, engagement: 4.0 },
    { date: '01/20', views: 4500, engagement: 4.6 },
  ],
}

// ============================================
// Analytics Mock Data
// ============================================

export function getVideoMetrics(videoId: string): VideoMetrics {
  const baseViews = parseInt(videoId) * 1000 + 5000
  return {
    views: baseViews,
    likes: Math.floor(baseViews * 0.05),
    comments: Math.floor(baseViews * 0.02),
    shares: Math.floor(baseViews * 0.01),
    watchTime: 45 + Math.floor(Math.random() * 30),
    completionRate: 55 + Math.floor(Math.random() * 35),
    engagementRate: 3 + Math.random() * 4,
    dailyViews: Array.from({ length: 14 }, (_, i) => ({
      date: `01/${String(7 + i).padStart(2, '0')}`,
      views: Math.floor(baseViews / 14 * (0.5 + Math.random())),
    })),
    hourlyViews: Array.from({ length: 24 }, (_, hour) => ({
      hour,
      views: Math.floor(baseViews / 24 * (hour >= 18 && hour <= 23 ? 2 : hour >= 12 && hour <= 17 ? 1.5 : 0.5)),
    })),
  }
}

export const memePerformanceData: MemePerformance[] = [
  { memeType: 'dudungtak', label: '두둥탁', videoCount: 8, totalViews: 52000, avgViews: 6500, avgCompletionRate: 78, avgEngagementRate: 6.2 },
  { memeType: 'must-buy', label: '어머 이건 사야해', videoCount: 6, totalViews: 45000, avgViews: 7500, avgCompletionRate: 72, avgEngagementRate: 5.8 },
  { memeType: 'real-review', label: '이게 실화냐', videoCount: 5, totalViews: 38000, avgViews: 7600, avgCompletionRate: 75, avgEngagementRate: 5.5 },
  { memeType: 'mz-flex', label: 'MZ 플렉스', videoCount: 4, totalViews: 28000, avgViews: 7000, avgCompletionRate: 68, avgEngagementRate: 4.9 },
  { memeType: 'asmr-unboxing', label: 'ASMR 언박싱', videoCount: 3, totalViews: 18000, avgViews: 6000, avgCompletionRate: 82, avgEngagementRate: 5.1 },
  { memeType: 'before-after', label: '비포애프터', videoCount: 4, totalViews: 32000, avgViews: 8000, avgCompletionRate: 85, avgEngagementRate: 6.8 },
]

export const categoryPerformanceData: CategoryPerformance[] = [
  { category: '식품/음료', videoCount: 7, totalViews: 42000, avgViews: 6000, avgEngagementRate: 5.4, topMemeType: 'dudungtak', trend: 'up' },
  { category: '뷰티/화장품', videoCount: 5, totalViews: 35000, avgViews: 7000, avgEngagementRate: 4.9, topMemeType: 'before-after', trend: 'up' },
  { category: '패션/의류', videoCount: 4, totalViews: 22000, avgViews: 5500, avgEngagementRate: 4.2, topMemeType: 'mz-flex', trend: 'stable' },
  { category: '전자기기', videoCount: 4, totalViews: 18000, avgViews: 4500, avgEngagementRate: 3.8, topMemeType: 'asmr-unboxing', trend: 'down' },
  { category: '생활용품', videoCount: 3, totalViews: 6000, avgViews: 2000, avgEngagementRate: 3.2, topMemeType: 'real-review', trend: 'stable' },
  { category: '기타', videoCount: 1, totalViews: 2000, avgViews: 2000, avgEngagementRate: 2.8, topMemeType: 'must-buy', trend: 'stable' },
]

// 현실적인 YouTube 조회수 패턴 (주말 상승, 저녁 시간대 피크)
export const trendData: TrendDataPoint[] = [
  // 1주차 (기준선)
  { date: '01/01', views: 2100, engagement: 3.5 },
  { date: '01/02', views: 2400, engagement: 3.8 },
  { date: '01/03', views: 2200, engagement: 3.6 },
  { date: '01/04', views: 2800, engagement: 4.0 }, // 주말
  { date: '01/05', views: 3100, engagement: 4.2 }, // 주말
  { date: '01/06', views: 2900, engagement: 3.9 },
  { date: '01/07', views: 3400, engagement: 4.4 },
  // 2주차 (성장)
  { date: '01/08', views: 3200, engagement: 4.1 },
  { date: '01/09', views: 3600, engagement: 4.3 },
  { date: '01/10', views: 3800, engagement: 4.5 },
  { date: '01/11', views: 4100, engagement: 4.6 }, // 주말
  { date: '01/12', views: 3900, engagement: 4.4 }, // 주말
  { date: '01/13', views: 4300, engagement: 4.7 },
  // 현재 주 (급성장)
  { date: '01/14', views: 4500, engagement: 4.8 },
  { date: '01/15', views: 4200, engagement: 4.5 },
  { date: '01/16', views: 4600, engagement: 4.9 },
  { date: '01/17', views: 4800, engagement: 5.0 },
  { date: '01/18', views: 5100, engagement: 5.2 }, // 주말
  { date: '01/19', views: 5300, engagement: 5.3 }, // 주말
  { date: '01/20', views: 5500, engagement: 5.4 },
  // 예측 데이터
  { date: '01/21', views: 5700, engagement: 5.5, predicted: true },
  { date: '01/22', views: 5900, engagement: 5.6, predicted: true },
  { date: '01/23', views: 6100, engagement: 5.7, predicted: true },
  { date: '01/24', views: 6300, engagement: 5.8, predicted: true },
  { date: '01/25', views: 6500, engagement: 5.9, predicted: true }, // 주말
  { date: '01/26', views: 6700, engagement: 6.0, predicted: true }, // 주말
  { date: '01/27', views: 6900, engagement: 6.1, predicted: true },
]

// 시간대별 조회수 분포 (YouTube Analytics 기반)
export const hourlyViewsDistribution = [
  { hour: 0, percent: 2.1 },
  { hour: 1, percent: 1.2 },
  { hour: 2, percent: 0.8 },
  { hour: 3, percent: 0.5 },
  { hour: 4, percent: 0.4 },
  { hour: 5, percent: 0.6 },
  { hour: 6, percent: 1.5 },
  { hour: 7, percent: 2.8 },
  { hour: 8, percent: 3.5 },
  { hour: 9, percent: 3.2 },
  { hour: 10, percent: 3.0 },
  { hour: 11, percent: 3.5 },
  { hour: 12, percent: 4.5 }, // 점심시간
  { hour: 13, percent: 4.2 },
  { hour: 14, percent: 3.8 },
  { hour: 15, percent: 4.0 },
  { hour: 16, percent: 4.5 },
  { hour: 17, percent: 5.2 },
  { hour: 18, percent: 7.5 }, // 저녁 피크 시작
  { hour: 19, percent: 9.8 }, // 피크
  { hour: 20, percent: 10.5 }, // 최고 피크
  { hour: 21, percent: 9.2 },
  { hour: 22, percent: 7.8 },
  { hour: 23, percent: 4.5 },
]

// trendInsights는 이제 generateInsights 함수로 동적 생성됨 (analytics.ts 참고)
// 아래는 기본 fallback용 데이터
export const trendInsights: TrendInsight[] = []

export const analyticsSummary: AnalyticsSummary = {
  totalVideos: 4,
  totalViews: 125400,
  avgEngagement: 5.2,
  topCategory: '뷰티/화장품',
  topMemeType: 'before-after',
  viewsChange: 47,
  engagementChange: 18,
}
