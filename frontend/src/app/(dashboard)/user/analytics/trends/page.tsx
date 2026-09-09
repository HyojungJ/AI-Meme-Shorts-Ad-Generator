'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { clientAnalyticsApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import type { TrendDataPoint, TrendInsight } from '@/types'

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

export default function UserTrendsAnalyticsPage() {
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'1W' | '1M' | '3M'>('1M')
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [insights, setInsights] = useState<TrendInsight[]>([])

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const data = await clientAnalyticsApi.getMyTrends()
        setTrendData(data.data)
        setInsights(data.insights)
      } catch (error) {
        showToast(error instanceof Error ? error.message : '데이터 로딩 실패', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [showToast])

  const filteredTrendData = period === '1W'
    ? trendData.slice(-7)
    : period === '1M'
    ? trendData.slice(-20)
    : trendData

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
            <span className="text-[var(--color-text)]">트렌드 분석</span>
          </div>
          <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">트렌드 분석</h1>
          <p className="text-[var(--color-text-secondary)]">시간에 따른 성과 추이를 확인하세요</p>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="glass-card p-6">
        {trendData.length > 0 ? (
          <>
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
          </>
        ) : (
          <div className="text-center py-12">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}
            >
              <svg className="w-8 h-8 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
            <p className="text-[var(--color-text)] font-medium mb-2">데이터가 없습니다</p>
            <p className="text-[var(--color-text-secondary)] text-sm">아직 완료된 영상이 없거나 성과 데이터가 수집되지 않았습니다</p>
          </div>
        )}
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">주요 인사이트</h2>
            <span className="text-xs text-[var(--color-text-tertiary)]">조회수 기반 자동 분석</span>
          </div>
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
        </div>
      )}
    </div>
  )
}
