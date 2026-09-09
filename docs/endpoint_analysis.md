# 엔드포인트 중복 분석

## 🔴 심각한 중복 (같은 prefix 사용)

### `/api/v1/videos` - 3개 라우터가 공유!

#### 1. video.router
- `GET /api/v1/videos/{ad_id}` - 광고 조회
- `DELETE /api/v1/videos/{ad_id}` - 광고 삭제
- `POST /api/v1/videos/generate` - 영상 생성 요청
- `GET /api/v1/videos/character/{character_id}` - 캐릭터 미리보기
- `POST /api/v1/videos/character/{character_id}/approve` - 캐릭터 승인
- `POST /api/v1/videos/character/{character_id}/revise` - 캐릭터 재생성
- `GET /api/v1/videos/characters` - 캐릭터 목록
- `POST /api/v1/videos/characters/generate` - 캐릭터 생성
- `POST /api/v1/videos/characters/{character_id}/voice/generate` - 음성 생성
- `GET /api/v1/videos/characters/{character_id}/voice` - 음성 미리보기
- `POST /api/v1/videos/characters/{character_id}/voice/approve` - 음성 승인
- `POST /api/v1/videos/characters/{character_id}/voice/revise` - 음성 재생성

#### 2. final.router
- `GET /api/v1/videos/{video_id}/download` - 영상 다운로드
- `GET /api/v1/videos/{video_id}/preview` - 영상 미리보기
- `POST /api/v1/videos/{video_id}/approve` - 영상 승인
- `POST /api/v1/videos/{video_id}/reject` - 영상 거부
- `POST /api/v1/videos/{video_id}/revise` - 영상 수정 요청

#### 3. scenario.router
- `GET /api/v1/videos/{job_id}/scenarios` - 시나리오 조회
- `POST /api/v1/videos/{job_id}/scenarios/{script_id}/approve` - 시나리오 승인
- `POST /api/v1/videos/{job_id}/scenarios/{script_id}/revise` - 시나리오 수정

**문제점:**
- `{ad_id}`, `{video_id}`, `{job_id}` 모두 숫자 타입이라 FastAPI가 구분 못함
- 예: `GET /api/v1/videos/123` → video.router의 ad_id인지 final.router의 video_id인지 모호

---

## 🟡 유사한 기능 중복

### content_pipeline.router vs video.router
둘 다 캐릭터/음성/시나리오/영상 생성 기능 제공

#### content_pipeline.router (`/api/v1/video/{ad_id}/...`)
- `POST /{ad_id}/character/generate`
- `POST /{ad_id}/voice/generate`
- `POST /{ad_id}/scenario/generate`
- `POST /{ad_id}/video/generate`
- `POST /{ad_id}/character/approve`
- `POST /{ad_id}/voice/approve`
- `POST /{ad_id}/scenario/approve`
- `POST /{ad_id}/video/approve`
- `POST /{ad_id}/content/generate` - 통합 생성
- `POST /{ad_id}/content/approve` - 통합 승인

#### video.router (`/api/v1/videos/...`)
- `POST /characters/generate`
- `POST /characters/{character_id}/voice/generate`
- `POST /character/{character_id}/approve`
- `POST /characters/{character_id}/voice/approve`

**문제점:**
- 같은 기능을 두 곳에서 제공
- 프론트엔드에서 어느 API를 써야 할지 혼란

---

## 🟢 정상 (중복 없음)

### `/api/v1/status`
- `GET /my-projects` - 내 프로젝트 목록
- `GET /{execution_id}` - 워크플로우 상태
- `GET /{execution_id}/detail` - 워크플로우 상세

### `/api/v1/admin`
- Admin 전용 엔드포인트들

### `/api/v1/analytics`
- Client 분석 데이터

### `/api/v1/admin/analytics`
- Admin 분석 데이터

---

## 📋 권장 수정 사항

### 1. `/api/v1/videos` 분리
```
video.router → /api/v1/requests (광고 요청 관리)
final.router → /api/v1/finals (최종 영상 관리)
scenario.router → /api/v1/scenarios (시나리오 관리)
```

### 2. content_pipeline.router 통합
- video.router의 캐릭터/음성 기능을 content_pipeline으로 이동
- 또는 content_pipeline을 제거하고 video.router로 통합

### 3. 명확한 리소스 구조
```
/api/v1/requests - 광고 요청 (AdRequest)
/api/v1/requests/{ad_id}/character - 캐릭터
/api/v1/requests/{ad_id}/voice - 음성
/api/v1/requests/{ad_id}/scenario - 시나리오
/api/v1/requests/{ad_id}/video - 영상
/api/v1/status - 진행 상태
```
