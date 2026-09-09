'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { useAuth } from '@/hooks/useAuth'
import { useToast } from '@/components/ui/Toast'

export default function ProfilePage() {
  const router = useRouter()
  const { user, logout, updateProfile } = useAuth()
  const { showToast } = useToast()
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(user?.name || '')
  const [companyName, setCompanyName] = useState(user?.companyName || '')
  const [department, setDepartment] = useState(user?.department || '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateProfile({ name, companyName, department })
      setIsEditing(false)
      showToast('프로필이 업데이트되었습니다', 'success')
    } catch (error) {
      showToast(error instanceof Error ? error.message : '프로필 업데이트 실패', 'error')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      showToast('로그아웃되었습니다', 'info')
      router.push('/login')
    } catch {
      showToast('로그아웃 실패', 'error')
    }
  }

  return (
    <div className="max-w-2xl mx-auto font-body">
      {/* Header */}
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl font-display font-bold text-[var(--color-text)] mb-2">프로필</h1>
        <p className="text-[var(--color-text-secondary)] text-sm md:text-base">계정 정보를 관리하세요</p>
      </div>

      {/* Profile Card */}
      <div className="glass-card p-6 md:p-8 mb-6">
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
          {/* Avatar */}
          <div className="relative shrink-0">
            <div className="w-20 h-20 md:w-24 md:h-24 bg-[var(--color-bg-muted)] rounded-xl flex items-center justify-center">
              {user?.profile_img ? (
                <Image
                  src={user.profile_img}
                  alt={user.name || '프로필'}
                  width={96}
                  height={96}
                  className="w-full h-full rounded-xl object-cover"
                />
              ) : (
                <span className="text-3xl md:text-4xl text-[var(--gradient-1)] font-bold">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 text-center sm:text-left w-full">
            {isEditing ? (
              <div className="space-y-4">
                <div>
                  <label htmlFor="profileName" className="block text-sm text-[var(--color-text-secondary)] mb-2">이름</label>
                  <input
                    id="profileName"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-3 glass-input text-[var(--color-text)]"
                  />
                </div>
                <div className="flex gap-2 justify-center sm:justify-start">
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 btn-primary rounded-lg disabled:opacity-50 flex items-center gap-2"
                  >
                    {saving && (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    )}
                    {saving ? '저장 중...' : '저장'}
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false)
                      setName(user?.name || '')
                    }}
                    className="px-4 py-2 glass-card text-[var(--color-text)] rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
                  >
                    취소
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-center sm:justify-start gap-3 mb-1">
                  <h2 className="text-xl md:text-2xl font-semibold text-[var(--color-text)]">{user?.name}</h2>
                  {user?.is_admin && (
                    <span className="px-2 py-0.5 bg-[var(--gradient-1)]/10 text-[var(--gradient-1)] text-xs font-medium rounded-full border border-[var(--gradient-1)]/20">
                      Admin
                    </span>
                  )}
                </div>
                <p className="text-[var(--color-text-secondary)] mb-4 text-sm md:text-base">{user?.email}</p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 glass-card text-[var(--color-text)] text-sm rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
                >
                  프로필 수정
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Company Info */}
      <div className="glass-card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--color-text)]">회사 정보</h3>
          {!isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--gradient-1)] transition-colors"
            >
              수정
            </button>
          )}
        </div>
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label htmlFor="profileCompanyName" className="block text-sm text-[var(--color-text-secondary)] mb-2">회사명</label>
              <input
                id="profileCompanyName"
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full px-4 py-3 glass-input text-[var(--color-text)]"
              />
            </div>
            <div>
              <label htmlFor="profileDepartment" className="block text-sm text-[var(--color-text-secondary)] mb-2">부서</label>
              <input
                id="profileDepartment"
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full px-4 py-3 glass-input text-[var(--color-text)]"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 btn-primary rounded-lg disabled:opacity-50 flex items-center gap-2"
              >
                {saving && (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                )}
                {saving ? '저장 중...' : '저장'}
              </button>
              <button
                onClick={() => {
                  setIsEditing(false)
                  setName(user?.name || '')
                  setCompanyName(user?.companyName || '')
                  setDepartment(user?.department || '')
                }}
                className="px-4 py-2 glass-card text-[var(--color-text)] rounded-lg hover:bg-[var(--color-bg-muted)] transition-colors"
              >
                취소
              </button>
            </div>
          </div>
        ) : (
          <dl className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:justify-between py-3 border-b border-[var(--color-border)] gap-1">
              <dt className="text-[var(--color-text-secondary)] text-sm sm:text-base">회사명</dt>
              <dd className="text-[var(--color-text)] text-sm sm:text-base">{user?.companyName || '-'}</dd>
            </div>
            <div className="flex flex-col sm:flex-row sm:justify-between py-3 gap-1">
              <dt className="text-[var(--color-text-secondary)] text-sm sm:text-base">부서</dt>
              <dd className="text-[var(--color-text)] text-sm sm:text-base">{user?.department || '-'}</dd>
            </div>
          </dl>
        )}
      </div>

      {/* Account Info */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-lg font-semibold text-[var(--color-text)] mb-4">계정 정보</h3>
        <dl className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:justify-between py-3 border-b border-[var(--color-border)] gap-1">
            <dt className="text-[var(--color-text-secondary)] text-sm sm:text-base">이메일</dt>
            <dd className="text-[var(--color-text)] text-sm sm:text-base break-all">{user?.email}</dd>
          </div>
          <div className="flex flex-col sm:flex-row sm:justify-between py-3 border-b border-[var(--color-border)] gap-1">
            <dt className="text-[var(--color-text-secondary)] text-sm sm:text-base">가입일</dt>
            <dd className="text-[var(--color-text)] text-sm sm:text-base">{user?.createdAt || '-'}</dd>
          </div>
          <div className="flex flex-col sm:flex-row sm:justify-between py-3 gap-1">
            <dt className="text-[var(--color-text-secondary)] text-sm sm:text-base">계정 유형</dt>
            <dd className="text-[var(--color-text)] text-sm sm:text-base">{user?.is_admin ? '관리자' : '일반 사용자'}</dd>
          </div>
        </dl>
      </div>

      {/* Danger Zone */}
      <div className="glass-card border-[var(--color-danger-border)] p-6">
        <h3 className="text-lg font-semibold text-[var(--color-danger-text)] mb-4">위험 구역</h3>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <p className="text-[var(--color-text)] font-medium">로그아웃</p>
            <p className="text-sm text-[var(--color-text-secondary)]">현재 기기에서 로그아웃합니다</p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-[var(--color-danger-bg)] text-[var(--color-danger-text)] rounded-lg border border-[var(--color-danger-border)] hover:bg-[var(--color-danger-bg)] transition-colors w-full sm:w-auto"
          >
            로그아웃
          </button>
        </div>
      </div>
    </div>
  )
}
