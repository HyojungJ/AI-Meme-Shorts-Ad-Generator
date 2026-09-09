# API 명세서

밈 기반 광고 영상 자동 생성 플랫폼 API 문서

## 기본 정보

- **Base URL**: `http://127.0.0.1:8000`
- **API Version**: v1
- **API Prefix**: `/api/v1`

## 인증

모든 API 요청은 JWT 토큰을 사용한 인증이 필요합니다 (회원가입, 로그인 제외).

**Authorization Header**:
```
Authorization: Bearer {access_token}
```

**토큰 타입**:
- Access Token: 30분 유효
- Refresh Token: 7일 유효

---

## 1. 인증 API (`/api/v1/auth`)

### 1.1 회원가입

**Endpoint**: `POST /api/v1/auth/signup`

**설명**: Client 계정 회원가입 (회사 정보 포함)

**Request Body**:
```json
{
  "email": "user@company.com",
  "password": "password123",
  "company_name": "회사명",
  "member_name": "담당자명"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

### 1.2 로그인

**Endpoint**: `POST /api/v1/auth/login`

**설명**: Client 및 Admin 로그인 (비밀번호 방식)

**Request Body**:
```json
{
  "email": "user@company.com",
  "password": "password123"
}
```

**Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

**Admin 로그인 시 Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "account_id": 2,
  "email": "admin@meme-fluencer.com",
  "account_type": "admin",
  "company_id": null,
  "role": null
}
```

### 1.3 로그아웃

**Endpoint**: `POST /api/v1/auth/logout`

**설명**: 로그아웃 (Refresh Token 삭제)

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "message": "로그아웃 되었습니다"
}
```

### 1.4 토큰 갱신

**Endpoint**: `POST /api/v1/auth/refresh`

**설명**: Access Token 갱신

**Request Body**:
```json
{
  "refresh_token": "eyJ..."
}
```

**Response** (200):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

### 1.5 현재 사용자 정보 조회

**Endpoint**: `GET /api/v1/auth/me`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "회사명",
  "role": "manager",
  "member_name": "담당자명",
  "department": "마케팅팀",
  "is_active": true
}
```

### 1.6 비밀번호 재설정 요청

**Endpoint**: `POST /api/v1/auth/password-reset/request`

**설명**: 비밀번호 재설정 이메일 발송

**Request Body**:
```json
{
  "email": "user@company.com"
}
```

**Response** (200):
```json
{
  "message": "비밀번호 재설정 이메일이 발송되었습니다"
}
```

### 1.7 비밀번호 재설정 확인

**Endpoint**: `POST /api/v1/auth/password-reset/confirm`

**설명**: 재설정 토큰으로 비밀번호 변경

**Request Body**:
```json
{
  "reset_token": "abc123...",
  "new_password": "newpassword123"
}
```

**Response** (200):
```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다"
}
```

---

## 2. 영상 생성 API (`/api/v1/videos`)

### 2.1 영상 제작 요청

**Endpoint**: `POST /api/v1/videos/generate`

**설명**: 새로운 영상 제작 요청

**Headers**: `Authorization: Bearer {access_token}`

**Content-Type**: `multipart/form-data`

**Form Data**:
- `product_name` (required): 제품명
- `product_category` (required): 제품 카테고리
- `product_highlight` (required): 제품 강조점
- `character_id` (optional): 기존 캐릭터 ID
- `character_mood` (optional): 캐릭터 분위기
- `character_style` (optional): 캐릭터 스타일
- `voice_tone` (optional): 음성 톤
- `character_name` (optional): 캐릭터 이름
- `product_images` (required): 제품 이미지 파일들
- `item_url` (optional): 제품 URL
- `meme_id` (optional): 밈 ID
- `reference_notes` (optional): 참고 사항

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "project_id": 1,
  "status": "created",
  "message": "영상 생성 요청이 접수되었습니다"
}
```

### 2.2 캐릭터 미리보기 조회

**Endpoint**: `GET /api/v1/videos/character/{character_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "character_id": 1,
  "character_name": "캐릭터명",
  "preview_image_url": "https://...",
  "voice_sample_url": "https://...",
  "status": "approved"
}
```

### 2.3 캐릭터 승인/거부

**Endpoint**: `POST /api/v1/videos/character/{character_id}/approve`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "approved": true,
  "feedback": "수정 요청 사항"
}
```

