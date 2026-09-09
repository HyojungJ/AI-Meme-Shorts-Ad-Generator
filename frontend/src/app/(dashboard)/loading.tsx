export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
        <p className="text-[var(--color-text-secondary)] font-body text-sm">로딩 중...</p>
      </div>
    </div>
  )
}
