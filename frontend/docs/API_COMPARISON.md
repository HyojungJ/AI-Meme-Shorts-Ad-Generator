# Backend API vs Frontend API 비교 문서

## 개요

이 문서는 백엔드 API와 프론트엔드 API 구현을 비교합니다.

- **백엔드**: FastAPI (`/Users/kimjm/Desktop/meme-fluencer/backend`)
- **프론트엔드**: Next.js (`/Users/kimjm/Desktop/meme-fluencer/frontend`)
- **문서 생성일**: 2026-01-28
- **최종 업데이트**: 2026-01-28 (모든 API 구현 완료)

---

## 구현 현황 요약

| 카테고리 | 백엔드 API 수 | 프론트 구현 | 구현률 |
|----------|--------------|------------|--------|
| Authentication | 8 | 8 | **100%** |
| Meme Management | 2 | 2 | **100%** |
| Video Generation | 11 | 11 | **100%** |
| Scenario Review | 3 | 3 | **100%** |
| Video Status | 3 | 3 | **100%** |
| Video Download/Approval | 5 | 5 | **100%** |
| Client Analytics | 3 | 3 | **100%** |
| Admin Videos/Workflows | 8 | 8 | **100%** |
| Admin Analytics | 7 | 7 | **100%** |
| User Management | 9 | 9 | **100%** |
| Cost Management | 4 | 4 | **100%** |
| Quality Management | 5 | 5 | **100%** |
| Health Check | 4 | 4 | **100%** |
| **총계** | **72** | **72** | **100%** |

---

## 신규 구현된 API 목록

### 1. Meme API (`src/lib/api/meme.ts`) - 신규 파일

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/memes` | `memeApi.getMemes()` |
| GET | `/api/v1/memes/{meme_id}` | `memeApi.getMemeDetail()` |

### 2. Video API (`src/lib/api/video.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| POST | `/api/v1/videos/character/{id}/revise` | `videoApi.reviseCharacterImage()` |
| POST | `/api/v1/videos/characters/{id}/voice/revise` | `videoApi.reviseVoice()` |

### 3. Final API (`src/lib/api/analytics.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/videos/{id}/preview` | `finalApi.previewVideo()` |
| POST | `/api/v1/videos/{id}/revise` | `finalApi.reviseVideo()` |

### 4. Analytics API (`src/lib/api/analytics.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/admin/analytics/export/{id}` | `analyticsApi.getExportStatus()` |
| GET | `/api/v1/admin/analytics/companies` | `analyticsApi.getCompanyPerformance()` |

### 5. Admin API (`src/lib/api/admin.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/admin/users/{id}/activity-logs` | `adminApi.getUserActivityLogs()` |
| POST | `/api/v1/admin/users/bulk-action` | `adminApi.bulkUserAction()` |

### 6. Costs API (`src/lib/api/analytics.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/admin/costs/details` | `costsApi.getCostDetails()` |

### 7. Quality API (`src/lib/api/analytics.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| POST | `/api/v1/admin/quality/validation/{id}/approve` | `qualityApi.approveValidation()` |

### 8. Auth API (`src/lib/api/auth.ts`) - 추가

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| POST | `/api/v1/auth/refresh` | `authApi.refreshToken()` |

### 9. Health API (`src/lib/api/health.ts`) - 신규 파일

| Method | Endpoint | 함수명 |
|--------|----------|--------|
| GET | `/api/v1/health` | `healthApi.check()` |
| GET | `/api/v1/health/db` | `healthApi.checkDatabase()` |
| GET | `/api/v1/health/s3` | `healthApi.checkS3()` |
| GET | `/api/v1/health/all` | `healthApi.checkAll()` |

---

## 전체 API 목록

### Authentication (`/api/v1/auth`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| POST | `/signup` | `authApi.register()` | auth.ts |
| POST | `/login` | `authApi.login()` | auth.ts |
| POST | `/logout` | `authApi.logout()` | auth.ts |
| POST | `/refresh` | `authApi.refreshToken()` | auth.ts |
| GET | `/me` | `authApi.getCurrentUser()` | auth.ts |
| PATCH | `/me` | `authApi.updateProfile()` | auth.ts |
| POST | `/password-reset/request` | `authApi.requestPasswordReset()` | auth.ts |
| POST | `/password-reset/confirm` | `authApi.confirmPasswordReset()` | auth.ts |

