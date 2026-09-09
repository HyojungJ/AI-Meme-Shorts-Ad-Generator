import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import type { VideoMetrics } from '@/types'

function MetricTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2">
        <p className="text-[var(--color-text-secondary)] text-xs mb-1">{label}</p>
        <p className="text-[var(--color-text)] font-bold text-sm">{payload[0].value.toLocaleString()}</p>
      </div>
    )
  }
  return null
}

export function PerformanceTab({ metrics }: { metrics: VideoMetrics }) {
  return (
    <>
      {/* Performance Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="glass-card p-4">
          <p className="text-[var(--color-text-secondary)] text-xs mb-1">총 조회수</p>
          <p className="text-[var(--color-text)] text-2xl font-bold">{metrics.views.toLocaleString()}</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-[var(--color-text-secondary)] text-xs mb-1">시청 완료율</p>
          <p className="text-[var(--color-text)] text-2xl font-bold">{metrics.completionRate}%</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-[var(--color-text-secondary)] text-xs mb-1">평균 시청 시간</p>
          <p className="text-[var(--color-text)] text-2xl font-bold">{metrics.watchTime}초</p>
        </div>
        <div className="glass-card p-4">
          <p className="text-[var(--color-text-secondary)] text-xs mb-1">참여율</p>
          <p className="text-[var(--color-text)] text-2xl font-bold">{metrics.engagementRate.toFixed(1)}%</p>
        </div>
      </div>

      {/* Engagement Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="glass-card p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-red-500/10 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
            </svg>
          </div>
          <div>
            <p className="text-[var(--color-text-secondary)] text-xs">좋아요</p>
            <p className="text-[var(--color-text)] text-lg font-bold">{metrics.likes.toLocaleString()}</p>
          </div>
        </div>
        <div className="glass-card p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div>
            <p className="text-[var(--color-text-secondary)] text-xs">댓글</p>
            <p className="text-[var(--color-text)] text-lg font-bold">{metrics.comments.toLocaleString()}</p>
          </div>
        </div>
        <div className="glass-card p-4 flex items-center gap-4">
          <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </div>
          <div>
            <p className="text-[var(--color-text-secondary)] text-xs">공유</p>
            <p className="text-[var(--color-text)] text-lg font-bold">{metrics.shares.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Daily Views Chart */}
      <div className="glass-card p-6 mb-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">일별 조회수</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={metrics.dailyViews}>
              <defs>
                <linearGradient id="viewsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ff6b6b" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#ff6b6b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" stroke="var(--color-text-tertiary)" fontSize={12} />
              <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
              <Tooltip content={<MetricTooltip />} />
              <Area
                type="monotone"
                dataKey="views"
                stroke="#ff6b6b"
                strokeWidth={2}
                fill="url(#viewsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Hourly Views Chart */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-2">시간대별 조회 패턴</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-4">언제 시청자들이 가장 많이 보는지 확인하세요</p>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={metrics.hourlyViews}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="hour"
                stroke="var(--color-text-tertiary)"
                fontSize={10}
                tickFormatter={(h) => `${h}시`}
              />
              <YAxis stroke="var(--color-text-tertiary)" fontSize={10} />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="glass-card px-3 py-2">
                        <p className="text-[var(--color-text-secondary)] text-xs mb-1">{label}시</p>
                        <p className="text-[var(--color-text)] font-bold text-sm">{(payload[0].value as number).toLocaleString()}회</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar dataKey="views" fill="#ff6b6b" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}
