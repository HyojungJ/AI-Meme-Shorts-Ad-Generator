import { AuthProvider } from '@/hooks/useAuth'
import { ThemeProvider } from '@/hooks/useTheme'
import { ToastProvider } from '@/components/ui/Toast'
import { GenerationProvider } from '@/contexts/GenerationContext'
import { DashboardContent } from './DashboardContent'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <GenerationProvider>
            <DashboardContent>{children}</DashboardContent>
          </GenerationProvider>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
