'use client'

import { useEffect } from 'react'
import { logger } from '@/lib/logger'

export default function MainError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    logger.error('ErrorBoundary', 'Main page error:', error)
  }, [error])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">대시보드를 불러올 수 없습니다</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          통계 데이터를 불러오는 중 문제가 발생했습니다. 네트워크 연결을 확인하고 다시 시도해주세요.
        </p>
        <button
          onClick={reset}
          className="px-5 py-2.5 btn-primary text-sm rounded-lg"
        >
          다시 시도
        </button>
      </div>
    </div>
  )
}
