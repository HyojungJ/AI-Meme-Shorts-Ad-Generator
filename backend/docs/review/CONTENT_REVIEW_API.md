# 콘텐츠 검수 API 문서

## 개요

콘텐츠 제작 워크플로우의 각 단계(캐릭터 이미지/음성, 시나리오, 영상)에서 사용자가 결과물을 검수하고 피드백을 제공하여 수정을 요청할 수 있는 API입니다.

**작업일**: 2026-01-27

---

## 1. 캐릭터 이미지 검수

### 1.1 캐릭터 미리보기

```http
GET /api/v1/videos/character/{character_id}
```

**응답**
```json
{
  "character_id": 1,
  "character_name": "밝은 캐릭터",
  "character_mood": "밝고 활기찬",
  "character_style": "귀여운 스타일",
  "voice_tone": "경쾌한 목소리",
  "image_url": "https://s3.amazonaws.com/...",
  "voice_url": null,
  "is_active": false,
  "created_at": "2026-01-27T10:00:00"
}
```

### 1.2 캐릭터 승인/거부

```http
POST /api/v1/videos/character/{character_id}/approve
```

**요청**
```json
{
  "approved": true,
  "rejection_reason": "눈이 너무 작아요",  // approved=false일 때
  "feedback": "전체적으로 좋습니다"  // 선택사항
}
```

**응답**
```json
{
  "character_id": 1,
  "status": "approved",  // 또는 "rejected"
  "message": "캐릭터가 승인되었습니다"
}
```

### 1.3 캐릭터 이미지 수정 요청 (신규)

```http
POST /api/v1/videos/character/{character_id}/revise
```

**요청**
```json
{
  "revision_notes": "눈을 더 크게, 미소를 더 밝게 해주세요",  // 필수
  "character_prompt": "optional 새 프롬프트"  // 선택
}
```

**응답**
```json
{
  "character_id": 1,
  "character_name": "밝은 캐릭터",
  "image_url": "https://s3.amazonaws.com/...",
  "size_bytes": 524288,
  "created_at": "2026-01-27T10:30:00",
  "message": "캐릭터 이미지가 재생성되었습니다"
}
```

**동작**
- `character_prompt`가 제공되면 해당 프롬프트로 재생성
- 없으면 기존 프롬프트 + `revision_notes` 결합하여 재생성
- AI 파이프라인 호출하여 즉시 재생성

---

## 2. 캐릭터 음성 검수

### 2.1 음성 생성

```http
POST /api/v1/videos/characters/{character_id}/voice/generate
```

**요청**
```json
{
  "sample_text": "안녕하세요, 저는 새로운 캐릭터입니다",
  "voice_description": "밝고 경쾌한 목소리"  // 선택
}
```

### 2.2 음성 미리듣기

```http
GET /api/v1/videos/characters/{character_id}/voice
```

**응답**
```json
{
  "character_id": 1,
  "character_name": "밝은 캐릭터",
  "voice_url": "https://s3.amazonaws.com/...",
  "voice_tone": "경쾌한 목소리",
  "duration_seconds": 3.5,
  "created_at": "2026-01-27T10:00:00"
}
```

### 2.3 음성 승인

```http
POST /api/v1/videos/characters/{character_id}/voice/approve
```

**요청**
```json
{
  "approved": true,
  "feedback": "목소리가 완벽합니다"  // 선택
}
```

### 2.4 음성 수정 요청

```http
POST /api/v1/videos/characters/{character_id}/voice/revise
```

**요청**
```json
{
  "revision_notes": "좀 더 밝고 경쾌하게 해주세요",  // 선택
  "rejection_reason": "너무 차분해요",  // 선택 (프론트 호환)
  "sample_text": "새로운 샘플 텍스트"  // 선택
}
```

**응답**
```json
{
  "character_id": 1,
  "voice_url": "https://s3.amazonaws.com/...",
  "voice_id": "elevenlabs_voice_id",
  "duration_seconds": 3.2,
  "size_bytes": 102400,
  "created_at": "2026-01-27T10:30:00",
  "message": "음성이 재생성되었습니다"
}
```

---

## 3. 시나리오 검수

### 3.1 시나리오 조회

```http
GET /api/v1/scenario/{job_id}/scenarios
```

