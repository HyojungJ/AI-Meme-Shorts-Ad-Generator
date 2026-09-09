'use client'

import { UseFormRegister, UseFormWatch, FieldErrors, UseFormSetValue, UseFormClearErrors } from 'react-hook-form'
import { PRODUCT_CATEGORIES } from '@/lib/constants'
import { FileDropzone } from '../FileDropzone'

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

export function ProductSection({
  register, watch, errors, setValue, clearErrors, productImage,
}: {
  register: UseFormRegister<FormData>
  watch: UseFormWatch<FormData>
  errors: FieldErrors<FormData>
  setValue: UseFormSetValue<FormData>
  clearErrors: UseFormClearErrors<FormData>
  productImage: File | null
}) {
  return (
    <>
      {/* 제품 기본 정보 */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-[var(--gradient-1)]/10 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">제품 정보</h3>
            <p className="text-sm text-[var(--color-input-hint)]">광고할 제품의 정보를 입력하세요</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="productName" className="block text-sm font-medium text-[var(--color-text)] mb-2">
              제품명 <span className="text-[var(--gradient-1)]">*</span>
            </label>
            <input
              id="productName"
              type="text"
              {...register('productName', { required: '제품명을 입력하세요' })}
              className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:ring-1 transition-all ${
                errors.productName
                  ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                  : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
              }`}
              placeholder="제품명을 입력하세요"
            />
            {errors.productName && (
              <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.productName.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="productCategory" className="block text-sm font-medium text-[var(--color-text)] mb-2">
              제품 카테고리 <span className="text-[var(--gradient-1)]">*</span>
            </label>
            <select
              id="productCategory"
              {...register('productCategory', { required: '카테고리를 선택하세요' })}
              className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] focus:outline-none focus:ring-1 transition-all appearance-none cursor-pointer ${
                errors.productCategory
                  ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                  : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
              }`}
            >
              <option value="" className="bg-[var(--color-bg-muted)]">선택하세요</option>
              {PRODUCT_CATEGORIES.map((cat) => (
                <option key={cat} value={cat} className="bg-[var(--color-bg-muted)]">
                  {cat}
                </option>
              ))}
            </select>
            {errors.productCategory && (
              <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.productCategory.message}</p>
            )}
          </div>

          {watch('productCategory') === '기타' && (
            <div>
              <label htmlFor="customCategory" className="block text-sm font-medium text-[var(--color-text)] mb-2">
                카테고리 직접 입력 <span className="text-[var(--gradient-1)]">*</span>
              </label>
              <input
                id="customCategory"
                type="text"
                {...register('customCategory', {
                  required: watch('productCategory') === '기타' ? '카테고리를 입력하세요' : false
                })}
                className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:ring-1 transition-all ${
                  errors.customCategory
                    ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                    : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
                }`}
                placeholder="카테고리를 입력하세요"
              />
              {errors.customCategory && (
                <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.customCategory.message}</p>
              )}
            </div>
          )}

          <div className="md:col-span-2">
            <label htmlFor="productHighlight" className="block text-sm font-medium text-[var(--color-text)] mb-2">
              제품 설명 <span className="text-[var(--gradient-1)]">*</span>
            </label>
            <textarea
              id="productHighlight"
              {...register('productHighlight', { required: '제품 설명을 입력하세요', maxLength: { value: 500, message: '500자 이하로 입력하세요' } })}
              rows={4}
              maxLength={500}
              placeholder={"제품의 특징, 장점, 사용 용도 등을 자유롭게 설명해주세요\n예시: 100% 유기농 원료로 만든 저자극 스킨케어 제품입니다. 민감한 피부에도 안심하고 사용할 수 있으며, 24시간 지속되는 보습력이 특징입니다."}
              className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:ring-1 transition-all resize-none ${
                errors.productHighlight
                  ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                  : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
              }`}
            />
            <div className="flex justify-between mt-1">
              {errors.productHighlight ? (
                <p className="text-sm text-[var(--status-error-text)]">{errors.productHighlight.message}</p>
              ) : (
                <span />
              )}
              <span className="text-xs text-[var(--color-input-placeholder)]">{watch('productHighlight')?.length || 0}/500</span>
            </div>
          </div>

          <div className="md:col-span-2 mt-3">
            <label htmlFor="productUrl" className="block text-sm font-medium text-[var(--color-text)] mb-2">제품 URL</label>
            <input
              id="productUrl"
              type="url"
              {...register('productUrl', {
                pattern: {
                  value: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/,
                  message: '올바른 URL 형식이 아닙니다'
                }
              })}
              placeholder="https://..."
              className={`w-full px-4 py-3 bg-[var(--color-input-bg)] border rounded-xl text-[var(--color-text)] placeholder-[var(--color-input-placeholder)] focus:outline-none focus:ring-1 transition-all ${
                errors.productUrl
                  ? 'border-[var(--status-error-border)] focus:border-[var(--status-error-border)] focus:ring-[var(--status-error-bg)]'
                  : 'border-[var(--color-input-border)] focus:border-[var(--gradient-1)]/50 focus:ring-[var(--gradient-1)]/20'
              }`}
            />
            {errors.productUrl && (
              <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.productUrl.message}</p>
            )}
          </div>
        </div>
      </section>

      {/* 제품 이미지 */}
      <section>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-[#a855f7]/10 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-[#a855f7]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text)]">제품 이미지 <span className="text-[var(--gradient-1)]">*</span></h3>
            <p className="text-sm text-[var(--color-input-hint)]">영상에 사용할 제품 이미지를 업로드하세요</p>
          </div>
        </div>

        <FileDropzone
          label="제품 이미지"
          accept={{ 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] }}
          value={productImage}
          onChange={(f) => { setValue('productImage', f); if (f) clearErrors('productImage') }}
          required
          hint="고해상도 이미지 권장 (PNG, JPG, WEBP, 최대 10MB)"
        />
        {errors.productImage && (
          <p className="mt-2 text-sm text-[var(--status-error-text)]">{errors.productImage.message}</p>
        )}
      </section>
    </>
  )
}
