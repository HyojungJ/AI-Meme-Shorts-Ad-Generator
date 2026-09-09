'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { AdminTableSkeleton } from '@/components/ui/Skeleton'
import { adminApi } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { getAdminStatusConfig } from '@/lib/constants'
import { logger } from '@/lib/logger'
import type { AdminRequest, WorkflowDetailData } from '@/types'

function mapToProgressStep(step: number): number {
  if (step <= 0) return 0  // 대기
  if (step <= 2) return 1  // 생성 (캐릭터/음성)
  if (step <= 4) return 2  // 시나리오
  if (step <= 6) return 3  // 영상
  return 4                  // 완료
}

function ProgressBar({ status }: { status: string }) {
  const config = getAdminStatusConfig(status)
  const currentStep = mapToProgressStep(config.step)
  const steps = [
    { label: '대기', icon: '1' },
    { label: '생성', icon: '2' },
    { label: '시나리오', icon: '3' },
    { label: '영상', icon: '4' },
    { label: '완료', icon: '✓' },
  ]

  if (status === 'error') {
    return (
      <div className="flex items-center gap-2 text-[var(--status-error-text)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span className="text-sm">오류 발생</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          <div
            className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium transition-all ${
              i < currentStep
                ? 'bg-[var(--gradient-1)] text-white'
                : i === currentStep
                ? 'bg-[var(--gradient-1)]/20 text-[var(--gradient-1)] border border-[var(--gradient-1)]/50'
                : 'bg-[var(--color-bg-muted)] text-[var(--color-text-tertiary)] border border-[var(--color-border)]'
            }`}
          >
            {i < currentStep ? '✓' : step.icon}
          </div>
          {i < steps.length - 1 && (
            <div
              className={`w-6 h-0.5 ${
                i < currentStep ? 'bg-[var(--gradient-1)]' : 'bg-[var(--color-border)]'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  )
}

type WorkflowLog = { timestamp: string; level: string; message: string }
type DetailTab = 'logs' | 'request' | 'history'

function WorkflowDetailModal({
  request,
  onClose,
}: {
  request: AdminRequest
  onClose: () => void
}) {
  const config = getAdminStatusConfig(request.status)
  const [activeTab, setActiveTab] = useState<DetailTab>('logs')
  const [logs, setLogs] = useState<WorkflowLog[]>([])
  const [logsLoading, setLogsLoading] = useState(true)
  const [detail, setDetail] = useState<WorkflowDetailData | null>(null)
  const [detailLoading, setDetailLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminApi.getWorkflowLogs(request.id)
        .then((res) => setLogs(res.logs || []))
        .catch((err) => { logger.warn('Admin', '워크플로우 로그 로딩 실패:', err); setLogs([]) }),
      adminApi.getWorkflowDetail(request.id)
        .then((res) => setDetail(res))
        .catch((err) => { logger.warn('Admin', '워크플로우 상세 로딩 실패:', err); setDetail(null) }),
    ]).finally(() => {
      setLogsLoading(false)
      setDetailLoading(false)
    })
  }, [request.id])

  const tabs: { key: DetailTab; label: string }[] = [
    { key: 'logs', label: '실행 로그' },
    { key: 'request', label: '신청 내용' },
    { key: 'history', label: '수정 이력' },
  ]

  const approvalLabel: Record<string, string> = {
    pending: '대기',
    approved: '승인',
    rejected: '거부',
    auto_approved: '자동 승인',
  }

  const videoStatusLabel: Record<string, string> = {
    processing: '생성 중',
    completed: '완료',
    client_approved: '클라이언트 승인',
    client_rejected: '클라이언트 거부',
    admin_approved: '관리자 승인',
    admin_rejected: '관리자 거부',
    published: '게시됨',
    failed: '실패',
  }

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

        <h2 className="text-xl font-display font-bold text-[var(--color-text)] mb-4">워크플로우 상세</h2>

        {/* 기본 정보 */}
        <div className="space-y-3 mb-5">
          <div className="flex justify-between items-start">
            <span className="text-[var(--color-text-secondary)]">회사</span>
            <span className="text-[var(--color-text)] text-right max-w-[60%]">{request.companyName}</span>
          </div>
          <div className="flex justify-between items-start">
            <span className="text-[var(--color-text-secondary)]">제품</span>
            <span className="text-[var(--color-text)] text-right max-w-[60%]">{request.productName}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-[var(--color-text-secondary)]">상태</span>
            <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${config.bgColor} ${config.color}`}>
              {config.label}
            </span>
          </div>
          {request.error && (
            <div className="flex justify-between items-start">
              <span className="text-[var(--color-text-secondary)]">에러</span>
              <span className="text-[var(--status-error-text)] text-right max-w-[60%] text-sm">{request.error}</span>
            </div>
          )}
        </div>

        {/* 탭 헤더 */}
        <div className="flex border-b border-[var(--color-border)] mb-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
                activeTab === tab.key
                  ? 'text-[var(--gradient-1)]'
                  : 'text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)]'
              }`}
            >
              {tab.label}
              {activeTab === tab.key && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--gradient-1)]" />
              )}
            </button>
          ))}
        </div>

        {/* 탭 콘텐츠 */}
        <div className="max-h-64 overflow-y-auto">
          {/* 실행 로그 탭 */}
          {activeTab === 'logs' && (
            <div className="space-y-2">
              {logsLoading ? (
                <div className="text-center py-4">
                  <div className="w-5 h-5 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
              ) : logs.length > 0 ? (
                logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <span className={`shrink-0 w-1.5 h-1.5 rounded-full mt-1.5 ${
                      log.level === 'error' ? 'bg-[var(--status-error-text)]' : log.level === 'warning' ? 'bg-[var(--status-warning-text)]' : 'bg-[var(--status-success-text)]'
                    }`} />
                    <span className="text-[var(--color-text-tertiary)] shrink-0">{log.timestamp.split('T')[1]?.slice(0, 8) || log.timestamp}</span>
                    <span className="text-[var(--color-text)]">{log.message}</span>
                  </div>
                ))
              ) : (
                <p className="text-[var(--color-text-tertiary)] text-sm text-center py-4">로그가 없습니다</p>
              )}
            </div>
          )}

          {/* 신청 내용 탭 */}
          {activeTab === 'request' && (
            <div className="space-y-3">
              {detailLoading ? (
                <div className="text-center py-4">
                  <div className="w-5 h-5 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
              ) : detail?.ad_request ? (
                <>
                  {[
                    { label: '상품명', value: detail.ad_request.item_name },
                    { label: '카테고리', value: detail.ad_request.item_category },
                    { label: '밈', value: detail.ad_request.meme_name },
                    { label: '제품 설명', value: detail.ad_request.item_description },
                    { label: '캐릭터 이미지 스타일', value: detail.ad_request.character_image_prompt },
                    { label: '상품 URL', value: detail.ad_request.item_url },
                    { label: '캐릭터 보이스 스타일', value: detail.ad_request.character_voice_prompt },
                  ].map((row) => row.value ? (
                    <div key={row.label} className="flex justify-between items-start text-sm">
                      <span className="text-[var(--color-text-tertiary)] shrink-0">{row.label}</span>
                      <span className="text-[var(--color-text)] text-right max-w-[65%] break-words">{row.value}</span>
                    </div>
                  ) : null)}
                  {detail.ad_request.item_images.length > 0 && (
                    <div className="text-sm">
                      <span className="text-[var(--color-text-tertiary)]">상품 이미지</span>
                      <div className="flex gap-2 mt-2 flex-wrap">
                        {detail.ad_request.item_images.map((url, i) => (
                          <img key={i} src={url} alt={`상품 ${i + 1}`} className="w-16 h-16 rounded-lg object-cover border border-[var(--color-border)]" />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-[var(--color-text-tertiary)] text-sm text-center py-4">신청 정보가 없습니다</p>
              )}
            </div>
          )}

          {/* 수정 이력 탭 */}
          {activeTab === 'history' && (
            <div className="space-y-5">
              {detailLoading ? (
                <div className="text-center py-4">
                  <div className="w-5 h-5 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin mx-auto" />
                </div>
              ) : (
                <>
                  {/* 시나리오 이력 */}
                  <div>
                    <h4 className="text-xs font-display font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider mb-2">시나리오</h4>
                    {detail?.revision_history.scenarios.length ? (
                      <div className="space-y-2">
                        {detail.revision_history.scenarios.map((s) => (
                          <div key={s.script_id} className="p-3 rounded-lg bg-[var(--color-bg-muted)] space-y-1.5 text-sm">
                            <div className="flex justify-between items-center">
                              <span className="text-[var(--color-text)] font-medium">{s.title}</span>
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                s.approval_status === 'approved' || s.approval_status === 'auto_approved'
                                  ? 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]'
                                  : s.approval_status === 'rejected'
                                  ? 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]'
                                  : 'bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]'
                              }`}>
                                {approvalLabel[s.approval_status] || s.approval_status}
                              </span>
                            </div>
                            <div className="flex gap-3 text-[var(--color-text-tertiary)] text-xs">
                              <span>{s.generation_type === 'initial' ? '초기 생성' : s.generation_type}</span>
                              <span>{s.quality_check_passed ? '품질 통과' : '품질 미통과'}</span>
                              {s.created_at && <span>{s.created_at.split('T')[0]}</span>}
                            </div>
                            {s.quality_issues.length > 0 && (
                              <div className="text-xs text-[var(--status-warning-text)]">
                                {s.quality_issues.join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[var(--color-text-tertiary)] text-sm py-2">시나리오 이력이 없습니다</p>
                    )}
                  </div>

                  {/* 영상 이력 */}
                  <div>
                    <h4 className="text-xs font-display font-semibold text-[var(--color-text-tertiary)] uppercase tracking-wider mb-2">영상</h4>
                    {detail?.revision_history.videos.length ? (
                      <div className="space-y-2">
                        {detail.revision_history.videos.map((v) => (
                          <div key={v.video_id} className="p-3 rounded-lg bg-[var(--color-bg-muted)] space-y-1.5 text-sm">
                            <div className="flex justify-between items-center">
                              <span className="text-[var(--color-text)] font-medium">{v.title}</span>
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                v.status === 'completed' || v.status === 'client_approved' || v.status === 'admin_approved' || v.status === 'published'
                                  ? 'bg-[var(--status-success-bg)] text-[var(--status-success-text)]'
                                  : v.status === 'client_rejected' || v.status === 'admin_rejected' || v.status === 'failed'
                                  ? 'bg-[var(--status-error-bg)] text-[var(--status-error-text)]'
                                  : 'bg-[var(--status-warning-bg)] text-[var(--status-warning-text)]'
                              }`}>
                                {videoStatusLabel[v.status] || v.status}
                              </span>
                            </div>
                            {v.rejection_reason && (
                              <div className="text-xs text-[var(--status-error-text)]">거부 사유: {v.rejection_reason}</div>
                            )}
                            {v.created_at && (
                              <div className="text-xs text-[var(--color-text-tertiary)]">{v.created_at.split('T')[0]}</div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-[var(--color-text-tertiary)] text-sm py-2">영상 이력이 없습니다</p>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
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

export default function AdminDashboardPage() {
  const router = useRouter()
  const { showToast } = useToast()
  const [filter, setFilter] = useState<string>('all')
  const [requests, setRequests] = useState<AdminRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRequest, setSelectedRequest] = useState<AdminRequest | null>(null)
  const [totalVideos, setTotalVideos] = useState(0)

  const fetchWorkflows = useCallback(async () => {
    try {
      setLoading(true)
      const [response, videoResponse] = await Promise.all([
        adminApi.getWorkflows(1, 100, 'all'),
        adminApi.getAllVideos(1, 1).catch((err) => { logger.warn('Admin', '영상 목록 로딩 실패:', err); return { total: 0 } }),
      ])
      setRequests(response.items.map((w: { execution_id: string; ad_id: number; company_id?: number; title?: string; company_name?: string; status: string; current_stage: string; created_at: string; error_message: string | null }) => ({
        id: w.execution_id,
        adId: w.ad_id,
        companyName: w.company_name || `회사 #${w.company_id || w.ad_id}`,
        productName: w.title || `광고 #${w.ad_id}`,
        status: (w.current_stage || w.status) as AdminRequest['status'],
        createdAt: w.created_at.split('T')[0],
        updatedAt: w.created_at.split('T')[0],
        error: w.error_message || undefined,
      })))
      setTotalVideos(videoResponse.total || 0)
    } catch (error) {
      showToast(error instanceof Error ? error.message : '워크플로우 로딩 실패', 'error')
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchWorkflows()
  }, [fetchWorkflows])

  const handleRetry = async (executionId: string) => {
    try {
      await adminApi.retryWorkflow(executionId)
      showToast('워크플로우가 재시작되었습니다', 'success')
      fetchWorkflows()
    } catch (error) {
      showToast(error instanceof Error ? error.message : '재시도 실패', 'error')
    }
  }

  const handleReview = (req: AdminRequest) => {
    const adId = req.adId || req.id
    window.open(`/user/video/${adId}`, '_blank')
  }

  const handleViewDetail = (req: AdminRequest) => {
    setSelectedRequest(req)
  }

  const filteredRequests =
    filter === 'all'
      ? requests
      : filter === 'error'
      ? requests.filter((r) => ['error', 'failed'].includes(r.status))
      : filter === 'completed'
      ? requests.filter((r) => r.status === 'completed')
      : requests.filter((r) => !['completed', 'error', 'failed'].includes(r.status))

  const errorCount = requests.filter((r) => ['error', 'failed'].includes(r.status)).length
  const processingCount = requests.filter((r) => !['completed', 'error', 'failed'].includes(r.status)).length
  const completedCount = requests.filter((r) => r.status === 'completed').length

  return (
    <div className="font-body">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">대시보드</h1>
          <p className="text-[var(--color-text-secondary)] text-sm md:text-base">영상 제작 파이프라인을 모니터링합니다</p>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap gap-3">
          <div className="px-4 py-2 glass-card flex items-center gap-3">
            <div className="w-2 h-2 bg-[var(--gradient-2)] rounded-full animate-pulse" />
            <span className="text-sm text-[var(--color-text-secondary)]">진행 중</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{processingCount}</span>
          </div>
          <div className="px-4 py-2 glass-card flex items-center gap-3">
            <div className="w-2 h-2 bg-[var(--status-success-text)] rounded-full" />
            <span className="text-sm text-[var(--color-text-secondary)]">완료</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{completedCount}</span>
          </div>
          <div className="px-4 py-2 glass-card flex items-center gap-3">
            <div className="w-2 h-2 bg-[var(--gradient-3)] rounded-full" />
            <span className="text-sm text-[var(--color-text-secondary)]">총 영상</span>
            <span className="text-[var(--color-text)] font-display font-semibold">{totalVideos}</span>
          </div>
          {errorCount > 0 && (
            <div className="px-4 py-2 glass-card flex items-center gap-3" style={{ borderColor: 'var(--color-danger-border)' }}>
              <div className="w-2 h-2 bg-[var(--status-error-text)] rounded-full" />
              <span className="text-sm text-[var(--status-error-text)]">오류</span>
              <span className="text-[var(--status-error-text)] font-display font-semibold">{errorCount}</span>
            </div>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { value: 'all', label: '전체', color: 'var(--gradient-1)' },
          { value: 'processing', label: '진행 중', color: 'var(--gradient-2)' },
          { value: 'completed', label: '완료', color: 'var(--status-success-text)' },
          { value: 'error', label: '오류', color: 'var(--status-error-text)' },
        ].map((item) => (
          <button
            key={item.value}
            onClick={() => setFilter(item.value)}
            className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
              filter === item.value
                ? 'text-white'
                : 'glass-card text-[var(--color-text-secondary)] hover:text-[var(--color-text)]'
            }`}
            style={filter === item.value ? { background: item.color } : undefined}
          >
            {item.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <p className="text-xs text-[var(--color-text-tertiary)] mb-2 sm:hidden">좌우로 스크롤하여 더 보기</p>
      {loading ? <AdminTableSkeleton /> : (
        <div className="glass-card overflow-x-auto">
          <table className="w-full min-w-[800px]">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">회사</th>
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">제품</th>
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">상태</th>
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">진행도</th>
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">요청일</th>
                <th className="px-6 py-4 text-left text-xs font-display font-medium text-[var(--color-text-tertiary)] uppercase tracking-wider">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {filteredRequests.map((req) => {
                const config = getAdminStatusConfig(req.status)
                return (
                  <tr
                    key={req.id}
                    className={`hover:bg-[var(--color-bg-muted)]/50 transition-colors ${
                      req.status === 'error' ? 'bg-[var(--status-error-bg)]' : ''
                    }`}
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-9 h-9 rounded-xl flex items-center justify-center"
                          style={{ background: 'linear-gradient(135deg, var(--gradient-1)20 0%, var(--gradient-4)20 100%)' }}
                        >
                          <span className="text-[var(--gradient-1)] font-medium text-sm">
                            {req.companyName.charAt(0)}
                          </span>
                        </div>
                        <span className="font-medium text-[var(--color-text)]">{req.companyName}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[var(--color-text-secondary)]">{req.productName}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1.5 text-xs font-medium rounded-full border ${config.bgColor} ${config.color}`}>
                        {config.label}
                      </span>
                      {req.error && (
                        <p className="mt-1.5 text-xs text-[var(--status-error-text)]">{req.error}</p>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <ProgressBar status={req.status} />
                    </td>
                    <td className="px-6 py-4 text-[var(--color-text-secondary)] text-sm">{req.createdAt}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {['error', 'failed'].includes(req.status) && (
                          <button
                            onClick={() => handleRetry(req.id)}
                            className="px-3 py-1.5 bg-[var(--status-error-bg)] text-[var(--status-error-text)] text-sm font-medium rounded-lg border border-[var(--status-error-border)] hover:bg-[var(--status-error-bg)] transition-colors"
                          >
                            재시도
                          </button>
                        )}
                        {req.status === 'review' && (
                          <button
                            onClick={() => handleReview(req)}
                            className="px-3 py-1.5 bg-[var(--gradient-2)]/10 text-[var(--gradient-2)] text-sm font-medium rounded-lg border border-[var(--gradient-2)]/20 hover:bg-[var(--gradient-2)]/20 transition-colors"
                          >
                            검수하기
                          </button>
                        )}
                        <button
                          onClick={() => handleViewDetail(req)}
                          className="px-3 py-1.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
                        >
                          상세보기
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {filteredRequests.length === 0 && (
            <div className="p-12 text-center">
              <div
                className="w-16 h-16 rounded-xl flex items-center justify-center mx-auto mb-4"
                style={{ background: 'linear-gradient(135deg, var(--gradient-1)10 0%, var(--gradient-4)10 100%)' }}
              >
                <svg className="w-8 h-8 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <p className="text-[var(--color-text-secondary)]">해당 조건의 요청이 없습니다</p>
            </div>
          )}
        </div>
      )}

      {selectedRequest && (
        <WorkflowDetailModal
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
        />
      )}
    </div>
  )
}
