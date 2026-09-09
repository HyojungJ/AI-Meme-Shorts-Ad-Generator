import Image from 'next/image'
import type { Video } from '@/types'

export function AssetReview({
  video,
  showCharacterRevision,
  setShowCharacterRevision,
  showVoiceRevision,
  setShowVoiceRevision,
  characterFeedback,
  setCharacterFeedback,
  voiceFeedback,
  setVoiceFeedback,
  submitting,
  isPlaying,
  handleReviseCharacter,
  handleReviseVoice,
  handleApproveAssets,
  toggleVoicePlay,
}: {
  video: Video
  showCharacterRevision: boolean
  setShowCharacterRevision: (v: boolean) => void
  showVoiceRevision: boolean
  setShowVoiceRevision: (v: boolean) => void
  characterFeedback: string
  setCharacterFeedback: (v: string) => void
  voiceFeedback: string
  setVoiceFeedback: (v: string) => void
  submitting: boolean
  isPlaying: boolean
  handleReviseCharacter: () => void
  handleReviseVoice: () => void
  handleApproveAssets: () => void
  toggleVoicePlay: () => void
}) {
  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">캐릭터 & 음성 검수</h2>
        <span className="px-3 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-full border border-purple-500/20">
          검수 필요
        </span>
      </div>

      {/* 캐릭터 이미지 비교 */}
      <div className="bg-[var(--color-bg)] rounded-xl p-5 mb-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium text-[var(--color-text)]">캐릭터 이미지</p>
          {!showCharacterRevision && (
            <button
              onClick={() => setShowCharacterRevision(true)}
              className="text-xs text-[var(--color-text-tertiary)] hover:text-[var(--gradient-1)] transition-colors"
            >
              수정
            </button>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {/* 좌: 요청 스타일 */}
          <div className="flex flex-col">
            <span className="text-xs text-purple-400 font-medium mb-2 uppercase tracking-wider">요청</span>
            <div className="flex-1 p-4 bg-purple-500/5 border border-purple-500/15 rounded-xl">
              <p className="text-sm text-[var(--color-text)] leading-relaxed">{video.characterImagePrompt}</p>
              {video.characterRevisionHistory && video.characterRevisionHistory.filter(h => h.feedback_type === 'image_revision').length > 0 && (
                <div className="mt-3 pt-3 border-t border-purple-500/10">
                  <p className="text-xs text-[var(--color-text-tertiary)] mb-1.5">수정 이력</p>
                  {video.characterRevisionHistory.filter(h => h.feedback_type === 'image_revision').map((h, i) => (
                    <p key={i} className="text-xs text-[var(--color-text-secondary)] mt-1">
                      <span className="text-[var(--color-text-tertiary)]">{new Date(h.requested_at).toLocaleDateString('ko-KR')}</span>{' '}
                      {h.revision_notes}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 우: 생성 결과 */}
          <div className="flex flex-col">
            <span className="text-xs text-purple-400 font-medium mb-2 uppercase tracking-wider">결과</span>
            {video.characterImageUrl ? (
              <div className="relative flex-1 min-h-[200px] rounded-xl overflow-hidden bg-[var(--color-bg-muted)] flex items-center justify-center">
                <Image
                  src={video.characterImageUrl}
                  alt="생성된 캐릭터"
                  fill
                  unoptimized
                  className="object-contain"
                />
              </div>
            ) : (
              <div className="flex-1 min-h-[200px] rounded-xl bg-[var(--color-bg-muted)] flex items-center justify-center">
                <p className="text-[var(--color-text-tertiary)] text-sm">생성 중...</p>
              </div>
            )}
          </div>
        </div>

        {/* 캐릭터 수정 요청 폼 */}
        {showCharacterRevision && (
          <div className="mt-4 p-4 bg-purple-500/5 rounded-xl border border-purple-500/20">
            <p className="text-sm font-medium text-purple-400 mb-3">캐릭터 수정</p>
            <textarea
              value={characterFeedback}
              onChange={(e) => setCharacterFeedback(e.target.value)}
              maxLength={1000}
              placeholder="원하는 수정 방향을 자세히 설명해주세요. (예: 머리카락을 더 짧게, 표정을 더 밝게...)"
              className="w-full h-24 px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] resize-none focus:outline-none focus:border-purple-500/50"
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleReviseCharacter}
                disabled={submitting || !characterFeedback.trim()}
                className="flex-1 py-2 bg-purple-500 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? '요청 중...' : '수정'}
              </button>
              <button
                onClick={() => { setShowCharacterRevision(false); setCharacterFeedback(''); }}
                className="px-4 py-2 text-[var(--color-text-secondary)] text-sm hover:text-[var(--color-text)]"
              >
                취소
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 음성 샘플 비교 */}
      <div className="bg-[var(--color-bg)] rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium text-[var(--color-text)]">음성 샘플</p>
          {!showVoiceRevision && (
            <button
              onClick={() => setShowVoiceRevision(true)}
              className="text-xs text-[var(--color-text-tertiary)] hover:text-[var(--gradient-1)] transition-colors"
            >
              수정
            </button>
          )}
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {/* 좌: 요청 스타일 */}
          <div className="flex flex-col">
            <span className="text-xs text-pink-400 font-medium mb-2 uppercase tracking-wider">요청</span>
            <div className="flex-1 p-4 bg-pink-500/5 border border-pink-500/15 rounded-xl">
              <p className="text-sm text-[var(--color-text)] leading-relaxed">{video.characterVoicePrompt}</p>
              {video.characterRevisionHistory && video.characterRevisionHistory.filter(h => h.feedback_type === 'voice_revision').length > 0 && (
                <div className="mt-3 pt-3 border-t border-pink-500/10">
                  <p className="text-xs text-[var(--color-text-tertiary)] mb-1.5">수정 이력</p>
                  {video.characterRevisionHistory.filter(h => h.feedback_type === 'voice_revision').map((h, i) => (
                    <p key={i} className="text-xs text-[var(--color-text-secondary)] mt-1">
                      <span className="text-[var(--color-text-tertiary)]">{new Date(h.requested_at).toLocaleDateString('ko-KR')}</span>{' '}
                      {h.revision_notes}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 우: 생성 결과 */}
          <div className="flex flex-col">
            <span className="text-xs text-pink-400 font-medium mb-2 uppercase tracking-wider">결과</span>
            <div className="flex-1 min-h-[200px] rounded-xl bg-[var(--color-bg-muted)] flex flex-col items-center justify-center">
              {video.voiceSampleUrl ? (
                <>
                  <button
                    onClick={toggleVoicePlay}
                    className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                      isPlaying
                        ? 'bg-pink-500 text-white'
                        : 'bg-[var(--color-bg)] text-pink-400 hover:bg-pink-500/20 border border-pink-500/30'
                    }`}
                  >
                    {isPlaying ? (
                      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                      </svg>
                    ) : (
                      <svg className="w-8 h-8 ml-1" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    )}
                  </button>
                  <p className="text-[var(--color-text-secondary)] text-sm mt-4">
                    {isPlaying ? '재생 중...' : '클릭하여 재생'}
                  </p>
                </>
              ) : (
                <p className="text-[var(--color-text-tertiary)] text-sm">생성 중...</p>
              )}
            </div>
          </div>
        </div>

        {/* 음성 수정 요청 폼 */}
        {showVoiceRevision && (
          <div className="mt-4 p-4 bg-pink-500/5 rounded-xl border border-pink-500/20">
            <p className="text-sm font-medium text-pink-400 mb-3">음성 수정</p>
            <textarea
              value={voiceFeedback}
              onChange={(e) => setVoiceFeedback(e.target.value)}
              maxLength={1000}
              placeholder="원하는 수정 방향을 자세히 설명해주세요. (예: 톤을 더 밝게, 말하는 속도를 더 느리게...)"
              className="w-full h-24 px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] resize-none focus:outline-none focus:border-pink-500/50"
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={handleReviseVoice}
                disabled={submitting || !voiceFeedback.trim()}
                className="flex-1 py-2 bg-pink-500 text-white text-sm rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? '요청 중...' : '수정'}
              </button>
              <button
                onClick={() => { setShowVoiceRevision(false); setVoiceFeedback(''); }}
                className="px-4 py-2 text-[var(--color-text-secondary)] text-sm hover:text-[var(--color-text)]"
              >
                취소
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 안내 및 승인 버튼 */}
      <div className="mt-6 p-4 bg-[var(--color-bg-muted)] rounded-xl">
        <p className="text-sm text-[var(--color-text-secondary)]">
          위 캐릭터와 음성으로 영상이 제작됩니다. 모두 확인 후 승인해주세요.
          수정이 필요한 항목이 있다면 각 항목의 &quot;수정&quot;을 클릭해주세요.
        </p>
      </div>

      <button
        onClick={handleApproveAssets}
        disabled={submitting || showCharacterRevision || showVoiceRevision}
        className="w-full mt-4 py-3.5 btn-primary rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? '처리 중...' : '모두 승인하고 시나리오 생성 시작'}
      </button>
    </div>
  )
}
