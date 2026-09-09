import { Metadata } from 'next'
import { AuthProvider } from '@/hooks/useAuth'
import { ThemeProvider } from '@/hooks/useTheme'
import { ToastProvider } from '@/components/ui/Toast'
import { AdminLayoutContent } from './AdminLayoutContent'

export const metadata: Metadata = {
  title: '관리자 - Admeme',
  description: '시스템 모니터링 및 관리',
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <AdminLayoutContent>{children}</AdminLayoutContent>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
