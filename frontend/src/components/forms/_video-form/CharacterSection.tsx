'use client'

import { useState, useEffect, useRef } from 'react'
import { UseFormRegister, UseFormWatch, FieldErrors, UseFormSetValue, UseFormClearErrors } from 'react-hook-form'
import { CharacterStyleTips } from '../CharacterStyleTips'
import { API_URL_EXPORT, type CharacterProfile } from '@/lib/api'

type FormData = {
  productName: string
  productCategory: string
  customCategory?: string
  productHighlight: string
  memeId: string
  characterChoice: 'existing' | 'new'
  characterId?: string
  characterImagePrompt: string
  productImage: File | null
  productUrl: string
  characterVoicePrompt: string
}

export function CharacterSection({
  register, watch, setValue, errors, clearErrors,
  existingCharacters, existingCharactersLoading,
  characterProfiles, isSuggesting, canSuggestPrompts,
  watchedCharacterChoice,
  onSuggestPrompts, showToast,
}: {
  register: UseFormRegister<FormData>
  watch: UseFormWatch<FormData>
  setValue: UseFormSetValue<FormData>
  errors: FieldErrors<FormData>
  clearErrors: UseFormClearErrors<FormData>
  existingCharacters: Array<{
    character_id: number
    image_url: string
    image_prompt?: string | null
    created_at?: string
  }>
  existingCharactersLoading: boolean
  characterProfiles: CharacterProfile[]
  isSuggesting: boolean
  canSuggestPrompts: boolean
  watchedCharacterChoice: 'existing' | 'new'
  onSuggestPrompts: () => void
  showToast: (message: string, type: 'success' | 'error') => void
}) {
  const [showTips, setShowTips] = useState(false)
  const [characterDropdownOpen, setCharacterDropdownOpen] = useState(false)
  const [previewImageUrl, setPreviewImageUrl] = useState<string | null>(null)
  const [selectedProfile, setSelectedProfile] = useState<CharacterProfile | null>(null)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const characterDropdownRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node
      if (characterDropdownRef.current && !characterDropdownRef.current.contains(target)) {
        setCharacterDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <>
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-[var(--gradient-3)]/10 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">캐릭터 선택 <span className="text-[var(--gradient-1)]">*</span></h3>
            <p className="text-sm text-[var(--color-input-hint)]">기존 캐릭터를 사용할지 새 캐릭터를 만들지 선택하세요</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <label className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
            watchedCharacterChoice === 'existing'
              ? 'border-[var(--gradient-1)]/60 bg-[var(--gradient-1)]/10'
              : 'border-[var(--color-input-border)] bg-[var(--color-input-bg)] hover:border-[var(--gradient-1)]/30'
          }`}>
            <input
              type="radio"
              value="existing"
              {...register('characterChoice', { required: '캐릭터 선택을 해주세요' })}
              className="accent-[var(--gradient-1)]"
            />
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">기존 캐릭터 사용</p>
              <p className="text-xs text-[var(--color-text-tertiary)]">이미 생성된 캐릭터를 선택</p>
            </div>
          </label>
          <label className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
            watchedCharacterChoice === 'new'
              ? 'border-[var(--gradient-1)]/60 bg-[var(--gradient-1)]/10'
              : 'border-[var(--color-input-border)] bg-[var(--color-input-bg)] hover:border-[var(--gradient-1)]/30'
          }`}>
            <input
              type="radio"
              value="new"
              {...register('characterChoice', { required: '캐릭터 선택을 해주세요' })}
              className="accent-[var(--gradient-1)]"
            />
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">새 캐릭터 생성</p>
              <p className="text-xs text-[var(--color-text-tertiary)]">신규 캐릭터를 생성</p>
            </div>
          </label>
        </div>

        {errors.characterChoice && (
          <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.characterChoice.message}</p>
        )}

        {watchedCharacterChoice === 'existing' && (
          <div className="mb-8">
            <label htmlFor="characterId" className="block text-sm font-medium text-[var(--color-text)] mb-2">
              기존 캐릭터 선택 <span className="text-[var(--gradient-1)]">*</span>
            </label>
            <div ref={characterDropdownRef} className="relative">
              <input type="hidden" {...register('characterId', {
                validate: (value) => watchedCharacterChoice !== 'existing' || Boolean(value) || '캐릭터를 선택하세요',
              })} />
              <button
                type="button"
                onClick={() => setCharacterDropdownOpen((prev) => !prev)}
                className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] focus:outline-none focus:ring-1 transition-all flex items-center justify-between ${
                  errors.characterId
                    ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                    : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
                }`}
              >
                <span className="truncate">
                  {(() => {
                    const selectedId = watch('characterId')
                    const selected = existingCharacters.find((c) => String(c.character_id) === selectedId)
                    if (!selected) return '선택하세요'
                    return `캐릭터 #${selected.character_id}${selected.image_prompt ? ` - ${selected.image_prompt.slice(0, 20)}` : ''}`
                  })()}
                </span>
                <svg className={`w-4 h-4 text-[var(--color-text-tertiary)] transition-transform ${characterDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {characterDropdownOpen && (
                <div className="absolute z-20 mt-2 w-full max-h-72 overflow-auto rounded-xl border border-[var(--color-input-border)] bg-[var(--color-input-bg)] shadow-xl">
                  {existingCharacters.length === 0 && (
                    <div className="px-4 py-3 text-xs text-[var(--color-text-tertiary)]">사용 가능한 기존 캐릭터가 없습니다</div>
                  )}
                  {existingCharacters.map((ch) => (
                    <button
                      key={ch.character_id}
                      type="button"
                      onClick={() => {
                        setValue('characterId', String(ch.character_id), { shouldValidate: true })
                        clearErrors('characterId')
                        setCharacterDropdownOpen(false)
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-[var(--color-bg-muted)] transition-colors ${
                        watch('characterId') === String(ch.character_id) ? 'bg-[var(--color-bg-muted)]' : ''
                      }`}
                    >
                      {ch.image_url ? (
                        <img
                          src={ch.image_url}
                          alt={`캐릭터 ${ch.character_id}`}
                          className="w-10 h-10 rounded-md object-cover bg-[var(--color-bg-muted)] border border-[var(--color-input-border)]"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-md bg-[var(--color-bg-muted)] border border-[var(--color-input-border)] flex items-center justify-center text-[var(--color-text-tertiary)] text-[10px]">
                          No Image
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="text-sm text-[var(--color-text)] truncate">캐릭터 #{ch.character_id}</p>
                        <p className="text-xs text-[var(--color-text-tertiary)] truncate">
                          {ch.image_prompt ? ch.image_prompt : '설명 없음'}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
            {existingCharactersLoading && (
              <p className="mt-2 text-xs text-[var(--color-text-tertiary)]">기존 캐릭터 불러오는 중...</p>
            )}
            {!existingCharactersLoading && existingCharacters.length === 0 && (
              <p className="mt-2 text-xs text-yellow-400">사용 가능한 기존 캐릭터가 없습니다</p>
            )}
            {errors.characterId && (
              <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.characterId.message}</p>
            )}

            {!existingCharactersLoading && existingCharacters.length > 0 && (
              <div className="mt-3 flex items-center gap-3">
                {(() => {
                  const selectedId = watch('characterId')
                  const selected = existingCharacters.find((c) => String(c.character_id) === selectedId)
                  if (!selected) return null
                  return (
                    <>
                      {selected.image_url ? (
                        <button
                          type="button"
                          onClick={() => setPreviewImageUrl(selected.image_url)}
                          className="w-14 h-14 rounded-lg border border-[var(--color-input-border)] overflow-hidden bg-[var(--color-bg-muted)] hover:border-[var(--gradient-1)]/50 transition-colors"
                          aria-label="캐릭터 이미지 미리보기 확대"
                        >
                          <img
                            src={selected.image_url}
                            alt={`캐릭터 ${selected.character_id}`}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        </button>
                      ) : (
                        <div className="w-14 h-14 rounded-lg bg-[var(--color-bg-muted)] border border-[var(--color-input-border)] flex items-center justify-center text-[var(--color-text-tertiary)] text-xs">
                          No Image
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="text-xs text-[var(--color-text-tertiary)]">선택된 캐릭터 미리보기</p>
                        <p className="text-sm text-[var(--color-text)] truncate">
                          캐릭터 #{selected.character_id}
                        </p>
                      </div>
                    </>
                  )
                })()}
              </div>
            )}
          </div>
        )}

        {previewImageUrl && (
          <div
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            onClick={() => setPreviewImageUrl(null)}
          >
            <div
              className="max-w-2xl w-full bg-[var(--color-input-bg)] border border-[var(--color-input-border)] rounded-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between p-4 border-b border-[var(--color-input-border)]">
                <h4 className="text-sm font-medium text-[var(--color-text)]">캐릭터 미리보기</h4>
                <button
                  type="button"
                  onClick={() => setPreviewImageUrl(null)}
                  className="text-[var(--color-input-hint)] hover:text-[var(--color-text)] transition-colors"
                  aria-label="미리보기 닫기"
                >
                  ✕
                </button>
              </div>
              <div className="p-4">
                <img
                  src={previewImageUrl}
                  alt="캐릭터 미리보기"
                  className="w-full max-h-[70vh] object-contain bg-[var(--color-bg-muted)] rounded-xl"
                />
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[var(--gradient-3)]/10 rounded-xl flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--gradient-3)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--color-text)]">캐릭터 스타일 <span className="text-[var(--gradient-1)]">*</span></h3>
              <p className="text-sm text-[var(--color-input-hint)]">원하는 캐릭터 스타일을 입력하거나 제품 정보를 기반으로 한 AI 추천으로 캐릭터를 생성해보세요</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowTips(!showTips)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
              showTips
                ? 'bg-[var(--gradient-3)]/10 text-[var(--gradient-3)]'
                : 'text-[var(--color-input-hint)] hover:text-[var(--gradient-3)] hover:bg-[var(--gradient-3)]/5'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            작성 팁
          </button>
        </div>

        <div className={showTips ? 'mb-6' : ''}>
          <CharacterStyleTips isOpen={showTips} onClose={() => setShowTips(false)} />
        </div>

        {/* 캐릭터 프로필 선택 */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-[var(--color-text)] mb-3">예시 프로필 (클릭하여 확인)</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(characterProfiles || []).map((profile) => (
              <button
                key={profile.id}
                type="button"
                disabled={watchedCharacterChoice === 'existing'}
                onClick={() => {
                  setSelectedProfile(profile)
                  setProfileModalOpen(true)
                }}
                className={`p-4 bg-[var(--color-input-bg)] border border-[var(--color-input-border)] rounded-xl text-left transition-all group ${
                  watchedCharacterChoice === 'existing'
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:border-[var(--gradient-3)]/50 hover:bg-[var(--color-bg-muted)]'
                }`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-12 h-12 bg-[var(--gradient-3)]/10 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-[var(--gradient-3)]/20 transition-colors">
                    <span className="text-2xl">{profile.emoji}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-semibold text-[var(--color-text)] mb-1 group-hover:text-[var(--gradient-3)] transition-colors">
                      {profile.name}
                    </h5>
                    <p className="text-xs text-[var(--color-text-tertiary)]">{profile.subtitle}</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-[var(--color-input-hint)]">외형:</span>
                    <p className="text-xs text-[var(--color-text-secondary)] mt-0.5 line-clamp-2">{profile.appearance}</p>
                  </div>
                  <div>
                    <span className="text-xs text-[var(--color-input-hint)]">목소리:</span>
                    <p className="text-xs text-[var(--color-text-secondary)] mt-0.5 line-clamp-2">{profile.voice}</p>
                  </div>
                </div>
                <div className="mt-3 text-xs text-[var(--gradient-3)] flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  샘플 보기
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className={showTips ? 'mt-4' : ''}>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="characterImagePrompt" className="block text-sm font-medium text-[var(--color-text)]">
              캐릭터 이미지
            </label>
            <button
              type="button"
              onClick={onSuggestPrompts}
              disabled={watchedCharacterChoice !== 'new' || !canSuggestPrompts || isSuggesting}
              title={!canSuggestPrompts ? '제품 정보를 모두 입력해야 가능합니다' : ''}
              className="px-3 py-1.5 text-xs rounded-md border border-[var(--color-input-border)] text-[var(--color-text)] hover:border-[var(--gradient-1)]/50 hover:text-[var(--gradient-1)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSuggesting ? '생성중...' : 'AI 추천'}
            </button>
          </div>
          <textarea
            id="characterImagePrompt"
            {...register('characterImagePrompt', {
              validate: (value) => {
                if (watchedCharacterChoice !== 'new') return true
                return Boolean(value?.trim()) || '캐릭터 스타일을 입력하세요'
              },
              maxLength: { value: 500, message: '500자 이하로 입력하세요' },
            })}
            rows={4}
            maxLength={500}
            placeholder="예: 밝고 친근한 20대 캐릭터, 캐주얼 복장, 3D 스타일"
            disabled={watchedCharacterChoice !== 'new'}
            className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:ring-1 transition-all resize-none disabled:opacity-60 ${
              errors.characterImagePrompt
                ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
            }`}
          />
          <div className="flex justify-between mt-2">
            {errors.characterImagePrompt ? (
              <p className="text-sm text-[var(--status-error-text)]">{errors.characterImagePrompt.message}</p>
            ) : (
              <span />
            )}
            <span className="text-xs text-[var(--color-input-placeholder)]">{watch('characterImagePrompt')?.length || 0}/500</span>
          </div>
        </div>

        <div className="mt-3">
          <label htmlFor="characterVoicePrompt" className="block text-sm font-medium text-[var(--color-text)] mb-2">캐릭터 음성</label>
          <textarea
            id="characterVoicePrompt"
            {...register('characterVoicePrompt', { maxLength: { value: 500, message: '500자 이하로 입력하세요' } })}
            rows={4}
            maxLength={500}
            placeholder="예: 30대 여성, 맑고 부드러운 음색, 차분한 톤, 대화 속도는 보통"
            disabled={watchedCharacterChoice !== 'new'}
            className="w-full px-4 py-3 bg-[var(--color-input-bg)] border border-[var(--color-input-border)] rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:border-[var(--gradient-1)]/50 focus:ring-1 focus:ring-[var(--gradient-1)]/20 transition-all resize-none disabled:opacity-60"
          />
          <div className="flex justify-end mt-2">
            <span className="text-xs text-[var(--color-input-placeholder)]">{watch('characterVoicePrompt')?.length || 0}/500</span>
          </div>
          <p className="text-xs text-[var(--color-input-placeholder)] mt-2">AI가 이 설명을 바탕으로 캐릭터 이미지와 음성을 생성합니다</p>
        </div>
      </section>

      {/* 캐릭터 프로필 모달 */}
      {profileModalOpen && selectedProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={() => setProfileModalOpen(false)}>
          <div className="bg-[var(--color-input-bg)] border border-[var(--color-border-strong)] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            {/* 모달 헤더 */}
            <div className="sticky top-0 bg-[var(--color-input-bg)] border-b border-[var(--color-border-strong)] p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-[var(--gradient-3)]/10 rounded-xl flex items-center justify-center">
                  <span className="text-3xl">{selectedProfile.emoji}</span>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[var(--color-text)]">{selectedProfile.name}</h3>
                  <p className="text-sm text-[var(--color-input-hint)]">{selectedProfile.subtitle}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setProfileModalOpen(false)}
                className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-[var(--color-input-border)] transition-colors text-[var(--color-input-hint)] hover:text-[var(--color-text)]"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 모달 내용 */}
            <div className="p-6 space-y-6">
              {/* 캐릭터 이미지 */}
              <div>
                <h4 className="text-sm font-medium text-[var(--color-text)] mb-3">캐릭터 이미지</h4>
                <div className="relative rounded-xl overflow-hidden bg-[var(--color-bg-muted)] border border-[var(--color-border-strong)]">
                  <img
                    src={`${API_URL_EXPORT}${selectedProfile.image_url}`}
                    alt={selectedProfile.name}
                    className="w-full h-auto object-contain max-h-[400px]"
                    onError={(e) => {
                      e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23141414" width="400" height="400"/%3E%3Ctext fill="%23666" font-family="sans-serif" font-size="18" x="50%25" y="50%25" text-anchor="middle" dominant-baseline="middle"%3E이미지 로드 실패%3C/text%3E%3C/svg%3E'
                    }}
                  />
                </div>
              </div>

              {/* 음성 샘플 */}
              <div>
                <h4 className="text-sm font-medium text-[var(--color-text)] mb-3">음성 샘플</h4>
                <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border-strong)] rounded-xl p-4">
                  <audio
                    ref={audioRef}
                    src={`${API_URL_EXPORT}${selectedProfile.audio_url}`}
                    controls
                    className="w-full"
                    style={{ height: '40px' }}
                  />
                </div>
              </div>

              {/* 상세 설명 */}
              <div className="space-y-3">
                <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border-strong)] rounded-xl p-4">
                  <h5 className="text-xs font-medium text-[var(--color-input-hint)] mb-2">외형</h5>
                  <p className="text-sm text-[var(--color-text)]">{selectedProfile.appearance}</p>
                </div>
                <div className="bg-[var(--color-bg-muted)] border border-[var(--color-border-strong)] rounded-xl p-4">
                  <h5 className="text-xs font-medium text-[var(--color-input-hint)] mb-2">목소리</h5>
                  <p className="text-sm text-[var(--color-text)]">{selectedProfile.voice}</p>
                </div>
              </div>

              {/* 액션 버튼 */}
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setProfileModalOpen(false)}
                  className="flex-1 px-4 py-3 bg-[var(--color-input-border)] text-[var(--color-text)] font-medium rounded-lg hover:bg-[var(--color-border-strong)] transition-colors"
                >
                  닫기
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setValue('characterChoice', 'new', { shouldValidate: true })
                    setValue('characterId', '')
                    clearErrors('characterId')
                    setValue('characterImagePrompt', selectedProfile.appearance)
                    setValue('characterVoicePrompt', selectedProfile.voice)
                    clearErrors('characterImagePrompt')
                    clearErrors('characterVoicePrompt')
                    setProfileModalOpen(false)
                    showToast('프로필이 적용되었습니다', 'success')
                  }}
                  className="flex-1 px-4 py-3 btn-primary rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  이 프로필 사용하기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