**응답**
```json
{
  "job_id": "ca44ed29-7586-49b4-abe4-84d9d1ced38e",
  "scenario": {
    "script_id": 1,
    "ad_id": 10,
    "title": "프리미엄 요가 매트 광고",
    "description": "건강한 라이프스타일을 위한 요가 매트",
    "scenes": [
      {
        "scene_number": 1,
        "scene_key": "intro",
        "text": "안녕하세요! 오늘은 특별한 요가 매트를 소개합니다",
        "duration": 5.0
      },
      {
        "scene_number": 2,
        "scene_key": "main",
        "text": "이 요가 매트는 친환경 소재로 만들어졌습니다",
        "duration": 7.0
      }
    ],
    "total_duration": 30.0,
    "approval_status": "pending",
    "created_at": "2026-01-27T10:00:00"
  }
}
```

### 3.2 시나리오 승인

```http
POST /api/v1/scenario/{job_id}/scenarios/{script_id}/approve
```

**응답**
```json
{
  "script_id": 1,
  "ad_id": 10,
  "status": "approved",
  "message": "시나리오가 승인되었습니다"
}
```

### 3.3 시나리오 씬별 수정 요청

```http
POST /api/v1/scenario/{job_id}/scenarios/{script_id}/revise
```

**요청**
```json
{
  "scene_revisions": [
    {
      "scene_number": 1,
      "revision_notes": "인트로를 더 짧게 해주세요"
    },
    {
      "scene_number": 2,
      "revision_notes": "친환경 소재 부분을 더 강조해주세요"
    }
  ],
}
```

**응답**
```json
{
  "script_id": 1,
  "ad_id": 10,
  "status": "pending",
  "message": "2개 씬에 대한 수정이 요청되었습니다"
}
```

**동작**
- 씬별 피드백을 `review_result` JSONB에 저장
- AI 파이프라인에 재생성 요청 (별도 처리)

---

## 4. 영상 검수

### 4.1 영상 미리보기 (신규)

```http
GET /api/v1/final/{video_id}/preview
```

**응답**
```json
{
  "video_id": 1,
  "preview_url": "https://s3.amazonaws.com/...?X-Amz-Expires=3600",
  "expires_at": "2026-01-27T11:00:00",
  "duration_seconds": 30.5,
  "thumbnail_url": "https://s3.amazonaws.com/..."
}
```

**특징**
- Pre-signed URL 유효기간: **1시간**
- 승인 전 미리보기용
- 스트리밍 재생 가능

### 4.2 영상 다운로드 (최종 승인 후)

```http
GET /api/v1/final/{video_id}/download
```

**응답**
```json
{
  "video_id": 1,
  "download_url": "https://s3.amazonaws.com/...?X-Amz-Expires=604800",
  "expires_at": "2026-02-03T10:00:00",
  "file_size_bytes": 10485760,
  "format": "mp4"
}
```

**특징**
- Pre-signed URL 유효기간: **7일**
- 최종 승인 후 다운로드용

### 4.3 영상 승인

```http
POST /api/v1/final/{video_id}/approve
```

**요청**
```json
{
  "feedback": "완벽합니다!"  // 선택
}
```

**응답**
```json
{
  "video_id": 1,
  "status": "approved",
  "message": "영상이 승인되었습니다"
}
```

### 4.4 영상 거부

```http
POST /api/v1/final/{video_id}/reject
```

**요청**
```json
{
  "reason": "배경음악이 너무 시끄럽습니다",  // 필수
  "feedback": "자막 크기는 좋습니다"  // 선택
}
```

**응답**
```json
{
  "video_id": 1,
  "status": "rejected",
  "message": "영상이 거부되었습니다"
}
```

### 4.5 영상 수정 요청 (신규)

```http
POST /api/v1/final/{video_id}/revise
```

**요청**
```json
{
  "revision_notes": "배경음악을 더 밝게, 자막 크기를 키워주세요",  // 필수
  "feedback": "전체적으로 좋은데 세부 조정이 필요해요"  // 선택
}
```

**응답**
```json
{
  "video_id": 1,
  "status": "regenerating",
  "message": "영상 재생성이 요청되었습니다"
}
```

**동작**
- AI 파이프라인에 재생성 요청
- 영상 상태를 `regenerating`으로 변경
- 피드백 내역을 `review_result` JSONB에 저장
- 재생성 완료 후 다시 미리보기 가능

