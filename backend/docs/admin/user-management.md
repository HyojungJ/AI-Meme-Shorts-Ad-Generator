# 사용자 관리 API

Admin이 플랫폼의 모든 사용자를 관리할 수 있는 API입니다.

## 인증

```http
Authorization: Bearer {admin_access_token}
```

Admin 권한 필요.

---

## 1. 전체 사용자 목록 조회

플랫폼의 모든 사용자를 조회합니다.

**Endpoint:** `GET /api/v1/admin/users`

**Query Parameters:**
- `account_type` (optional): 계정 유형 필터 (`client`, `admin`)
- `status` (optional): 상태 필터 (`active`, `inactive`, `suspended`)
- `company_id` (optional): 특정 회사의 사용자만 조회
- `search` (optional): 이름 또는 이메일 검색
- `sort_by` (optional, default: `created_at`): 정렬 기준
- `order` (optional, default: `desc`): 정렬 순서 (`asc`, `desc`)
- `offset` (optional, default: 0): 페이지네이션 오프셋
- `limit` (optional, default: 20, max: 100): 페이지당 항목 수

**Response:**
```json
{
  "total_count": 450,
  "offset": 0,
  "limit": 20,
  "users": [
    {
      "account_id": 123,
      "email": "john@abc-marketing.com",
      "name": "John Doe",
      "account_type": "client",
      "status": "active",
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "role": "manager",
      "created_at": "2023-12-01T10:00:00Z",
      "last_login_at": "2024-01-23T09:30:00Z",
      "total_videos": 45,
      "is_email_verified": true
    },
    {
      "account_id": 124,
      "email": "sarah@xyz-brand.com",
      "name": "Sarah Kim",
      "account_type": "client",
      "status": "active",
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "role": "member",
      "created_at": "2023-11-15T14:20:00Z",
      "last_login_at": "2024-01-22T16:45:00Z",
      "total_videos": 12,
      "is_email_verified": true
    }
  ]
}
```

---

## 2. 사용자 상세 정보 조회

특정 사용자의 상세 정보를 조회합니다.

**Endpoint:** `GET /api/v1/admin/users/{account_id}`

**Path Parameters:**
- `account_id`: 계정 ID

**Response:**
```json
{
  "account_id": 123,
  "email": "john@abc-marketing.com",
  "name": "John Doe",
  "account_type": "client",
  "status": "active",
  "company": {
    "company_id": 5,
    "company_name": "ABC 마케팅",
    "role": "manager",
    "joined_at": "2023-12-01T10:00:00Z"
  },
  "profile": {
    "phone": "+82-10-1234-5678",
    "department": "마케팅팀",
    "position": "팀장"
  },
  "statistics": {
    "total_videos": 45,
    "total_views": 850000,
    "total_projects": 38,
    "active_projects": 3,
    "average_engagement_rate": 9.8
  },
  "activity": {
    "created_at": "2023-12-01T10:00:00Z",
    "last_login_at": "2024-01-23T09:30:00Z",
    "last_video_created_at": "2024-01-22T15:20:00Z",
    "login_count": 145
  },
  "verification": {
    "is_email_verified": true,
    "email_verified_at": "2023-12-01T10:15:00Z",
    "is_phone_verified": false
  },
  "recent_videos": [
    {
      "video_id": 456,
      "title": "신제품 런칭 광고",
      "status": "completed",
      "views": 125000,
      "created_at": "2024-01-22T15:20:00Z"
    }
  ]
}
```

---

## 3. 사용자 활성화/비활성화

사용자 계정을 활성화하거나 비활성화합니다.

**Endpoint:** `PATCH /api/v1/admin/users/{account_id}/status`

**Path Parameters:**
- `account_id`: 계정 ID

**Request Body:**
```json
{
  "status": "inactive",
  "reason": "장기 미사용으로 인한 비활성화",
  "notify_user": true
}
```

**Fields:**
- `status`: 변경할 상태 (`active`, `inactive`, `suspended`)
- `reason`: 변경 사유 (optional)
- `notify_user`: 사용자에게 이메일 알림 전송 여부 (optional, default: false)

**Response:**
```json
{
  "account_id": 123,
  "status": "inactive",
  "previous_status": "active",
  "changed_at": "2024-01-23T10:30:00Z",
  "changed_by": "admin@example.com",
  "reason": "장기 미사용으로 인한 비활성화",
  "message": "사용자 상태가 변경되었습니다"
}
```