**Response** (200):
```json
{
  "character_id": 1,
  "status": "approved",
  "message": "캐릭터가 승인되었습니다"
}
```

### 2.4 회사 캐릭터 목록 조회

**Endpoint**: `GET /api/v1/videos/characters`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `active_only` (optional, default: true): 활성 캐릭터만 조회

**Response** (200):
```json
[
  {
    "character_id": 1,
    "character_name": "캐릭터명",
    "preview_image_url": "https://...",
    "created_at": "2026-01-20T10:00:00Z",
    "is_active": true
  }
]
```

### 2.5 내 프로젝트 목록 조회

**Endpoint**: `GET /api/v1/videos/my-projects`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `offset` (optional, default: 0): 페이지 오프셋
- `limit` (optional, default: 10): 페이지 크기
- `status` (optional): 상태 필터

**Response** (200):
```json
{
  "total_count": 50,
  "offset": 0,
  "limit": 10,
  "workflows": [
    {
      "execution_id": "uuid-string",
      "project_id": 1,
      "product_name": "제품명",
      "status": "completed",
      "created_at": "2026-01-20T10:00:00Z",
      "updated_at": "2026-01-20T11:00:00Z"
    }
  ]
}
```

---

## 3. 시나리오 검수 API (`/api/v1/videos`)

### 3.1 시나리오 후보 조회

**Endpoint**: `GET /api/v1/videos/{job_id}/scenarios`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "job_id": "uuid-string",
  "scenarios": [
    {
      "script_id": 1,
      "script_text": "시나리오 내용...",
      "estimated_duration": 30,
      "meme_used": "밈 이름"
    }
  ]
}
```

### 3.2 시나리오 승인

**Endpoint**: `POST /api/v1/videos/{job_id}/scenarios/{script_id}/approve`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "script_id": 1,
  "status": "approved",
  "message": "시나리오가 승인되었습니다"
}
```

### 3.3 시나리오 수정 요청

**Endpoint**: `POST /api/v1/videos/{job_id}/scenarios/{script_id}/revise`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "revision_notes": "수정 요청 사항"
}
```

**Response** (200):
```json
{
  "script_id": 1,
  "status": "revision_requested",
  "message": "수정 요청이 접수되었습니다"
}
```

---

## 4. 영상 다운로드 API (`/api/v1/videos`)

### 4.1 영상 다운로드 링크 생성

**Endpoint**: `GET /api/v1/videos/{video_id}/download`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "video_id": 1,
  "download_url": "https://...",
  "expires_at": "2026-01-21T10:00:00Z"
}
```

### 4.2 영상 승인

**Endpoint**: `POST /api/v1/videos/{video_id}/approve`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "quality_rating": 5,
  "comments": "완벽합니다"
}
```

**Response** (200):
```json
{
  "video_id": 1,
  "status": "approved",
  "message": "영상이 승인되었습니다"
}
```

### 4.3 영상 거부

**Endpoint**: `POST /api/v1/videos/{video_id}/reject`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "rejection_reason": "품질 문제",
  "detailed_feedback": "상세 피드백"
}
```

**Response** (200):
```json
{
  "video_id": 1,
  "status": "rejected",
  "message": "영상이 거부되었습니다"
}
```

---

## 5. 상태 추적 API (`/api/v1/status`)

### 5.1 워크플로우 기본 상태 조회

**Endpoint**: `GET /api/v1/status/{execution_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "status": "in_progress",
  "current_step": "video_rendering",
  "progress_percentage": 75,
  "estimated_completion": "2026-01-20T12:00:00Z"
}
```

### 5.2 워크플로우 상세 상태 조회