---

## 전체 워크플로우

### 캐릭터 이미지
```
1. 생성 (POST /characters/generate)
   ↓
2. 미리보기 (GET /character/{id})
   ↓
3-A. 승인 (POST /character/{id}/approve) → 완료
   OR
3-B. 수정 요청 (POST /character/{id}/revise)
   ↓
4. 재생성 (자동)
   ↓
5. 미리보기 (GET /character/{id})
   ↓
6. 승인 → 완료
```

### 캐릭터 음성
```
1. 생성 (POST /characters/{id}/voice/generate)
   ↓
2. 미리듣기 (GET /characters/{id}/voice)
   ↓
3-A. 승인 (POST /characters/{id}/voice/approve) → 완료
   OR
3-B. 수정 요청 (POST /characters/{id}/voice/revise)
   ↓
4. 재생성 (자동)
   ↓
5. 미리듣기 (GET /characters/{id}/voice)
   ↓
6. 승인 → 완료
```

### 시나리오
```
1. 조회 (GET /scenario/{job_id}/scenarios)
   ↓
2-A. 승인 (POST /scenario/{job_id}/scenarios/{script_id}/approve) → 완료
   OR
2-B. 씬별 수정 요청 (POST /scenario/{job_id}/scenarios/{script_id}/revise)
   ↓
3. 재생성 (별도 처리)
   ↓
4. 조회 (GET /scenario/{job_id}/scenarios)
   ↓
5. 승인 → 완료
```

### 영상
```
1. 미리보기 (GET /final/{video_id}/preview)
   ↓
2-A. 승인 (POST /final/{video_id}/approve)
   ↓
   다운로드 (GET /final/{video_id}/download) → 완료
   OR
2-B. 수정 요청 (POST /final/{video_id}/revise)
   ↓
3. 재생성 (자동)
   ↓
4. 미리보기 (GET /final/{video_id}/preview)
   ↓
5. 승인 → 다운로드 → 완료
```

---

## 피드백 저장 구조

모든 피드백은 각 테이블의 `review_result` JSONB 컬럼에 저장됩니다.

```json
{
  "latest": {
    "revision_notes": "최신 수정 요청 내용",
    "feedback": "추가 피드백",
    "requested_by": 13,
    "requested_at": "2026-01-27T10:30:00"
  },
  "history": [
    {
      "revision_notes": "첫 번째 수정 요청",
      "requested_at": "2026-01-27T10:00:00"
    },
    {
      "revision_notes": "두 번째 수정 요청",
      "requested_at": "2026-01-27T10:30:00"
    }
  ]
}
```

---

## 권한 확인

모든 엔드포인트는 다음 권한을 확인합니다:
- 사용자 인증 (JWT 토큰)
- 회사 ID 일치 확인 (같은 회사의 콘텐츠만 접근 가능)
- Admin은 모든 콘텐츠 접근 가능

---

## 에러 응답

```json
{
  "detail": "에러 메시지"
}
```

**주요 에러 코드**
- `400`: 잘못된 요청 (필수 필드 누락, 유효성 검증 실패)
- `401`: 인증 실패
- `403`: 권한 없음 (다른 회사의 콘텐츠)
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 오류 (AI 파이프라인 통신 오류 등)
- `502`: AI 파이프라인 통신 오류

---

## 구현 파일

- `app/schemas/video.py` - 요청/응답 스키마
- `app/api/v1/endpoints/video.py` - 캐릭터 검수 API
- `app/api/v1/endpoints/scenario.py` - 시나리오 검수 API
- `app/api/v1/endpoints/final.py` - 영상 검수 API
- `app/crud/scenario.py` - 시나리오 CRUD 로직
- `app/crud/final.py` - 영상 CRUD 로직
- `app/services/ai_pipeline_client.py` - AI 파이프라인 클라이언트 (재생성 요청)

---

## TODO

- [ ] AI 파이프라인 `regenerate_video` 메서드 구현
- [ ] 피드백 전용 테이블 구현 (현재는 JSONB에 저장)
- [ ] 수정 요청 횟수 제한 로직 추가
- [ ] 자동 승인 스케줄러 구현 (24시간 경과 시)
