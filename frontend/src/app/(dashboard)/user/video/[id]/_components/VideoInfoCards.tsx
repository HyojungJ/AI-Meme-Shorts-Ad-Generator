import type { Video } from '@/types'

export function VideoInfoCards({ video }: { video: Video }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">영상 정보</h2>
        <dl className="space-y-3">
          <div className="flex justify-between">
            <dt className="text-[var(--color-text-secondary)]">제품명</dt>
            <dd className="text-[var(--color-text)]">{video.title}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--color-text-secondary)]">제품 카테고리</dt>
            <dd className="text-[var(--color-text)]">{video.productCategory || '-'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-[var(--color-text-secondary)]">요청일</dt>
            <dd className="text-[var(--color-text)]">{video.createdAt}</dd>
          </div>
        </dl>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">제품 설명</h2>
        <p className="text-[var(--color-text-secondary)] leading-relaxed">
          {video.productHighlight || '등록된 제품 설명이 없습니다.'}
        </p>
      </div>
    </div>
  )
}