**Endpoint**: `GET /api/v1/status/{execution_id}/detail`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "status": "in_progress",
  "steps": [
    {
      "step_name": "character_generation",
      "status": "completed",
      "started_at": "2026-01-20T10:00:00Z",
      "completed_at": "2026-01-20T10:15:00Z"
    },
    {
      "step_name": "video_rendering",
      "status": "in_progress",
      "started_at": "2026-01-20T10:15:00Z",
      "progress": 75
    }
  ]
}
```

---

## 6. Admin 관리 API (`/api/v1/admin`)

**권한**: Admin 계정만 접근 가능

### 6.1 전체 영상 목록 조회

**Endpoint**: `GET /api/v1/admin/videos/all`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `company_id` (optional): 회사 ID 필터
- `status` (optional): 상태 필터
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "total_count": 100,
  "offset": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": 1,
      "title": "영상 제목",
      "company_id": 1,
      "company_name": "회사명",
      "status": "completed",
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 6.2 게시 대기 영상 목록

**Endpoint**: `GET /api/v1/admin/videos/pending`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "total_count": 10,
  "videos": [
    {
      "video_id": 1,
      "title": "영상 제목",
      "company_name": "회사명",
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 6.3 YouTube 게시 승인

**Endpoint**: `POST /api/v1/admin/videos/{video_id}/publish`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "scheduled_time": "2026-01-21T10:00:00Z",
  "notes": "게시 관련 메모"
}
```

**Response** (200):
```json
{
  "video_id": 1,
  "status": "scheduled",
  "message": "게시가 예약되었습니다"
}
```

### 6.4 게시 보류

**Endpoint**: `POST /api/v1/admin/videos/{video_id}/hold`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "video_id": 1,
  "status": "on_hold",
  "message": "게시가 보류되었습니다"
}
```

### 6.5 워크플로우 목록 조회

**Endpoint**: `GET /api/v1/admin/workflows`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `status_filter` (optional): 상태 필터
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "total_count": 50,
  "offset": 0,
  "limit": 20,
  "workflows": [
    {
      "execution_id": "uuid-string",
      "company_name": "회사명",
      "status": "in_progress",
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 6.6 워크플로우 상세 로그

**Endpoint**: `GET /api/v1/admin/workflows/{execution_id}/logs`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "logs": [
    {
      "timestamp": "2026-01-20T10:00:00Z",
      "level": "info",
      "message": "워크플로우 시작"
    }
  ]
}
```

### 6.7 워크플로우 재시도

**Endpoint**: `POST /api/v1/admin/workflows/{execution_id}/retry`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "status": "retrying",
  "message": "워크플로우가 재시도되었습니다"
}
```

### 6.8 워크플로우 취소

**Endpoint**: `POST /api/v1/admin/workflows/{execution_id}/cancel`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "execution_id": "uuid-string",
  "status": "cancelled",
  "message": "워크플로우가 취소되었습니다"
}
```

---

## 7. 성과 분석 API (`/api/v1/admin/analytics`)

**권한**: Admin 계정만 접근 가능

### 7.1 전체 대시보드 조회

**Endpoint**: `GET /api/v1/admin/analytics/dashboard`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (optional): 시작 날짜 (ISO 8601)
- `date_to` (optional): 종료 날짜 (ISO 8601)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "summary": {
    "total_videos": 150,
    "total_views": 50000,
    "total_likes": 5000,
    "total_comments": 1000,
    "total_shares": 500,
    "average_engagement_rate": 12.5,
    "average_view_duration_seconds": 25.3,
    "total_companies": 10,
    "active_companies": 8
  },
  "trends": {
    "views_growth": 15.5,
    "engagement_growth": 8.2,
    "video_count_growth": 10.0
  },
  "top_performing_videos": [
    {
      "video_id": 1,
      "title": "영상 제목",
      "company_name": "회사명",
      "views": 10000,
      "engagement_rate": 18.5,
      "published_at": "2026-01-15T10:00:00Z"
    }
  ],
  "top_companies": [
    {
      "company_id": 1,
      "company_name": "회사명",
      "total_videos": 20,
      "total_views": 15000,
      "average_engagement_rate": 14.2
    }
  ]
}
```

### 7.2 밈별 성과 비교

**Endpoint**: `GET /api/v1/admin/analytics/memes`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (optional)
- `date_to` (optional)
- `sort_by` (optional, default: 'views'): 정렬 기준
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "memes": [
    {
      "meme_id": 1,
      "meme_name": "밈 이름",
      "category": "유머",
      "usage_count": 25,
      "total_views": 20000,
      "average_views_per_video": 800,
      "average_engagement_rate": 15.2,
      "average_view_duration": 28.5,
      "top_performing_video": {
        "video_id": 1,
        "title": "영상 제목",
        "views": 5000,
        "engagement_rate": 20.1
      }
    }
  ],
  "total_memes_used": 15
}
```

