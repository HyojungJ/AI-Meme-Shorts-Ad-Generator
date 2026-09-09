# Service Flow Bugfix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all bugs and inconsistencies found during the full service flow simulation (user + admin pages).

**Architecture:** Frontend API 함수의 잘못된 경로/ID를 수정하고, 비동기 BackgroundTasks 호출과 프론트 순차 호출 사이의 타이밍 문제를 해결하며, 관리자 페이지의 인증/라우팅 문제를 수정한다.

**Tech Stack:** Next.js (TypeScript), FastAPI (Python), SQLAlchemy

---

## Issue Summary

| # | Severity | Issue |
|---|----------|-------|
| 6 | HIGH | `handleApproveAssets`: 시나리오 생성(BackgroundTasks) 직후 영상 생성 호출 → 시나리오 미완료 |
| 11 | HIGH | `approveScenario(video.id, 1)`: script_id 하드코딩 + job_id로 ad_id 사용 |
| 13 | HIGH | `downloadVideo(parseInt(video.id))`: ad_id를 video_id로 사용 → 잘못된 영상 다운로드 |
| 14 | HIGH | `handleReview`: productName 정규식으로 ad_id 추출 → 실제 제품명이면 UUID로 폴백 |
| 15 | HIGH | 관리자가 `/user/video/` 이동 → 별도 인증 가드에 걸림 |
| 4 | MED | approve API 두 세트 혼재 (video.py vs content_pipeline.py) |
| 7 | MED | VideoRequestForm productImage 필수 validation 미동작 |
| 3 | MED | 대시보드 → `/user/video/${video.video_id}` 라우팅: video_id vs ad_id |
| 1 | LOW | Admin 로그아웃이 서버에 refresh token 무효화 안 함 |
| 9 | LOW | presigned URL 만료 시 음성 재생 에러 핸들링 없음 |

---

## Task 1: Fix `approveScenario` — hardcoded script_id + wrong API path

**Files:**
- Modify: `frontend/src/lib/api/video.ts:384-391` (approveScenario)
- Modify: `frontend/src/app/(dashboard)/user/video/[id]/page.tsx:322` (handleApproveScenario)
- Modify: `frontend/src/types/index.ts` (Video type에 scriptId 추가)

**Problem:**
- `approveScenario(video.id, 1)` → `script_id=1` 하드코딩
- API path `POST /api/v1/videos/{videoId}/scenarios/{scenarioId}/approve` (scenario.py) 존재하지만, `video.id`는 `ad_id`이고 `job_id`로 사용됨
- Content pipeline에도 `POST /api/v1/video/{ad_id}/scenario/approve` (content_pipeline.py:672) 존재

**Fix:**
content_pipeline.py의 `POST /video/{ad_id}/scenario/approve`를 사용하도록 변경. 이 API는 ad_id 기반이고, scenario를 내부적으로 조회하므로 script_id 불필요.

**Step 1: Modify `approveScenario` API function**

`frontend/src/lib/api/video.ts:384-391` 변경:

```typescript
// Before:
async approveScenario(videoId: string, scenarioId: number) {
  // ...mock...
  return api.post<{ message: string }>(`/api/v1/videos/${videoId}/scenarios/${scenarioId}/approve`, {})
}

// After:
async approveScenario(adId: string) {
  // ...mock...
  return api.post<{ message: string }>(`/api/v1/video/${adId}/scenario/approve`, { approved: true })
}
```

**Step 2: Update caller in video detail page**

`frontend/src/app/(dashboard)/user/video/[id]/page.tsx:322`:

```typescript
// Before:
await scenarioApi.approveScenario(video.id, 1)

// After:
await scenarioApi.approveScenario(video.id)
```

**Step 3: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

Expected: No errors

---

## Task 2: Fix `handleApproveAssets` — BackgroundTasks timing issue

**Files:**
- Modify: `frontend/src/app/(dashboard)/user/video/[id]/page.tsx:220-265` (handleApproveAssets)

**Problem:**
`generateScenario` → BackgroundTasks (즉시 `{status: "generating_scenario"}` 반환) → 바로 `generateVideo` 호출 → 시나리오 미완료라 실패

**Fix:**
에셋 승인 후 시나리오 생성만 트리거하고, 영상 생성은 시나리오 검수 후 별도 플로우에서 처리. 현재 UI는 이미 `scenario_review` 상태에서 영상 생성 버튼이 별도로 있으므로, `handleApproveAssets`에서 영상 생성 호출을 제거.

**Step 1: Simplify handleApproveAssets**

`frontend/src/app/(dashboard)/user/video/[id]/page.tsx`:

