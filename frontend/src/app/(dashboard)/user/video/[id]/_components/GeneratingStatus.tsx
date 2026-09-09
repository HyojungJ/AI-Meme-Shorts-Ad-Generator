import Link from 'next/link'
import type { VideoStatus } from '@/types'

const GENERATING_LABELS: Record<string, string> = {
  pending: '영상 제작을 준비하고 있습니다',
  generating_character: '캐릭터를 생성하고 있습니다',
  character_generating: '캐릭터 이미지를 생성하고 있습니다',
  voice_generating: '음성을 생성하고 있습니다',
  asset_generating: '캐릭터와 음성을 생성하고 있습니다',
  scenario_generating: '시나리오를 생성하고 있습니다',
  content_generating: '시나리오와 영상을 생성하고 있습니다',
  video_generating: '영상을 생성하고 있습니다',
}

const GENERATION_STEPS = [
  { key: 'pending', label: '정보 입력' },
  { key: 'character_generating', label: '이미지 생성' },
  { key: 'voice_generating', label: '음성 생성' },
  { key: 'scenario_generating', label: '시나리오 생성' },
  { key: 'video_generating', label: '영상 생성' },
]

function getGenerationStepIndex(status: string): number {
  // generating_character는 character_generating과 동일하게 처리
  const normalizedStatus = status === 'generating_character' ? 'character_generating' : status
  const idx = GENERATION_STEPS.findIndex(s => s.key === normalizedStatus)
  return idx >= 0 ? idx : 0
}

export function GeneratingStatus({
  status,
  regeneratingType,
  submitting,
  retrying,
  progressPercentage,
  getProgressPercentage,
  handleStartScenario,
  handleRetryGeneration,
}: {
  status: string
  regeneratingType: 'character' | 'voice' | null
  submitting: boolean
  retrying: boolean
  progressPercentage?: number
  getProgressPercentage: (status: string, backendProgress?: number) => number
  handleStartScenario: (auto?: boolean) => void
  handleRetryGeneration: () => void
}) {
  if (status === 'failed') {
    return (
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-400">생성 중 오류가 발생했습니다</h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              일시적인 오류일 수 있습니다. 다시 시도해주세요.
            </p>
          </div>
        </div>

        <div className="p-4 bg-red-500/5 border border-red-500/15 rounded-xl mb-6">
          <p className="text-sm text-[var(--color-text-secondary)]">
            생성 과정에서 문제가 발생했습니다. 아래 버튼으로 처음부터 다시 생성을 시도할 수 있습니다.
            문제가 반복되면 관리자에게 문의해주세요.
          </p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleRetryGeneration}
            disabled={retrying}
            className="flex-1 py-3.5 btn-primary rounded-xl flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {retrying ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                재생성 중...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                다시 생성하기
              </>
            )}
          </button>
          <Link
            href="/user"
            className="flex-1 py-3.5 glass-card text-[var(--color-text)] rounded-xl hover:bg-[var(--color-bg-muted)] transition-colors flex items-center justify-center gap-2"
          >
            목록으로 돌아가기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card p-6 mb-6">
      {status === 'pending' && (
        <div className="mb-6 p-4 bg-[var(--color-bg-muted)] rounded-xl">
          <p className="text-sm text-[var(--color-text-secondary)]">
            기존 캐릭터를 선택했으므로, 시나리오 생성을 자동으로 시작합니다.
          </p>
          <button
            onClick={() => handleStartScenario(false)}
            disabled={submitting}
            className="w-full mt-4 py-3.5 btn-primary rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? '처리 중...' : '시나리오 다시 시작'}
          </button>
        </div>
      )}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="w-10 h-10 border-3 border-[var(--color-border-strong)] rounded-full" />
          <div className="absolute top-0 left-0 w-10 h-10 border-3 border-transparent border-t-[var(--gradient-1)] rounded-full animate-spin" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-[var(--color-text)]">
            {status === ('generating_character' as VideoStatus) && regeneratingType === 'character'
              ? '캐릭터 이미지를 생성하고 있습니다'
              : status === ('generating_character' as VideoStatus) && regeneratingType === 'voice'
              ? '음성을 생성하고 있습니다'
              : GENERATING_LABELS[status] || 'AI가 작업 중입니다'}
          </h3>
          <p className="text-sm text-[var(--color-text-secondary)]">
            완료되면 자동으로 검수 화면으로 전환됩니다
          </p>
        </div>
      </div>

      {/* Step Checklist */}
      <div className="space-y-3 mb-6">
        {GENERATION_STEPS.map((step, i) => {
          const activeIdx = getGenerationStepIndex(status)
          const isDone = i < activeIdx
          const isActive = i === activeIdx
          return (
            <div key={step.key} className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
              isActive ? 'bg-[var(--gradient-1)]/10 border border-[var(--gradient-1)]/20' :
              isDone ? 'bg-[var(--color-bg-muted)]' :
              'bg-[var(--color-bg-muted)]/50'
            }`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 transition-all ${
                isDone ? 'bg-[var(--gradient-1)] text-white' :
                isActive ? 'border-2 border-[var(--gradient-1)] text-[var(--gradient-1)]' :
                'border-2 border-[var(--color-border-strong)] text-[var(--color-text-tertiary)]'
              }`}>
                {isDone ? (
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : isActive ? (
                  <div className="w-2 h-2 bg-[var(--gradient-1)] rounded-full animate-pulse" />
                ) : (
                  <span className="text-xs font-medium">{i + 1}</span>
                )}
              </div>
              <span className={`text-sm ${
                isActive ? 'text-[var(--color-text)] font-medium' :
                isDone ? 'text-[var(--color-text-secondary)]' :
                'text-[var(--color-text-tertiary)]'
              }`}>
                {step.label}
                {isActive && <span className="ml-2 text-[var(--gradient-1)]">진행 중...</span>}
                {isDone && <span className="ml-2 text-[var(--color-text-tertiary)]">완료</span>}
              </span>
            </div>
          )
        })}
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-[var(--color-text-tertiary)]">전체 진행률</span>
          <span className="text-xs font-medium text-[var(--color-text)]">{getProgressPercentage(status, progressPercentage)}%</span>
        </div>
        <div className="w-full h-2 bg-[var(--color-bg-muted)] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${getProgressPercentage(status, progressPercentage)}%`,
              background: 'linear-gradient(90deg, var(--gradient-1), var(--gradient-4))',
            }}
          />
        </div>
      </div>

      {/* Hint */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[var(--color-bg-muted)] rounded-lg">
        <svg className="w-4 h-4 text-[var(--color-text-tertiary)] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-xs text-[var(--color-text-tertiary)]">
          다른 페이지로 이동해도 알림을 받을 수 있습니다
        </p>
      </div>
    </div>
  )
}
