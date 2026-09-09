'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export function FileDropzone({
  label,
  accept,
  value,
  onChange,
  required,
  hint,
}: {
  label: string
  accept: Record<string, string[]>
  value: File | null
  onChange: (file: File | null) => void
  required?: boolean
  hint?: string
}) {
  const onDrop = useCallback(
    (files: File[]) => {
      if (files[0]) onChange(files[0])
    },
    [onChange]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
  })

  return (
    <div>
      <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
        {label} {required && <span className="text-[var(--gradient-1)]">*</span>}
      </label>
      <div
        {...getRootProps()}
        aria-label={label}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-[var(--gradient-1)] bg-[var(--gradient-1)]/5'
            : 'border-[var(--color-input-border)] hover:border-[var(--color-border-strong)] bg-[var(--color-input-bg)]'
        }`}
      >
        <input {...getInputProps()} />
        {value ? (
          <div className="flex items-center justify-center gap-3">
            <div className="w-10 h-10 bg-[var(--gradient-1)]/10 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <span className="text-sm text-[var(--color-text)]">{value.name}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                onChange(null)
              }}
              className="p-1 text-[var(--color-input-hint)] hover:text-[var(--color-danger-text)] transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ) : (
          <div>
            <div className="w-12 h-12 bg-[var(--color-input-border)] rounded-xl flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-[var(--color-input-placeholder)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p className="text-sm text-[var(--color-input-hint)]">
              {isDragActive ? '파일을 놓으세요' : '파일을 드래그하거나 클릭하여 업로드'}
            </p>
            {hint && <p className="text-xs text-[var(--color-input-placeholder)] mt-1">{hint}</p>}
          </div>
        )}
      </div>
    </div>
  )
}