---

## 4. 사용자 권한 변경

회사 내 사용자의 권한을 변경합니다.

**Endpoint:** `PATCH /api/v1/admin/users/{account_id}/role`

**Path Parameters:**
- `account_id`: 계정 ID

**Request Body:**
```json
{
  "company_id": 5,
  "role": "manager",
  "reason": "팀장 승진"
}
```

**Fields:**
- `company_id`: 회사 ID
- `role`: 변경할 권한 (`manager`, `member`)
- `reason`: 변경 사유 (optional)

**Response:**
```json
{
  "account_id": 123,
  "company_id": 5,
  "role": "manager",
  "previous_role": "member",
  "changed_at": "2024-01-23T10:35:00Z",
  "changed_by": "admin@example.com",
  "reason": "팀장 승진",
  "message": "사용자 권한이 변경되었습니다"
}
```

---

## 5. 사용자 활동 로그 조회

사용자의 활동 내역을 조회합니다.

**Endpoint:** `GET /api/v1/admin/users/{account_id}/activity-logs`

**Path Parameters:**
- `account_id`: 계정 ID

**Query Parameters:**
- `action_type` (optional): 활동 유형 필터 (`login`, `video_create`, `video_approve`, `video_reject`)
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `offset` (optional, default: 0)
- `limit` (optional, default: 50, max: 200)

**Response:**
```json
{
  "account_id": 123,
  "total_count": 245,
  "offset": 0,
  "limit": 50,
  "logs": [
    {
      "log_id": 9876,
      "action_type": "video_approve",
      "action_description": "영상 승인",
      "resource_type": "video",
      "resource_id": 456,
      "details": {
        "video_title": "신제품 런칭 광고",
        "approval_comment": "완벽합니다!"
      },
      "ip_address": "123.45.67.89",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-23T09:30:00Z"
    },
    {
      "log_id": 9875,
      "action_type": "login",
      "action_description": "로그인",
      "resource_type": null,
      "resource_id": null,
      "details": {
        "login_method": "email"
      },
      "ip_address": "123.45.67.89",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-23T09:28:00Z"
    },
    {
      "log_id": 9874,
      "action_type": "video_create",
      "action_description": "영상 제작 요청",
      "resource_type": "video",
      "resource_id": 455,
      "details": {
        "video_title": "여름 시즌 프로모션",
        "meme_used": "Drake Hotline Bling"
      },
      "ip_address": "123.45.67.89",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-22T15:20:00Z"
    }
  ]
}
```

---

## 6. 사용자 계정 삭제

사용자 계정을 완전히 삭제합니다. (주의: 복구 불가)

**Endpoint:** `DELETE /api/v1/admin/users/{account_id}`

**Path Parameters:**
- `account_id`: 계정 ID

**Request Body:**
```json
{
  "confirmation": "DELETE",
  "reason": "사용자 요청에 의한 계정 삭제",
  "delete_videos": false
}
```

**Fields:**
- `confirmation`: 삭제 확인 문자열 (반드시 "DELETE" 입력)
- `reason`: 삭제 사유
- `delete_videos`: 사용자의 영상도 함께 삭제할지 여부 (default: false)

**Response:**
```json
{
  "account_id": 123,
  "status": "deleted",
  "deleted_at": "2024-01-23T10:40:00Z",
  "deleted_by": "admin@example.com",
  "videos_deleted": false,
  "message": "사용자 계정이 삭제되었습니다"
}
```

---

## 7. 사용자 통계 요약

전체 사용자 통계를 요약합니다.

**Endpoint:** `GET /api/v1/admin/users/statistics`