### 7.3 카테고리별 성과 분석

**Endpoint**: `GET /api/v1/admin/analytics/categories`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (optional)
- `date_to` (optional)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "categories": [
    {
      "category": "유머",
      "video_count": 50,
      "total_views": 30000,
      "average_engagement_rate": 14.5,
      "top_memes": [
        {
          "meme_name": "밈 이름",
          "usage_count": 15,
          "average_engagement_rate": 16.2
        }
      ]
    }
  ]
}
```

### 7.4 시계열 성과 추이

**Endpoint**: `GET /api/v1/admin/analytics/trends`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `granularity` (optional, default: 'day'): 집계 단위 (day, week, month)
- `metric` (optional, default: 'views'): 지표 (views, engagement_rate, video_count)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "granularity": "day",
  "metric": "views",
  "data_points": [
    {
      "date": "2026-01-01",
      "value": 1500.0,
      "video_count": 5
    },
    {
      "date": "2026-01-02",
      "value": 1800.0,
      "video_count": 6
    }
  ],
  "summary": {
    "total": 50000.0,
    "average": 1612.9,
    "peak": {
      "date": "2026-01-15",
      "value": 3500.0
    },
    "lowest": {
      "date": "2026-01-05",
      "value": 800.0
    }
  }
}
```

### 7.5 성과 데이터 내보내기

**Endpoint**: `POST /api/v1/admin/analytics/export`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "report_type": "dashboard",
  "date_from": "2026-01-01",
  "date_to": "2026-01-31",
  "format": "excel",
  "include_details": true,
  "filters": {
    "company_ids": [1, 2, 3],
    "meme_categories": ["유머", "감동"]
  }
}
```

**Response** (200):
```json
{
  "export_id": "export-uuid",
  "status": "processing",
  "estimated_completion": "2026-01-20T10:05:00Z",
  "message": "데이터 내보내기가 시작되었습니다"
}
```

### 7.6 내보내기 상태 확인

**Endpoint**: `GET /api/v1/admin/analytics/export/{export_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "export_id": "export-uuid",
  "status": "completed",
  "download_url": "https://...",
  "file_size_mb": 2.5,
  "expires_at": "2026-01-21T10:00:00Z",
  "created_at": "2026-01-20T10:00:00Z",
  "completed_at": "2026-01-20T10:03:00Z"
}
```

### 7.7 회사별 성과 비교

**Endpoint**: `GET /api/v1/admin/analytics/companies`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (optional)
- `date_to` (optional)
- `sort_by` (optional, default: 'total_views'): 정렬 기준
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01T00:00:00Z",
    "to": "2026-01-31T23:59:59Z"
  },
  "companies": [
    {
      "company_id": 1,
      "company_name": "회사명",
      "total_videos": 25,
      "total_views": 20000,
      "total_engagement": 2500,
      "average_engagement_rate": 12.5,
      "average_views_per_video": 800,
      "most_used_meme": "밈 이름",
      "best_performing_video": {
        "video_id": 1,
        "title": "영상 제목",
        "views": 5000,
        "engagement_rate": 18.5
      }
    }
  ],
  "total_companies": 10
}
```

---

## 8. 사용자 관리 API (`/api/v1/admin/users`)

**권한**: Admin 계정만 접근 가능

### 8.1 전체 사용자 목록 조회

