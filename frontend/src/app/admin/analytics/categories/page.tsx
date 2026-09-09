'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { analyticsApi } from '@/lib/api/analytics'
import { getMemeTypeConfig } from '@/lib/constants'
import { logger } from '@/lib/logger'
import type { CategoryPerformance, CategorySortBy, SortOrder, PaginatedCategoryPerformance } from '@/types'

const CATEGORY_COLORS = ['var(--gradient-1)', 'var(--gradient-3)', 'var(--gradient-4)', 'var(--gradient-2)', 'var(--gradient-5)', 'var(--color-text-tertiary)']
const ITEMS_PER_PAGE = 10

export default function CategoriesAnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [topCategories, setTopCategories] = useState<CategoryPerformance[]>([])
  const [tableData, setTableData] = useState<PaginatedCategoryPerformance | null>(null)

  // Table controls
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<CategorySortBy>('avgViews')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const searchDebounceRef = useRef<NodeJS.Timeout | null>(null)
  const tableRef = useRef<HTMLDivElement>(null)

  // Load top categories for cards and chart
  useEffect(() => {
    async function loadTopCategories() {
      try {
        const data = await analyticsApi.getTopCategories(10, 'avgViews')
        setTopCategories(data)
        setError(null)
      } catch (err) {
        logger.error('Analytics', 'Failed to load top categories:', err)
        setError(err instanceof Error ? err.message : '카테고리 데이터를 불러오는데 실패했습니다')
      } finally {
        setLoading(false)
      }
    }
    loadTopCategories()
  }, [])

  // Load table data with pagination/sorting/search
  useEffect(() => {
    async function loadTableData() {
      try {
        const data = await analyticsApi.getCategoryPerformance({
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

  function handleSort(field: CategorySortBy) {
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

  const top5Categories = topCategories.slice(0, 5)
  const chartCategories = topCategories.slice(0, 10)

  const selectedCategoryData = selectedCategory
    ? (tableData?.items.find(c => c.category === selectedCategory) || topCategories.find(c => c.category === selectedCategory))
    : null

  return (
    <div className="space-y-6 font-body">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <Link href="/admin/analytics" className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
          성과 분석
        </Link>
        <span className="text-[var(--color-text-tertiary)]">/</span>
        <span className="text-[var(--color-text)]">카테고리별 분석</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-display font-bold text-[var(--color-text)] mb-2">카테고리별 분석</h1>
        <p className="text-[var(--color-text-secondary)]">제품 카테고리별 성과를 비교합니다</p>
      </div>

      {/* Top 5 Summary Cards */}
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
          {top5Categories.map((cat, i) => (
            <button
              key={cat.category}
              onClick={() => setSelectedCategory(selectedCategory === cat.category ? null : cat.category)}
              className={`glass-card p-5 text-left transition-all ${
                selectedCategory === cat.category
                  ? 'border-[var(--gradient-1)]'
                  : 'hover:border-[var(--color-border-strong)]'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[i] }} />
                {cat.trend === 'up' && <span className="text-emerald-400 text-xs px-2 py-0.5 bg-emerald-500/10 rounded-full">↑ 상승</span>}
                {cat.trend === 'down' && <span className="text-red-400 text-xs px-2 py-0.5 bg-red-500/10 rounded-full">↓ 하락</span>}
                {cat.trend === 'stable' && <span className="text-[var(--color-text-tertiary)] text-xs px-2 py-0.5 bg-[var(--color-bg-muted)] rounded-full">- 유지</span>}
              </div>
              <p className="text-[var(--color-text)] font-display font-semibold mb-1">{cat.category}</p>
              <p className="text-[var(--color-text-secondary)] text-sm">{cat.videoCount}개 영상 · 평균 {cat.avgViews.toLocaleString()}회</p>
            </button>
          ))}
        </div>
      </div>

      {/* Chart - Top 10 */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-2">카테고리별 평균 조회수 (Top 10)</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-4">클릭하여 상세 정보 확인</p>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartCategories} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis type="number" stroke="var(--color-text-tertiary)" fontSize={12} />
              <YAxis
                dataKey="category"
                type="category"
                stroke="var(--color-text-tertiary)"
                fontSize={11}
                width={100}
                tick={({ x, y, payload }: { x: number; y: number; payload: { value: string } }) => (
                  <text
                    x={x}
                    y={y}
                    dy={4}
                    textAnchor="end"
                    fill="var(--color-text-tertiary)"
                    fontSize={11}
                  >
                    {payload.value.length > 10 ? payload.value.slice(0, 10) + '..' : payload.value}
                  </text>
                )}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    const memeConfig = getMemeTypeConfig(data.topMemeType)
                    return (
                      <div className="glass-card px-4 py-3">
                        <p className="text-[var(--color-text)] font-bold mb-2">{data.category}</p>
                        <p className="text-[var(--color-text-secondary)] text-sm">평균 조회: {data.avgViews.toLocaleString()}</p>
                        <p className="text-[var(--color-text-secondary)] text-sm">참여율: {data.avgEngagementRate}%</p>
                        <p className="text-[var(--color-text-secondary)] text-sm">추천 밈: {memeConfig.label}</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar
                dataKey="avgViews"
                radius={[0, 4, 4, 0]}
                onClick={(data) => setSelectedCategory((data as unknown as { category: string }).category)}
                cursor="pointer"
              >
                {chartCategories.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={selectedCategory === entry.category ? 'var(--gradient-1)' : CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                    fillOpacity={selectedCategory === entry.category ? 1 : 0.7}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Selected Category Detail */}
      {selectedCategoryData && (
        <div className="glass-card p-6" style={{ borderColor: 'rgba(255, 107, 107, 0.3)' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-display font-semibold text-[var(--color-text)]">{selectedCategoryData.category} 상세</h2>
            <button
              onClick={() => setSelectedCategory(null)}
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
              aria-label="닫기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">영상 수</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedCategoryData.videoCount}</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">총 조회수</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedCategoryData.totalViews.toLocaleString()}</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">평균 참여율</p>
              <p className="text-[var(--color-text)] text-2xl font-display font-bold">{selectedCategoryData.avgEngagementRate}%</p>
            </div>
            <div className="bg-[var(--color-bg-muted)] rounded-xl p-4">
              <p className="text-[var(--color-text-secondary)] text-xs mb-1">추천 밈</p>
              <p className="text-2xl font-display font-bold" style={{ color: getMemeTypeConfig(selectedCategoryData.topMemeType).color }}>
                {getMemeTypeConfig(selectedCategoryData.topMemeType).label}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Category Table with Search, Sort, Pagination */}
      <div ref={tableRef} className="glass-card p-6">
        <h2 className="text-lg font-display font-semibold text-[var(--color-text)] mb-4">전체 카테고리 목록</h2>

        {/* Search and Sort Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="카테고리 검색..."
              value={searchInput}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] focus:outline-none focus:border-[var(--gradient-1)]"
            />
          </div>
          <div className="flex gap-2">
            <span className="text-[var(--color-text-secondary)] text-sm self-center">정렬:</span>
            {[
              { key: 'avgViews' as CategorySortBy, label: '조회수' },
              { key: 'avgEngagementRate' as CategorySortBy, label: '참여율' },
              { key: 'videoCount' as CategorySortBy, label: '영상수' },
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
                <th className="text-left text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">카테고리</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">영상 수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">총 조회수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">평균 조회수</th>
                <th className="text-right text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">참여율</th>
                <th className="text-center text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">추천 밈</th>
                <th className="text-center text-[var(--color-text-tertiary)] text-xs font-display font-medium pb-3 uppercase tracking-wider">트렌드</th>
              </tr>
            </thead>
            <tbody>
              {tableData?.items.map((cat, i) => {
                const memeConfig = getMemeTypeConfig(cat.topMemeType)
                return (
                  <tr
                    key={cat.category}
                    className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg-muted)]/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedCategory(cat.category)}
                  >
                    <td className="py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                        <span className="text-[var(--color-text)] font-medium max-w-[120px] truncate block" title={cat.category}>
                          {cat.category}
                        </span>
                      </div>
                    </td>
                    <td className="py-4 text-right text-[var(--color-text)] font-display">{cat.videoCount}</td>
                    <td className="py-4 text-right text-[var(--color-text)] font-display">{cat.totalViews.toLocaleString()}</td>
                    <td className="py-4 text-right text-[var(--color-text)] font-display">{cat.avgViews.toLocaleString()}</td>
                    <td className="py-4 text-right text-[var(--color-text)] font-display">{cat.avgEngagementRate}%</td>
                    <td className="py-4 text-center">
                      <span
                        className="px-2 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: `${memeConfig.color}20`,
                          color: memeConfig.color,
                        }}
                      >
                        {memeConfig.label}
                      </span>
                    </td>
                    <td className="py-4 text-center">
                      {cat.trend === 'up' && <span className="text-emerald-400">↑</span>}
                      {cat.trend === 'down' && <span className="text-red-400">↓</span>}
                      {cat.trend === 'stable' && <span className="text-[var(--color-text-tertiary)]">-</span>}
                    </td>
                  </tr>
                )
              })}
              {tableData?.items.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[var(--color-text-secondary)]">
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
