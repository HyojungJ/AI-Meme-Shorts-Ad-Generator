'use client'

import { useState, useEffect, useCallback } from 'react'
import { adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { getAdminStatusConfig } from '@/lib/constants'
import type { Video } from '@/types'

type VideoListItem = {
  id: string
  title: string
  company: string
  status: string
  views: number
  createdAt: string
}

const filterColors: Record<string, string> = {
  all: 'var(--gradient-1)',
  processing: 'var(--gradient-3)',
  completed: 'var(--gradient-4)',
  client_approved: 'var(--gradient-2)',
  published: 'var(--gradient-5)',
  failed: '#ef4444',
}

function VideoDetailModal({
  video,
  onClose,
  onPublish,
  onHold,
}: {
  video: Video
  onClose: () => void
  onPublish: () => void
  onHold: () => void
}) {
  const config = getAdminStatusConfig(video.status)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative glass-card w-full max-w-lg p-6">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <h2 className="text-xl font-display font-bold text-[var(--color-text)] mb-6">영상 상세 정보</h2>

        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <span className="text-[var(--color-text-secondary)]">제목</span>
            <span className="text-[var(--color-text)] text-right max-w-[60%]">{video.title}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">상태</span>
            <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${config.bgColor} ${config.color}`}>
              {config.label}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">생성일</span>
            <span className="text-[var(--color-text)]">{video.createdAt}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">회사</span>
            <span className="text-[var(--color-text)]">{video.companyName || '-'}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">카테고리</span>
            <span className="text-[var(--color-text)]">{video.productCategory || '-'}</span>
          </div>
          {video.productHighlight && (
            <div className="flex justify-between items-start">
              <span className="text-[var(--color-text-secondary)]">특징</span>
              <span className="text-[var(--color-text)] text-right max-w-[60%]">{video.productHighlight}</span>
            </div>
          )}
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">조회수</span>
            <span className="text-[var(--color-text)] font-display">{video.views?.toLocaleString() || 0}</span>
          </div>
        </div>

        <div className="flex gap-3 mt-8">
          {(video.status === 'client_approved' || video.status === 'admin_approved') && (
            <button
              onClick={onPublish}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all"
              style={{ background: 'var(--gradient-1)' }}
            >
              게시하기
            </button>
          )}
          {['pending', 'scenario_review', 'character_review', 'voice_review'].includes(video.status) && (
            <button
              onClick={onHold}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
            >
              보류
            </button>
          )}
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium glass-card text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AdminVideosPage() {
  const { showToast } = useToast()
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [videos, setVideos] = useState<VideoListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null)
  const [modalLoading, setModalLoading] = useState(false)

  const fetchVideos = useCallback(async () => {
    try {
      setLoading(true)
      const response = await adminApi.getAllVideos(1, 100)
      setVideos(response.items.map((v: { ad_id?: number; video_id?: number; id?: string; title?: string; company_name?: string; company?: string; status?: string; views?: number; created_at?: string; createdAt?: string }) => ({
        id: String(v.video_id || v.id || 0),
        title: v.title || '제목 없음',
        company: v.company_name || v.company || '-',
        status: v.status || 'pending',
        views: v.views || 0,
        createdAt: (v.created_at || v.createdAt || '').split('T')[0] || '-',
      })))
    } catch (error) {
      showToast(error instanceof Error ? error.message : '영상 목록 로딩 실패', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchVideos()
  }, [fetchVideos])

  const handleOpenDetail = async (videoId: string) => {
    try {
      setModalLoading(true)
      const video = await adminApi.getVideoDetail(videoId)
      setSelectedVideo(video)
    } catch (error) {
      showToast(error instanceof Error ? error.message : '영상 정보 로딩 실패', 'error')
    } finally {
      setModalLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!selectedVideo) return
    try {
      await adminApi.publishVideo(selectedVideo.id, 1)
      showToast('영상이 게시되었습니다', 'success')
      setSelectedVideo(null)
      fetchVideos()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '게시 실패', 'error')
    }
  }

  const handleHold = async () => {
    if (!selectedVideo) return
    try {
      await adminApi.holdVideo(selectedVideo.id)
      showToast('영상이 보류되었습니다', 'success')
      setSelectedVideo(null)
      fetchVideos()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '보류 처리 실패', 'error')
    }
  }

  const filteredVideos = videos.filter(v => {
    const matchesFilter = filter === 'all' || v.status === filter
    const matchesSearch = v.title.toLowerCase().includes(search.toLowerCase()) ||
      v.company.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const totalViews = videos.reduce((acc, v) => acc + v.views, 0)

  return (
    <div className="font-body">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">영상 관리</h1>
          <p className="text-[var(--color-text-secondary)]">전체 영상 목록을 관리합니다</p>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 glass-card flex items-center gap-2">
            <span className="text-[var(--color-text-secondary)] text-sm">총</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{videos.length}</span>
            <span className="text-[var(--color-text-secondary)] text-sm">개</span>
          </div>
          <div className="px-4 py-2 glass-card flex items-center gap-2">
            <span className="text-[var(--color-text-secondary)] text-sm">조회수</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{totalViews.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-xs">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="영상 또는 회사명 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-12 pr-4 py-2.5 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)]"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'processing', 'completed', 'client_approved', 'published', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                filter === status
                  ? 'text-white'
                  : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
              }`}
              style={filter === status ? { background: filterColors[status] } : undefined}
            >
              {status === 'all' ? '전체' : getAdminStatusConfig(status).label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">영상</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">회사</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">상태</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">조회수</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">생성일</th>
              <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">액션</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {filteredVideos.map((video) => {
              const config = getAdminStatusConfig(video.status)
              return (
                <tr key={video.id} className="hover:bg-[var(--color-bg-muted)]/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{ background: 'linear-gradient(135deg, var(--gradient-3)20 0%, var(--gradient-4)20 100%)' }}
                      >
                        <svg className="w-5 h-5 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <span className="font-medium text-[var(--color-text)]">{video.title}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[var(--color-text-secondary)]">{video.company}</td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${config.bgColor} ${config.color}`}>
                      {config.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-[var(--color-text)] font-display">{(video.views ?? 0).toLocaleString()}</td>
                  <td className="px-6 py-4 text-[var(--color-text-secondary)]">{video.createdAt}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleOpenDetail(video.id)}
                      disabled={modalLoading}
                      className="px-3 py-1.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors disabled:opacity-50"
                    >
                      상세
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {filteredVideos.length === 0 && (
          <div className="p-12 text-center">
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, var(--gradient-3)10 0%, var(--gradient-4)10 100%)' }}
            >
              <svg className="w-8 h-8 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-[var(--color-text-secondary)]">검색 결과가 없습니다</p>
          </div>
        )}
      </div>

      {selectedVideo && (
        <VideoDetailModal
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
          onPublish={handlePublish}
          onHold={handleHold}
        />
      )}
    </div>
  )
}
