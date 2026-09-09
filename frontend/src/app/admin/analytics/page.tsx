'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { analyticsApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { getMemeTypeConfig } from '@/lib/constants'
import type { MemeType, AnalyticsSummary, TrendDataPoint, TrendInsight, MemePerformance, CategoryPerformance } from '@/types'

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2">
        <p className="text-[var(--color-text-tertiary)] text-xs mb-1">{label}</p>
        <p className="text-[var(--color-text)] font-bold text-sm">{payload[0].value.toLocaleString()}</p>
      </div>
    )
  }
  return null
}

export default function AnalyticsPage() {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'1W' | '1M' | '3M'>('1M')
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [insights, setInsights] = useState<TrendInsight[]>([])
  const [memeData, setMemeData] = useState<MemePerformance[]>([])
  const [categoryData, setCategoryData] = useState<CategoryPerformance[]>([])

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [dashboardData, trendsData, memePerfData, catPerfData] = await Promise.all([
        analyticsApi.getDashboard(),
        analyticsApi.getTrends('month'),
        analyticsApi.getTopMemes(5, 'avgViews'),
        analyticsApi.getTopCategories(5, 'avgViews'),
      ])
      setSummary(dashboardData)
      setTrendData(trendsData.data)
      setInsights(trendsData.insights)
      setMemeData(memePerfData)
      setCategoryData(catPerfData)
    } catch (error) {
      showToast(error instanceof Error ? error.message : '데이터 로딩 실패', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const filteredTrendData = period === '1W'
    ? trendData.slice(-7)
    : period === '1M'
    ? trendData.slice(-20)
    : trendData

  if (loading || !summary) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6 font-body">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">성과 분석</h1>
        <p className="text-[var(--color-text-secondary)]">영상, 밈, 카테고리별 성과를 한눈에 확인하세요</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-[var(--gradient-1)]/10 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400">
              +{summary.viewsChange}%
            </span>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">총 조회수</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary.totalViews.toLocaleString()}</p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-[var(--gradient-3)]/10 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <span className="text-xs px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400">
              +{summary.engagementChange}%
            </span>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">평균 참여율</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary.avgEngagement}%</p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 bg-[var(--gradient-4)]/10 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--gradient-4)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">최고 성과 카테고리</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary.topCategory}</p>
        </div>

        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--gradient-2)]/10">
              <svg className="w-5 h-5 text-[var(--gradient-2)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">최고 성과 밈</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary.topMemeType || '-'}</p>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-3 gap-4">
        <Link href="/admin/analytics/memes" className="glass-card p-4 hover:border-[var(--gradient-1)]/30 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--gradient-1)]/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <svg className="w-4 h-4 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-[var(--color-text)] font-medium text-sm">밈별 분석</p>
              <p className="text-[var(--color-text-tertiary)] text-xs">밈 유형별 비교</p>
            </div>
          </div>
        </Link>
        <Link href="/admin/analytics/categories" className="glass-card p-4 hover:border-[var(--gradient-3)]/30 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--gradient-3)]/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <svg className="w-4 h-4 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <div>
              <p className="text-[var(--color-text)] font-medium text-sm">카테고리별</p>
              <p className="text-[var(--color-text-tertiary)] text-xs">카테고리 성과</p>
            </div>
          </div>
        </Link>
        <Link href="/admin/analytics/trends" className="glass-card p-4 hover:border-[var(--gradient-4)]/30 transition-all group">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-[var(--gradient-4)]/10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <svg className="w-4 h-4 text-[var(--gradient-4)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div>
              <p className="text-[var(--color-text)] font-medium text-sm">트렌드</p>
              <p className="text-[var(--color-text-tertiary)] text-xs">추세 및 예측</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Trend Chart */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">조회수 추이</h2>
            <p className="text-sm text-[var(--color-text-secondary)]">일별 총 조회수</p>
          </div>
          <div className="flex gap-2">
            {(['1W', '1M', '3M'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
                  period === p ? 'bg-[var(--gradient-1)]/10 text-[var(--gradient-1)]' : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-muted)]'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredTrendData}>
              <defs>
                <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--gradient-1)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--gradient-1)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} />
              <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="views"
                stroke="var(--gradient-1)"
                strokeWidth={2}
                fill="url(#viewsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Insights */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">주요 인사이트</h2>
          <span className="text-xs text-[var(--color-text-tertiary)]">조회수 기반 자동 분석</span>
        </div>
        {insights.length > 0 ? (
          <div className="grid gap-3">
            {insights.map((insight, i) => (
              <div
                key={i}
                className={`p-4 rounded-xl border ${
                  insight.type === 'positive'
                    ? 'bg-emerald-500/5 border-emerald-500/20'
                    : insight.type === 'negative'
                    ? 'bg-red-500/5 border-red-500/20'
                    : 'bg-[var(--gradient-3)]/5 border-[var(--gradient-3)]/20'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <div className={`w-2 h-2 rounded-full ${
                    insight.type === 'positive' ? 'bg-emerald-400' : insight.type === 'negative' ? 'bg-red-400' : 'bg-[var(--gradient-3)]'
                  }`} />
                  <p className="text-[var(--color-text)] font-medium text-sm">{insight.title}</p>
                </div>
                <p className="text-[var(--color-text-secondary)] text-sm">{insight.description}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-[var(--color-text-tertiary)]">
            <p>데이터가 충분히 수집되면 인사이트가 표시됩니다</p>
          </div>
        )}
      </div>

      {/* Top Performers */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Top Memes */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">밈 TOP 5</h2>
            <Link href="/admin/analytics/memes" className="text-[var(--gradient-1)] text-sm hover:underline">전체 보기</Link>
          </div>
          <div className="space-y-3">
            {memeData.map((meme, i) => (
              <div key={`${meme.memeType}-${meme.label}-${i}`} className="flex items-center justify-between p-3 bg-[var(--color-bg-muted)] rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 bg-[var(--color-bg-card)] rounded-lg flex items-center justify-center text-xs text-[var(--color-text-tertiary)]">{i + 1}</span>
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getMemeTypeConfig(meme.memeType).color }} />
                  <span className="text-[var(--color-text)] font-medium">{meme.label}</span>
                </div>
                <div className="text-right">
                  <p className="text-[var(--color-text)] font-display font-bold">{meme.avgViews.toLocaleString()}</p>
                  <p className="text-[var(--color-text-tertiary)] text-xs">평균 조회</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Categories */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">카테고리 TOP 5</h2>
            <Link href="/admin/analytics/categories" className="text-[var(--gradient-1)] text-sm hover:underline">전체 보기</Link>
          </div>
          <div className="space-y-3">
            {categoryData.map((cat, i) => (
              <div key={cat.category} className="flex items-center justify-between p-3 bg-[var(--color-bg-muted)] rounded-xl">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 bg-[var(--color-bg-card)] rounded-lg flex items-center justify-center text-xs text-[var(--color-text-tertiary)]">{i + 1}</span>
                  <span className="text-[var(--color-text)] font-medium">{cat.category}</span>
                  {cat.trend === 'up' && <span className="text-emerald-400 text-xs">↑</span>}
                  {cat.trend === 'down' && <span className="text-red-400 text-xs">↓</span>}
                </div>
                <div className="text-right">
                  <p className="text-[var(--color-text)] font-display font-bold">{cat.avgViews.toLocaleString()}</p>
                  <p className="text-[var(--color-text-tertiary)] text-xs">평균 조회</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