```typescript
const handleApproveAssets = async () => {
  if (!video) return
  const characterId = video.characterId
  if (!characterId) {
    showToast('캐릭터 정보를 찾을 수 없습니다', 'error')
    return
  }
  setSubmitting(true)
  let currentStep = ''
  try {
    // 1. 승인 처리
    currentStep = '캐릭터 승인'
    await scenarioApi.approveCharacter(characterId, video.id)
    currentStep = '음성 승인'
    await scenarioApi.approveVoice(characterId, video.id)
    showToast('에셋이 승인되었습니다! 시나리오 생성을 시작합니다.', 'success')

    // 2. 시나리오 생성 (BackgroundTasks → 폴링으로 완료 감지)
    currentStep = '시나리오 생성 요청'
    await scenarioApi.generateScenario(video.id)

    // 3. 생성 중 상태로 전환 → 폴링이 완료를 감지
    setVideo(prev => prev ? { ...prev, status: 'scenario_generating' } : prev)
    showToast('시나리오 생성이 시작되었습니다. 완료되면 알려드리겠습니다.', 'info')
  } catch (error) {
    const msg = error instanceof Error ? error.message : '알 수 없는 오류'
    showToast(`${currentStep} 단계에서 실패했습니다: ${msg}`, 'error')
    await fetchVideo()
  } finally {
    setSubmitting(false)
  }
}
```

**Step 2: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

---

## Task 3: Fix `downloadVideo` — ad_id vs video_id mismatch

**Files:**
- Modify: `frontend/src/app/(dashboard)/user/video/[id]/page.tsx:178-193` (handleDownload)
- Modify: `frontend/src/lib/api/analytics.ts:874-881` (downloadVideo)

**Problem:**
`video.id` = `String(ad_id)` → `parseInt(video.id)` = `ad_id` → download API expects `video_id`

**Fix:**
Download API를 ad_id 기반으로 변경. Backend `final.py`의 download 엔드포인트는 `video_id`를 받지만, frontend에서는 `ad_id`밖에 없으므로 backend에서 ad_id로 video를 조회하는 엔드포인트 추가.

Option A: Backend에 `GET /api/v1/videos/ad/{ad_id}/download` 추가
Option B: Frontend에서 video 상세 조회 시 `video_id`를 저장하고 다운로드 시 사용

Option B가 기존 API를 건드리지 않아서 더 안전.

**Step 1: Add videoId to Video type**

`frontend/src/types/index.ts`:
```typescript
// Video type에 videoId 추가 (DB의 video.video_id)
videoId?: number
```

**Step 2: Map videoId from API response**

`frontend/src/lib/api/video.ts:186` (getProjectById):
```typescript
videoId: response.video?.video_id,
```

**Step 3: Use videoId in handleDownload**

`frontend/src/app/(dashboard)/user/video/[id]/page.tsx:178-193`:
```typescript
const handleDownload = async () => {
  if (!video) return
  if (!video.videoId) {
    showToast('다운로드할 영상이 없습니다', 'error')
    return
  }
  try {
    const response = await finalApi.downloadVideo(video.videoId)
    // ...rest same...
  }
}
```

**Step 4: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

---

## Task 4: Fix admin `handleReview` — wrong ID extraction + auth guard issue

**Files:**
- Modify: `frontend/src/app/admin/page.tsx:352-360` (AdminRequest mapping — add ad_id)
- Modify: `frontend/src/app/admin/page.tsx:383-388` (handleReview)

**Problem:**
1. `productName.match(/#(\d+)/)` → 실제 제품명이면 실패 → UUID로 폴백
2. `/user/video/{id}` 는 `(dashboard)` layout의 인증 가드 사용 → 관리자 세션과 분리

**Fix:**
1. AdminRequest에 `adId` 필드 추가. 워크플로우 응답에서 `ad_id`를 직접 저장.
2. 관리자는 같은 /user/video/ 경로를 사용하되, backend API는 이미 admin 권한도 허용 (`account_type != 'admin'` 체크). 프론트엔드의 인증 가드가 문제이므로, admin 토큰이 `useAuth`에서도 인식되도록 하거나, admin 전용 비디오 상세 페이지를 만들어야 함.

현실적인 Fix: admin에서 `/user/video/` 대신 `admin/videos/{id}` 페이지로 라우팅. 이미 `/admin/videos` 페이지가 있으므로 거기서 상세 보기를 처리.