**Query Parameters:**
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "total_users": 450,
  "active_users": 385,
  "inactive_users": 45,
  "suspended_users": 20,
  "new_users_this_period": 28,
  "user_growth_rate": 6.6,
  "by_account_type": {
    "client": 445,
    "admin": 5
  },
  "by_role": {
    "manager": 95,
    "member": 350
  },
  "engagement": {
    "daily_active_users": 245,
    "weekly_active_users": 320,
    "monthly_active_users": 385,
    "average_videos_per_user": 2.8
  },
  "top_active_users": [
    {
      "account_id": 123,
      "name": "John Doe",
      "company_name": "ABC 마케팅",
      "total_videos": 45,
      "total_views": 850000
    }
  ]
}
```

---

## 8. 대량 사용자 작업

여러 사용자에게 동시에 작업을 수행합니다.

**Endpoint:** `POST /api/v1/admin/users/bulk-action`

**Request Body:**
```json
{
  "action": "deactivate",
  "account_ids": [123, 124, 125],
  "reason": "장기 미사용 계정 일괄 비활성화",
  "notify_users": true
}
```

**Fields:**
- `action`: 수행할 작업 (`activate`, `deactivate`, `suspend`, `send_notification`)
- `account_ids`: 대상 계정 ID 목록
- `reason`: 작업 사유 (optional)
- `notify_users`: 사용자에게 알림 전송 여부 (optional)

**Response:**
```json
{
  "action": "deactivate",
  "total_requested": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "account_id": 123,
      "status": "success",
      "message": "비활성화 완료"
    },
    {
      "account_id": 124,
      "status": "success",
      "message": "비활성화 완료"
    },
    {
      "account_id": 125,
      "status": "success",
      "message": "비활성화 완료"
    }
  ],
  "executed_at": "2024-01-23T10:45:00Z",
  "executed_by": "admin@example.com"
}
```

---

## 사용 예시

### Python

```python
import requests

headers = {"Authorization": f"Bearer {admin_token}"}

# 전체 사용자 목록 조회
users = requests.get(
    "http://localhost:8000/api/v1/admin/users",
    headers=headers,
    params={
        "status": "active",
        "limit": 50
    }
).json()

print(f"활성 사용자: {users['total_count']}명")

# 사용자 상세 정보
user_detail = requests.get(
    f"http://localhost:8000/api/v1/admin/users/123",
    headers=headers
).json()

print(f"{user_detail['name']} - 총 영상: {user_detail['statistics']['total_videos']}개")

# 사용자 비활성화
deactivate = requests.patch(
    "http://localhost:8000/api/v1/admin/users/123/status",
    headers=headers,
    json={
        "status": "inactive",
        "reason": "장기 미사용",
        "notify_user": True
    }
).json()

print(deactivate['message'])

# 권한 변경
role_change = requests.patch(
    "http://localhost:8000/api/v1/admin/users/124/role",
    headers=headers,
    json={
        "company_id": 5,
        "role": "manager",
        "reason": "승진"
    }
).json()

print(f"권한 변경: {role_change['previous_role']} → {role_change['role']}")

# 활동 로그 조회
logs = requests.get(
    "http://localhost:8000/api/v1/admin/users/123/activity-logs",
    headers=headers,
    params={
        "action_type": "video_create",
        "limit": 20
    }
).json()

for log in logs['logs']:
    print(f"{log['created_at']}: {log['action_description']}")
```

### cURL

```bash
# 사용자 목록
curl -X GET "http://localhost:8000/api/v1/admin/users?status=active" \
  -H "Authorization: Bearer {admin_token}"

# 사용자 상세 정보
curl -X GET "http://localhost:8000/api/v1/admin/users/123" \
  -H "Authorization: Bearer {admin_token}"

# 사용자 비활성화
curl -X PATCH "http://localhost:8000/api/v1/admin/users/123/status" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "inactive",
    "reason": "장기 미사용"
  }'

# 대량 작업
curl -X POST "http://localhost:8000/api/v1/admin/users/bulk-action" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "deactivate",
    "account_ids": [123, 124, 125],
    "reason": "일괄 비활성화"
  }'
```

---

## 구현 상태

- ⏳ 전체 사용자 목록 조회 (구현 예정)
- ⏳ 사용자 상세 정보 조회 (구현 예정)
- ⏳ 사용자 활성화/비활성화 (구현 예정)
- ⏳ 사용자 권한 변경 (구현 예정)
- ⏳ 사용자 활동 로그 조회 (구현 예정)
- ⏳ 사용자 계정 삭제 (구현 예정)
- ⏳ 사용자 통계 요약 (구현 예정)
- ⏳ 대량 사용자 작업 (구현 예정)

---

## 관련 파일

- API 엔드포인트: `app/api/v1/endpoints/users.py` (생성 예정)
- CRUD 로직: `app/crud/users.py` (생성 예정)
- 스키마: `app/schemas/users.py` (생성 예정)
- 모델: `app/models/account.py`, `app/models/company.py`
