'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { videoApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { useGeneration } from '@/contexts/GenerationContext'
import { STATUS_CONFIG } from '@/lib/constants'
import { isReviewStatus, isGeneratingStatus, isPendingStatus } from '@/lib/utils/status-helpers'
import { VideoCardSkeleton } from '@/components/ui/Skeleton'
import type { Video } from '@/types'

const ITEMS_PER_PAGE = 6

const statusColors: Record<string, string> = {
  pending: 'var(--gradient-2)',
  generating: 'var(--gradient-3)',
  review: 'var(--gradient-5)',
  completed: 'var(--gradient-1)',
  failed: 'var(--status-error-text, #ef4444)',
}

export default function UserPage() {
  const router = useRouter()
  const { showToast } = useToast()
  const { tasks } = useGeneration()
  const [filter, setFilter] = useState<string>('all')
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  const fetchVideos = useCallback(async () => {
    try {
      setLoading(true)
      const response = await videoApi.getMyProjects()
      setVideos(response.items)
    } catch (error) {
      showToast(error instanceof Error ? error.message : '영상 목록 로딩 실패', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchVideos()
  }, [fetchVideos])

  // SSE 상태로 실시간 갱신 (제거 - API 상태 사용)
  // const videosWithLiveStatus = useMemo(() => videos.map(v => {
  //   const task = tasks.get(v.id)
  //   return (task && task.status !== v.status) ? { ...v, status: task.status } : v
  // }), [videos, tasks])

  // SSE 상태 변경 시 전체 목록 새로고침
  const videosRef = useRef(videos)
  videosRef.current = videos

  useEffect(() => {
    const hasStatusChange = Array.from(tasks.values()).some(task => {
      const video = videosRef.current.find(v => v.id === task.adId)
      return video && task.status !== video.status
    })
    if (hasStatusChange) {
      fetchVideos()
    }
  }, [tasks, fetchVideos])

  const handleDelete = (id: string, title: string) => {
    setDeleteTarget({ id, title })
  }

  const confirmDelete = async () => {
    if (deleteTarget) {
      try {
        await videoApi.deleteProject(deleteTarget.id)
        await fetchVideos()
        showToast('영상이 삭제되었습니다', 'success')
      } catch (error) {
        showToast(error instanceof Error ? error.message : '삭제 실패', 'error')
      } finally {
        setDeleteTarget(null)
      }
    }
  }

  const filteredVideos = videos.filter((v) => {
    if (filter === 'all') return true
    if (filter === 'pending') return isPendingStatus(v.status)
    if (filter === 'generating') return isGeneratingStatus(v.status)
    if (filter === 'review') return isReviewStatus(v.status)
    if (filter === 'failed') return v.status === 'failed'
    return v.status === filter
  })

  const totalPages = Math.ceil(filteredVideos.length / ITEMS_PER_PAGE)
  const paginatedVideos = filteredVideos.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  useEffect(() => {
    setCurrentPage(1)
  }, [filter])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && deleteTarget) {
        setDeleteTarget(null)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [deleteTarget])

  const pendingCount = videos.filter((v) => isPendingStatus(v.status)).length
  const generatingCount = videos.filter((v) => isGeneratingStatus(v.status)).length
  const reviewCount = videos.filter((v) => isReviewStatus(v.status)).length
  const completedCount = videos.filter((v) => v.status === 'completed').length
  const failedCount = videos.filter((v) => v.status === 'failed').length

  const filterButtons = [
    { value: 'all', label: '전체', count: videos.length },
    { value: 'pending', label: '대기', count: pendingCount },
    { value: 'generating', label: '생성중', count: generatingCount },
    { value: 'review', label: '검수중', count: reviewCount },
    { value: 'completed', label: '완료', count: completedCount },
    ...(failedCount > 0 ? [{ value: 'failed', label: '실패', count: failedCount }] : []),
  ]

  return (
    <div className="font-body">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">My Videos</h1>
          <p className="text-[var(--color-text-secondary)] text-sm md:text-base">제작 요청한 영상들을 관리하세요</p>
        </div>
        <button
          onClick={() => router.push('/user/request')}
          className="btn-primary w-full md:w-auto"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 영상 요청
        </button>
      </div>

      {/* Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 -mx-1 px-1 mb-5">
        {filterButtons.map((item) => (
          <button
            key={item.value}
            onClick={() => setFilter(item.value)}
            className={`px-3 py-2 rounded-xl text-xs font-display font-medium transition-all flex items-center gap-1.5 whitespace-nowrap shrink-0 ${
              filter === item.value
                ? 'text-white'
                : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
            style={filter === item.value ? { background: `linear-gradient(135deg, ${statusColors[item.value] || 'var(--gradient-1)'} 0%, var(--gradient-4) 100%)` } : undefined}
          >
            {item.label}
            <span
              className={`px-1.5 py-0.5 rounded text-xs ${
                filter === item.value ? 'bg-white/20' : 'bg-[var(--color-bg-muted)]'
              }`}
            >
              {item.count}
            </span>
          </button>
        ))}
      </div>

      {/* Video Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <VideoCardSkeleton key={i} />
          ))}
        </div>
      ) : paginatedVideos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {paginatedVideos.map((video) => {
            const status = STATUS_CONFIG[video.status] || STATUS_CONFIG.pending
            const statusColor = statusColors[video.status] || statusColors.pending
            const thumbnailUrl = video.sceneImageUrl || ''
            return (
              <div
                key={video.id}
                role="link"
                tabIndex={0}
                className={`glass-card glow overflow-hidden transition-all group cursor-pointer`}
                onClick={() => router.push(`/user/video/${video.id}`)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); router.push(`/user/video/${video.id}`) } }}
              >
                {/* Thumbnail */}
                <div className="aspect-video relative" style={{ background: `linear-gradient(135deg, ${statusColor}10 0%, ${statusColor}20 100%)` }}>
                  {/* Placeholder (이미지 로드 실패 시 보임) */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div
                      className="w-12 h-12 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform"
                      style={{ background: `linear-gradient(135deg, ${statusColor}30 0%, ${statusColor}50 100%)` }}
                    >
                      <svg className="w-6 h-6" style={{ color: statusColor }} fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  {/* 썸네일 이미지 (로드 성공 시 placeholder 위에 덮음) */}
                  {thumbnailUrl && (
                    <img
                      src={thumbnailUrl}
                      alt={`${video.title} 씬 이미지`}
                      className="absolute inset-0 w-full h-full object-cover"
                      loading="lazy"
                      onError={(e) => { e.currentTarget.style.display = 'none' }}
                    />
                  )}
                  {/* Status badge */}
                  <div
                    className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-lg text-xs font-display font-medium text-white"
                    style={{ background: statusColor }}
                  >
                    {status.text}
                  </div>
                </div>

                {/* Info */}
                <div className="p-4">
                  <h3 className="text-sm font-display font-medium text-[var(--color-text)] mb-1.5 truncate">{video.title}</h3>
                  <div className="flex items-center text-xs">
                    <span className="text-[var(--color-text-tertiary)]">{video.createdAt}</span>
                  </div>

                  {/* Actions */}
                  <div className="mt-3 pt-3 border-t border-[var(--color-border)] flex gap-2">
                    {video.status === 'completed' && (
                      <>
                        <button className="flex-1 btn-primary text-xs py-2">
                          미리보기
                        </button>
                        <button className="px-2.5 py-2 glass-card text-[var(--color-text)] text-xs rounded-xl hover:border-[var(--color-border-strong)] transition-colors" aria-label="다운로드">
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                        </button>
                      </>
                    )}
                    {isReviewStatus(video.status) && (
                      <button
                        className="flex-1 px-3 py-2 text-xs font-display font-medium rounded-xl transition-colors"
                        style={{ background: `${statusColors.review}20`, color: statusColors.review }}
                      >
                        검수 필요
                      </button>
                    )}
                    {isGeneratingStatus(video.status) && (
                      <div
                        className="flex-1 px-3 py-2 text-xs text-center rounded-xl flex items-center justify-center gap-1.5 font-display"
                        style={{ background: `${statusColors.generating}10`, color: statusColors.generating }}
                        role="status"
                      >
                        <div className="w-2.5 h-2.5 border-2 border-current border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                        생성 진행 중...
                      </div>
                    )}
                    {isPendingStatus(video.status) && (
                      <div
                        className="flex-1 px-3 py-2 text-xs text-center rounded-xl font-display"
                        style={{ background: `${statusColors.pending}10`, color: statusColors.pending }}
                      >
                        대기 중...
                      </div>
                    )}
                    {video.status === 'failed' && (
                      <div
                        className="flex-1 px-3 py-2 text-xs text-center rounded-xl font-display"
                        style={{ background: `${statusColors.failed}10`, color: statusColors.failed }}
                      >
                        생성 실패
                      </div>
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDelete(video.id, video.title) }}
                      className="px-2.5 py-2 text-[var(--color-text-tertiary)] hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-colors"
                      aria-label={`${video.title} 삭제`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="glass-card p-10 text-center">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-3"
            style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}
          >
            <svg className="w-6 h-6 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm mb-4">아직 영상이 없습니다</p>
          <Link
            href="/user/request"
            className="btn-primary inline-flex text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            첫 영상 요청하기
          </Link>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <nav className="flex items-center justify-center gap-1.5 mt-6" aria-label="페이지 네비게이션">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-2 glass-card rounded-xl text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="이전 페이지"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
            <button
              key={page}
              onClick={() => setCurrentPage(page)}
              aria-label={`${page} 페이지`}
              aria-current={currentPage === page ? 'page' : undefined}
              className={`w-9 h-9 rounded-xl text-xs font-display font-medium transition-colors ${
                currentPage === page
                  ? 'text-white'
                  : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              }`}
              style={currentPage === page ? { background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' } : undefined}
            >
              {page}
            </button>
          ))}
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-2 glass-card rounded-xl text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="다음 페이지"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </nav>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="delete-modal-title">
          <div className="glass-card gradient-border p-6 max-w-sm w-full mx-4 animate-scale-in">
            <h3 id="delete-modal-title" className="text-base font-display font-semibold text-[var(--color-text)] mb-2">영상 삭제</h3>
            <p className="text-[var(--color-text-secondary)] text-sm mb-6">
              "{deleteTarget.title}" 영상을 삭제하시겠습니까?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteTarget(null)}
                className="btn-secondary text-sm px-4 py-2"
              >
                취소
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 bg-red-500 text-white text-sm font-display font-medium rounded-xl hover:bg-red-600 transition-colors"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