단기 Fix: `handleReview`에서 `ad_id`를 직접 사용하고, 관리자 인증 문제는 현재 `(dashboard)` 레이아웃의 `DashboardContent`가 `useAuth()`를 사용하므로, 관리자 토큰도 `useAuth` cookie에 저장되어 있다면 동작 가능. admin 로그인은 별도이므로 동작 안 함이 확실. 따라서 admin용 비디오 상세를 별도로 만드는 것이 가장 확실.

**Step 1: Add ad_id to AdminRequest mapping**

`frontend/src/app/admin/page.tsx:352`:
```typescript
setRequests(response.items.map((w: ...) => ({
  id: w.execution_id,
  adId: w.ad_id,  // ← 추가
  ...
})))
```

`frontend/src/types/index.ts` AdminRequest type에 `adId?: number` 추가.

**Step 2: Fix handleReview to use adId**

```typescript
const handleReview = (req: AdminRequest) => {
  if (req.adId) {
    window.open(`/user/video/${req.adId}`, '_blank')
  } else {
    showToast('영상 정보를 찾을 수 없습니다', 'error')
  }
}
```

Note: window.open으로 새 탭에서 열면, 사용자가 별도로 로그인된 상태라면 접근 가능. 완전한 해결은 admin 전용 비디오 상세 페이지 구현이지만, 이는 이 bugfix 범위를 초과하므로 TODO로 남김.

**Step 3: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

---

## Task 5: Unify approve API usage — use content_pipeline APIs

**Files:**
- Modify: `frontend/src/lib/api/video.ts:426-460` (approveCharacter, approveVoice, reviseCharacter, reviseVoice)

**Problem:**
프론트엔드가 `video.py`의 character_id 기반 API를 사용하는데, content_pipeline.py에 ad_id 기반 통합 API가 있음.

**Fix:**
content_pipeline.py의 ad_id 기반 API로 통일:
- `POST /api/v1/video/{ad_id}/character/approve`
- `POST /api/v1/video/{ad_id}/voice/approve`
- `POST /api/v1/video/{ad_id}/character/revise`
- `POST /api/v1/video/{ad_id}/voice/revise`

**Step 1: Update approve/revise API functions**

```typescript
async approveCharacter(characterId: number, adId?: string) {
  // ...mock...
  return api.post(`/api/v1/video/${adId}/character/approve`, { approved: true })
}

async approveVoice(characterId: number, adId?: string) {
  // ...mock...
  return api.post(`/api/v1/video/${adId}/voice/approve`, { approved: true })
}

async reviseCharacter(characterId: number, rejectionReason: string, adId?: string) {
  // ...mock...
  return api.post(`/api/v1/video/${adId}/character/revise`, { revision_notes: rejectionReason })
}

async reviseVoice(characterId: number, rejectionReason: string, adId?: string) {
  // ...mock...
  return api.post(`/api/v1/video/${adId}/voice/revise`, { revision_notes: rejectionReason })
}
```

**Step 2: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

---

## Task 6: Fix VideoRequestForm productImage validation

**Files:**
- Modify: `frontend/src/components/forms/VideoRequestForm.tsx`

**Problem:**
`productImage`가 react-hook-form `register`로 등록되지 않아 required validation 미동작.

**Fix:**
`onSubmit` 시점에 productImage null 체크 추가.

**Step 1: Add productImage validation in submit handler**

VideoRequestForm의 submit handler에서 체크:
```typescript
// onSubmit 핸들러 내부
if (!productImage) {
  setError('productImage', { message: '상품 이미지를 업로드해주세요' })
  return
}
```

또는 form validation에 custom validation 추가.

**Step 2: Run TypeScript check**

```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend && npx tsc --noEmit
```

---

## Task 7: Fix admin workflow mapping — include ad_id from API

**Files:**
- Modify: `frontend/src/types/index.ts` (AdminRequest type)

**Problem:**
`AdminRequest` type에 `adId` 필드가 없어서 Task 4의 수정이 type-safe하지 않음.

**Fix:** Task 4에서 함께 처리.

---

## Validation

After all tasks:

1. `cd frontend && npx tsc --noEmit` — TypeScript 에러 없음
2. `cd backend && python -c "import ast; ast.parse(open('app/api/v1/endpoints/admin.py').read()); print('OK')"` — Python 구문 오류 없음
3. 수동 검증:
   - 시나리오 승인 API 호출 경로가 content_pipeline의 `/video/{ad_id}/scenario/approve`로 변경됨
   - handleApproveAssets에서 영상 생성 호출 제거됨
   - 다운로드 시 video.videoId (실제 video_id) 사용
   - 관리자 검수하기 버튼이 ad_id로 이동
   - approve API가 content_pipeline으로 통일됨
