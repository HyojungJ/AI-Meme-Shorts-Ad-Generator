'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { GradientMesh } from '@/components/ui/GradientMesh'
import type { User } from '@/types'

const navItems = [
  {
    href: '/admin',
    label: '대시보드',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
      </svg>
    ),
    color: 'var(--gradient-1)',
  },
  {
    href: '/admin/analytics',
    label: '성과 분석',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    color: 'var(--gradient-4)',
  },
  {
    href: '/admin/videos',
    label: '영상 관리',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    color: 'var(--gradient-3)',
  },
  {
    href: '/admin/users',
    label: '사용자 관리',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
    color: 'var(--gradient-5)',
  },
]

const ADMIN_BLOB_OPACITIES = [0.4, 0.4, 0.3, 0.3]

function AdminSidebar({ onLogout }: { onLogout: () => void }) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('admin-sidebar-collapsed')
    if (saved !== null) setCollapsed(JSON.parse(saved))
  }, [])

  const toggle = () => {
    const next = !collapsed
    setCollapsed(next)
    localStorage.setItem('admin-sidebar-collapsed', JSON.stringify(next))
  }

  return (
    <aside className={`${collapsed ? 'w-[80px]' : 'w-72'} glass-card rounded-none border-l-0 border-t-0 border-b-0 min-h-screen p-4 font-body flex flex-col transition-all duration-300`}>
      {/* Logo + Toggle */}
      <div className={`flex items-center ${collapsed ? 'justify-center mb-4' : 'justify-between mb-10'}`}>
        <Link href="/admin" className="flex items-center gap-3 group">
          <div
            className="w-11 h-11 rounded-2xl flex items-center justify-center group-hover:scale-105 transition-all shadow-lg"
            style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
          >
            <span className="text-white font-display font-bold text-lg">A</span>
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-[var(--color-text)] text-lg tracking-tight whitespace-nowrap">
                  Admeme
                </span>
                <span className="px-2 py-0.5 text-[10px] font-display font-semibold rounded-full bg-[var(--gradient-1)]/10 text-[var(--gradient-1)] border border-[var(--gradient-1)]/20">
                  Admin
                </span>
              </div>
              <p className="text-[var(--color-text-tertiary)] text-xs">관리자 콘솔</p>
            </div>
          )}
        </Link>
        {!collapsed && (
          <button
            onClick={toggle}
            className="p-2 rounded-xl text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-all"
            aria-label="사이드바 접기"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7" />
            </svg>
          </button>
        )}
      </div>

      {/* Expand button when collapsed */}
      {collapsed && (
        <button
          onClick={toggle}
          className="mb-6 p-2.5 rounded-xl glass-card text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] transition-all flex justify-center"
          aria-label="사이드바 펼치기"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Navigation */}
      <nav className="space-y-2 flex-1">
        {!collapsed && <p className="text-[var(--color-text-tertiary)] text-xs uppercase tracking-widest mb-4 px-4 font-display">관리</p>}
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/admin' && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={collapsed ? item.label : undefined}
              className={`flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'glass-card'
                  : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-muted)]'
              } ${collapsed ? 'justify-center px-0' : ''}`}
              style={isActive ? { borderColor: `${item.color}40` } : undefined}
            >
              <span
                className="transition-transform group-hover:scale-110 shrink-0"
                style={{ color: isActive ? item.color : undefined }}
              >
                {item.icon}
              </span>
              {!collapsed && (
                <span
                  className="font-medium"
                  style={{ color: isActive ? item.color : undefined }}
                >
                  {item.label}
                </span>
              )}
              {!collapsed && isActive && (
                <div
                  className="ml-auto w-2 h-2 rounded-full"
                  style={{ background: item.color }}
                />
              )}
            </Link>
          )
        })}
      </nav>

      {/* Logout */}
      <div className="pt-6 border-t border-[var(--color-border)]">
        <button
          onClick={onLogout}
          aria-label={collapsed ? '로그아웃' : undefined}
          className={`w-full flex items-center gap-3 px-4 py-3 text-[var(--color-text-secondary)] hover:text-[var(--gradient-1)] hover:bg-[var(--gradient-1)]/10 rounded-xl transition-colors ${collapsed ? 'justify-center px-0' : ''}`}
        >
          <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {!collapsed && <span className="font-medium">로그아웃</span>}
        </button>
      </div>
    </aside>
  )
}

function AdminHeader({ user }: { user: User }) {
  return (
    <header className="h-20 glass-card rounded-none border-t-0 border-l-0 border-r-0 flex items-center justify-between px-8 font-body">
      <div>
        <h2 className="text-[var(--color-text)] font-display font-semibold">관리자 콘솔</h2>
        <p className="text-[var(--color-text-tertiary)] text-sm">시스템 모니터링 및 관리</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm font-medium text-[var(--color-text)]">{user.name}</p>
          <p className="text-xs text-[var(--color-text-tertiary)]">{user.email}</p>
        </div>
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
        >
          <span className="text-white font-bold text-sm">
            {user.name?.charAt(0).toUpperCase() || 'A'}
          </span>
        </div>
      </div>
    </header>
  )
}

export function AdminLayoutContent({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.replace('/login')
      return
    }

    const mockMode = process.env.NEXT_PUBLIC_MOCK_MODE === 'true'
    if (mockMode) {
      const mockUser = {
        user_id: 1,
        email: 'admin@admeme.com',
        name: '관리자',
        is_admin: true,
      }
      setUser(mockUser)
      setLoading(false)
      return
    }

    import('@/lib/api').then(({ getCurrentUser }) => {
      getCurrentUser()
        .then((data) => {
          if (!data.is_admin) {
            router.replace('/main')
            return
          }
          setUser(data)
        })
        .catch(() => {
          router.replace('/login')
        })
        .finally(() => setLoading(false))
    })
  }, [router])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen relative flex items-center justify-center">
        <GradientMesh blobOpacities={ADMIN_BLOB_OPACITIES} />
        <div className="flex flex-col items-center gap-4 relative z-10">
          <div className="w-12 h-12 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
          <p className="text-[var(--color-text-secondary)] font-body">로딩 중...</p>
        </div>
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="flex min-h-screen relative">
      <GradientMesh blobOpacities={ADMIN_BLOB_OPACITIES} />
      <AdminSidebar onLogout={handleLogout} />
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        <AdminHeader user={user} />
        <main className="flex-1 p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
