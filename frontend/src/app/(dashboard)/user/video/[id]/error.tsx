'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { logger } from '@/lib/logger'

export default function VideoDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    logger.error('ErrorBoundary', 'Video detail error:', error)
  }, [error])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-[var(--color-text)] mb-2">영상을 불러올 수 없습니다</h2>
        <p className="text-[var(--color-text-secondary)] text-sm mb-6">
          영상 정보를 가져오는 중 문제가 발생했습니다. 영상이 삭제되었거나 접근 권한이 없을 수 있습니다.
        </p>
        <div className="flex gap-3 justify-center">
          <Link
            href="/user"
            className="px-4 py-2.5 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
          >
            영상 목록으로
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
