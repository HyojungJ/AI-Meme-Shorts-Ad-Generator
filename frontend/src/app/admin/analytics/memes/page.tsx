'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Cell } from 'recharts'
import { analyticsApi } from '@/lib/api/analytics'
import { getMemeTypeConfig } from '@/lib/constants'
import { logger } from '@/lib/logger'
import type { MemeType, MemePerformance, MemeSortBy, SortOrder, PaginatedMemePerformance } from '@/types'

const ITEMS_PER_PAGE = 10

export default function MemesAnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMeme, setSelectedMeme] = useState<MemeType | null>(null)
  const [topMemes, setTopMemes] = useState<MemePerformance[]>([])
  const [tableData, setTableData] = useState<PaginatedMemePerformance | null>(null)

  // Table controls
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<MemeSortBy>('avgViews')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const searchDebounceRef = useRef<NodeJS.Timeout | null>(null)
  const tableRef = useRef<HTMLDivElement>(null)

  // Load top memes for cards and charts
  useEffect(() => {
    async function loadTopMemes() {
      try {
        const data = await analyticsApi.getTopMemes(10, 'avgViews')
        setTopMemes(data)
        setError(null)
      } catch (err) {
        logger.error('Analytics', 'Failed to load top memes:', err)
        setError(err instanceof Error ? err.message : '밈 데이터를 불러오는데 실패했습니다')
      } finally {
        setLoading(false)
      }
    }
    loadTopMemes()
  }, [])

  // Load table data with pagination/sorting/search
  useEffect(() => {
    async function loadTableData() {
      try {
        const data = await analyticsApi.getMemePerformance({
          page,
          limit: ITEMS_PER_PAGE,
          sortBy,
          sortOrder,
          search: search || undefined,
        })
        setTableData(data)
      } catch (err) {
        logger.error('Analytics', 'Failed to load table data:', err)
      }
    }
    loadTableData()
  }, [page, sortBy, sortOrder, search])

  // Debounced search
  function handleSearchChange(value: string) {
    setSearchInput(value)
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current)
    searchDebounceRef.current = setTimeout(() => {
      setSearch(value)
      setPage(1)
    }, 300)
  }

  function handleSort(field: MemeSortBy) {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setPage(1)
  }

  function scrollToTable() {
    tableRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="w-8 h-8 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] gap-4">
        <div className="w-16 h-16 rounded-xl bg-red-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p className="text-red-400 font-medium">데이터 로딩 실패</p>
        <p className="text-[var(--color-text-secondary)] text-sm">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-[var(--gradient-1)] text-white rounded-lg text-sm hover:opacity-90 transition-opacity"
        >
          다시 시도
        </button>
      </div>
    )
  }

  const top5Memes = topMemes.slice(0, 5)
  const chartMemes = topMemes.slice(0, 10)
  const radarMemes = topMemes.slice(0, 6)

  const radarData = radarMemes.map(m => ({
    meme: m.label,
    조회수: Math.round(m.avgViews / 100),
    완료율: m.avgCompletionRate,
    참여율: m.avgEngagementRate * 10,
  }))

  const selectedMemeData = selectedMeme
    ? (tableData?.items.find(m => m.memeType === selectedMeme) || topMemes.find(m => m.memeType === selectedMeme))
    : null

  const totalViews = topMemes.reduce((acc, m) => acc + m.totalViews, 0)

  return (
    <div className="space-y-6 font-body">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <Link href="/admin/analytics" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
          성과 분석
        </Link>
        <span className="text-[var(--color-text-tertiary)]">/</span>
        <span className="text-[var(--color-text)]">밈별 분석</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">밈별 분석</h1>
        <p className="text-[var(--color-text-secondary)]">어떤 밈 유형이 가장 효과적인지 비교 분석합니다</p>
      </div>

      {/* Top 5 Meme Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">조회수 상위 5개</h2>
          <button
            onClick={scrollToTable}
            className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
          >
            전체 보기 →
          </button>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {top5Memes.map((meme, index) => (
            <button
              key={`${meme.memeType}-${meme.label}-${index}`}
              onClick={() => setSelectedMeme(selectedMeme === meme.memeType ? null : meme.memeType)}
              className={`glass-card p-4 text-left transition-all ${
                selectedMeme === meme.memeType
                  ? 'border-[var(--gradient-1)]'
                  : 'hover:border-[var(--color-border-strong)]'
              }`}
            >
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getMemeTypeConfig(meme.memeType).color }}
                />
                <span className="text-[var(--color-text)] font-display font-semibold">{meme.label}</span>
              </div>
              <p className="text-[var(--color-text-secondary)] text-xs mb-2">{getMemeTypeConfig(meme.memeType).description}</p>
              <p className="text-[var(--color-text)] text-lg font-display font-bold">{meme.avgViews.toLocaleString()}</p>
              <p className="text-[var(--color-text-tertiary)] text-xs">평균 조회수</p>
            </button>
          ))}
        </div>
      </div>

      {/* Charts - Top 10 Bar, Top 6 Radar */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-2">밈별 평균 조회수 (Top 10)</h2>
          <p className="text-[var(--color-text-secondary)] text-sm mb-4">밈 유형별 평균 조회수 비교</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartMemes}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="label"
                  stroke="var(--color-text-tertiary)"
                  fontSize={11}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                  interval={0}
                  tick={({ x, y, payload }: { x: number; y: number; payload: { value: string } }) => (
                    <text
                      x={x}
                      y={y}
                      dy={10}
                      textAnchor="end"
                      fill="var(--color-text-tertiary)"
                      fontSize={11}
                      transform={`rotate(-45, ${x}, ${y})`}
                    >
                      {payload.value.length > 8 ? payload.value.slice(0, 8) + '...' : payload.value}
                    </text>
                  )}
                />
                <YAxis stroke="var(--color-text-tertiary)" fontSize={12} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload
                      return (
                        <div className="glass-card px-4 py-3">
                          <p className="text-[var(--color-text)] font-bold mb-1">{data.label}</p>
                          <p className="text-[var(--color-text-secondary)] text-sm">평균 조회: {data.avgViews.toLocaleString()}</p>
                          <p className="text-[var(--color-text-secondary)] text-sm">영상 수: {data.videoCount}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Bar dataKey="avgViews" radius={[4, 4, 0, 0]}>
                  {chartMemes.map((entry, index) => (
                    <Cell
                      key={`${entry.memeType}-${entry.label}-${index}`}
                      fill={getMemeTypeConfig(entry.memeType).color}
                      fillOpacity={selectedMeme === entry.memeType ? 1 : 0.7}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card p-6">
          <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-2">밈 성과 레이더 (Top 6)</h2>
          <p className="text-[var(--color-text-secondary)] text-sm mb-4">조회수, 완료율, 참여율 비교</p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="var(--color-border)" />
                <PolarAngleAxis
                  dataKey="meme"
                  stroke="var(--color-text-secondary)"
                  fontSize={10}
                  tick={(props) => {
                    const { payload, x, y, cx } = props as { payload?: { value: string }; x?: number; y?: number; cx?: number }
                    const value = payload?.value ?? ''
                    const xPos = x ?? 0
                    const yPos = y ?? 0
                    const cxPos = cx ?? 0
                    return (
                      <text
                        x={xPos}
                        y={yPos}
                        textAnchor={xPos > cxPos ? 'start' : 'end'}
                        fill="var(--color-text-secondary)"
                        fontSize={10}
                      >
                        {value.length > 6 ? value.slice(0, 6) + '..' : value}
                      </text>
                    )
                  }}
                />
                <PolarRadiusAxis stroke="var(--color-text-tertiary)" fontSize={10} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="glass-card px-4 py-3">
                          <p className="text-[var(--color-text)] font-bold mb-1">{payload[0].payload.meme}</p>
                          {payload.map((p, i) => (
                            <p key={i} className="text-[var(--color-text-secondary)] text-sm">{p.name}: {p.value}</p>
                          ))}
                        </div>
                      )
                    }
                    return null
                  }}
                />
                <Radar name="조회수" dataKey="조회수" stroke="var(--gradient-1)" fill="var(--gradient-1)" fillOpacity={0.3} />
                <Radar name="완료율" dataKey="완료율" stroke="var(--gradient-3)" fill="var(--gradient-3)" fillOpacity={0.3} />
                <Radar name="참여율" dataKey="참여율" stroke="var(--gradient-4)" fill="var(--gradient-4)" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-6 mt-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[var(--gradient-1)] rounded-full" />
              <span className="text-[var(--color-text-secondary)] text-xs">조회수</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[var(--gradient-3)] rounded-full" />
              <span className="text-[var(--color-text-secondary)] text-xs">완료율</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-[var(--gradient-4)] rounded-full" />
              <span className="text-[var(--color-text-secondary)] text-xs">참여율</span>
            </div>
          </div>
        </div>
      </div>

      {/* Selected Meme Detail */}
      {selectedMemeData && (
        <div className="glass-card p-6" style={{ borderColor: `${getMemeTypeConfig(selectedMeme!).color}50` }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: getMemeTypeConfig(selectedMeme!).color }}
              />
              <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">{selectedMemeData.label} 밈 상세</h2>
            </div>
            <button
              onClick={() => setSelectedMeme(null)}
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
              aria-label="닫기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-[var(--color-text-secondary)] mb-4">{getMemeTypeConfig(selectedMeme!).description}</p>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">영상 수</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedMemeData.videoCount}</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">총 조회수</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedMemeData.totalViews.toLocaleString()}</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">평균 조회수</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedMemeData.avgViews.toLocaleString()}</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">시청 완료율</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedMemeData.avgCompletionRate}%</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">참여율</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedMemeData.avgEngagementRate}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Meme Distribution (using top memes) */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-4">밈 사용 분포 (Top 10)</h2>
        <div className="space-y-4">
          {chartMemes.map((meme, i) => {
            const percentage = totalViews > 0 ? Math.round((meme.totalViews / totalViews) * 100) : 0
            return (
              <div key={`${meme.memeType}-${meme.label}-${i}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getMemeTypeConfig(meme.memeType).color }}
                    />
                    <span className="text-[var(--color-text)] text-sm max-w-[100px] truncate block" title={meme.label}>
                      {meme.label}
                    </span>
                  </div>
                  <span className="text-[var(--color-text-secondary)] text-sm">{percentage}% ({meme.totalViews.toLocaleString()}회)</span>
                </div>
                <div className="h-2 bg-[var(--color-bg-muted)] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getMemeTypeConfig(meme.memeType).color,
                    }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Table with Search, Sort, Pagination */}
      <div ref={tableRef} className="glass-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-4">전체 밈 목록</h2>

        {/* Search and Sort Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="밈 이름 검색..."
              value={searchInput}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--gradient-1)]"
            />
          </div>
          <div className="flex gap-2">
            <span className="text-[var(--color-text-secondary)] text-sm self-center">정렬:</span>
            {[
              { key: 'avgViews' as MemeSortBy, label: '조회수' },
              { key: 'avgCompletionRate' as MemeSortBy, label: '완료율' },
              { key: 'avgEngagementRate' as MemeSortBy, label: '참여율' },
            ].map((item) => (
              <button
                key={item.key}
                onClick={() => handleSort(item.key)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  sortBy === item.key
                    ? 'bg-[var(--gradient-1)] text-white'
                    : 'bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                }`}
              >
                {item.label} {sortBy === item.key && (sortOrder === 'desc' ? '↓' : '↑')}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="text-left text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">밈 이름</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">영상 수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">총 조회수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">평균 조회수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">완료율</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">참여율</th>
              </tr>
            </thead>
            <tbody>
              {tableData?.items.map((meme, index) => (
                <tr
                  key={`${page}-${index}-${meme.label}`}
                  className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-muted)]/50 cursor-pointer transition-colors"
                  onClick={() => setSelectedMeme(meme.memeType as MemeType)}
                >
                  <td className="py-4">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getMemeTypeConfig(meme.memeType).color }}
                      />
                      <span className="text-[var(--color-text)] font-medium max-w-[150px] truncate block" title={meme.label}>
                        {meme.label}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 text-right text-[var(--color-text)] font-display">{meme.videoCount}</td>
                  <td className="py-4 text-right text-[var(--color-text)] font-display">{meme.totalViews.toLocaleString()}</td>
                  <td className="py-4 text-right text-[var(--color-text)] font-display">{meme.avgViews.toLocaleString()}</td>
                  <td className="py-4 text-right text-[var(--color-text)] font-display">{meme.avgCompletionRate}%</td>
                  <td className="py-4 text-right text-[var(--color-text)] font-display">{meme.avgEngagementRate}%</td>
                </tr>
              ))}
              {tableData?.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[var(--color-text-secondary)]">
                    검색 결과가 없습니다
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {tableData && tableData.totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => { setPage(Math.max(1, page - 1)); scrollToTable() }}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:text-[var(--color-text)] transition-colors"
            >
              ← 이전
            </button>
            {Array.from({ length: tableData.totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => { setPage(p); scrollToTable() }}
                className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                  page === p
                    ? 'bg-[var(--gradient-1)] text-white'
                    : 'bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => { setPage(Math.min(tableData.totalPages, page + 1)); scrollToTable() }}
              disabled={page === tableData.totalPages}
              className="px-3 py-1.5 text-sm bg-[var(--color-bg-muted)] text-[var(--color-text-secondary)] rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:text-[var(--color-text)] transition-colors"
            >
              다음 →
            </button>
          </div>
        )}

        {/* Results count */}
        {tableData && (
          <p className="text-center text-[var(--color-text-tertiary)] text-sm mt-4">
            총 {tableData.total}개 중 {(page - 1) * ITEMS_PER_PAGE + 1}-{Math.min(page * ITEMS_PER_PAGE, tableData.total)}개 표시
          </p>
        )}
      </div>
    </div>
  )
}
