'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { clientAnalyticsApi, ClientDashboardResponse } from '@/lib/api'
import { STATUS_CONFIG_WITH_BORDER } from '@/lib/constants'
import { StatCardSkeleton, ChartSkeleton, VideoRowSkeleton } from '@/components/ui/Skeleton'
import { useToast } from '@/components/ui/Toast'


function StatCard({
  label,
  value,
  change,
  icon,
  color = 'var(--gradient-1)',
}: {
  label: string
  value: string | number
  change?: string
  icon: React.ReactNode
  color?: string
}) {
  const isPositive = change?.startsWith('+')

  return (
    <div className="glass-card glow p-6 group">
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-110"
          style={{ background: `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)` }}
        >
          <span style={{ color }}>{icon}</span>
        </div>
        {change && (
          <span
            className={`text-xs px-2.5 py-1 rounded-full font-display font-medium ${
              isPositive ? 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]' : 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      <p className="text-[var(--color-text-secondary)] text-sm mb-1 font-body">{label}</p>
      <p className="text-[var(--color-text)] text-3xl font-display font-bold">{value}</p>
    </div>
  )
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-4 py-3">
        <p className="text-[var(--color-text-secondary)] text-xs mb-1">{label}</p>
        <p className="text-[var(--color-text)] font-display font-bold">{payload[0].value.toLocaleString()}</p>
      </div>
    )
  }
  return null
}

export default function MainPage() {
  const router = useRouter()
  const { showToast } = useToast()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<ClientDashboardResponse | null>(null)

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const response = await clientAnalyticsApi.getDashboard()
        setData(response)
      } catch (error) {
        showToast(error instanceof Error ? error.message : '대시보드 로딩 실패', 'error')
      } finally {
        setLoading(false)
      }
    }
    fetchDashboard()
  }, [showToast])

  if (loading || !data) {
    return (
      <div className="space-y-8 font-body">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">Dashboard</h1>
            <p className="text-[var(--color-text-secondary)]">영상 제작 현황과 성과를 한눈에 확인하세요</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {[...Array(4)].map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
        <div className="glass-card glow p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-display font-semibold text-[var(--color-text)]">최근 영상</h3>
          </div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <VideoRowSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    )
  }

  const { summary, views_timeline, engagement_timeline, recent_videos } = data

  return (
    <div className="space-y-6 md:space-y-8 font-body">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">Dashboard</h1>
          <p className="text-[var(--color-text-secondary)] text-sm md:text-base">영상 제작 현황과 성과를 한눈에 확인하세요</p>
        </div>
        <button
          onClick={() => router.push('/user/request')}
          className="btn-primary w-full md:w-auto"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 영상 요청
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="총 영상 수"
          value={summary.total_videos}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          }
          color="var(--gradient-1)"
        />
        <StatCard
          label="총 조회수"
          value={summary.total_views.toLocaleString()}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          }
          color="var(--gradient-3)"
        />
        <StatCard
          label="평균 반응률"
          value={`${summary.avg_engagement_rate}%`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          }
          color="var(--gradient-4)"
        />
        <StatCard
          label="제작 중"
          value={summary.processing_projects}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="var(--gradient-2)"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Views Chart */}
        <div className="glass-card glow p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-display font-semibold text-[var(--color-text)]">조회수 추이</h3>
              <p className="text-sm text-[var(--color-text-secondary)]">최근 30일</p>
            </div>
          </div>
          <div className="h-64 min-h-[256px]">
            {views_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={200}>
                <AreaChart data={views_timeline}>
                  <defs>
                    <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ff6b6b" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#ff6b6b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} />
                  <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="views"
                    stroke="#ff6b6b"
                    strokeWidth={2}
                    fill="url(#viewsGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center gap-2 text-[var(--color-text-tertiary)]">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm">데이터가 없습니다</p>
              </div>
            )}
          </div>
        </div>

        {/* Engagement Chart */}
        <div className="glass-card glow p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-display font-semibold text-[var(--color-text)]">반응률</h3>
              <p className="text-sm text-[var(--color-text-secondary)]">일별 평균</p>
            </div>
          </div>
          <div className="h-64 min-h-[256px]">
            {engagement_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%" minWidth={200} minHeight={200}>
                <BarChart data={engagement_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} />
                  <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="engagement_rate" fill="#ff9ff3" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center gap-2 text-[var(--color-text-tertiary)]">
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm">데이터가 없습니다</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-3 gap-4">
        <Link href="/user/analytics/memes" className="glass-card p-4 hover:border-[var(--gradient-1)]/30 transition-all group">
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
        <Link href="/user/analytics/categories" className="glass-card p-4 hover:border-[var(--gradient-3)]/30 transition-all group">
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
        <Link href="/user/analytics/trends" className="glass-card p-4 hover:border-[var(--gradient-4)]/30 transition-all group">
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

      {/* Recent Videos */}
      <div className="glass-card glow p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-display font-semibold text-[var(--color-text)]">최근 영상</h3>
          <button
            onClick={() => router.push('/user')}
            className="text-[var(--color-text)] text-sm font-bold hover:underline font-display"
          >
            전체 보기
          </button>
        </div>
        {recent_videos.length > 0 ? (
          <div className="space-y-3">
            {recent_videos.map((video, index) => {
              const statusConfig = STATUS_CONFIG_WITH_BORDER[video.status as keyof typeof STATUS_CONFIG_WITH_BORDER] || STATUS_CONFIG_WITH_BORDER.pending
              return (
                <div
                  key={video.video_id}
                  onClick={() => router.push(`/user/video/${video.video_id}`)}
                  className="flex items-center justify-between p-4 rounded-xl bg-[var(--color-bg-muted)]/50 hover:bg-[var(--color-bg-muted)] border border-transparent hover:border-[var(--color-border)] transition-all cursor-pointer"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}>
                      <svg className="w-6 h-6 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-display font-medium text-[var(--color-text)]">{video.title}</p>
                      <p className="text-sm text-[var(--color-text-tertiary)]">{video.created_at.split('T')[0]}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span
                      className={`px-3 py-1.5 text-xs font-display font-medium rounded-full border ${statusConfig.bgColor} ${statusConfig.color}`}
                    >
                      {statusConfig.text}
                    </span>
                    <div className="text-right">
                      <p className="text-[var(--color-text)] font-display font-medium">{video.views.toLocaleString()}</p>
                      <p className="text-xs text-[var(--color-text-tertiary)]">조회수</p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="py-12 text-center text-[var(--color-text-tertiary)]">
            아직 영상이 없습니다. 첫 영상을 요청해보세요!
          </div>
        )}
      </div>
    </div>
  )
}
