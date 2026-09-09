import type { Video, ScenarioVersion } from '@/types'

export function ScenarioReview({
  video,
  scenarioVersions,
  selectedVersionId,
  setSelectedVersionId,
  loadingVersions,
  sceneScenarioFeedbacks,
  setSceneScenarioFeedbacks,
  submitting,
  handleApproveScenario,
  handleReviseScenarioWithScenes,
}: {
  video: Video
  scenarioVersions: ScenarioVersion[]
  selectedVersionId: number | null
  setSelectedVersionId: (id: number) => void
  loadingVersions: boolean
  sceneScenarioFeedbacks: Record<number, string>
  setSceneScenarioFeedbacks: (v: Record<number, string> | ((prev: Record<number, string>) => Record<number, string>)) => void
  submitting: boolean
  handleApproveScenario: () => void
  handleReviseScenarioWithScenes: () => void
}) {
  return (
    <div className="glass-card p-6 mb-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-[var(--color-text)]">시나리오 / 영상 통합 검수</h2>
        <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-full border border-blue-500/20">
          검수 필요
        </span>
      </div>

      {/* Video Player */}
      <div className="mb-6">
        <p className="text-sm text-[var(--color-text-secondary)] mb-3">미리보기 영상</p>
        {video.videoUrl ? (
          <div className="aspect-video bg-[var(--color-bg)] rounded-xl overflow-hidden">
            <video
              src={video.videoUrl}
              controls
              className="w-full h-full object-contain"
              poster="https://placehold.co/1280x720/1a1a1a/666666?text=Loading..."
            >
              브라우저가 비디오 태그를 지원하지 않습니다.
            </video>
          </div>
        ) : (
          <div className="aspect-video bg-[var(--color-bg)] rounded-xl flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 bg-[var(--color-bg-muted)] rounded-full flex items-center justify-center mx-auto mb-3">
                <svg className="w-8 h-8 text-[var(--color-text-tertiary)]" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <p className="text-[var(--color-text-tertiary)] text-sm">영상 준비 중...</p>
            </div>
          </div>
        )}
      </div>

      {/* Scenario Version History */}
      {scenarioVersions.length > 0 && (
        <div className="mb-6 bg-[var(--color-bg)] rounded-xl p-5 border border-[var(--color-border)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-[var(--gradient-1)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-sm font-semibold text-[var(--color-text)]">시나리오 버전 히스토리</h3>
            </div>
            <span className="text-xs text-[var(--color-text-tertiary)]">
              총 {scenarioVersions.length}개 버전
            </span>
          </div>

          {loadingVersions ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-[var(--gradient-1)] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-3">
              {scenarioVersions.map((version, index) => {
                const isLatest = index === 0
                const isSelected = selectedVersionId === version.script_id
                const isCurrentVideo = video.scriptId != null
                  ? version.script_id === video.scriptId
                  : index === 0

                return (
                  <div
                    key={version.script_id}
                    className={`relative p-4 rounded-lg border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[var(--gradient-1)]/10 border-[var(--gradient-1)]/30'
                        : 'bg-[var(--color-bg-muted)] border-[var(--color-border)] hover:border-[var(--gradient-1)]/20'
                    }`}
                    onClick={() => setSelectedVersionId(version.script_id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-[var(--color-text)]">
                            버전 {scenarioVersions.length - index}
                          </span>
                          {isLatest && (
                            <span className="px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded border border-green-500/20">
                              최신
                            </span>
                          )}
                          {isCurrentVideo && (
                            <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded border border-blue-500/20">
                              현재 영상
                            </span>
                          )}
                          {version.approval_status === 'approved' && (
                            <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded border border-purple-500/20">
                              승인됨
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-4 text-xs text-[var(--color-text-secondary)]">
                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {new Date(version.created_at).toLocaleString('ko-KR', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>

                          <span className="flex items-center gap-1">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                            {version.scenes?.length || 0}개 씬
                          </span>

                          {version.generation_type && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                              </svg>
                              {version.generation_type === 'initial' ? '최초 생성' :
                               version.generation_type === 'regenerated' ? '재생성' :
                               version.generation_type === 'revised' ? '수정됨' : version.generation_type}
                            </span>
                          )}
                        </div>

                        {version.revision_notes && (
                          <div className="mt-2 p-2 bg-[var(--color-bg)]/50 rounded text-xs text-[var(--color-text-secondary)] border-l-2 border-yellow-500/30">
                            <span className="text-yellow-400 font-medium">수정 요청: </span>
                            {version.revision_notes}
                          </div>
                        )}
                      </div>

                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                        isSelected
                          ? 'border-[var(--gradient-1)] bg-[var(--gradient-1)]'
                          : 'border-[var(--color-border-strong)]'
                      }`}>
                        {isSelected && (
                          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Scene-by-Scene Scenario - 2x2 Grid */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-medium text-[var(--color-text)]">
            {selectedVersionId && scenarioVersions.find(v => v.script_id === selectedVersionId)
              ? `버전 ${scenarioVersions.length - scenarioVersions.findIndex(v => v.script_id === selectedVersionId)} 씬별 내용`
              : '씬별 검수'}
          </p>
          <span className="text-xs text-[var(--color-text-tertiary)]">수정이 필요한 씬에만 피드백을 입력하세요</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {(() => {
            // 선택된 버전의 씬 데이터 가져오기
            const selectedVersion = scenarioVersions.find(v => v.script_id === selectedVersionId)
            const scenesToDisplay = [...(selectedVersion?.scenes || video.scenes || [])].sort(
              (a, b) => a.scene_number - b.scene_number
            )

            return scenesToDisplay.length > 0 ? (
              scenesToDisplay.map((scene) => {
                const sceneColors = [
                  { bg: 'from-blue-500/10 to-blue-600/5', border: 'border-blue-500/20', accent: 'text-blue-400', ring: 'focus:ring-blue-500/30' },
                  { bg: 'from-purple-500/10 to-purple-600/5', border: 'border-purple-500/20', accent: 'text-purple-400', ring: 'focus:ring-purple-500/30' },
                  { bg: 'from-pink-500/10 to-pink-600/5', border: 'border-pink-500/20', accent: 'text-pink-400', ring: 'focus:ring-pink-500/30' },
                  { bg: 'from-orange-500/10 to-orange-600/5', border: 'border-orange-500/20', accent: 'text-orange-400', ring: 'focus:ring-orange-500/30' },
                ]
                const color = sceneColors[(scene.scene_number - 1) % 4]
                return (
                  <div
                    key={scene.scene_number}
                    className={`relative bg-gradient-to-br ${color.bg} rounded-2xl p-5 border ${color.border} transition-all hover:scale-[1.01]`}
                  >
                    {/* Scene Header */}
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-8 h-8 rounded-lg bg-[var(--color-bg)] flex items-center justify-center text-sm font-bold ${color.accent}`}>
                        {scene.scene_number}
                      </div>
                      <div className="flex-1">
                        <span className="text-sm font-medium text-[var(--color-text)]">Scene {scene.scene_number}</span>
                        {scene.timestamp && (
                          <span className="text-xs text-[var(--color-text-tertiary)] ml-2">{scene.timestamp}</span>
                        )}
                      </div>
                    </div>

                    {/* Scene Content */}
                    <div className="bg-[var(--color-bg)]/50 rounded-xl p-3 mb-4 max-h-24 overflow-y-auto">
                      <pre className="text-[var(--color-text-secondary)] text-xs whitespace-pre-wrap font-body leading-relaxed">
                        {scene.content}
                      </pre>
                    </div>

                    {/* Feedback Input - 최신 버전에만 표시 */}
                    {selectedVersionId === scenarioVersions[0]?.script_id && (
                      <div>
                        <div className="flex items-center gap-2 mb-1.5">
                          <svg className="w-3.5 h-3.5 text-[var(--color-text-tertiary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          <label className="text-xs text-[var(--color-text-tertiary)]">수정 요청</label>
                        </div>
                        <textarea
                          value={sceneScenarioFeedbacks[scene.scene_number] || ''}
                          onChange={(e) => setSceneScenarioFeedbacks(prev => ({ ...prev, [scene.scene_number]: e.target.value }))}
                          placeholder="대사, 내용 수정 요청..."
                          className={`w-full h-14 px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-xs text-[var(--color-text)] placeholder-[var(--color-text-tertiary)] resize-none focus:outline-none focus:ring-2 ${color.ring} focus:border-transparent transition-all`}
                        />
                      </div>
                    )}
                  </div>
                )
              })
            ) : (
              <div className="col-span-2 bg-[var(--color-bg)] rounded-xl p-8 text-center">
                <p className="text-[var(--color-text-tertiary)] text-sm">시나리오가 없습니다.</p>
              </div>
            )
          })()}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleReviseScenarioWithScenes}
          disabled={submitting || Object.values(sceneScenarioFeedbacks).every(f => !f.trim())}
          className="flex-1 py-3.5 glass-card text-[var(--color-text)] rounded-xl hover:bg-[var(--color-bg-muted)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          {submitting ? '처리 중...' : '수정 요청'}
        </button>
        <button
          onClick={handleApproveScenario}
          disabled={submitting}
          className="flex-1 py-3.5 btn-primary rounded-xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          {submitting ? '처리 중...' : '최종 승인'}
        </button>
      </div>
    </div>
  )
}