**Endpoint**: `GET /api/v1/admin/users`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `account_type` (optional): 계정 유형 (client, admin)
- `status` (optional): 상태 (active, inactive, suspended)
- `company_id` (optional): 회사 ID
- `search` (optional): 이름 또는 이메일 검색
- `sort_by` (optional, default: 'created_at'): 정렬 기준
- `order` (optional, default: 'desc'): 정렬 순서 (asc, desc)
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "total_count": 100,
  "offset": 0,
  "limit": 20,
  "users": [
    {
      "account_id": 1,
      "email": "user@company.com",
      "account_type": "client",
      "company_id": 1,
      "company_name": "회사명",
      "member_name": "담당자명",
      "role": "manager",
      "is_active": true,
      "created_at": "2026-01-10T10:00:00Z",
      "last_login": "2026-01-20T09:00:00Z"
    }
  ]
}
```

### 8.2 사용자 상세 정보 조회

**Endpoint**: `GET /api/v1/admin/users/{account_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Response** (200):
```json
{
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "회사명",
  "member_name": "담당자명",
  "department": "마케팅팀",
  "role": "manager",
  "is_active": true,
  "created_at": "2026-01-10T10:00:00Z",
  "last_login": "2026-01-20T09:00:00Z",
  "total_videos": 15,
  "total_projects": 20,
  "activity_summary": {
    "last_30_days_logins": 25,
    "videos_created": 5,
    "videos_approved": 4
  }
}
```

### 8.3 사용자 활성화/비활성화

**Endpoint**: `PATCH /api/v1/admin/users/{account_id}/status`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "status": "inactive",
  "reason": "장기 미사용",
  "notify_user": true
}
```

**Response** (200):
```json
{
  "account_id": 1,
  "status": "inactive",
  "updated_at": "2026-01-20T10:00:00Z",
  "updated_by": "admin@meme-fluencer.com",
  "message": "사용자 상태가 변경되었습니다"
}
```

### 8.4 사용자 권한 변경

**Endpoint**: `PATCH /api/v1/admin/users/{account_id}/role`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "company_id": 1,
  "role": "manager",
  "reason": "승진"
}
```

**Response** (200):
```json
{
  "account_id": 1,
  "company_id": 1,
  "role": "manager",
  "updated_at": "2026-01-20T10:00:00Z",
  "updated_by": "admin@meme-fluencer.com",
  "message": "사용자 권한이 변경되었습니다"
}
```

### 8.5 사용자 활동 로그 조회

**Endpoint**: `GET /api/v1/admin/users/{account_id}/activity-logs`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `action_type` (optional): 활동 유형
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `offset` (optional, default: 0)
- `limit` (optional, default: 50, max: 200)

**Response** (200):
```json
{
  "account_id": 1,
  "total_count": 150,
  "offset": 0,
  "limit": 50,
  "logs": [
    {
      "log_id": 1,
      "action_type": "login",
      "action_details": "로그인 성공",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2026-01-20T09:00:00Z"
    },
    {
      "log_id": 2,
      "action_type": "video_create",
      "action_details": "영상 생성 요청",
      "resource_id": 123,
      "created_at": "2026-01-20T09:30:00Z"
    }
  ]
}
```

### 8.6 사용자 계정 삭제

**Endpoint**: `DELETE /api/v1/admin/users/{account_id}`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "confirmation": "DELETE",
  "reason": "사용자 요청",
  "delete_videos": false
}
```

**Response** (200):
```json
{
  "account_id": 1,
  "deleted_at": "2026-01-20T10:00:00Z",
  "deleted_by": "admin@meme-fluencer.com",
  "videos_deleted": false,
  "message": "사용자 계정이 삭제되었습니다"
}
```

### 8.7 사용자 통계 요약

**Endpoint**: `GET /api/v1/admin/users/statistics/summary`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (optional)
- `date_to` (optional)

**Response** (200):
```json
{
  "total_users": 100,
  "active_users": 85,
  "inactive_users": 10,
  "suspended_users": 5,
  "new_users_this_period": 15,
  "by_account_type": {
    "client": 95,
    "admin": 5
  },
  "by_role": {
    "manager": 30,
    "member": 65
  },
  "top_active_users": [
    {
      "account_id": 1,
      "email": "user@company.com",
      "login_count": 50,
      "videos_created": 10
    }
  ],
  "user_growth_trend": [
    {
      "date": "2026-01-01",
      "new_users": 5,
      "total_users": 85
    }
  ]
}
```

### 8.8 대량 사용자 작업

**Endpoint**: `POST /api/v1/admin/users/bulk-action`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "action": "deactivate",
  "account_ids": [1, 2, 3, 4, 5],
  "reason": "정책 위반"
}
```

**Response** (200):
```json
{
  "action": "deactivate",
  "total_requested": 5,
  "successful": 4,
  "failed": 1,
  "results": [
    {
      "account_id": 1,
      "success": true,
      "message": "성공"
    },
    {
      "account_id": 5,
      "success": false,
      "message": "사용자를 찾을 수 없습니다"
    }
  ],
  "executed_by": "admin@meme-fluencer.com",
  "executed_at": "2026-01-20T10:00:00Z"
}
```

