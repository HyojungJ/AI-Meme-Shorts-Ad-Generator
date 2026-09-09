import Image from 'next/image'
import type { Video } from '@/types'

export function CompletedVideo({
  video,
  isPlaying,
  toggleVoicePlay,
  handleDownload,
  handleShare,
}: {
  video: Video
  isPlaying: boolean
  toggleVoicePlay: () => void
  handleDownload: () => void
  handleShare: () => void
}) {
  return (
    <>
      {/* Approved Items Summary */}
      {(video.characterImageUrl || video.voiceSampleUrl) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {video.characterImageUrl && (
            <div className="glass-card p-4">
              <p className="text-sm text-[var(--color-text-secondary)] mb-3">캐릭터</p>
              <div className="relative aspect-square rounded-lg overflow-hidden bg-[var(--color-bg)]">
                <Image
                  src={video.characterImageUrl}
                  alt="캐릭터"
                  fill
                  unoptimized
                  className="object-contain"
                />
              </div>
            </div>
          )}
          {video.voiceSampleUrl && (
            <div className="glass-card p-4">
              <p className="text-sm text-[var(--color-text-secondary)] mb-3">음성</p>
              <div className="aspect-square rounded-lg bg-[var(--color-bg)] flex items-center justify-center">
                <button
                  onClick={toggleVoicePlay}
                  className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                    isPlaying
                      ? 'bg-pink-500 text-white'
                      : 'bg-[var(--color-bg-muted)] text-pink-400 hover:bg-pink-500/20'
                  }`}
                >
                  {isPlaying ? (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 ml-1" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Video Preview */}
      <div className="glass-card p-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)] mb-4">완성 영상</h2>
        <div className="aspect-video bg-[var(--color-bg)] rounded-xl overflow-hidden mb-4">
          {video.videoUrl ? (
            <video
              src={video.videoUrl}
              controls
              className="w-full h-full object-contain"
              poster="https://placehold.co/1280x720/1a1a1a/666666?text=Loading..."
            >
              브라우저가 비디오 태그를 지원하지 않습니다.
            </video>
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 bg-[var(--color-bg-muted)] rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-[var(--gradient-1)]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
                <p className="text-[var(--color-text-secondary)] text-sm">영상을 불러올 수 없습니다</p>
              </div>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleDownload}
            className="flex-1 py-3 btn-primary rounded-xl flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            다운로드
          </button>
          <button
            onClick={handleShare}
            className="px-6 py-3 glass-card text-[var(--color-text)] rounded-xl hover:bg-[var(--color-bg-muted)] transition-colors"
          >
            공유
          </button>
        </div>
      </div>
    </>
  )
}
