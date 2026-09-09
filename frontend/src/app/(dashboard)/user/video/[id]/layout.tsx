import { Metadata } from 'next'

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params

  return {
    title: `영상 상세 #${id} - Admeme`,
    description: '영상 상세 정보와 시나리오를 확인하세요',
  }
}

export default function VideoDetailLayout({ children }: { children: React.ReactNode }) {
  return children
}
