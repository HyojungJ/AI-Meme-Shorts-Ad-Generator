import React from 'react'

const progressSteps = [
  { key: 'pending', label: '정보 입력' },
  { key: 'character_generating', label: '이미지 생성' },
  { key: 'voice_generating', label: '음성 생성' },
  { key: 'asset_review', label: '캐릭터 검수' },
  { key: 'scenario_generating', label: '시나리오 생성' },
  { key: 'video_generating', label: '영상 생성' },
  { key: 'video_review', label: '영상 검수' },
  { key: 'completed', label: '완료' },
]

export function ProgressBar({ currentStep }: { currentStep: number }) {
  return (
    <div className="glass-card p-6 mb-6">
      <h2 className="text-lg font-semibold text-[var(--color-text)] mb-6">진행 상황</h2>
      <div className="flex items-center justify-between relative">
        {progressSteps.map((step, i) => (
          <React.Fragment key={step.key}>
            <div className="flex flex-col items-center relative z-10">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  currentStep === -1
                    ? 'bg-red-500/10 text-red-400 border-2 border-red-500/30'
                    : i < currentStep
                    ? 'bg-[var(--gradient-1)] text-white'
                    : i === currentStep
                    ? 'bg-transparent text-[var(--gradient-1)] border-2 border-[var(--gradient-1)] shadow-[0_0_12px_rgba(255,107,107,0.4)]'
                    : 'bg-transparent text-[var(--color-text-tertiary)] border-2 border-[var(--color-border-strong)]'
                }`}
              >
                {currentStep === -1 ? '!' : i < currentStep ? '✓' : i + 1}
              </div>
              <span className={`mt-3 text-xs whitespace-nowrap ${i <= currentStep ? 'text-[var(--color-text)]' : 'text-[var(--color-text-tertiary)]'}`}>
                {step.label}
              </span>
            </div>
            {i < progressSteps.length - 1 && (
              <div
                className={`flex-1 h-0.5 transition-colors ${
                  i < currentStep
                    ? 'bg-[var(--gradient-1)]'
                    : 'bg-[var(--color-border-strong)]'
                }`}
                style={{ marginTop: '-20px' }}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
