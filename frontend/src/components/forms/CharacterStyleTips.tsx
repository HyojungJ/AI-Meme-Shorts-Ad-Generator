'use client'

import { useState } from 'react'

export function CharacterStyleTips({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'image' | 'voice'>('image')

  if (!isOpen) return null

  return (
    <div className="mt-4 mb-6 p-4 bg-[var(--color-bg-muted)] border border-[var(--color-input-border)] rounded-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('image')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              activeTab === 'image'
                ? 'bg-[var(--gradient-1)] text-black font-medium'
                : 'text-[var(--color-input-hint)] hover:text-[var(--color-text)]'
            }`}
          >
            캐릭터 외형
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('voice')}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              activeTab === 'voice'
                ? 'bg-[var(--gradient-3)] text-black font-medium'
                : 'text-[var(--color-input-hint)] hover:text-[var(--color-text)]'
            }`}
          >
            음성 스타일
          </button>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1 text-[var(--color-input-hint)] hover:text-[var(--color-text)] transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {activeTab === 'image' ? (
        <div className="space-y-3 text-sm">
          <p className="text-[var(--gradient-1)] font-medium">이미지 생성 프롬프트 팁</p>
          <ul className="space-y-2 text-[var(--color-text-secondary)]">
            <li className="flex gap-2">
              <span className="text-[var(--gradient-1)]">•</span>
              <span><strong className="text-[var(--color-text)]">장면을 설명하세요</strong> - 키워드만 나열하지 말고 구체적으로 묘사</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-1)]">•</span>
              <span><strong className="text-[var(--color-text)]">스타일 명시</strong> - 일러스트, 3D, 애니메이션 등 원하는 스타일 언급</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-1)]">•</span>
              <span><strong className="text-[var(--color-text)]">조명과 분위기</strong> - 밝은, 따뜻한, 차가운, 네온 등</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-1)]">•</span>
              <span><strong className="text-[var(--color-text)]">캐릭터 특징</strong> - 나이대, 성별, 헤어스타일, 의상, 표정</span>
            </li>
          </ul>
          <div className="mt-3 p-3 bg-[var(--color-input-bg)] rounded-lg">
            <p className="text-xs text-[var(--color-input-hint)] mb-1">예시</p>
            <p className="text-[var(--color-text-secondary)]">&ldquo;20대 여성, 짧은 단발머리, 밝은 미소, 캐주얼한 흰색 티셔츠, 파스텔톤 배경, 친근하고 따뜻한 느낌의 일러스트 스타일&rdquo;</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3 text-sm">
          <p className="text-[var(--gradient-3)] font-medium">음성 디자인 프롬프트 팁</p>
          <ul className="space-y-2 text-[var(--color-text-secondary)]">
            <li className="flex gap-2">
              <span className="text-[var(--gradient-3)]">•</span>
              <span><strong className="text-[var(--color-text)]">나이와 성별</strong> - 젊은, 중년, 노년 / 남성, 여성</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-3)]">•</span>
              <span><strong className="text-[var(--color-text)]">목소리 특성</strong> - 깊은, 따뜻한, 허스키, 부드러운, 날카로운</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-3)]">•</span>
              <span><strong className="text-[var(--color-text)]">말하는 속도</strong> - 빠른, 느린, 차분한, 에너지 넘치는</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-3)]">•</span>
              <span><strong className="text-[var(--color-text)]">감정과 톤</strong> - 친근한, 전문적인, 유쾌한, 진지한, 장난스러운</span>
            </li>
            <li className="flex gap-2">
              <span className="text-[var(--gradient-3)]">•</span>
              <span><strong className="text-[var(--color-text)]">악센트</strong> - 필요시 지역 특성 (서울, 부산, 제주 등)</span>
            </li>
          </ul>
          <div className="mt-3 p-3 bg-[var(--color-input-bg)] rounded-lg">
            <p className="text-xs text-[var(--color-input-hint)] mb-1">예시</p>
            <p className="text-[var(--color-text-secondary)]">&ldquo;30대 여성, 밝고 에너지 넘치는 목소리, 빠른 말투, 친근하고 장난스러운 톤&rdquo;</p>
          </div>
        </div>
      )}
    </div>
  )
}