---

## 9. 비용 관리 API (`/api/v1/admin/costs`)

**권한**: Admin 계정만 접근 가능

### 9.1 회사별 월별 비용 리포트

**Endpoint**: `GET /api/v1/admin/costs/companies`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `year` (required): 연도
- `month` (required): 월 (1-12)
- `company_id` (optional): 특정 회사 필터
- `sort_by` (optional, default: 'total_cost'): 정렬 기준
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "period": {
    "year": 2026,
    "month": 1
  },
  "total_companies": 10,
  "companies": [
    {
      "company_id": 1,
      "company_name": "회사명",
      "costs": {
        "character_generation": 50000,
        "voice_synthesis": 30000,
        "video_rendering": 100000,
        "storage": 20000,
        "api_calls": 10000,
        "total": 210000
      },
      "usage": {
        "total_videos": 25,
        "total_characters": 10,
        "total_duration_minutes": 750,
        "storage_gb": 15.5
      },
      "average_cost_per_video": 8400,
      "comparison": {
        "previous_month_total": 180000,
        "growth_rate": 16.7
      }
    }
  ],
  "summary": {
    "total_cost_all_companies": 2100000,
    "average_cost_per_company": 210000,
    "highest_cost_company": {
      "company_id": 1,
      "company_name": "회사명",
      "total_cost": 350000
    }
  }
}
```

### 9.2 전체 비용 통계

**Endpoint**: `GET /api/v1/admin/costs/statistics`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `granularity` (optional, default: 'month'): 집계 단위 (day, week, month)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  },
  "total_costs": {
    "character_generation": 500000,
    "voice_synthesis": 300000,
    "video_rendering": 1000000,
    "storage": 200000,
    "api_calls": 100000,
    "total": 2100000
  },
  "cost_breakdown_percentage": {
    "character_generation": 23.8,
    "voice_synthesis": 14.3,
    "video_rendering": 47.6,
    "storage": 9.5,
    "api_calls": 4.8
  },
  "usage_statistics": {
    "total_videos": 250,
    "total_characters": 100,
    "total_duration_minutes": 7500,
    "total_storage_gb": 155,
    "total_api_calls": 50000
  },
  "averages": {
    "cost_per_video": 8400,
    "cost_per_minute": 280,
    "cost_per_character": 21000
  },
  "trends": [
    {
      "date": "2026-01-01",
      "total_cost": 70000,
      "video_count": 8
    }
  ],
  "comparison": {
    "previous_period_total": 1800000,
    "growth_rate": 16.7,
    "cost_efficiency_improvement": -5.2
  }
}
```

### 9.3 비용 상세 내역

**Endpoint**: `GET /api/v1/admin/costs/details`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `company_id` (optional): 회사 ID 필터
- `cost_type` (optional): 비용 유형 필터
- `offset` (optional, default: 0)
- `limit` (optional, default: 50, max: 200)

