import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '성과 분석 - Admeme Admin',
  description: '밈 영상 성과를 분석합니다',
}

export default function AnalyticsLayout({ children }: { children: React.ReactNode }) {
  return children
}