### Meme Management (`/api/v1/memes`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/` | `memeApi.getMemes()` | meme.ts |
| GET | `/{meme_id}` | `memeApi.getMemeDetail()` | meme.ts |

### Video Generation (`/api/v1/videos`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/{ad_id}` | `videoApi.getProjectById()` | video.ts |
| POST | `/generate` | `videoApi.generateVideo()` | video.ts |
| GET | `/character/{id}` | `videoApi.getCharacterPreview()` | video.ts |
| POST | `/character/{id}/approve` | `scenarioApi.approveCharacter()` | video.ts |
| POST | `/character/{id}/revise` | `videoApi.reviseCharacterImage()` | video.ts |
| GET | `/characters` | `videoApi.getCharacters()` | video.ts |
| POST | `/characters/generate` | `videoApi.generateCharacter()` | video.ts |
| POST | `/characters/{id}/voice/generate` | `videoApi.generateVoice()` | video.ts |
| GET | `/characters/{id}/voice` | `videoApi.getVoicePreview()` | video.ts |
| POST | `/characters/{id}/voice/approve` | `scenarioApi.approveVoice()` | video.ts |
| POST | `/characters/{id}/voice/revise` | `videoApi.reviseVoice()` | video.ts |

### Scenario Review (`/api/v1/videos`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/{job_id}/scenarios` | `scenarioApi.getScenarios()` | video.ts |
| POST | `/{job_id}/scenarios/{id}/approve` | `scenarioApi.approveScenario()` | video.ts |
| POST | `/{job_id}/scenarios/{id}/revise` | `scenarioApi.reviseScenario()` | video.ts |

### Video Status (`/api/v1/status`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/my-projects` | `videoApi.getMyProjects()` | video.ts |
| GET | `/{execution_id}` | `statusApi.getWorkflowStatus()` | video.ts |
| GET | `/{execution_id}/detail` | `statusApi.getWorkflowDetail()` | video.ts |

### Video Download & Approval (`/api/v1/videos`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/{id}/download` | `finalApi.downloadVideo()` | analytics.ts |
| GET | `/{id}/preview` | `finalApi.previewVideo()` | analytics.ts |
| POST | `/{id}/approve` | `finalApi.approveVideo()` | analytics.ts |
| POST | `/{id}/reject` | `finalApi.rejectVideo()` | analytics.ts |
| POST | `/{id}/revise` | `finalApi.reviseVideo()` | analytics.ts |

### Client Analytics (`/api/v1/analytics`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/dashboard` | `clientAnalyticsApi.getDashboard()` | analytics.ts |
| GET | `/videos/{video_id}` | `clientAnalyticsApi.getVideoPerformance()` | analytics.ts |
| GET | `/summary` | `clientAnalyticsApi.getSummary()` | analytics.ts |

### Admin Videos/Workflows (`/api/v1/admin`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/videos/all` | `adminApi.getAllVideos()` | admin.ts |
| GET | `/videos/pending` | `adminApi.getPendingVideos()` | admin.ts |
| GET | `/videos/{id}` | `adminApi.getVideoDetail()` | admin.ts |
| POST | `/videos/{id}/publish` | `adminApi.publishVideo()` | admin.ts |
| POST | `/videos/{id}/hold` | `adminApi.holdVideo()` | admin.ts |
| GET | `/workflows` | `adminApi.getWorkflows()` | admin.ts |
| GET | `/workflows/{id}/logs` | `adminApi.getWorkflowLogs()` | admin.ts |
| POST | `/workflows/{id}/retry` | `adminApi.retryWorkflow()` | admin.ts |
| POST | `/workflows/{id}/cancel` | `adminApi.cancelWorkflow()` | admin.ts |

### Admin Analytics (`/api/v1/admin/analytics`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/dashboard` | `analyticsApi.getDashboard()` | analytics.ts |
| GET | `/memes` | `analyticsApi.getMemePerformance()` | analytics.ts |
| GET | `/categories` | `analyticsApi.getCategoryPerformance()` | analytics.ts |
| GET | `/trends` | `analyticsApi.getTrends()` | analytics.ts |
| POST | `/export` | `analyticsApi.exportData()` | analytics.ts |
| GET | `/export/{id}` | `analyticsApi.getExportStatus()` | analytics.ts |
| GET | `/companies` | `analyticsApi.getCompanyPerformance()` | analytics.ts |

