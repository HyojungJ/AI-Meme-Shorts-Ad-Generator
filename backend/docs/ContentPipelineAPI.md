# Content Pipeline API 문서

> **작성일:** 2026-01-28
> **담당:** Backend
> **상태:** 구현 완료 (AI 서버 연동 대기)

---

## 1. 개요

사용자가 광고 영상을 단계별로 생성하고 검수할 수 있는 API입니다.

### 핵심 특징
- **단계별 생성**: 전체 파이프라인 한방 실행이 아닌, 각 단계를 개별 API로 호출
- **검수 플로우**: 각 단계마다 승인/수정 요청 가능
- **씬별 수정**: 시나리오와 영상을 씬 단위로 수정 요청 가능

---

## 2. 워크플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                        AdRequest 생성                            │
│                    POST /api/v1/videos/generate                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  [1단계] 캐릭터 + 음성 생성                                       │
├─────────────────────────────────────────────────────────────────┤
│  POST /video/{ad_id}/character/generate  → 캐릭터 이미지 생성     │
│  POST /video/{ad_id}/voice/generate      → 음성 샘플 생성         │
│                                                                  │
│  GET  /video/{ad_id}/character/preview   → 미리보기               │
│  GET  /video/{ad_id}/voice/preview       → 미리듣기               │
│                                                                  │
│  POST /video/{ad_id}/character/approve   → 개별 승인/거부         │
│  POST /video/{ad_id}/character/revise    → 수정 요청 (재생성)     │
│  POST /video/{ad_id}/voice/approve       → 개별 승인/거부         │
│  POST /video/{ad_id}/voice/revise        → 수정 요청 (재생성)     │
│                                                                  │
│  POST /video/{ad_id}/assets/approve      → 둘 다 승인 확인        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼ (둘 다 승인 시)
┌─────────────────────────────────────────────────────────────────┐
│  [2단계] 시나리오 + 영상 생성                                     │
├─────────────────────────────────────────────────────────────────┤
│  POST /video/{ad_id}/scenario/generate   → 시나리오 생성          │
│  GET  /video/{ad_id}/scenario            → 시나리오 조회          │
│  POST /video/{ad_id}/scenario/approve    → 승인/거부              │
│  POST /video/{ad_id}/scenario/revise     → 씬별 수정 요청         │
│                                                                  │
│  POST /video/{ad_id}/video/generate      → 영상 생성              │
│  GET  /video/{ad_id}/video/preview       → 영상 미리보기          │
│  POST /video/{ad_id}/video/approve       → 승인/거부              │
│  POST /video/{ad_id}/video/revise        → 씬별 수정 요청         │
│                                                                  │
│  POST /video/{ad_id}/content/approve     → 둘 다 승인 → 완료      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 상태 흐름

| 시점 | status | current_stage | progress |
|------|--------|---------------|----------|
| 요청 생성 | `created` | - | 0% |
| 캐릭터 생성 중 | `generating_character` | `character_generation` | 10% |
| 캐릭터 생성 완료 | `pending_approval` | `character_generation` | 20% |
| 음성 생성 완료 | `pending_approval` | `character_generation` | 30% |
| 에셋 승인 | `processing` | `scenario_generation` | 35% |
| 시나리오 생성 완료 | `pending_approval` | `scenario_generation` | 50% |
| 시나리오 승인 | `processing` | `video_generation` | 55% |
| 영상 생성 완료 | `pending_approval` | `video_generation` | 80% |
| 최종 승인 | `completed` | `final_processing` | 100% |

---

## 4. API 상세

### Base URL
```
/api/v1/video/{ad_id}
```

### 인증
모든 API는 Firebase JWT 토큰 필요:
```
Authorization: Bearer {token}
```

---

### 4.1 캐릭터 생성

#### `POST /video/{ad_id}/character/generate`

캐릭터 이미지를 AI로 생성합니다.

