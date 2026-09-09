'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navItems = [
  {
    href: '/main',
    label: 'Dashboard',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
      </svg>
    ),
    color: 'var(--gradient-3)',
  },
  {
    href: '/user/request',
    label: 'Video Generation',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
      </svg>
    ),
    color: 'var(--gradient-1)',
  },
  {
    href: '/user',
    label: 'My Videos',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    color: 'var(--gradient-4)',
  },
]

interface SidebarProps {
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('sidebar-collapsed')
    if (saved !== null) setCollapsed(JSON.parse(saved))
  }, [])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && mobileOpen && onMobileClose) {
        onMobileClose()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [mobileOpen, onMobileClose])

  const toggle = () => {
    const next = !collapsed
    setCollapsed(next)
    localStorage.setItem('sidebar-collapsed', JSON.stringify(next))
  }

  const handleNavClick = () => {
    if (onMobileClose) onMobileClose()
  }

  const sidebarContent = (
    <aside className={`${collapsed ? 'w-[80px]' : 'w-72'} glass-card rounded-none border-l-0 border-t-0 border-b-0 min-h-screen p-4 font-body flex flex-col transition-all duration-300`}>
      {/* Logo + Toggle */}
      <div className={`flex items-center ${collapsed ? 'justify-center mb-4' : 'justify-between mb-10'}`}>
        <div className="flex items-center gap-3">
          <div
            className="w-11 h-11 rounded-2xl flex items-center justify-center transition-all shadow-lg"
            style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
          >
            <span className="text-white font-display font-bold text-lg">A</span>
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <span className="font-display font-bold text-[var(--color-text)] text-lg tracking-tight whitespace-nowrap">
                Admeme
              </span>
              <p className="text-[var(--color-text-tertiary)] text-xs">AI Video Platform</p>
            </div>
          )}
        </div>
        {!collapsed && (
          <button
            onClick={toggle}
            className="p-2 rounded-xl text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-all"
            aria-label="사이드바 접기"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
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
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7" />
          </svg>
        </button>
      )}

      {/* Navigation */}
      <nav className="space-y-2 flex-1" aria-label="메인 네비게이션">
        {!collapsed && <p className="text-[var(--color-text-tertiary)] text-xs uppercase tracking-widest mb-4 px-4 font-display">Menu</p>}
        {navItems.map((item) => {
          // /user는 정확히 일치하거나 /user/video/ 하위경로일 때, 나머지는 startsWith로 체크
          const isActive = item.href === '/user'
            ? pathname === '/user' || pathname.startsWith('/user/video/')
            : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={handleNavClick}
              aria-label={collapsed ? item.label : undefined}
              aria-current={isActive ? 'page' : undefined}
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
                  aria-hidden="true"
                />
              )}
            </Link>
          )
        })}
      </nav>

    </aside>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <div className="hidden md:block relative z-20">
        {sidebarContent}
      </div>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onMobileClose}
          />
          <div className="absolute left-0 top-0 h-full w-80 glass-card rounded-none p-5 font-body flex flex-col animate-slide-in-right">
            {/* Mobile header */}
            <div className="flex items-center justify-between mb-10">
              <div className="flex items-center gap-3">
                <div
                  className="w-11 h-11 rounded-2xl flex items-center justify-center transition-all shadow-lg"
                  style={{ background: 'linear-gradient(135deg, var(--gradient-1) 0%, var(--gradient-4) 100%)' }}
                >
                  <span className="text-white font-display font-bold text-lg">A</span>
                </div>
                <div className="overflow-hidden">
                  <span className="font-display font-bold text-[var(--color-text)] text-lg tracking-tight whitespace-nowrap">
                    Admeme
                  </span>
                  <p className="text-[var(--color-text-tertiary)] text-xs">AI Video Platform</p>
                </div>
              </div>
              <button
                onClick={onMobileClose}
                className="p-2 rounded-xl text-[var(--color-text-tertiary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-muted)] transition-all"
                aria-label="메뉴 닫기"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Mobile nav */}
            <nav className="space-y-2 flex-1" aria-label="메인 네비게이션">
              <p className="text-[var(--color-text-tertiary)] text-xs uppercase tracking-widest mb-4 px-4 font-display">Menu</p>
              {navItems.map((item) => {
                // /user는 정확히 일치하거나 /user/video/ 하위경로일 때, 나머지는 startsWith로 체크
                const isActive = item.href === '/user'
                  ? pathname === '/user' || pathname.startsWith('/user/video/')
                  : pathname.startsWith(item.href)
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={handleNavClick}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-200 group ${
                      isActive
                        ? 'glass-card'
                        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-bg-muted)]'
                    }`}
                    style={isActive ? { borderColor: `${item.color}40` } : undefined}
                  >
                    <span
                      className="transition-transform group-hover:scale-110 shrink-0"
                      style={{ color: isActive ? item.color : undefined }}
                    >
                      {item.icon}
                    </span>
                    <span
                      className="font-medium"
                      style={{ color: isActive ? item.color : undefined }}
                    >
                      {item.label}
                    </span>
                    {isActive && (
                      <div
                        className="ml-auto w-2 h-2 rounded-full"
                        style={{ background: item.color }}
                        aria-hidden="true"
                      />
                    )}
                  </Link>
                )
              })}
            </nav>

          </div>
        </div>
      )}
    </>
  )
}