**Response** (200):
```json
{
  "total_count": 500,
  "offset": 0,
  "limit": 50,
  "details": [
    {
      "cost_id": 1,
      "company_id": 1,
      "company_name": "회사명",
      "video_id": 123,
      "video_title": "영상 제목",
      "cost_type": "video_rendering",
      "amount": 4000,
      "details": {
        "duration_seconds": 30,
        "resolution": "1080p",
        "processing_time_minutes": 15
      },
      "created_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 9.4 비용 최적화 제안

**Endpoint**: `GET /api/v1/admin/costs/optimization-suggestions`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `company_id` (optional): 특정 회사 필터
- `min_savings` (optional, default: 10000): 최소 절감 금액

**Response** (200):
```json
{
  "total_potential_savings": 150000,
  "suggestions": [
    {
      "suggestion_id": 1,
      "company_id": 1,
      "company_name": "회사명",
      "category": "storage",
      "title": "오래된 영상 아카이빙",
      "description": "6개월 이상 된 영상을 저비용 스토리지로 이동",
      "current_cost": 50000,
      "optimized_cost": 15000,
      "potential_savings": 35000,
      "savings_percentage": 70.0,
      "implementation_effort": "low",
      "affected_videos": 50
    },
    {
      "suggestion_id": 2,
      "company_id": 1,
      "company_name": "회사명",
      "category": "rendering",
      "title": "배치 렌더링 활용",
      "description": "여러 영상을 동시에 렌더링하여 비용 절감",
      "current_cost": 100000,
      "optimized_cost": 80000,
      "potential_savings": 20000,
      "savings_percentage": 20.0,
      "implementation_effort": "medium",
      "affected_videos": 25
    }
  ]
}
```

---

## 10. 품질 관리 API (`/api/v1/admin/quality`)

**권한**: Admin 계정만 접근 가능

### 10.1 품질 점수 낮은 영상 목록

**Endpoint**: `GET /api/v1/admin/quality/low-score-videos`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `threshold` (optional, default: 70): 품질 점수 임계값 (0-100)
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `sort_by` (optional, default: 'quality_score'): 정렬 기준
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "threshold": 70,
  "total_count": 15,
  "offset": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": 1,
      "title": "영상 제목",
      "company_id": 1,
      "company_name": "회사명",
      "quality_score": 65,
      "quality_issues": [
        {
          "category": "audio",
          "issue": "배경 소음",
          "severity": "medium",
          "details": "0:15-0:20 구간에서 배경 소음 감지"
        },
        {
          "category": "visual",
          "issue": "낮은 해상도",
          "severity": "low",
          "details": "일부 프레임의 해상도가 기준 미달"
        }
      ],
      "status": "completed",
      "created_at": "2026-01-20T10:00:00Z",
      "client_approved": true,
      "views": 1500,
      "engagement_rate": 8.5
    }
  ],
  "summary": {
    "average_quality_score": 62.5,
    "most_common_issues": [
      {
        "category": "audio",
        "count": 8
      },
      {
        "category": "visual",
        "count": 5
      }
    ]
  }
}
```

### 10.2 자동 품질 검증 실패 목록

**Endpoint**: `GET /api/v1/admin/quality/validation-failures`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `failure_type` (optional): 실패 유형 필터
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `status` (optional): 상태 필터 (pending, reviewing, resolved)
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response** (200):
```json
{
  "total_count": 25,
  "offset": 0,
  "limit": 20,
  "failures": [
    {
      "validation_id": 1,
      "video_id": 123,
      "title": "영상 제목",
      "company_id": 1,
      "company_name": "회사명",
      "failure_type": "audio_quality",
      "failure_reason": "음성 품질이 기준 미달",
      "severity": "high",
      "validation_details": {
        "audio_bitrate": "64kbps",
        "required_bitrate": "128kbps",
        "noise_level": "high"
      },
      "status": "pending",
      "retry_count": 0,
      "created_at": "2026-01-20T10:00:00Z",
      "reviewed_at": null,
      "reviewed_by": null,
      "review_note": null,
      "resolved_at": null
    }
  ],
  "summary": {
    "by_failure_type": {
      "audio_quality": 10,
      "video_quality": 8,
      "content_policy": 5,
      "technical_error": 2
    },
    "by_status": {
      "pending": 15,
      "reviewing": 7,
      "resolved": 3
    },
    "by_severity": {
      "high": 8,
      "medium": 12,
      "low": 5
    }
  }
}
```

### 10.3 품질 검증 재시도

