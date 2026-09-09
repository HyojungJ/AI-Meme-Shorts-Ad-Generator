# Admin 관리 API

Admin 계정 전용 API로, 전체 영상 관리 및 워크플로우 모니터링 기능을 제공합니다.

## 인증

모든 Admin API는 Admin 계정 권한이 필요합니다.

```http
Authorization: Bearer {admin_access_token}
```

Admin이 아닌 계정으로 접근 시 `403 Forbidden` 에러가 발생합니다.

## API 엔드포인트

### 1. 전체 영상 목록 조회

모든 회사의 영상을 조회하고 필터링할 수 있습니다.

**Endpoint:** `GET /api/v1/admin/videos/all`

**Query Parameters:**
- `company_id` (optional): 특정 회사의 영상만 조회
- `status` (optional): 영상 상태 필터 (`pending`, `processing`, `completed`, `failed`, `client_approved`)
- `offset` (optional, default: 0): 페이지네이션 오프셋
- `limit` (optional, default: 20, max: 100): 페이지당 항목 수

**Response:**
```json
{
  "total_count": 150,
  "offset": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": 123,
      "title": "신제품 광고 영상",
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "status": "completed",
      "duration_seconds": 60,
      "file_size_mb": 45.2,
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T11:45:00Z"
    }
  ]
}
```

### 2. 게시 대기 영상 목록

클라이언트가 승인한 영상 중 YouTube 게시 대기 중인 영상 목록을 조회합니다.

**Endpoint:** `GET /api/v1/admin/videos/pending`

**Query Parameters:**
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response:**
```json
{
  "total_count": 12,
  "offset": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": 456,
      "title": "여름 시즌 프로모션",
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "status": "client_approved",
      "created_at": "2024-01-20T14:00:00Z",
      "completed_at": "2024-01-20T15:30:00Z"
    }
  ]
}
```

### 3. YouTube 게시 승인

영상을 YouTube에 게시하도록 승인합니다.

**Endpoint:** `POST /api/v1/admin/videos/{video_id}/publish`

**Path Parameters:**
- `video_id`: 영상 ID

**Request Body:**
```json
{
  "channel_id": 1,
  "yt_title": "신제품 출시 광고 | ABC 마케팅",
  "yt_description": "새로운 제품을 소개합니다...",
  "scheduled_at": "2024-01-25T09:00:00Z"
}
```

**Response:**
```json
{
  "post_id": 789,
  "video_id": 456,
  "status": "scheduled",
  "message": "영상 게시가 예약되었습니다"
}
```

### 4. 게시 보류

영상 게시를 보류합니다.

**Endpoint:** `POST /api/v1/admin/videos/{video_id}/hold`

**Path Parameters:**
- `video_id`: 영상 ID

**Response:**
```json
{
  "post_id": 790,
  "video_id": 456,
  "status": "held",
  "message": "영상 게시가 보류되었습니다"
}
```

### 5. 워크플로우 목록 조회

전체 워크플로우 실행 내역을 조회합니다.

**Endpoint:** `GET /api/v1/admin/workflows`

**Query Parameters:**
- `status_filter` (optional): 상태 필터 (`created`, `processing`, `completed`, `failed`, `cancelled`)
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response:**
```json
{
  "total_count": 500,
  "offset": 0,
  "limit": 20,
  "workflows": [
    {
      "execution_id": "550e8400-e29b-41d4-a716-446655440000",
      "project_id": 123,
      "company_id": 5,
      "status": "processing",
      "current_stage": "영상 렌더링",
      "progress_percentage": 65,
      "retry_count": 0,
      "created_at": "2024-01-23T10:00:00Z",
      "completed_at": null
    }
  ]
}
```

### 6. 워크플로우 상세 로그

특정 워크플로우의 상세 실행 로그를 조회합니다.

**Endpoint:** `GET /api/v1/admin/workflows/{execution_id}/logs`

