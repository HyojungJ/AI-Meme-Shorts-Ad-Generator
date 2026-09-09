export function Skeleton({ className = '', style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`animate-pulse bg-[var(--color-bg-muted)] rounded ${className}`}
      style={style}
    />
  )
}

export function StatCardSkeleton() {
  return (
    <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-6">
      <div className="flex items-start justify-between mb-4">
        <Skeleton className="w-12 h-12 rounded-xl" />
        <Skeleton className="w-12 h-5 rounded-full" />
      </div>
      <Skeleton className="w-20 h-4 mb-2" />
      <Skeleton className="w-24 h-8" />
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="w-24 h-5 mb-2" />
          <Skeleton className="w-16 h-4" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="w-10 h-7 rounded-lg" />
          <Skeleton className="w-10 h-7 rounded-lg" />
          <Skeleton className="w-10 h-7 rounded-lg" />
        </div>
      </div>
      <div className="h-64 flex items-end justify-between gap-2 px-4">
        {[40, 65, 45, 80, 55, 70, 60].map((h, i) => (
          <Skeleton key={i} className="flex-1 rounded-t" style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  )
}

export function VideoCardSkeleton() {
  return (
    <div className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-xl overflow-hidden">
      <Skeleton className="aspect-video w-full rounded-none" />
      <div className="p-4">
        <Skeleton className="h-4 w-3/4 mb-2" />
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-12" />
        </div>
        <div className="mt-3 pt-3 border-t border-[var(--color-border)] flex gap-2">
          <Skeleton className="flex-1 h-8 rounded-md" />
          <Skeleton className="w-9 h-8 rounded-md" />
        </div>
      </div>
    </div>
  )
}

export function VideoRowSkeleton() {
  return (
    <div className="flex items-center justify-between p-4 bg-[var(--color-bg)] rounded-xl border border-[var(--color-border)]">
      <div className="flex items-center gap-4">
        <Skeleton className="w-12 h-12 rounded-lg" />
        <div>
          <Skeleton className="w-32 h-4 mb-2" />
          <Skeleton className="w-20 h-3" />
        </div>
      </div>
      <div className="flex items-center gap-6">
        <div className="text-right">
          <Skeleton className="w-16 h-4 mb-1" />
          <Skeleton className="w-10 h-3" />
        </div>
        <Skeleton className="w-16 h-6 rounded-full" />
      </div>
    </div>
  )
}

export function VideoDetailSkeleton() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-6">
        <Skeleton className="w-20 h-4" />
        <Skeleton className="w-3 h-4" />
        <Skeleton className="w-32 h-4" />
      </div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Skeleton className="w-48 h-8" />
            <Skeleton className="w-16 h-6 rounded-full" />
          </div>
          <Skeleton className="w-40 h-4" />
        </div>
        <Skeleton className="w-24 h-10 rounded-lg" />
      </div>
      {/* Progress bar */}
      <div className="flex items-center gap-2 mb-8">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="flex items-center">
            <Skeleton className="w-8 h-8 rounded-full" />
            {i < 7 && <Skeleton className="w-12 h-1 mx-1" />}
          </div>
        ))}
      </div>
      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-5">
            <Skeleton className="w-24 h-4 mb-3" />
            <Skeleton className="w-full h-4" />
          </div>
        ))}
      </div>
    </div>
  )
}

export function ProfileSkeleton() {
  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Skeleton className="w-24 h-8 mb-2" />
        <Skeleton className="w-40 h-4" />
      </div>
      {/* Profile card */}
      <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-8 mb-6">
        <div className="flex items-start gap-6">
          <Skeleton className="w-24 h-24 rounded-xl" />
          <div className="flex-1">
            <Skeleton className="w-32 h-6 mb-2" />
            <Skeleton className="w-48 h-4 mb-4" />
            <Skeleton className="w-24 h-9 rounded-lg" />
          </div>
        </div>
      </div>
      {/* Info sections */}
      {[...Array(2)].map((_, i) => (
        <div key={i} className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl p-6 mb-6">
          <Skeleton className="w-20 h-5 mb-4" />
          <div className="space-y-4">
            <div className="flex justify-between py-3">
              <Skeleton className="w-16 h-4" />
              <Skeleton className="w-32 h-4" />
            </div>
            <div className="flex justify-between py-3">
              <Skeleton className="w-16 h-4" />
              <Skeleton className="w-32 h-4" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function AdminTableSkeleton() {
  return (
    <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border)] rounded-2xl overflow-hidden">
      {/* Table header */}
      <div className="flex gap-4 px-6 py-4 border-b border-[var(--color-border)]">
        {[80, 100, 60, 120, 80, 80].map((w, i) => (
          <Skeleton key={i} className="h-4 rounded" style={{ width: w }} />
        ))}
      </div>
      {/* Table rows */}
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-6 py-4 border-b border-[var(--color-border)] last:border-b-0">
          <div className="flex items-center gap-3 flex-1">
            <Skeleton className="w-9 h-9 rounded-xl" />
            <Skeleton className="w-24 h-4" />
          </div>
          <Skeleton className="w-28 h-4 flex-1" />
          <Skeleton className="w-16 h-6 rounded-full" />
          <div className="flex items-center gap-1 flex-1">
            {[...Array(5)].map((_, j) => (
              <Skeleton key={j} className="w-7 h-7 rounded-full" />
            ))}
          </div>
          <Skeleton className="w-20 h-4" />
          <Skeleton className="w-20 h-8 rounded-lg" />
        </div>
      ))}
    </div>
  )
}

export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
  }

  return (
    <div
      className={`${sizeClasses[size]} border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin`}
    />
  )
}
