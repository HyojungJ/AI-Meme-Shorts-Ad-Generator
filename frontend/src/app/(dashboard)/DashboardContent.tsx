'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Sidebar } from '@/components/layout/Sidebar'
import { Header } from '@/components/layout/Header'
import { GradientMesh } from '@/components/ui/GradientMesh'

const DASHBOARD_BLOB_OPACITIES = [1, 1, 0.4]

export function DashboardContent({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    if (!loading && !user) {
      router.replace('/login')
    }
  }, [user, loading, router])

  if (loading) {
    return (
      <div className="min-h-screen relative flex items-center justify-center">
        <GradientMesh blobOpacities={DASHBOARD_BLOB_OPACITIES} noise={false} />
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
      <GradientMesh blobOpacities={DASHBOARD_BLOB_OPACITIES} noise={false} />
      <div className="noise-overlay" />
      <Sidebar
        mobileOpen={mobileMenuOpen}
        onMobileClose={() => setMobileMenuOpen(false)}
      />
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        <Header onMenuClick={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 md:p-8 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
