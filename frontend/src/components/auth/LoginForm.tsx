'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { GradientMesh } from '@/components/ui/GradientMesh'

export function LoginForm() {
  const router = useRouter()
  const { loginWithEmail, register } = useAuth()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [department, setDepartment] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let user
      if (mode === 'login') {
        user = await loginWithEmail(email, password)
      } else {
        if (!name.trim() || name.trim().length < 2) {
          setError('이름은 2자 이상 입력하세요')
          setLoading(false)
          return
        }
        if (!companyName.trim() || companyName.trim().length < 2) {
          setError('회사명은 2자 이상 입력하세요')
          setLoading(false)
          return
        }
        if (!department.trim() || department.trim().length < 2) {
          setError('부서명은 2자 이상 입력하세요')
          setLoading(false)
          return
        }
        user = await register(email, password, name, companyName, department)
      }
      router.push(user.is_admin ? '/admin' : '/main')
    } catch (e) {
      setError(e instanceof Error ? e.message : '오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative flex font-body overflow-hidden">
      <GradientMesh />

      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center px-16 xl:px-24 relative z-10">
        <div className="animate-fade-up">
          <span className="badge badge-gradient mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--gradient-1)] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[var(--gradient-1)]"></span>
            </span>
            AI-Powered Platform
          </span>
        </div>

        <h1 className="heading-hero animate-fade-up-1">
          Make Your
          <br />
          <span className="text-gradient">Product</span>
          <br />
          Go Viral
        </h1>

        <p className="mt-8 body-lg max-w-md animate-fade-up-2">
          AI가 시나리오부터 영상까지.
          <br />
          밈 광고 영상을 자동으로 생성합니다.
        </p>

        <div className="flex flex-wrap gap-3 mt-12 animate-fade-up-3">
          {[
            { label: 'AI 시나리오', color: 'var(--gradient-1)' },
            { label: '자동 영상 생성', color: 'var(--gradient-4)' },
            { label: '밈 트렌드 분석', color: 'var(--gradient-3)' },
          ].map((tag) => (
            <span
              key={tag.label}
              className="px-4 py-2 glass-card text-sm rounded-full font-display"
              style={{ color: tag.color, borderColor: `${tag.color}30` }}
            >
              {tag.label}
            </span>
          ))}
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-10">
        <div className="w-full max-w-md relative animate-fade-up">
          <div className="lg:hidden text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-3">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg"
                style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
              >
                <span className="text-white font-display font-bold text-xl">A</span>
              </div>
            </div>
            <h1 className="font-display text-3xl font-bold text-[var(--color-text)]">
              Admeme
            </h1>
            <p className="text-[var(--color-text-secondary)] text-sm mt-1">밈 영상 자동 생성 플랫폼</p>
          </div>

          <div className="glass-card gradient-border p-8 animate-scale-in">
            <div className="text-center mb-8">
              <h2 className="text-xl font-display font-bold text-[var(--color-text)] mb-2">
                {mode === 'login' ? '로그인' : '회원가입'}
              </h2>
              <p className="text-[var(--color-text-secondary)] text-sm">
                {mode === 'login' ? '계정에 로그인하세요' : '새 계정을 만드세요'}
              </p>
            </div>

            <form onSubmit={handleEmailSubmit} className="space-y-4 mb-6">
              {mode === 'register' && (
                <div>
                  <label htmlFor="name" className="block text-sm text-[var(--color-text-secondary)] mb-2 font-display">이름</label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="이름을 입력하세요"
                    className="w-full px-4 py-3 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] text-sm"
                    disabled={loading}
                  />
                </div>
              )}
              <div>
                <label htmlFor="email" className="block text-sm text-[var(--color-text-secondary)] mb-2 font-display">이메일</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@example.com"
                  className="w-full px-4 py-3 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] text-sm"
                  required
                  disabled={loading}
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm text-[var(--color-text-secondary)] mb-2 font-display">비밀번호</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] text-sm"
                  required
                  disabled={loading}
                  minLength={8}
                />
                {mode === 'register' && (
                  <p className="mt-1 text-xs text-[var(--color-text-tertiary)]">최소 8자 이상</p>
                )}
              </div>
              {mode === 'register' && (
                <>
                  <div>
                    <label htmlFor="companyName" className="block text-sm text-[var(--color-text-secondary)] mb-2 font-display">회사명</label>
                    <input
                      id="companyName"
                      type="text"
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      placeholder="회사명을 입력하세요"
                      className="w-full px-4 py-3 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] text-sm"
                      disabled={loading}
                    />
                  </div>
                  <div>
                    <label htmlFor="department" className="block text-sm text-[var(--color-text-secondary)] mb-2 font-display">부서</label>
                    <input
                      id="department"
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      placeholder="부서를 입력하세요"
                      className="w-full px-4 py-3 glass-input text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] text-sm"
                      disabled={loading}
                    />
                  </div>
                </>
              )}
              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3.5 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    처리 중...
                  </span>
                ) : mode === 'login' ? '로그인' : '회원가입'}
              </button>
            </form>

            <p className="text-center text-sm text-[var(--color-text-secondary)]">
              {mode === 'login' ? (
                <>
                  계정이 없으신가요?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('register'); setError('') }}
                    className="text-gradient font-medium hover:underline"
                  >
                    회원가입
                  </button>
                </>
              ) : (
                <>
                  이미 계정이 있으신가요?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('login'); setError('') }}
                    className="text-gradient font-medium hover:underline"
                  >
                    로그인
                  </button>
                </>
              )}
            </p>

            {error && (
              <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <p className="text-sm text-red-400 text-center">{error}</p>
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-[var(--color-border)]">
              <p className="text-xs text-[var(--color-text-tertiary)] text-center leading-relaxed">
                로그인 시{' '}
                <Link href="/terms" className="text-[var(--color-text-secondary)] hover:text-[var(--gradient-1)] transition-colors">
                  서비스 이용약관
                </Link>
                {' '}및{' '}
                <Link href="/privacy" className="text-[var(--color-text-secondary)] hover:text-[var(--gradient-1)] transition-colors">
                  개인정보 처리방침
                </Link>
                에 동의하는 것으로 간주됩니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
