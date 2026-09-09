# 콘텐츠 통합 검수 설계

## 배경

사용자가 시나리오만 봐서는 좋은 영상이 될지 판단할 수 없다.
시나리오+영상을 함께 보여주고, 함께 수정/승인하는 것이 서비스 의도.

프론트엔드는 이미 통합 검수 UI로 구현되어 있으나 (영상 미리보기 + 씬별 카드 + 통합 피드백),
Backend API가 이 의도와 맞지 않는 부분이 있어 수정한다.

## 발견된 이슈

### CRITICAL 1: `scenario/approve`가 즉시 completed 처리
`scenario/approve` 호출 시 `ad.status = completed`, `progress = 100%`로 설정.
영상 검수 없이 완료 처리됨. `video/approve`, `content/approve` 무의미.

### CRITICAL 2: 프론트엔드 수정 요청 시 2번 API 호출
`scenario/revise` + `video/generate` 분리 호출. 중간에 실패하면 불일치 상태.

### HIGH 1: scene_key 네이밍 불일치
- Backend: `{1: "hook", 2: "body_1", 3: "body_2", 4: "close"}`
- AI Pipeline: `{1: "scene_1", 2: "scene_2", 3: "scene_3", 4: "scene_4"}`

### MEDIUM 1: CLAUDE.md 상태명과 Backend 상태명 불일치
CLAUDE.md: `asset_generating`, `content_pending` 등
Backend: `generating_character`, `pending_approval` 등

---

## 설계

### 핵심 원칙
시나리오와 영상은 항상 **함께 생성**, **함께 검수**, **함께 재생성**된다.

### 상태 흐름

```
asset_approved
  |
  v
POST /content/generate       --> content_generating (progress 40~75%)
  |
  v
content_pending (progress 75%)
  |
  +--> POST /content/approve  --> completed (progress 100%)
  |
  +--> POST /content/revise   --> content_generating --> content_pending
```

### API 변경

#### 신규: `POST /{ad_id}/content/generate`

기존 `scenario/generate`의 background 로직 (시나리오+영상 자동 체이닝)을 명시적 통합 엔드포인트로 노출.

```
요청: { meme_id?: int }
응답: { ad_id, status: "content_generating" }

Background:
  1. 시나리오 생성 (run_scenario_step)
  2. TTS 생성 (run_tts_step x 4씬)
  3. 씬 이미지 생성 (선택적)
  4. 영상 생성 + 병합 (run_video_step)
  5. status -> content_pending, progress 75%
```

#### 신규: `POST /{ad_id}/content/revise`

시나리오+영상 통합 재생성. 프론트엔드가 1번만 호출.

```
요청: {
  scene_revisions: [
    { scene_number: 1, scenario_notes: "...", video_notes: "..." }
  ],
  general_notes?: string
}
응답: { ad_id, status: "content_generating" }

Background:
  1. review_result에 피드백 저장
  2. 시나리오 재생성 (run_scenario_regenerate_step)
  3. TTS 재생성 (run_tts_step x 4씬)
  4. 영상 재생성 (run_video_step)
  5. status -> content_pending, progress 75%
```

#### 수정: `POST /{ad_id}/content/approve`

현재 gate 역할만 하던 것을 유일한 콘텐츠 완료 경로로 변경.

```
동작:
  1. scenario.approval_status = 'approved'
  2. video.status = 'client_approved'
  3. ad.status = 'completed', progress = 100%
```

#### 수정: `POST /{ad_id}/scenario/approve`

**버그 수정**: 즉시 completed 처리 제거.

```
변경 전: ad.status = 'completed', progress = 100%
변경 후: scenario.approval_status = 'approved' (ad status 변경 안 함)
```

#### 수정: scene_key 통일

Backend `scenario/revise`의 scene_key_map 변경:

```python
# 변경 전
scene_key_map = {1: "hook", 2: "body_1", 3: "body_2", 4: "close"}

# 변경 후
scene_key_map = {1: "scene_1", 2: "scene_2", 3: "scene_3", 4: "scene_4"}
```

### 기존 엔드포인트 유지

개별 엔드포인트는 디버깅/테스트용으로 유지:
- `scenario/generate` — 시나리오만 생성
- `scenario/approve` — 시나리오만 승인 (단독 completed 안 함)
- `scenario/revise` — 시나리오만 재생성
- `video/generate` — 영상만 생성
- `video/approve` — 영상만 승인 (단독 completed 안 함)

---

## 변경 파일

| 파일 | 작업 |
|------|------|
| `backend/.../content_pipeline.py` | content/generate, content/revise 추가 + scenario/approve 수정 |
| `frontend/.../video/[id]/page.tsx` | approve/revise를 통합 API로 변경 |
| `frontend/.../api/video.ts` | approveContent(), reviseContent() 추가 |
| `AI/CLAUDE.md` | 서비스 플로우 문서 업데이트 |

---

## AI Pipeline 변경

변경 없음. 기존 composite 함수 활용:
- `run_content_generation_step()` — 시나리오+TTS+영상 통합 생성
- `run_content_regenerate_step()` — 피드백 기반 통합 재생성

Backend가 자체 orchestration 패턴을 유지 (중간 DB 저장/상태 업데이트 필요).
