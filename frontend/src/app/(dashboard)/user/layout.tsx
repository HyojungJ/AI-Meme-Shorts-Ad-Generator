import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '내 영상 - Admeme',
  description: '제작 요청한 영상들을 관리하세요',
}

export default function UserLayout({ children }: { children: React.ReactNode }) {
  return children
}
