'use client'

import { useState, useEffect, useRef } from 'react'
import { UseFormRegister, UseFormWatch, FieldErrors, UseFormSetValue } from 'react-hook-form'
import type { Meme, MemeSortItem } from '@/lib/api'

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

export function MemeDropdown({
  memes, memesLoading, setValue, register, watch, errors,
  memeSimilarities, isSortingMemes, isSorted,
  watchedProductHighlight,
  onSortMemes, onSetIsSorted,
}: {
  memes: Meme[]
  memesLoading: boolean
  setValue: UseFormSetValue<FormData>
  register: UseFormRegister<FormData>
  watch: UseFormWatch<FormData>
  errors: FieldErrors<FormData>
  memeSimilarities: Record<number, MemeSortItem>
  isSortingMemes: boolean
  isSorted: boolean
  watchedProductHighlight: string | undefined
  onSortMemes: () => void
  onSetIsSorted: (v: boolean) => void
}) {
  const [memeDropdownOpen, setMemeDropdownOpen] = useState(false)
  const [memeSearch, setMemeSearch] = useState('')
  const [memeSortBy, setMemeSortBy] = useState<'latest' | 'usage'>('latest')
  const memeDropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node
      if (memeDropdownRef.current && !memeDropdownRef.current.contains(target)) {
        setMemeDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredMemes = memes
    .filter(m => m.meme_name.toLowerCase().includes(memeSearch.toLowerCase()))
    .sort((a, b) => {
      if (isSorted) {
        const simA = memeSimilarities[a.meme_id]?.similarity ?? -1
        const simB = memeSimilarities[b.meme_id]?.similarity ?? -1
        return simB - simA
      } else if (memeSortBy === 'latest') {
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      } else {
        return (b.usage_count || 0) - (a.usage_count || 0)
      }
    })

  return (
    <section>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-[var(--gradient-1)]/10 rounded-xl flex items-center justify-center">
          <svg className="w-5 h-5 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-[var(--color-text)]">밈 선택 <span className="text-[var(--gradient-1)]">*</span></h3>
          <p className="text-sm text-[var(--color-input-hint)]">영상에 사용할 밈 스타일을 선택하세요</p>
        </div>
      </div>

      <input type="hidden" {...register('memeId', { required: '밈을 선택하세요' })} />
      <div ref={memeDropdownRef} className="relative">
        <button
          type="button"
          onClick={() => !memesLoading && setMemeDropdownOpen(!memeDropdownOpen)}
          disabled={memesLoading}
          className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-left text-[var(--color-text)] focus:outline-none focus:ring-1 transition-all disabled:opacity-50 flex items-center justify-between ${
            errors.memeId
              ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
              : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
          }`}
        >
          <span className={watch('memeId') ? 'text-[var(--color-text)]' : 'text-[var(--color-input-placeholder)]'}>
            {memesLoading
              ? '밈 로딩 중...'
              : watch('memeId')
                ? memes.find(m => String(m.meme_id) === watch('memeId'))?.meme_name
                : '밈을 선택하세요'}
          </span>
          <svg className={`w-5 h-5 text-[var(--color-input-placeholder)] transition-transform ${memeDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {memeDropdownOpen && (
          <div className="absolute z-50 w-full mt-2 bg-[var(--color-bg-muted)] border border-[var(--color-border-strong)] rounded-xl shadow-xl overflow-hidden">
            <div className="p-2 border-b border-[var(--color-border-strong)] space-y-2">
              <input
                type="text"
                placeholder="밈 검색..."
                value={memeSearch}
                onChange={(e) => setMemeSearch(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--color-input-bg)] border border-[var(--color-border-strong)] rounded-lg text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:border-[var(--gradient-1)]/50 text-sm"
                onClick={(e) => e.stopPropagation()}
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setMemeSortBy('latest')
                    onSetIsSorted(false)
                  }}
                  className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    memeSortBy === 'latest' && !isSorted
                      ? 'bg-[var(--gradient-1)] text-white'
                      : 'bg-[var(--color-input-bg)] text-[var(--color-input-hint)] hover:text-[var(--color-text)]'
                  }`}
                >
                  최신순
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMemeSortBy('usage')
                    onSetIsSorted(false)
                  }}
                  className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                    memeSortBy === 'usage' && !isSorted
                      ? 'bg-[var(--gradient-1)] text-white'
                      : 'bg-[var(--color-input-bg)] text-[var(--color-input-hint)] hover:text-[var(--color-text)]'
                  }`}
                >
                  사용횟수순
                </button>
                <button
                  type="button"
                  onClick={onSortMemes}
                  disabled={isSortingMemes || !watchedProductHighlight?.trim()}
                  title={!watchedProductHighlight?.trim() ? '제품 설명을 입력해야 가능합니다' : ''}
                  className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    isSorted
                      ? 'bg-[var(--gradient-1)] text-white'
                      : 'bg-[var(--color-input-bg)] text-[var(--color-input-hint)] hover:text-[var(--color-text)]'
                  }`}
                >
                  {isSortingMemes ? '분석 중...' : '밈 추천'}
                </button>
              </div>
            </div>
            <div className="max-h-72 overflow-y-auto">
              {filteredMemes.length === 0 ? (
                <div className="px-4 py-3 text-[var(--color-input-placeholder)] text-sm">검색 결과가 없습니다</div>
              ) : (
                filteredMemes.map((meme) => {
                  const sim = memeSimilarities[meme.meme_id]
                  return (
                    <button
                      key={meme.meme_id}
                      type="button"
                      onClick={() => {
                        setValue('memeId', String(meme.meme_id))
                        setMemeDropdownOpen(false)
                        setMemeSearch('')
                      }}
                      className={`w-full px-4 py-3 text-left hover:bg-[var(--color-input-border)] transition-colors border-b border-[var(--color-input-border)] last:border-b-0 ${
                        watch('memeId') === String(meme.meme_id)
                          ? 'bg-[var(--gradient-1)]/10'
                          : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`font-medium ${watch('memeId') === String(meme.meme_id) ? 'text-[var(--gradient-1)]' : 'text-[var(--color-text)]'}`}>
                          {meme.meme_name}
                        </span>
                        <div className="flex items-center gap-2">
                          {sim && (
                            <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                              sim.similarity >= 0.7
                                ? 'bg-green-500/10 text-green-400'
                                : sim.similarity >= 0.5
                                  ? 'bg-yellow-500/10 text-yellow-400'
                                  : 'bg-[var(--color-input-border)] text-[var(--color-text-tertiary)]'
                            }`}>
                              {(sim.similarity * 100).toFixed(1)}%
                            </span>
                          )}
                          <span className="text-xs text-[var(--color-text-tertiary)]">{meme.usage_count}회 사용</span>
                        </div>
                      </div>
                      {sim ? (
                        <p className="text-xs text-[var(--color-input-hint)] line-clamp-2">{sim.situation}</p>
                      ) : meme.description ? (
                        <p className="text-xs text-[var(--color-input-hint)] line-clamp-2">{meme.description}</p>
                      ) : null}
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}
      </div>
      {errors.memeId && (
        <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.memeId.message}</p>
      )}
      {!memesLoading && memes.length === 0 && (
        <p className="mt-2 text-sm text-yellow-400">사용 가능한 밈이 없습니다</p>
      )}
    </section>
  )
}
