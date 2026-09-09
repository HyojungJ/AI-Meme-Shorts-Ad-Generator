# 영상 승인/거부 API v1

## 개요

완성된 영상을 승인하거나 거부하는 API입니다. 2단계 승인 프로세스를 지원합니다.

**작업 기간**: 2026-01-22  
**위치**: `scripts/final/`

---

## 승인 프로세스

### 2단계 승인 시스템

```
영상 생성 완료 (status: completed)
  ↓
[1단계] 기업 고객 검토
  ↓
  ├─ 승인 (status: client_approved)
  │    ↓
  │    [2단계] Admin 검토
  │    ↓
  │    ├─ 승인 (status: admin_approved) → 유튜브 게시 가능
  │    │
  │    └─ 거부 (status: admin_rejected)
  │
  └─ 거부 (status: client_rejected)
```

---

## API 엔드포인트

### 1. POST /api/videos/{video_id}/approve

영상 승인

**경로 파라미터**
- `video_id` (int): 영상 ID

**요청 헤더**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**요청 본문**

```json
{
  "approval_type": "client"
}
```

**요청 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| approval_type | string | ✅ | 승인 타입: `client` 또는 `admin` |

**응답 (200 OK)**

```json
{
  "video_id": 123,
  "status": "client_approved",
  "message": "영상이 승인되었습니다. Admin 검토 대기 중입니다.",
  "updated_at": "2026-01-22T10:30:00Z"
}
```

**에러 응답**

**400 Bad Request** - 승인할 수 없는 상태
```json
{
  "detail": "승인할 수 없는 상태입니다. 현재 상태: processing"
}
```

**403 Forbidden** - 권한 없음
```json
{
  "detail": "접근 권한이 없습니다"
}
```

**404 Not Found** - 영상을 찾을 수 없음
```json
{
  "detail": "영상을 찾을 수 없습니다"
}
```

---

### 2. POST /api/videos/{video_id}/reject

영상 거부

**경로 파라미터**
- `video_id` (int): 영상 ID

**요청 헤더**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**요청 본문**

```json
{
  "rejection_type": "client",
  "rejection_reason": "제품 이미지가 잘못 표시되었습니다"
}
```

**요청 필드**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| rejection_type | string | ✅ | 거부 타입: `client` 또는 `admin` |
| rejection_reason | string | ✅ | 거부 사유 (최소 1자 이상) |

**응답 (200 OK)**

```json
{
  "video_id": 123,
  "status": "client_rejected",
  "message": "영상이 거부되었습니다.",
  "updated_at": "2026-01-22T10:30:00Z"
}
```

**에러 응답**

**400 Bad Request** - 거부할 수 없는 상태
```json
{
  "detail": "거부할 수 없는 상태입니다. 현재 상태: processing"
}
```

**403 Forbidden** - 권한 없음
```json
{
  "detail": "접근 권한이 없습니다"
}
```

**404 Not Found** - 영상을 찾을 수 없음
```json
{
  "detail": "영상을 찾을 수 없습니다"
}
```

---

## 승인 타입별 권한

### Client 승인/거부
- **권한**: 같은 회사의 영상만
- **승인 가능 상태**: `completed`
- **승인 후 상태**: `client_approved`
- **거부 후 상태**: `client_rejected`

### Admin 승인/거부
- **권한**: 모든 영상 (Admin 계정만)
- **승인 가능 상태**: `client_approved`
- **승인 후 상태**: `admin_approved`
- **거부 후 상태**: `admin_rejected`

---

## 상태 전환 규칙

### 승인 가능 상태

| 현재 상태 | 승인 타입 | 다음 상태 |
|-----------|-----------|-----------|
| completed | client | client_approved |
| client_approved | admin | admin_approved |

### 거부 가능 상태

| 현재 상태 | 거부 타입 | 다음 상태 |
|-----------|-----------|-----------|
| completed | client | client_rejected |
| client_approved | admin | admin_rejected |

### 불가능한 전환

- `processing` → 승인/거부 불가 (아직 완성 안 됨)
- `failed` → 승인/거부 불가 (생성 실패)
- `client_rejected` → 승인 불가 (이미 거부됨)
- `admin_rejected` → 승인 불가 (이미 거부됨)
- `published` → 거부 불가 (이미 게시됨)

---

## 거부 사유 관리

### 저장 정보
- `rejection_reason`: 거부 사유 텍스트
- `rejected_at`: 거부 시간
- `rejected_by_account_id`: 거부자 계정 ID

### 거부 사유 예시
- "제품 이미지가 잘못 표시되었습니다"
- "음성이 부자연스럽습니다"
- "밈 사용이 부적절합니다"
- "브랜드 가이드라인에 맞지 않습니다"
- "영상 품질이 낮습니다"

---

## 사용 예시

### 1. 기업 고객 승인

```bash
curl -X POST "https://api.example.com/api/videos/123/approve" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_type": "client"
  }'
```

### 2. 기업 고객 거부

```bash
curl -X POST "https://api.example.com/api/videos/123/reject" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_type": "client",
    "rejection_reason": "제품 이미지가 잘못 표시되었습니다"
  }'
```

### 3. Admin 승인

```bash
curl -X POST "https://api.example.com/api/videos/123/approve" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_type": "admin"
  }'
```

### 4. Python 예시

```python
import requests

video_id = 123
access_token = "YOUR_ACCESS_TOKEN"

# 승인
response = requests.post(
    f"https://api.example.com/api/videos/{video_id}/approve",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "approval_type": "client"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"승인 완료: {data['message']}")
    print(f"새 상태: {data['status']}")
else:
    print(f"에러: {response.json()['detail']}")

# 거부
response = requests.post(
    f"https://api.example.com/api/videos/{video_id}/reject",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "rejection_type": "client",
        "rejection_reason": "제품 이미지가 잘못 표시되었습니다"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"거부 완료: {data['message']}")
    print(f"새 상태: {data['status']}")
else:
    print(f"에러: {response.json()['detail']}")
```

