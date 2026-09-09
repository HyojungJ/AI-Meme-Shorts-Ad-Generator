import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '대시보드 - Admeme',
  description: '영상 제작 현황과 성과를 한눈에 확인하세요',
}

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return children
}
