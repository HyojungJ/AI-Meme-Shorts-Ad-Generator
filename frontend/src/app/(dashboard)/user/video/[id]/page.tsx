'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import {
  videoApi,
  scenarioApi,
  finalApi,
  clientAnalyticsApi
} from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { logger } from '@/lib/logger'
import { VideoDetailSkeleton } from '@/components/ui/Skeleton'
import { useGeneration } from '@/contexts/GenerationContext'
import { STATUS_CONFIG_WITH_BORDER, STATUS_PROGRESS } from '@/lib/constants'
import type { Video, VideoMetrics, ScenarioVersion, VideoStatus } from '@/types'
import { ProgressBar } from './_components/ProgressBar'
import { VideoInfoCards } from './_components/VideoInfoCards'
import { AssetReview } from './_components/AssetReview'
import { GeneratingStatus } from './_components/GeneratingStatus'
import { ScenarioReview } from './_components/ScenarioReview'
import { CompletedVideo } from './_components/CompletedVideo'
import { PerformanceTab } from './_components/PerformanceTab'

function getProgressPercentage(status: string, backendProgress?: number): number {
  // 백엔드에서 제공하는 실제 진행률 우선 사용
  if (backendProgress !== undefined && backendProgress > 0) {
    return backendProgress
  }
  // fallback: 상태 기반 기본값
  return STATUS_PROGRESS[status] ?? 0
}

function getStepIndex(status: string, regeneratingType?: 'character' | 'voice' | null): number {
  const map: Record<string, number> = {
    pending: 0,
    character_generating: 1,
    generating_character: 1, // 백엔드에서 보내는 상태
    voice_generating: 2,
    character_review: 3,
    voice_review: 3,
    asset_generating: 1,
    asset_review: 3,
    scenario_generating: 4,
    scenario_review: 6,
    content_generating: 4,
    video_generating: 5,
    video_review: 6,
    completed: 7,
    failed: -1,
  }

  // generating_character 상태일 때 regeneratingType으로 구분
  if (status === 'generating_character') {
    if (regeneratingType === 'character') {
      return 1 // 이미지 생성
    } else if (regeneratingType === 'voice') {
      return 2 // 음성 생성
    }
    // regeneratingType이 없으면 기본값 (처음 생성 시)
    return 1
  }

  return map[status] ?? 0
}

function isAssetReviewStatus(status: string): boolean {
  return ['character_review', 'voice_review', 'asset_review'].includes(status)
}

function isGeneratingStatus(status: string): boolean {
  return ['pending', 'scenario_generating', 'video_generating', 'character_generating', 'voice_generating', 'asset_generating', 'content_generating', 'generating_character'].includes(status)
}