### User Management (`/api/v1/admin/users`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/` | `adminApi.getUsers()` | admin.ts |
| GET | `/{id}` | `adminApi.getUserDetail()` | admin.ts |
| PATCH | `/{id}/status` | `adminApi.updateUserStatus()` | admin.ts |
| PATCH | `/{id}/role` | `adminApi.updateUserRole()` | admin.ts |
| GET | `/{id}/activity-logs` | `adminApi.getUserActivityLogs()` | admin.ts |
| DELETE | `/{id}` | `adminApi.deleteUser()` | admin.ts |
| POST | `/{id}/delete` | `adminApi.deleteUser()` | admin.ts |
| GET | `/statistics/summary` | `adminApi.getUserStatistics()` | admin.ts |
| POST | `/bulk-action` | `adminApi.bulkUserAction()` | admin.ts |

### Cost Management (`/api/v1/admin/costs`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/companies` | `costsApi.getCompanyCosts()` | analytics.ts |
| GET | `/statistics` | `costsApi.getStatistics()` | analytics.ts |
| GET | `/details` | `costsApi.getCostDetails()` | analytics.ts |
| GET | `/optimization-suggestions` | `costsApi.getOptimizationSuggestions()` | analytics.ts |

### Quality Management (`/api/v1/admin/quality`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/low-score-videos` | `qualityApi.getLowQualityVideos()` | analytics.ts |
| GET | `/validation-failures` | `qualityApi.getValidationFailures()` | analytics.ts |
| POST | `/validation/{id}/retry` | `qualityApi.retryValidation()` | analytics.ts |
| POST | `/validation/{id}/approve` | `qualityApi.approveValidation()` | analytics.ts |
| GET | `/trends` | `qualityApi.getQualityTrends()` | analytics.ts |

### Health Check (`/api/v1/health`)

| Method | Endpoint | 프론트 함수 | 파일 |
|--------|----------|------------|------|
| GET | `/` | `healthApi.check()` | health.ts |
| GET | `/db` | `healthApi.checkDatabase()` | health.ts |
| GET | `/s3` | `healthApi.checkS3()` | health.ts |
| GET | `/all` | `healthApi.checkAll()` | health.ts |

---

## 파일 구조

```
src/lib/api/
├── index.ts       # 모든 API export
├── client.ts      # API 클라이언트 & 토큰 관리
├── auth.ts        # 인증 API
├── video.ts       # 영상/시나리오/상태 API
├── meme.ts        # 밈 API (신규)
├── admin.ts       # 관리자 API
├── analytics.ts   # 분석/비용/품질/최종 API
├── health.ts      # 헬스체크 API (신규)
└── mock.ts        # Mock 데이터
```

---

## 사용 예시

### Meme API
```typescript
import { memeApi } from '@/lib/api'

// 밈 목록 조회
const { memes, total_count } = await memeApi.getMemes({
  meme_type: 'quotable',
  search: '두둥',
  limit: 10,
})

// 밈 상세 조회
const meme = await memeApi.getMemeDetail(1)
```

### Health API
```typescript
import { healthApi } from '@/lib/api'

// 전체 시스템 상태 확인
const status = await healthApi.checkAll()
console.log(status.overall.status) // 'healthy' | 'unhealthy' | 'degraded'
```

### 신규 Video API
```typescript
import { videoApi, finalApi } from '@/lib/api'

// 캐릭터 이미지 재생성
await videoApi.reviseCharacterImage(characterId, {
  revision_notes: '더 밝은 색상으로',
  style_adjustments: '애니메이션 스타일',
})

// 영상 미리보기
const { preview_url } = await finalApi.previewVideo(videoId)

// 영상 재생성 요청
await finalApi.reviseVideo(videoId, '전체적으로 더 빠른 템포로')
```

### Admin 신규 API
```typescript
import { adminApi, analyticsApi, costsApi, qualityApi } from '@/lib/api'

// 사용자 활동 로그
const { logs } = await adminApi.getUserActivityLogs(userId)

// 대량 사용자 작업
await adminApi.bulkUserAction([1, 2, 3], 'suspend')

// 회사별 성과
const { companies } = await analyticsApi.getCompanyPerformance()

// 비용 상세
const { details, total_cost } = await costsApi.getCostDetails({ year: 2026, month: 1 })

// 검증 수동 승인
await qualityApi.approveValidation(validationId, '수동 승인 사유')
```