**Request:**
```json
{
  "character_prompt": "20대 여성, 밝고 친근한 느낌, 캐주얼한 복장",
  "aspect_ratio": "9:16"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| character_prompt | string | O | 캐릭터 설명 (1-2000자) |
| aspect_ratio | string | X | 이미지 비율 (기본: "9:16") |

**Response (200):**
```json
{
  "character_id": 123,
  "image_url": "https://s3.../character_123.png",
  "status": "generated"
}
```

---

### 4.2 음성 생성

#### `POST /video/{ad_id}/voice/generate`

캐릭터 음성 샘플을 생성합니다.

**Request:**
```json
{
  "sample_text": "안녕하세요, 오늘 소개할 제품은...",
  "voice_description": "밝고 경쾌한 20대 여성 목소리"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| sample_text | string | O | 샘플 텍스트 (1-1000자) |
| voice_description | string | X | 음성 스타일 설명 |

**Response (200):**
```json
{
  "character_id": 123,
  "voice_url": "https://s3.../voice_123.mp3",
  "voice_id": "eleven_xxx",
  "status": "generated"
}
```

---

### 4.3 시나리오 생성

#### `POST /video/{ad_id}/scenario/generate`

광고 시나리오를 AI로 생성합니다.

**전제조건:** 캐릭터 + 음성이 모두 승인된 상태

**Request:**
```json
{
  "meme_id": 5
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| meme_id | int | X | 밈 ID (미입력시 AdRequest의 meme_id 사용) |

**Response (200):**
```json
{
  "script_id": 456,
  "title": "두둥탁 광고",
  "scenes": [
    { "scene_number": 1, "content": "인트로 - 제품 등장", "timestamp": "0:00" },
    { "scene_number": 2, "content": "메인 - 특징 설명", "timestamp": "0:05" },
    { "scene_number": 3, "content": "아웃트로 - CTA", "timestamp": "0:12" }
  ],
  "total_duration": 15.0,
  "status": "generated"
}
```

---

### 4.4 영상 생성

#### `POST /video/{ad_id}/video/generate`

시나리오 기반으로 영상을 생성합니다.

**전제조건:** 시나리오가 승인된 상태

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "video_id": 789,
  "status": "processing",
  "estimated_duration": 120
}
```

---

### 4.5 미리보기 API

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /video/{ad_id}/character/preview` | 캐릭터 이미지 URL |
| `GET /video/{ad_id}/voice/preview` | 음성 파일 URL |
| `GET /video/{ad_id}/scenario` | 시나리오 전체 내용 |
| `GET /video/{ad_id}/video/preview` | 영상 URL |

---

### 4.6 승인 API

#### 개별 승인

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /video/{ad_id}/character/approve` | 캐릭터 승인/거부 |
| `POST /video/{ad_id}/voice/approve` | 음성 승인/거부 |
| `POST /video/{ad_id}/scenario/approve` | 시나리오 승인/거부 |
| `POST /video/{ad_id}/video/approve` | 영상 승인/거부 |

**Request:**
```json
{
  "approved": true,
  "feedback": "좋습니다"
}
```

**Response:**
```json
{
  "status": "approved",
  "message": "캐릭터가 승인되었습니다"
}
```

#### 통합 승인 (다음 단계 진행)

| 엔드포인트 | 설명 |
|-----------|------|
| `POST /video/{ad_id}/assets/approve` | 캐릭터+음성 둘 다 승인 확인 → 시나리오 단계로 |
| `POST /video/{ad_id}/content/approve` | 시나리오+영상 둘 다 승인 확인 → 완료 |

---

### 4.7 수정 요청 API

#### 캐릭터/음성 수정 (재생성)

**`POST /video/{ad_id}/character/revise`**
```json
{
  "revision_notes": "머리 색상을 갈색으로 변경해주세요",
  "character_prompt": "20대 여성, 갈색 머리, 밝은 느낌"
}
```

**`POST /video/{ad_id}/voice/revise`**
```json
{
  "revision_notes": "좀 더 밝은 톤으로",
  "sample_text": "안녕하세요!"
}
```

#### 씬별 수정 (시나리오)

**`POST /video/{ad_id}/scenario/revise`**
```json
{
  "scene_revisions": [
    { "scene_number": 1, "scenario_notes": "대사를 더 짧게" },
    { "scene_number": 3, "scenario_notes": "제품 특징 강조" }
  ]
}
```

#### 씬별 수정 (영상)

**`POST /video/{ad_id}/video/revise`**
```json
{
  "scene_revisions": [
    { "scene_number": 1, "video_notes": "전환 효과 추가" },
    { "scene_number": 2, "video_notes": "자막 위치 조정" }
  ]
}
```

---

## 5. AI 서버 연동 (AI팀 필독)

### 현재 상태
- Backend: API 구현 완료
- AI 서버: **연동 대기**

### Mock 모드
```bash
# .env
AI_PIPELINE_MOCK_MODE=true  # AI 서버 없이 테스트 가능
```

### AI 서버에서 구현 필요한 엔드포인트

| 엔드포인트 | 상태 | 설명 |
|-----------|------|------|
| `POST /generate-character` | 기존 | 캐릭터 이미지 생성 |
| `POST /generate-voice` | 기존 | 음성 생성 |
| `POST /generate-scenario` | 기존 | 시나리오 생성 |
| `POST /generate-video` | **신규** | 영상 생성 |
| `POST /revise-scenario` | **신규** | 시나리오 씬별 수정 |
| `POST /revise-video` | **신규** | 영상 씬별 수정 |

### 신규 엔드포인트 스펙

#### `POST /generate-video`

**Request:**
```json
{
  "ad_id": 1,
  "script_id": 456,
  "company_id": 10
}
```

**Response:**
```json
{
  "video_id": 789,
  "video_url": "https://s3.../video.mp4",
  "status": "processing",
  "estimated_duration": 120
}
```

#### `POST /revise-scenario`

**Request:**
```json
{
  "script_id": 456,
  "scene_revisions": [
    { "scene_number": 1, "scenario_notes": "대사를 더 짧게" }
  ],
  "company_id": 10
}
```

**Response:**
```json
{
  "script_id": 456,
  "scenes": [
    { "scene_number": 1, "content": "수정된 내용", "timestamp": "0:00" }
  ],
  "status": "revised"
}
```

#### `POST /revise-video`

**Request:**
```json
{
  "video_id": 789,
  "scene_revisions": [
    { "scene_number": 1, "video_notes": "전환 효과 추가" }
  ],
  "company_id": 10
}
```

**Response:**
```json
{
  "video_id": 789,
  "status": "processing",
  "estimated_duration": 120
}
```

---

## 6. 프론트엔드 연동 (프론트팀 필독)

### 호출 순서

```typescript
// 1. 캐릭터 생성
const char = await api.post(`/video/${adId}/character/generate`, {
  character_prompt: "...",
  aspect_ratio: "9:16"
});

// 2. 음성 생성
const voice = await api.post(`/video/${adId}/voice/generate`, {
  sample_text: "...",
  voice_description: "..."
});

// 3. 미리보기
const charPreview = await api.get(`/video/${adId}/character/preview`);
const voicePreview = await api.get(`/video/${adId}/voice/preview`);

// 4. 승인
await api.post(`/video/${adId}/character/approve`, { approved: true });
await api.post(`/video/${adId}/voice/approve`, { approved: true });

// 5. 에셋 승인 확인 (다음 단계로)
const assets = await api.post(`/video/${adId}/assets/approve`);
if (!assets.can_proceed) {
  // 아직 승인 안된 항목 있음
}

// 6. 시나리오 생성 & 승인
// 7. 영상 생성 & 승인
// 8. 최종 완료
await api.post(`/video/${adId}/content/approve`);
```

### UI 필요 화면

1. **캐릭터/음성 검수 화면**
   - 이미지 미리보기
   - 음성 재생
   - 승인/거부/수정요청 버튼

2. **시나리오 검수 화면**
   - 씬 목록 표시
   - 씬별 수정 요청 입력
   - 승인/거부 버튼

3. **영상 검수 화면**
   - 영상 플레이어
   - 씬별 수정 요청 입력
   - 승인/거부 버튼

---

## 7. 테스트

### curl 예시

```bash
# 1. 캐릭터 생성
curl -X POST http://localhost:8000/api/v1/video/1/character/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"character_prompt": "20대 여성"}'

# 2. 음성 생성
curl -X POST http://localhost:8000/api/v1/video/1/voice/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sample_text": "안녕하세요"}'

# 3. 에셋 승인
curl -X POST http://localhost:8000/api/v1/video/1/assets/approve \
  -H "Authorization: Bearer $TOKEN"

# 4. 시나리오 생성
curl -X POST http://localhost:8000/api/v1/video/1/scenario/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'

# 5. 최종 완료
curl -X POST http://localhost:8000/api/v1/video/1/content/approve \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. 파일 구조

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── video.py              # 기존 영상 API
│   │   └── content_pipeline.py   # ⭐ Content Pipeline API (신규)
│   ├── schemas/
│   │   └── video.py              # Request/Response 스키마
│   ├── crud/
│   │   └── video.py              # DB CRUD 로직
│   └── services/
│       ├── ai_pipeline_client.py # AI 서버 HTTP 클라이언트
│       └── ai_pipeline_mock.py   # Mock 클라이언트 (테스트용)
└── docs/
    └── ContentPipelineAPI.md     # 이 문서
```

---

## 9. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-01-28 | Content Pipeline API 초기 구현 |

---