export default function VideoDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { showToast } = useToast()
  const { getTask } = useGeneration()
  const [video, setVideo] = useState<Video | null>(null)
  const [metrics, setMetrics] = useState<VideoMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'info' | 'performance'>('info')
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [showCharacterRevision, setShowCharacterRevision] = useState(false)
  const [showVoiceRevision, setShowVoiceRevision] = useState(false)
  const [characterFeedback, setCharacterFeedback] = useState('')
  const [voiceFeedback, setVoiceFeedback] = useState('')
  const [sceneScenarioFeedbacks, setSceneScenarioFeedbacks] = useState<Record<number, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [loadError, setLoadError] = useState<'not_found' | 'server_error' | null>(null)
  const [retrying, setRetrying] = useState(false)
  const [scenarioVersions, setScenarioVersions] = useState<ScenarioVersion[]>([])
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null)
  const [loadingVersions, setLoadingVersions] = useState(false)
  const [regeneratingType, setRegeneratingType] = useState<'character' | 'voice' | null>(null)
  const autoScenarioTriggeredRef = useRef(false)

  const videoId = Array.isArray(params.id) ? params.id[0] : (params.id as string)
  const generationTask = getTask(videoId)

  const fetchVideo = useCallback(async () => {
    const id = videoId
    setLoadError(null)
    try {
      const v = await videoApi.getProjectById(id)
      logger.debug('VideoDetail', 'Received video data:', { id, status: v?.status, title: v?.title })

      // 재생성이 완료되면 regeneratingType 초기화
      if (v && regeneratingType) {
        if (regeneratingType === 'character' && v.status !== ('generating_character' as VideoStatus)) {
          setRegeneratingType(null)
        } else if (regeneratingType === 'voice' && v.status !== ('generating_character' as VideoStatus)) {
          setRegeneratingType(null)
        }
      }

      // 시나리오 검수 상태일 때 씬 데이터 추가 로드
      if (v && (v.status === 'scenario_review' || v.status === 'video_review') && (!v.scenes || v.scenes.length === 0)) {
        try {
          const scenario = await scenarioApi.getScenarioByAd(id)
          if (scenario?.scenes) {
            v.scenes = scenario.scenes
          }
        } catch {
          // 시나리오 조회 실패는 무시 (아직 생성 중일 수 있음)
        }
      }
      setVideo(v)

      // 시나리오 검수 또는 영상 검수 상태일 때 버전 히스토리 로드
      if (v && (v.status === 'scenario_review' || v.status === 'video_review')) {
        fetchScenarioVersions(id)
      }

      // 완료된 영상이고 videoId가 있으면 실제 성과 데이터 로드
      if (v && v.status === 'completed' && v.videoId) {
        try {
          const performanceData = await clientAnalyticsApi.getVideoPerformance(v.videoId)
          // VideoPerformanceResponse를 VideoMetrics로 변환
          const transformedMetrics: VideoMetrics = {
            views: performanceData.latest_performance.views,
            likes: performanceData.latest_performance.likes,
            comments: performanceData.latest_performance.comments,
            shares: performanceData.latest_performance.shares,
            watchTime: performanceData.latest_performance.average_view_duration,
            completionRate: performanceData.duration_seconds
              ? Math.round((performanceData.latest_performance.average_view_duration / performanceData.duration_seconds) * 100)
              : 0,
            engagementRate: performanceData.latest_performance.engagement_rate,
            dailyViews: performanceData.timeline.map(t => ({
              date: new Date(t.captured_at).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
              views: t.views
            })),
            hourlyViews: performanceData.hourly_views || []
          }
          setMetrics(transformedMetrics)
        } catch (error) {
          logger.error('VideoDetail', '성과 데이터 로드 실패:', error)
          // 성과 데이터 로드 실패는 무시 (영상은 표시)
        }
      }
    } catch (error: unknown) {
      const isNotFound = error instanceof Error && error.message.includes('404')
      setLoadError(isNotFound ? 'not_found' : 'server_error')
      if (!isNotFound) {
        showToast('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error')
      }
    } finally {
      setLoading(false)
    }
  }, [videoId, showToast, regeneratingType])

  const fetchScenarioVersions = async (adId: string) => {
    setLoadingVersions(true)
    try {
      const versions = await scenarioApi.getScenarioVersions(adId)
      setScenarioVersions(versions)
      // 가장 최신 버전을 기본 선택
      if (versions.length > 0) {
        setSelectedVersionId(versions[0].script_id)
      }
    } catch (error) {
      logger.error('VideoDetail', '시나리오 버전 로드 실패:', error)
    } finally {
      setLoadingVersions(false)
    }
  }

  useEffect(() => {
    fetchVideo()
  }, [fetchVideo])

  useEffect(() => {
    autoScenarioTriggeredRef.current = false
  }, [videoId])

  // Context SSE 상태 변경 감지 → 전체 데이터 새로고침
  useEffect(() => {
    if (!video || !generationTask) return
    if (generationTask.status !== video.status) {
      fetchVideo()
    }
  }, [generationTask?.status, video?.status, fetchVideo])

  const handleDownload = async () => {
    if (!video) return
    if (!video.videoId) {
      showToast('다운로드할 영상이 아직 생성되지 않았습니다', 'error')
      return
    }
    try {
      const videoId = video.videoId
      if (!videoId) {
        showToast('영상 ID를 찾을 수 없습니다', 'error')
        return
      }
      const response = await finalApi.downloadVideo(videoId)
      try {
        const url = new URL(response.download_url)
        if (url.protocol !== 'https:' && url.protocol !== 'http:') {
          showToast('유효하지 않은 다운로드 URL입니다', 'error')
          return
        }
      } catch {
        showToast('유효하지 않은 다운로드 URL입니다', 'error')
        return
      }
      const safeName = video.title.replace(/[^a-zA-Z0-9가-힣\s_-]/g, '_')
      const link = document.createElement('a')
      link.href = response.download_url
      link.download = `${safeName}.mp4`
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      showToast('다운로드가 시작되었습니다', 'success')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '다운로드 실패', 'error')
    }
  }

  const handleShare = async () => {
    const url = window.location.href
    try {
      await navigator.clipboard.writeText(url)
      showToast('링크가 클립보드에 복사되었습니다', 'success')
    } catch {
      showToast('링크 복사에 실패했습니다', 'error')
    }
  }

  const handleRetryGeneration = async () => {
    if (!video) return
    const characterImagePrompt = video.characterImagePrompt
    if (!characterImagePrompt) {
      showToast('캐릭터 스타일 정보가 없습니다. 새로 요청해주세요.', 'error')
      return
    }
    setRetrying(true)
    try {
      await scenarioApi.retryGeneration(video.id, characterImagePrompt)
      showToast('재생성이 시작되었습니다', 'success')
      await fetchVideo()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '재생성 요청 실패', 'error')
    } finally {
      setRetrying(false)
    }
  }

  const toggleVoicePlay = () => {
    if (!video?.voiceSampleUrl) return
    if (isPlaying) {
      audioRef.current?.pause()
      setIsPlaying(false)
    } else {
      if (!audioRef.current || audioRef.current.src !== video.voiceSampleUrl) {
        audioRef.current = new Audio(video.voiceSampleUrl)
        audioRef.current.onended = () => setIsPlaying(false)
      }
      audioRef.current.play().catch(() => setIsPlaying(false))
      setIsPlaying(true)
    }
  }

  // 에셋(캐릭터+음성) 통합 승인 → 시나리오 생성 트리거 (폴링으로 완료 감지)
  const handleApproveAssets = async () => {
    if (!video) return
    const characterId = video.characterId
    if (!characterId) {
      showToast('캐릭터 정보를 찾을 수 없습니다', 'error')
      return
    }
    setSubmitting(true)
    let currentStep = ''
    try {
      // 1. 승인 처리
      currentStep = '캐릭터 승인'
      await scenarioApi.approveCharacter(video.id)
      currentStep = '음성 승인'
      await scenarioApi.approveVoice(video.id)
      showToast('에셋이 승인되었습니다! 시나리오 생성을 시작합니다.', 'success')

      // 2. 콘텐츠 통합 생성 요청 (시나리오+TTS+영상, BackgroundTasks → 폴링으로 완료 감지)
      currentStep = '콘텐츠 생성 요청'
      await scenarioApi.generateContent(video.id)

      // 3. 생성 중 상태로 전환 → 폴링이 완료를 감지
      setVideo(prev => prev ? { ...prev, status: 'content_generating' as Video['status'] } : prev)
      showToast('시나리오와 영상 생성이 시작되었습니다. 완료되면 자동으로 전환됩니다.', 'info')
    } catch (error) {
      const msg = error instanceof Error ? error.message : '알 수 없는 오류'
      showToast(`${currentStep} 단계에서 실패했습니다: ${msg}`, 'error')
      await fetchVideo()
    } finally {
      setSubmitting(false)
    }
  }

  // 기존 캐릭터 사용 시 시나리오 생성부터 자동 시작
  const handleStartScenario = useCallback(async (auto = false) => {
    if (!video) return
    setSubmitting(true)
    try {
      await scenarioApi.approveCharacter(video.id)
      await scenarioApi.approveVoice(video.id)
      await scenarioApi.generateScenario(video.id)
      setVideo(prev => prev ? { ...prev, status: 'scenario_generating' as Video['status'] } : prev)
      showToast(auto ? '시나리오 생성을 자동으로 시작했습니다.' : '시나리오 생성을 시작했습니다.', 'success')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '시나리오 생성 요청 실패', 'error')
      await fetchVideo()
    } finally {
      setSubmitting(false)
    }
  }, [video, fetchVideo, showToast])

  // 기존 캐릭터 선택 + pending 상태면 자동으로 시나리오 시작
  useEffect(() => {
    if (!video) return
    if (video.status !== 'pending') return
    if (!video.characterId) return
    if (submitting) return
    if (autoScenarioTriggeredRef.current) return
    autoScenarioTriggeredRef.current = true
    handleStartScenario(true)
  }, [video, submitting, handleStartScenario])

  // 캐릭터 수정 요청 (피드백 포함)
  const handleReviseCharacter = async () => {
    if (!video || !characterFeedback.trim()) {
      showToast('수정 요청 내용을 입력해주세요.', 'error')
      return
    }
    if (characterFeedback.length > 1000) {
      showToast('수정 요청은 1000자 이내로 입력해주세요.', 'error')
      return
    }
    const characterId = video.characterId
    if (!characterId) {
      showToast('캐릭터 정보를 찾을 수 없습니다', 'error')
      return
    }
    setSubmitting(true)
    setRegeneratingType('character') // 캐릭터 재생성 중임을 표시
    try {
      await scenarioApi.reviseCharacter(video.id, characterFeedback)
      await fetchVideo()
      setCharacterFeedback('')
      setShowCharacterRevision(false)
      showToast('캐릭터 수정 요청이 접수되었습니다.', 'info')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '수정 요청 실패', 'error')
      setRegeneratingType(null)
    } finally {
      setSubmitting(false)
    }
  }

  // 음성 수정 요청 (피드백 포함)
  const handleReviseVoice = async () => {
    if (!video || !voiceFeedback.trim()) {
      showToast('수정 요청 내용을 입력해주세요.', 'error')
      return
    }
    if (voiceFeedback.length > 1000) {
      showToast('수정 요청은 1000자 이내로 입력해주세요.', 'error')
      return
    }
    const characterId = video.characterId
    if (!characterId) {
      showToast('캐릭터 정보를 찾을 수 없습니다', 'error')
      return
    }
    setSubmitting(true)
    setRegeneratingType('voice') // 음성 재생성 중임을 표시
    try {
      await scenarioApi.reviseVoice(video.id, voiceFeedback)
      await fetchVideo()
      setVoiceFeedback('')
      setShowVoiceRevision(false)
      showToast('음성 수정 요청이 접수되었습니다.', 'info')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '수정 요청 실패', 'error')
      setRegeneratingType(null)
    } finally {
      setSubmitting(false)
    }
  }

  // 시나리오+영상 최종 승인 (통합 API)
  const handleApproveScenario = async () => {
    if (!video) return
    setSubmitting(true)
    try {
      await scenarioApi.approveContent(video.id)
      await fetchVideo()
      showToast('시나리오와 영상이 최종 승인되었습니다.', 'success')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '최종 승인 실패', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  // 시나리오+영상 통합 수정 요청 (단일 API 호출)
  const handleReviseScenarioWithScenes = async () => {
    if (!video) return
    const sceneRevisions = Object.keys(sceneScenarioFeedbacks)
      .map(Number)
      .filter(sceneNumber => sceneScenarioFeedbacks[sceneNumber]?.trim())
      .map(sceneNumber => ({
        scene_number: sceneNumber,
        scenario_notes: sceneScenarioFeedbacks[sceneNumber].trim(),
      }))

    if (sceneRevisions.length === 0) {
      showToast('수정할 내용을 입력해주세요.', 'error')
      return
    }

    setSubmitting(true)
    try {
      await scenarioApi.reviseContent(video.id, sceneRevisions)

      showToast('수정이 반영되어 시나리오와 영상을 재생성 중입니다.', 'info')
      setSceneScenarioFeedbacks({})

      // 서버 상태 새로고침
      await fetchVideo()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '수정 요청 실패', 'error')
      await fetchVideo()
    } finally {
      setSubmitting(false)
    }
  }


  if (loading) {
    return <VideoDetailSkeleton />
  }

  if (!video) {
    return (
      <div className="text-center py-20">
        {loadError === 'server_error' ? (
          <>
            <p className="text-red-400 mb-2">서버 오류가 발생했습니다</p>
            <p className="text-[var(--color-text-secondary)] mb-4">잠시 후 다시 시도해주세요.</p>
            <button
              onClick={() => { setLoading(true); fetchVideo(); }}
              className="px-4 py-2 btn-primary rounded-lg mr-3"
            >
              다시 시도
            </button>
            <Link href="/user" className="text-[var(--color-text-secondary)] hover:underline">
              목록으로 돌아가기
            </Link>
          </>
        ) : (
          <>
            <p className="text-[var(--color-text-secondary)] mb-4">
              {loadError === 'not_found' ? '프로젝트를 찾을 수 없습니다' : '프로젝트가 아직 생성되지 않았습니다'}
            </p>
            <Link href="/user" className="text-[var(--gradient-1)] hover:underline">
              목록으로 돌아가기
            </Link>
          </>
        )}
      </div>
    )
  }

  const status = STATUS_CONFIG_WITH_BORDER[video.status] || { text: video.status, color: 'text-[var(--color-text-tertiary)]', bgColor: 'bg-[var(--color-bg-muted)] border-[var(--color-border)]' }
  const currentStep = getStepIndex(video.status, regeneratingType)

  return (
    <div className="max-w-4xl mx-auto font-body">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link href="/user" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
          My Videos
        </Link>
        <span className="text-[var(--color-text-tertiary)]">/</span>
        <span className="text-[var(--color-text)]">{video.title}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-display font-bold text-[var(--color-text)]">{video.title}</h1>
            <span aria-live="polite" className={`px-3 py-1 text-xs font-medium rounded-full border ${status.bgColor} ${status.color}`}>
              {status.text}
            </span>
          </div>
          <p className="text-[var(--color-text-secondary)]">{video.companyName} · {video.productCategory}</p>
        </div>
        <button
          onClick={() => router.back()}
          className="px-4 py-2 glass-card text-[var(--color-text)] rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
        >
          뒤로가기
        </button>
      </div>

      {/* Tabs (only for completed videos) */}
      {video.status === 'completed' && (
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('info')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'info'
                ? 'btn-primary'
                : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
          >
            영상 정보
          </button>
          <button
            onClick={() => setActiveTab('performance')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'performance'
                ? 'btn-primary'
                : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
          >
            성과 분석
          </button>
        </div>
      )}

      {/* Info Tab Content */}
      {(activeTab === 'info' || video.status !== 'completed') && (
        <>
          <ProgressBar currentStep={currentStep} />

          <VideoInfoCards video={video} />

          {isAssetReviewStatus(video.status) && (
            <AssetReview
              video={video}
              showCharacterRevision={showCharacterRevision}
              setShowCharacterRevision={setShowCharacterRevision}
              showVoiceRevision={showVoiceRevision}
              setShowVoiceRevision={setShowVoiceRevision}
              characterFeedback={characterFeedback}
              setCharacterFeedback={setCharacterFeedback}
              voiceFeedback={voiceFeedback}
              setVoiceFeedback={setVoiceFeedback}
              submitting={submitting}
              isPlaying={isPlaying}
              handleReviseCharacter={handleReviseCharacter}
              handleReviseVoice={handleReviseVoice}
              handleApproveAssets={handleApproveAssets}
              toggleVoicePlay={toggleVoicePlay}
            />
          )}

          {isGeneratingStatus(video.status) && (
            <GeneratingStatus
              status={video.status}
              regeneratingType={regeneratingType}
              submitting={submitting}
              retrying={retrying}
              progressPercentage={video.progressPercentage}
              getProgressPercentage={getProgressPercentage}
              handleStartScenario={handleStartScenario}
              handleRetryGeneration={handleRetryGeneration}
            />
          )}

          {video.status === 'failed' && (
            <GeneratingStatus
              status={video.status}
              regeneratingType={regeneratingType}
              submitting={submitting}
              retrying={retrying}
              progressPercentage={video.progressPercentage}
              getProgressPercentage={getProgressPercentage}
              handleStartScenario={handleStartScenario}
              handleRetryGeneration={handleRetryGeneration}
            />
          )}

          {(video.status === 'scenario_review' || video.status === 'video_review') && (
            <ScenarioReview
              video={video}
              scenarioVersions={scenarioVersions}
              selectedVersionId={selectedVersionId}
              setSelectedVersionId={setSelectedVersionId}
              loadingVersions={loadingVersions}
              sceneScenarioFeedbacks={sceneScenarioFeedbacks}
              setSceneScenarioFeedbacks={setSceneScenarioFeedbacks}
              submitting={submitting}
              handleApproveScenario={handleApproveScenario}
              handleReviseScenarioWithScenes={handleReviseScenarioWithScenes}
            />
          )}

          {video.status === 'completed' && (
            <CompletedVideo
              video={video}
              isPlaying={isPlaying}
              toggleVoicePlay={toggleVoicePlay}
              handleDownload={handleDownload}
              handleShare={handleShare}
            />
          )}
        </>
      )}

      {/* Performance Tab Content */}
      {activeTab === 'performance' && video.status === 'completed' && metrics && (
        <PerformanceTab metrics={metrics} />
      )}
    </div>
  )
}