### 5. JavaScript 예시

```javascript
const videoId = 123;
const accessToken = "YOUR_ACCESS_TOKEN";

// 승인
async function approveVideo() {
  try {
    const response = await fetch(
      `https://api.example.com/api/videos/${videoId}/approve`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          approval_type: 'client'
        })
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      console.log(`승인 완료: ${data.message}`);
      console.log(`새 상태: ${data.status}`);
    } else {
      console.error(`에러: ${data.detail}`);
    }
  } catch (error) {
    console.error('승인 실패:', error);
  }
}

// 거부
async function rejectVideo(reason) {
  try {
    const response = await fetch(
      `https://api.example.com/api/videos/${videoId}/reject`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          rejection_type: 'client',
          rejection_reason: reason
        })
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      console.log(`거부 완료: ${data.message}`);
      console.log(`새 상태: ${data.status}`);
    } else {
      console.error(`에러: ${data.detail}`);
    }
  } catch (error) {
    console.error('거부 실패:', error);
  }
}

// 사용
approveVideo();
rejectVideo('제품 이미지가 잘못 표시되었습니다');
```

---

## 프론트엔드 연동 가이드

### 1. 승인/거부 버튼 구현

```javascript
// 승인 버튼
document.getElementById('approve-btn').addEventListener('click', async () => {
  const confirmed = confirm('이 영상을 승인하시겠습니까?');
  if (!confirmed) return;
  
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(
      `https://api.example.com/api/videos/${videoId}/approve`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ approval_type: 'client' })
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      alert(data.message);
      location.reload(); // 페이지 새로고침
    } else {
      alert(`에러: ${data.detail}`);
    }
  } catch (error) {
    alert('승인 처리 중 오류가 발생했습니다.');
  }
});

// 거부 버튼
document.getElementById('reject-btn').addEventListener('click', async () => {
  const reason = prompt('거부 사유를 입력하세요:');
  if (!reason) return;
  
  const token = localStorage.getItem('access_token');
  
  try {
    const response = await fetch(
      `https://api.example.com/api/videos/${videoId}/reject`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          rejection_type: 'client',
          rejection_reason: reason
        })
      }
    );
    
    const data = await response.json();
    
    if (response.ok) {
      alert(data.message);
      location.reload();
    } else {
      alert(`에러: ${data.detail}`);
    }
  } catch (error) {
    alert('거부 처리 중 오류가 발생했습니다.');
  }
});
```

### 2. 상태별 버튼 표시

```javascript
function updateButtons(videoStatus) {
  const approveBtn = document.getElementById('approve-btn');
  const rejectBtn = document.getElementById('reject-btn');
  
  // 기본적으로 숨김
  approveBtn.style.display = 'none';
  rejectBtn.style.display = 'none';
  
  // 상태에 따라 버튼 표시
  if (videoStatus === 'completed') {
    // 기업 고객 검토 단계
    approveBtn.style.display = 'inline-block';
    rejectBtn.style.display = 'inline-block';
    approveBtn.textContent = '승인';
    rejectBtn.textContent = '거부';
  } else if (videoStatus === 'client_approved') {
    // Admin 검토 단계 (Admin만 표시)
    if (userRole === 'admin') {
      approveBtn.style.display = 'inline-block';
      rejectBtn.style.display = 'inline-block';
      approveBtn.textContent = '최종 승인';
      rejectBtn.textContent = '거부';
    }
  } else if (videoStatus === 'admin_approved') {
    // 최종 승인 완료
    document.getElementById('status-message').textContent = '승인 완료';
  } else if (videoStatus === 'client_rejected' || videoStatus === 'admin_rejected') {
    // 거부됨
    document.getElementById('status-message').textContent = '거부됨';
  }
}
```

---

## 알림 연동

### 승인/거부 시 알림 발송

```python
# 승인 시
if approval_type == 'client':
    # Admin에게 알림
    send_notification(
        to="admin@company.com",
        subject="새로운 영상 승인 요청",
        message=f"영상 ID {video_id}가 기업 고객에 의해 승인되었습니다."
    )
elif approval_type == 'admin':
    # 기업 고객에게 알림
    send_notification(
        to=user_email,
        subject="영상 최종 승인 완료",
        message=f"영상 ID {video_id}가 최종 승인되었습니다. 유튜브 게시가 가능합니다."
    )

# 거부 시
send_notification(
    to=user_email,
    subject="영상 거부됨",
    message=f"영상 ID {video_id}가 거부되었습니다.\n사유: {rejection_reason}"
)
```

---

## 주의사항

1. **권한 확인**: 기업 고객은 본인 회사 영상만, Admin은 모든 영상 승인/거부 가능
2. **상태 확인**: 승인/거부 가능한 상태인지 확인 필요
3. **거부 사유 필수**: 거부 시 반드시 사유 입력
4. **되돌리기 불가**: 한 번 승인/거부하면 되돌릴 수 없음 (재생성 필요)
5. **순차 처리**: 기업 승인 → Admin 승인 순서로 진행

---

## 관련 API

- [영상 다운로드 API](./VideoDownloadAPI_v1.md) - 영상 다운로드
- [영상 생성 API](../generation/VideoGenerationAPI_v3.md) - 영상 제작 요청
- [영상 상태 API](../status/GenerationStatusAPI.md) - 제작 상태 조회

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-01-22 | 초기 버전 작성 |

---

## 작업 완료일

2026.01.22
