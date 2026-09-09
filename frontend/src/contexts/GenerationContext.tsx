'use client'

import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/components/ui/Toast'
import { getAccessToken } from '@/lib/api'
import { API_URL } from '@/lib/config'
import type { VideoStatus } from '@/types'

type GenerationTask = {
  adId: string
  status: VideoStatus
  currentStage: string | null
  progress: number
}

type Notification = {
  id: number
  adId: string
  message: string
  type: 'success' | 'info'
  timestamp: number
  read: boolean
}

type GenerationContextType = {
  tasks: Map<string, GenerationTask>
  notifications: Notification[]
  unreadCount: number
  isGenerating: (adId: string) => boolean
  getTask: (adId: string) => GenerationTask | undefined
  markAllRead: () => void
  clearNotifications: () => void
}

const GenerationContext = createContext<GenerationContextType | null>(null)

const TERMINAL_STATUSES: VideoStatus[] = ['completed', 'failed']
const GENERATING_STATUSES: VideoStatus[] = [
  'character_generating', 'voice_generating', 'scenario_generating', 'video_generating',
  'asset_generating', 'content_generating',
]

const STAGE_LABELS: Record<string, string> = {
  character_review: '캐릭터/음성 검수가 필요합니다',
  voice_review: '음성 검수가 필요합니다',
  scenario_review: '시나리오 검수가 필요합니다',
  video_review: '영상 검수가 필요합니다',
  asset_pending: '캐릭터/음성 검수가 필요합니다',
  content_pending: '시나리오/영상 검수가 필요합니다',
  completed: '영상 생성이 완료되었습니다',
  failed: '생성 중 오류가 발생했습니다',
}

function mapBackendStatus(status: string, currentStage: string | null): VideoStatus {
  const map: Record<string, VideoStatus> = {
    draft: 'pending',
    created: 'pending',
    generating_character: 'character_generating',
    generating_voice: 'voice_generating',
    generating_scenario: 'scenario_generating',
    generating_video: 'video_generating',
    asset_generating: 'asset_generating',
    content_generating: 'content_generating',
    asset_pending: 'asset_pending',
    asset_approved: 'asset_approved',
    content_pending: 'content_pending',
    completed: 'completed',
    failed: 'failed',
  }

  if (map[status]) return map[status]

  if (status === 'pending_approval' || status === 'pending') {
    if (currentStage === 'character_generation') return 'character_review'
    if (currentStage === 'voice_generation') return 'voice_review'
    if (currentStage === 'scenario_generation') return 'scenario_review'
    if (currentStage === 'video_generation') return 'video_review'
    return 'pending'
  }

  const directStatuses: VideoStatus[] = [
    'pending', 'character_generating', 'character_review',
    'voice_generating', 'voice_review', 'scenario_generating',
    'scenario_review', 'video_generating', 'video_review',
    'asset_generating', 'asset_pending', 'asset_approved',
    'content_generating', 'content_pending', 'completed', 'failed',
  ]
  if (directStatuses.includes(status as VideoStatus)) return status as VideoStatus

  return 'pending'
}

export function GenerationProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [tasks, setTasks] = useState<Map<string, GenerationTask>>(new Map())
  const [notifications, setNotifications] = useState<Notification[]>([])
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevTasksRef = useRef<Map<string, GenerationTask>>(new Map())
  const retryCountRef = useRef(0)
  const MAX_SSE_RETRIES = 10
  const BASE_RETRY_MS = 1000

  const connect = useCallback(() => {
    const token = getAccessToken()
    if (!token) return

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const es = new EventSource(`${API_URL}/api/v1/sse/generation-status?token=${token}`)
    eventSourceRef.current = es

    es.onmessage = (event) => {
      retryCountRef.current = 0 // 성공 시 재시도 카운트 초기화

      const data = JSON.parse(event.data) as {
        ad_id: number
        status: string
        current_stage: string | null
        progress: number
      }

      const adId = String(data.ad_id)
      const mappedStatus = mapBackendStatus(data.status, data.current_stage)

      setTasks(prev => {
        const next = new Map(prev)
        next.set(adId, {
          adId,
          status: mappedStatus,
          currentStage: data.current_stage,
          progress: data.progress,
        })
        return next
      })
    }

    es.onerror = () => {
      es.close()
      eventSourceRef.current = null

      if (retryCountRef.current >= MAX_SSE_RETRIES) {
        showToast('실시간 업데이트 연결이 끊어졌습니다. 페이지를 새로고침해주세요.', 'error')
        return
      }

      const delay = Math.min(BASE_RETRY_MS * Math.pow(2, retryCountRef.current), 30000)
      retryCountRef.current += 1
      reconnectTimerRef.current = setTimeout(connect, delay)
    }
  }, [showToast])

  useEffect(() => {
    if (user) {
      retryCountRef.current = 0
      connect()
    } else {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      retryCountRef.current = 0
      setTasks(new Map())
      setNotifications([])
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current)
      }
    }
  }, [user, connect])

  // 탭 복귀 시 SSE 재연결
  useEffect(() => {
    function handleVisibilityChange() {
      if (document.visibilityState === 'visible' && user && !eventSourceRef.current) {
        retryCountRef.current = 0
        connect()
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [user, connect])

  // 상태 전환 감지 → 토스트 + 알림
  useEffect(() => {
    const prev = prevTasksRef.current
    tasks.forEach((task, adId) => {
      const prevTask = prev.get(adId)
      if (!prevTask) return

      const wasGenerating = GENERATING_STATUSES.includes(prevTask.status)
      const nowTerminal = TERMINAL_STATUSES.includes(task.status)
      const nowReview = task.status.endsWith('_review')

      if (wasGenerating && (nowTerminal || nowReview)) {
        const message = STAGE_LABELS[task.status] || '상태가 변경되었습니다'
        const type = nowTerminal ? 'success' as const : 'info' as const

        showToast(message, type)

        setNotifications(prev => [{
          id: Date.now(),
          adId,
          message,
          type,
          timestamp: Date.now(),
          read: false,
        }, ...prev].slice(0, 20)) // 최대 20개
      }
    })
    prevTasksRef.current = new Map(tasks)
  }, [tasks, showToast])

  const unreadCount = notifications.filter(n => !n.read).length

  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }, [])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const isGenerating = useCallback((adId: string) => {
    const task = tasks.get(adId)
    return task ? GENERATING_STATUSES.includes(task.status) : false
  }, [tasks])

  const getTask = useCallback((adId: string) => {
    return tasks.get(adId)
  }, [tasks])

  return (
    <GenerationContext.Provider value={{
      tasks, notifications, unreadCount,
      isGenerating, getTask, markAllRead, clearNotifications,
    }}>
      {children}
    </GenerationContext.Provider>
  )
}

export function useGeneration() {
  const context = useContext(GenerationContext)
  if (!context) {
    throw new Error('useGeneration must be used within GenerationProvider')
  }
  return context
}