**Endpoint**: `POST /api/v1/admin/quality/validation/{validation_id}/retry`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "force_reprocess": true,
  "skip_checks": ["audio_bitrate"],
  "note": "음성 비트레이트 체크 제외하고 재검증"
}
```

**Response** (200):
```json
{
  "validation_id": 1,
  "video_id": 123,
  "status": "retrying",
  "retry_count": 1,
  "message": "품질 검증이 재시도되었습니다",
  "estimated_completion": "2026-01-20T10:15:00Z"
}
```

### 10.4 품질 검증 승인

**Endpoint**: `POST /api/v1/admin/quality/validation/{validation_id}/approve`

**Headers**: `Authorization: Bearer {access_token}`

**Request Body**:
```json
{
  "reason": "수동 검토 결과 문제 없음",
  "override_checks": ["audio_quality"]
}
```

**Response** (200):
```json
{
  "validation_id": 1,
  "video_id": 123,
  "status": "approved",
  "approved_by": "admin@meme-fluencer.com",
  "approved_at": "2026-01-20T10:00:00Z",
  "message": "품질 검증이 승인되었습니다"
}
```

### 10.5 품질 트렌드 분석

**Endpoint**: `GET /api/v1/admin/quality/trends`

**Headers**: `Authorization: Bearer {access_token}`

**Query Parameters**:
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `granularity` (optional, default: 'week'): 집계 단위 (day, week, month)

**Response** (200):
```json
{
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  },
  "granularity": "week",
  "trends": [
    {
      "period": "2026-W01",
      "average_quality_score": 82.5,
      "total_videos": 50,
      "validation_failures": 5,
      "failure_rate": 10.0,
      "most_common_issue": "audio_quality"
    },
    {
      "period": "2026-W02",
      "average_quality_score": 85.2,
      "total_videos": 55,
      "validation_failures": 3,
      "failure_rate": 5.5,
      "most_common_issue": "video_quality"
    }
  ],
  "summary": {
    "average_quality_score": 83.8,
    "quality_improvement": 3.3,
    "average_failure_rate": 7.8,
    "failure_rate_improvement": -4.5
  }
}
```

---

## 11. 헬스 체크 API

### 11.1 루트 엔드포인트

**Endpoint**: `GET /`

**설명**: API 정보 조회

**Response** (200):
```json
{
  "message": "밈 기반 광고 영상 자동 생성 플랫폼",
  "version": "4.0.0",
  "description": "밈 기반 광고 영상 자동 생성 플랫폼",
  "docs": "/docs",
  "api": {
    "v1": "/api/v1"
  },
  "features": {
    "인증": "회원가입, 로그인, 토큰 관리",
    "영상 생성": "캐릭터 생성, 영상 제작 요청",
    "시나리오 검수": "시나리오 승인/수정 요청",
    "영상 다운로드": "영상 다운로드 및 승인/거부",
    "Admin 관리": "전체 영상 관리, 워크플로우 모니터링"
  }
}
```

### 11.2 헬스 체크

**Endpoint**: `GET /health`

**설명**: 서버 상태 확인

**Response** (200):
```json
{
  "status": "healthy",
  "version": "4.0.0"
}
```

---

## 에러 응답 형식

모든 API는 에러 발생 시 다음 형식으로 응답합니다:

**4xx 클라이언트 에러**:
```json
{
  "detail": "에러 메시지"
}
```

**5xx 서버 에러**:
```json
{
  "detail": "서버 내부 오류가 발생했습니다"
}
```

### 주요 HTTP 상태 코드

- `200 OK`: 요청 성공
- `201 Created`: 리소스 생성 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 실패
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스를 찾을 수 없음
- `422 Unprocessable Entity`: 유효성 검증 실패
- `500 Internal Server Error`: 서버 내부 오류
- `501 Not Implemented`: 구현되지 않은 기능

---

## 인증 에러 예시

**토큰 없음**:
```json
{
  "detail": "Authorization 헤더가 필요합니다"
}
```

**유효하지 않은 토큰**:
```json
{
  "detail": "유효하지 않은 토큰입니다"
}
```

**만료된 토큰**:
```json
{
  "detail": "만료된 토큰입니다"
}
```

**권한 없음**:
```json
{
  "detail": "Admin 권한이 필요합니다"
}
```

---

## 페이지네이션

목록 조회 API는 다음과 같은 페이지네이션을 지원합니다:

**Query Parameters**:
- `offset`: 시작 위치 (default: 0)
- `limit`: 페이지 크기 (default: 20, max: 100)

**Response 형식**:
```json
{
  "total_count": 100,
  "offset": 0,
  "limit": 20,
  "items": [...]
}
```

---

## 날짜 형식

모든 날짜는 ISO 8601 형식을 사용합니다:

- `2026-01-20T10:00:00Z` (UTC)
- `2026-01-20T19:00:00+09:00` (KST)

---

## API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 변경 이력

### v4.0.0 (2026-01-23)
- Admin 전용 API 추가 (성과 분석, 사용자 관리, 비용 관리, 품질 관리)
- Admin 로그인 방식 간소화 (비밀번호 로그인만 지원)
- 전체 API 구조 개선

### v3.4.0 (2026-01-20)
- 기본 Client API 구현
- 인증, 영상 생성, 시나리오 검수, 영상 다운로드 기능

---

## 문의

기술 지원: dev@meme-fluencer.com
