'use client'

import { useEffect } from 'react'
import { logger } from '@/lib/logger'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    logger.error('ErrorBoundary', 'Dashboard error:', error)
  }, [error])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">문제가 발생했습니다</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          페이지를 불러오는 중 오류가 발생했습니다. 다시 시도하거나 잠시 후 다시 방문해주세요.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => window.location.href = '/main'}
            className="px-4 py-2.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
          >
            홈으로 이동
          </button>
          <button
            onClick={reset}
            className="px-4 py-2.5 btn-primary text-sm rounded-lg"
          >
            다시 시도
          </button>
        </div>
      </div>
    </div>
  )
}
