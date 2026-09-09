'use client'

import { useRouter } from 'next/navigation'
import { VideoRequestForm } from '@/components/forms/VideoRequestForm'
import { videoApi } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/components/ui/Toast'

type VideoFormData = {
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

export default function VideoRequestPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { showToast } = useToast()

  const handleSubmit = (data: unknown) => {
    const formValues = data as VideoFormData

    const formData = new FormData()
    formData.append('product_name', formValues.productName)
    // "기타" 선택 시 customCategory 값을 사용, 아니면 선택한 카테고리 사용
    const finalCategory = formValues.productCategory === '기타' && formValues.customCategory 
      ? formValues.customCategory 
      : formValues.productCategory
    formData.append('product_category', finalCategory)
    formData.append('product_description', formValues.productHighlight)  // product_highlight → product_description
    if (formValues.memeId) {
      formData.append('meme_id', formValues.memeId)
    }
    formData.append('character_choice', formValues.characterChoice)
    if (formValues.characterChoice === 'existing' && formValues.characterId) {
      formData.append('character_id', formValues.characterId)
    }
    formData.append('character_image_prompt', formValues.characterImagePrompt)
    formData.append('company_name', user?.companyName || '')
    if (formValues.productImage) {
      formData.append('product_image', formValues.productImage)
    }
    if (formValues.productUrl) {
      formData.append('product_url', formValues.productUrl)
    }
    if (formValues.characterVoicePrompt) {
      formData.append('character_voice_prompt', formValues.characterVoicePrompt)
    }

    // API 호출 후 페이지 이동
    showToast('영상 제작 요청이 접수되었습니다', 'info')
    router.push('/user')

    videoApi.generateVideo(formData).catch((error) => {
      showToast(error instanceof Error ? error.message : '영상 제작 요청 실패', 'error')
    })
  }

  return (
    <div className="max-w-4xl mx-auto font-body">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">Video Generation</h1>
        <p className="text-[var(--color-text-secondary)] text-sm md:text-base">AI가 자동으로 밈 광고 영상을 제작해드립니다</p>
      </div>

      {/* Form Card */}
      <div className="glass-card p-8">
        <VideoRequestForm onSubmit={handleSubmit} onCancel={() => router.back()} />
      </div>

      {/* Tips */}
      <div className="mt-6 p-5 bg-[var(--gradient-1)]/5 border border-[var(--gradient-1)]/20 rounded-xl">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-[var(--gradient-1)]/10 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-4 h-4 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--gradient-1)] mb-1">제작 팁</p>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
              제품 설명을 명확하게 작성할수록 더 효과적인 영상이 제작됩니다.
              제품의 핵심 특징과 타겟 고객층을 고려해 작성해보세요.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
