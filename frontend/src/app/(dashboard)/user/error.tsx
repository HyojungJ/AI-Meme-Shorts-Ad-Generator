'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { logger } from '@/lib/logger'

export default function UserError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    logger.error('ErrorBoundary', 'User videos error:', error)
  }, [error])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">영상 목록을 불러올 수 없습니다</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          영상 목록을 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            href="/user/request"
            className="px-4 py-2.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
          >
            새 영상 요청
          </Link>
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
