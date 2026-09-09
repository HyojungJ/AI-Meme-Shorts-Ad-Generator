'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { memeApi, characterProfilesApi, videoApi, type Meme, type CharacterProfile, type MemeSortItem } from '@/lib/api'
import { useToast } from '@/components/ui/Toast'
import { logger } from '@/lib/logger'
import { ProductSection } from './_video-form/ProductSection'
import { MemeDropdown } from './_video-form/MemeDropdown'
import { CharacterSection } from './_video-form/CharacterSection'

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

export function VideoRequestForm({ onSubmit, onCancel }: { onSubmit: (data: FormData) => void; onCancel: () => void }) {
  const [memes, setMemes] = useState<Meme[]>([])
  const [memesLoading, setMemesLoading] = useState(true)
  const [characterProfiles, setCharacterProfiles] = useState<CharacterProfile[]>([])
  const [existingCharacters, setExistingCharacters] = useState<Array<{
    character_id: number
    image_url: string
    image_prompt?: string | null
    created_at?: string
  }>>([])
  const [existingCharactersLoading, setExistingCharactersLoading] = useState(true)
  const [isSuggesting, setIsSuggesting] = useState(false)
  const [isSortingMemes, setIsSortingMemes] = useState(false)
  const [memeSimilarities, setMemeSimilarities] = useState<Record<number, MemeSortItem>>({})
  const [isSorted, setIsSorted] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    async function fetchMemes() {
      try {
        const response = await memeApi.getMemes({ limit: 200 })
        setMemes(response.memes)
      } catch (error) {
        logger.error('VideoForm', 'Failed to load memes:', error)
      } finally {
        setMemesLoading(false)
      }
    }
    fetchMemes()
  }, [])

  useEffect(() => {
    async function fetchProfiles() {
      try {
        const profiles = await characterProfilesApi.getProfiles()
        logger.debug('VideoForm', 'Fetched profiles:', profiles)
        setCharacterProfiles(profiles)
      } catch (error) {
        logger.error('VideoForm', 'Failed to load character profiles:', error)
      }
    }
    fetchProfiles()
  }, [])

  useEffect(() => {
    async function fetchExistingCharacters() {
      try {
        const characters = await videoApi.getCharacters()
        logger.debug('VideoForm', 'getCharacters response:', characters)
        const sorted = (characters || [])
          .map((c) => ({
            character_id: c.character_id,
            image_url: c.image_url,
            image_prompt: c.image_prompt,
            created_at: c.created_at,
          }))
          .sort((a, b) => {
            if (!a.created_at || !b.created_at) return 0
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          })
          .slice(0, 5)
        setExistingCharacters(sorted)
      } catch (error) {
        logger.error('VideoForm', 'Failed to load existing characters:', error)
        if (error instanceof Error) {
          logger.error('VideoForm', 'Existing characters error message:', error.message)
        }
      } finally {
        setExistingCharactersLoading(false)
      }
    }
    fetchExistingCharacters()
  }, [])

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    setError,
    clearErrors,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    defaultValues: {
      productImage: null,
      productUrl: '',
      characterVoicePrompt: '',
      characterChoice: 'new',
      characterId: '',
    },
  })

  const watchedProductName = watch('productName')
  const watchedProductCategory = watch('productCategory')
  const watchedCustomCategory = watch('customCategory')
  const watchedProductHighlight = watch('productHighlight')
  const watchedCharacterChoice = watch('characterChoice')
  const canSuggestPrompts = Boolean(watchedProductName?.trim())
    && Boolean((watchedProductCategory === '기타' ? watchedCustomCategory : watchedProductCategory)?.trim())
    && Boolean(watchedProductHighlight?.trim())

  const productImage = watch('productImage')

  const handleSuggestPrompts = async () => {
    const values = getValues()
    const productName = values.productName?.trim()
    const productCategory = values.productCategory?.trim()
    const productHighlight = values.productHighlight?.trim()

    if (!productName) {
      setError('productName', { message: '제품 이름을 입력하세요' })
      return
    }
    if (!productCategory) {
      setError('productCategory', { message: '카테고리를 선택하세요' })
      return
    }
    if (!productHighlight) {
      setError('productHighlight', { message: '제품 설명을 입력하세요' })
      return
    }

    const finalCategory = productCategory === '기타' && values.customCategory
      ? values.customCategory
      : productCategory

    setIsSuggesting(true)
    try {
      const result = await videoApi.suggestCharacterPrompts({
        product_name: productName,
        product_category: finalCategory,
        product_description: productHighlight,
      })

      if (result.character_image_prompt) {
        setValue('characterImagePrompt', result.character_image_prompt, { shouldValidate: true })
        clearErrors('characterImagePrompt')
      }
      if (result.character_voice_prompt) {
        setValue('characterVoicePrompt', result.character_voice_prompt)
      }
      showToast('생성이 완료되었습니다.', 'success')
    } catch (error) {
      logger.error('VideoForm', 'Failed to suggest prompts:', error)
      showToast('프롬프트 생성에 실패했습니다.', 'error')
    } finally {
      setIsSuggesting(false)
    }
  }

  const handleSortMemes = async () => {
    logger.debug('VideoForm', 'MEME SORT 버튼 클릭됨')
    const productHighlight = getValues('productHighlight')?.trim()
    logger.debug('VideoForm', 'MEME SORT 제품 설명:', productHighlight)

    if (!productHighlight) {
      setError('productHighlight', { message: '추천 정렬을 위해 제품 설명을 먼저 입력하세요' })
      return
    }

    setIsSortingMemes(true)
    try {
      logger.debug('VideoForm', 'MEME SORT API 호출 시작')
      const response = await memeApi.sortMemes(productHighlight)
      logger.debug('VideoForm', 'MEME SORT API 응답:', response)

      const simMap: Record<number, MemeSortItem> = {}
      response.results.forEach((item) => {
        simMap[item.meme_id] = item
      })
      setMemeSimilarities(simMap)

      const sortedIds = response.results.map((r) => r.meme_id)
      setMemes((prev) => {
        const inSort = prev.filter((m) => sortedIds.includes(m.meme_id))
        const notInSort = prev.filter((m) => !sortedIds.includes(m.meme_id))
        inSort.sort((a, b) => sortedIds.indexOf(a.meme_id) - sortedIds.indexOf(b.meme_id))
        return [...inSort, ...notInSort]
      })
      setIsSorted(true)
      showToast('제품에 맞는 밈 순서로 정렬했습니다.', 'success')
    } catch (error) {
      logger.error('VideoForm', 'MEME SORT 에러:', error)
      showToast('밈 추천 정렬에 실패했습니다.', 'error')
    } finally {
      setIsSortingMemes(false)
    }
  }

  const onSubmitWithImageCheck = (data: FormData) => {
    if (!data.productImage) {
      setError('productImage', { message: '제품 이미지를 업로드하세요' })
      return
    }
    onSubmit(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmitWithImageCheck)} className="space-y-8">
      <ProductSection
        register={register}
        watch={watch}
        errors={errors}
        setValue={setValue}
        clearErrors={clearErrors}
        productImage={productImage}
      />

      <MemeDropdown
        memes={memes}
        memesLoading={memesLoading}
        setValue={setValue}
        register={register}
        watch={watch}
        errors={errors}
        memeSimilarities={memeSimilarities}
        isSortingMemes={isSortingMemes}
        isSorted={isSorted}
        watchedProductHighlight={watchedProductHighlight}
        onSortMemes={handleSortMemes}
        onSetIsSorted={setIsSorted}
      />

      <CharacterSection
        register={register}
        watch={watch}
        setValue={setValue}
        errors={errors}
        clearErrors={clearErrors}
        existingCharacters={existingCharacters}
        existingCharactersLoading={existingCharactersLoading}
        characterProfiles={characterProfiles}
        isSuggesting={isSuggesting}
        canSuggestPrompts={canSuggestPrompts}
        watchedCharacterChoice={watchedCharacterChoice}
        onSuggestPrompts={handleSuggestPrompts}
        showToast={showToast}
      />

      {/* Actions */}
      <div className="flex justify-end gap-4 pt-6 border-t border-[var(--color-input-border)]">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2.5 bg-[var(--color-input-border)] text-[var(--color-text)] font-medium rounded-lg hover:bg-[var(--color-border-strong)] transition-colors"
        >
          취소
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2.5 btn-primary rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
              처리 중...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              제작 요청
            </>
          )}
        </button>
      </div>
    </form>
  )
}
