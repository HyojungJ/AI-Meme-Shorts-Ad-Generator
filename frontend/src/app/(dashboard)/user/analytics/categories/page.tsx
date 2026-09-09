'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { clientAnalyticsApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import type { CategoryPerformance } from '@/types'

export default function UserCategoriesAnalyticsPage() {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [categoryData, setCategoryData] = useState<CategoryPerformance[]>([])

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const data = await clientAnalyticsApi.getMyCategories()
        setCategoryData(data)
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
            <span className="text-[var(--color-text)]">카테고리별 분석</span>
          </div>
          <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">카테고리별 성과 분석</h1>
          <p className="text-[var(--color-text-secondary)]">제품 카테고리별 영상 성과를 비교하세요</p>
        </div>
      </div>

      {/* Category List */}
      <div className="glass-card p-6">
        {categoryData.length > 0 ? (
          <div className="space-y-3">
            {categoryData.map((category, index) => (
              <div
                key={category.category}
                className="flex items-center justify-between p-4 bg-[var(--color-bg-muted)] rounded-xl hover:bg-[var(--color-bg-muted)]/80 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <span className="w-8 h-8 bg-[var(--color-bg-card)] rounded-lg flex items-center justify-center text-sm text-[var(--color-text-tertiary)] font-display font-bold">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-[var(--color-text)] font-display font-medium">{category.category}</p>
                    <p className="text-xs text-[var(--color-text-tertiary)]">{category.videoCount}개 영상</p>
                  </div>
                  {category.trend === 'up' && <span className="text-emerald-400 text-sm">↑</span>}
                  {category.trend === 'down' && <span className="text-red-400 text-sm">↓</span>}
                </div>
                <div className="text-right">
                  <p className="text-[var(--color-text)] font-display font-bold text-lg">{category.avgViews.toLocaleString()}</p>
                  <p className="text-[var(--color-text-tertiary)] text-xs">평균 조회수</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}
            >
              <svg className="w-8 h-8 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
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
