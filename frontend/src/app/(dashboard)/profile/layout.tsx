import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '프로필 - Admeme',
  description: '계정 정보를 관리하세요',
}

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return children
}