**Path Parameters:**
- `execution_id`: 워크플로우 실행 ID (UUID)

**Response:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": 123,
  "status": "processing",
  "stages": [
    {
      "stage_name": "프로젝트 생성",
      "status": "completed",
      "started_at": "2024-01-23T10:00:00Z",
      "completed_at": "2024-01-23T10:00:15Z",
      "duration_seconds": 15
    },
    {
      "stage_name": "캐릭터 생성",
      "status": "completed",
      "started_at": "2024-01-23T10:00:15Z",
      "completed_at": "2024-01-23T10:05:30Z",
      "duration_seconds": 315
    },
    {
      "stage_name": "영상 렌더링",
      "status": "processing",
      "started_at": "2024-01-23T10:05:30Z",
      "completed_at": null,
      "duration_seconds": null
    }
  ],
  "error_message": null,
  "retry_count": 0
}
```

### 7. 워크플로우 재시도

실패한 워크플로우를 재시도합니다.

**Endpoint:** `POST /api/v1/admin/workflows/{execution_id}/retry`

**Path Parameters:**
- `execution_id`: 워크플로우 실행 ID (UUID)

**Response:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "워크플로우가 재시도되었습니다"
}
```

### 8. 워크플로우 취소

진행 중인 워크플로우를 취소합니다.

**Endpoint:** `POST /api/v1/admin/workflows/{execution_id}/cancel`

**Path Parameters:**
- `execution_id`: 워크플로우 실행 ID (UUID)

**Response:**
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "워크플로우가 취소되었습니다"
}
```

## 에러 응답

### 403 Forbidden - Admin 권한 없음
```json
{
  "detail": "Admin 권한이 필요합니다"
}
```

### 404 Not Found - 리소스 없음
```json
{
  "detail": "영상을 찾을 수 없습니다"
}
```

### 501 Not Implemented - 구현 예정
```json
{
  "detail": "Not implemented"
}
```

## 사용 예시

### Python (requests)

```python
import requests

# Admin 로그인
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "admin@example.com",
        "password": "admin_password"
    }
)
access_token = login_response.json()["access_token"]

# 전체 영상 목록 조회
headers = {"Authorization": f"Bearer {access_token}"}
videos_response = requests.get(
    "http://localhost:8000/api/v1/admin/videos/all",
    headers=headers,
    params={"status": "completed", "limit": 50}
)
videos = videos_response.json()

# 영상 게시 승인
publish_response = requests.post(
    f"http://localhost:8000/api/v1/admin/videos/{video_id}/publish",
    headers=headers,
    json={
        "channel_id": 1,
        "yt_title": "신제품 광고",
        "scheduled_at": "2024-01-25T09:00:00Z"
    }
)
```

### cURL

```bash
# 전체 영상 목록 조회
curl -X GET "http://localhost:8000/api/v1/admin/videos/all?limit=20" \
  -H "Authorization: Bearer {access_token}"

# 워크플로우 재시도
curl -X POST "http://localhost:8000/api/v1/admin/workflows/{execution_id}/retry" \
  -H "Authorization: Bearer {access_token}"
```

## 구현 상태

- ✅ Admin 권한 체크
- ✅ 전체 영상 목록 조회 (기본 구조)
- ✅ 워크플로우 목록 조회 (기본 구조)
- ⏳ 게시 대기 영상 목록 (구현 예정)
- ⏳ YouTube 게시 승인 (구현 예정)
- ⏳ 게시 보류 (구현 예정)
- ⏳ 워크플로우 상세 로그 (구현 예정)
- ⏳ 워크플로우 재시도 (구현 예정)
- ⏳ 워크플로우 취소 (구현 예정)

## 관련 파일

- API 엔드포인트: `app/api/v1/endpoints/admin.py`
- CRUD 로직: `app/crud/admin.py`
- 스키마: `app/schemas/admin.py`
- 모델: `app/models/video.py` (FinalVideo, WorkflowExecution, VideoPost)
