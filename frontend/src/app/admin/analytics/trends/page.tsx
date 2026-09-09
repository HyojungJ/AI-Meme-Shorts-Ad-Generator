'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { analyticsApi } from '@/lib/api'
import type { TrendDataPoint, TrendInsight, AnalyticsSummary } from '@/types'

const periodMap = { '1W': 'week', '1M': 'month', '3M': 'quarter' } as const

export default function TrendsAnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState<'1W' | '1M' | '3M'>('1M')
  const [metric, setMetric] = useState<'views' | 'engagement'>('views')
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [trendInsights, setTrendInsights] = useState<TrendInsight[]>([])
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [trendsResult, dashboardResult] = await Promise.all([
        analyticsApi.getTrends(periodMap[period]),
        analyticsApi.getDashboard(),
      ])
      setTrendData(trendsResult.data)
      setTrendInsights(trendsResult.insights)
      setSummary(dashboardResult)
    } catch {
      // keep existing data on error
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const filteredData = trendData

  const actualData = filteredData.filter(d => !d.predicted)
  const predictedData = filteredData.filter(d => d.predicted)
  const lastActual = actualData[actualData.length - 1]
  const firstPredicted = predictedData[0]

  const combinedPredictedData = firstPredicted
    ? [lastActual, ...predictedData]
    : []

  const currentValue = actualData[actualData.length - 1]?.[metric] || 0
  const previousValue = actualData[0]?.[metric] || 0
  const changePercent = previousValue ? Math.round(((currentValue - previousValue) / previousValue) * 100) : 0

  const predictedEndValue = predictedData[predictedData.length - 1]?.[metric] || currentValue
  const predictedChangePercent = currentValue ? Math.round(((predictedEndValue - currentValue) / currentValue) * 100) : 0

  return (
    <div className="space-y-6 font-body">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <Link href="/admin/analytics" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
          성과 분석
        </Link>
        <span className="text-[var(--color-text-tertiary)]">/</span>
        <span className="text-[var(--color-text)]">트렌드 분석</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">트렌드 분석</h1>
        <p className="text-[var(--color-text-secondary)]">과거 성과 추이와 미래 예측을 확인하세요</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-5">
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">현재 일 조회수</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{currentValue.toLocaleString()}</p>
          <div className={`flex items-center gap-1 mt-2 ${changePercent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            <span className="text-sm">{changePercent >= 0 ? '↑' : '↓'} {Math.abs(changePercent)}%</span>
            <span className="text-[var(--color-text-tertiary)] text-xs">vs 기간 시작</span>
          </div>
        </div>
        <div className="glass-card p-5">
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">예측 조회수 (7일 후)</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{predictedEndValue.toLocaleString()}</p>
          <div className={`flex items-center gap-1 mt-2 ${predictedChangePercent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            <span className="text-sm">{predictedChangePercent >= 0 ? '↑' : '↓'} {Math.abs(predictedChangePercent)}%</span>
            <span className="text-[var(--color-text-tertiary)] text-xs">예상 변화</span>
          </div>
        </div>
        <div className="glass-card p-5">
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">현재 참여율</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary?.avgEngagement ?? 0}%</p>
          <div className="flex items-center gap-1 mt-2 text-emerald-400">
            <span className="text-sm">↑ {summary?.engagementChange ?? 0}%</span>
            <span className="text-[var(--color-text-tertiary)] text-xs">vs 지난주</span>
          </div>
        </div>
        <div className="glass-card p-5">
          <p className="text-[var(--color-text-secondary)] text-sm mb-1">총 영상 수</p>
          <p className="text-[var(--color-text)] text-2xl font-display font-bold">{summary?.totalVideos ?? 0}</p>
          <p className="text-[var(--color-text-tertiary)] text-xs mt-2">누적 데이터 기준</p>
        </div>
      </div>

      {/* Main Trend Chart */}
      <div className="glass-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">
              {metric === 'views' ? '조회수' : '참여율'} 추이 및 예측
            </h2>
            <p className="text-sm text-[var(--color-text-secondary)]">점선은 AI 예측 데이터입니다</p>
          </div>
          <div className="flex gap-2">
            <div className="flex gap-1 bg-[var(--color-bg-muted)] rounded-lg p-1">
              <button
                onClick={() => setMetric('views')}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  metric === 'views' ? 'bg-[var(--color-bg-card)] text-[var(--color-text)]' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                }`}
              >
                조회수
              </button>
              <button
                onClick={() => setMetric('engagement')}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                  metric === 'engagement' ? 'bg-[var(--color-bg-card)] text-[var(--color-text)]' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                }`}
              >
                참여율
              </button>
            </div>
            <div className="flex gap-1 bg-[var(--color-bg-muted)] rounded-lg p-1">
              {(['1W', '1M', '3M'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                    period === p ? 'bg-[var(--gradient-1)]/10 text-[var(--gradient-1)]' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredData}>
              <defs>
                <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--gradient-1)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="var(--gradient-1)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="predictedGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--gradient-1)" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="var(--gradient-1)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} />
              <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="glass-card px-4 py-3">
                        <p className="text-[var(--color-text-tertiary)] text-xs mb-1">
                          {label} {data.predicted && '(예측)'}
                        </p>
                        <p className="text-[var(--color-text)] font-bold">
                          {metric === 'views'
                            ? `${(payload[0].value as number).toLocaleString()}회`
                            : `${payload[0].value}%`
                          }
                        </p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              {lastActual && (
                <ReferenceLine
                  x={lastActual.date}
                  stroke="var(--color-text-tertiary)"
                  strokeDasharray="5 5"
                  label={{ value: '오늘', fill: 'var(--color-text-secondary)', fontSize: 10, position: 'top' }}
                />
              )}
              <Area
                type="monotone"
                dataKey={metric}
                data={actualData}
                stroke="var(--gradient-1)"
                strokeWidth={2}
                fill="url(#actualGradient)"
              />
              {combinedPredictedData.length > 0 && (
                <Area
                  type="monotone"
                  dataKey={metric}
                  data={combinedPredictedData}
                  stroke="var(--gradient-1)"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  fill="url(#predictedGradient)"
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[var(--gradient-1)]" />
            <span className="text-[var(--color-text-secondary)] text-xs">실제 데이터</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[var(--gradient-1)] border-dashed" style={{ borderStyle: 'dashed' }} />
            <span className="text-[var(--color-text-secondary)] text-xs">예측 데이터</span>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 bg-[var(--gradient-1)]/10 rounded-lg flex items-center justify-center">
            <svg className="w-4 h-4 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">AI 인사이트</h2>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {trendInsights.map((insight, i) => (
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
              <div className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                  insight.type === 'positive'
                    ? 'bg-emerald-500/20'
                    : insight.type === 'negative'
                    ? 'bg-red-500/20'
                    : 'bg-[var(--gradient-3)]/20'
                }`}>
                  {insight.type === 'positive' && (
                    <svg className="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  {insight.type === 'negative' && (
                    <svg className="w-3 h-3 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  )}
                  {insight.type === 'neutral' && (
                    <svg className="w-3 h-3 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  )}
                </div>
                <div>
                  <p className="text-[var(--color-text)] font-medium text-sm mb-1">{insight.title}</p>
                  <p className="text-[var(--color-text-secondary)] text-sm">{insight.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prediction Explanation */}
      <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 bg-[var(--color-bg-card)] rounded-xl flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-[var(--color-text)] font-display font-medium mb-2">예측 모델 안내</h3>
            <p className="text-[var(--color-text-secondary)] text-sm leading-relaxed">
              예측 데이터는 과거 성과 패턴, 요일별 트렌드, 계절성 등을 분석한 AI 모델 기반입니다.
              실제 성과는 컨텐츠 품질, 업로드 시점, 외부 요인에 따라 달라질 수 있습니다.
              예측 정확도는 지속적으로 개선되고 있으며, 현재 평균 85%의 신뢰도를 보입니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
