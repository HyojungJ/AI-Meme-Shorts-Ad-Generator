'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { clientAnalyticsApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { getMemeTypeConfig } from '@/lib/constants'
import type { MemePerformance } from '@/types'

export default function UserMemesAnalyticsPage() {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [memeData, setMemeData] = useState<MemePerformance[]>([])

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const data = await clientAnalyticsApi.getMyMemes()
        setMemeData(data)
      } catch (error) {
        showToast(error instanceof Error ? error.message : '데이터 로딩 실패', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [showToast])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 font-body">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm mb-2">
            <Link href="/main" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
              Dashboard
            </Link>
            <span className="text-[var(--color-text-tertiary)]">/</span>
            <span className="text-[var(--color-text)]">밈별 분석</span>
          </div>
          <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">밈별 성과 분석</h1>
          <p className="text-[var(--color-text-secondary)]">밈 유형별 영상 성과를 비교하세요</p>
        </div>
      </div>

      {/* Meme List */}
      <div className="glass-card p-6">
        {memeData.length > 0 ? (
          <div className="space-y-3">
            {memeData.map((meme, index) => {
              const config = getMemeTypeConfig(meme.memeType)
              return (
                <div
                  key={`${meme.memeType}-${meme.label}-${index}`}
                  className="flex items-center justify-between p-4 bg-[var(--color-bg-muted)] rounded-xl hover:bg-[var(--color-bg-muted)]/80 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <span className="w-8 h-8 bg-[var(--color-bg-card)] rounded-lg flex items-center justify-center text-sm text-[var(--color-text-tertiary)] font-display font-bold">
                      {index + 1}
                    </span>
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: config.color }} />
                    <div>
                      <p className="text-[var(--color-text)] font-display font-medium">{meme.label}</p>
                      <p className="text-xs text-[var(--color-text-tertiary)]">{meme.videoCount}개 영상</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[var(--color-text)] font-display font-bold text-lg">{meme.avgViews.toLocaleString()}</p>
                    <p className="text-[var(--color-text-tertiary)] text-xs">평균 조회수</p>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}
            >
              <svg className="w-8 h-8 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-[var(--color-text)] font-medium mb-2">데이터가 없습니다</p>
            <p className="text-[var(--color-text-secondary)] text-sm">아직 완료된 영상이 없거나 성과 데이터가 수집되지 않았습니다</p>
          </div>
        )}
      </div>
    </div>
  )
}
