# 영상 다운로드 API v1

## 개요

완성된 영상의 다운로드 링크를 생성하고, 영상 메타데이터를 제공하는 API입니다.

**작업 기간**: 2026-01-22  
**위치**: `scripts/final/`

---

## 주요 기능

- S3 Signed URL 생성 (7일 유효)
- 다운로드 권한 검증 (본인 회사 영상만)
- 영상 메타데이터 조회 (길이, 해상도, 파일 크기)
- 썸네일 URL 제공
- 제작 비용 표시
- 생성 소요 시간 표시
- 다운로드 횟수 추적

---

## API 엔드포인트

### GET /api/videos/{video_id}/download

영상 다운로드 링크 생성 및 메타데이터 조회

**경로 파라미터**
- `video_id` (int): 영상 ID

**요청 헤더**
```
Authorization: Bearer {access_token}
```

**응답 (200 OK)**

```json
{
  "video_id": 123,
  "title": "제품명 - 밈 이름",
  "description": "영상 설명",
  
  "download_url": "https://s3.amazonaws.com/bucket/video.mp4?X-Amz-...",
  "download_expires_at": "2026-01-29T10:00:00Z",
  
  "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnail.jpg?X-Amz-...",
  
  "file_size_bytes": 52428800,
  "file_size_mb": 50.0,
  "duration_seconds": 18,
  "resolution": "1080x1920",
  "format": "mp4",
  
  "production_cost_usd": 2.5,
  "processing_time_minutes": 8,
  
  "status": "completed",
  "created_at": "2026-01-22T10:00:00Z",
  "completed_at": "2026-01-22T10:08:00Z",
  
  "download_count": 0
}
```

**응답 필드 설명**

| 필드 | 타입 | 설명 |
|------|------|------|
| video_id | int | 영상 ID |
| title | string | 영상 제목 |
| description | string | 영상 설명 |
| download_url | string | S3 Presigned URL (7일 유효) |
| download_expires_at | string | 다운로드 링크 만료 시간 (ISO 8601) |
| thumbnail_url | string | 썸네일 이미지 URL |
| file_size_bytes | int | 파일 크기 (바이트) |
| file_size_mb | float | 파일 크기 (MB) |
| duration_seconds | int | 영상 길이 (초) |
| resolution | string | 해상도 (예: 1080x1920) |
| format | string | 파일 포맷 (예: mp4) |
| production_cost_usd | float | 제작 비용 (USD) |
| processing_time_minutes | int | 제작 소요 시간 (분) |
| status | string | 영상 상태 |
| created_at | string | 생성 시간 (ISO 8601) |
| completed_at | string | 완료 시간 (ISO 8601) |
| download_count | int | 다운로드 횟수 (항상 0, 컬럼 삭제됨) |

**에러 응답**

**400 Bad Request** - 영상이 아직 완성되지 않음
```json
{
  "detail": "영상이 아직 완성되지 않았습니다. 현재 상태: processing"
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

**500 Internal Server Error** - 다운로드 링크 생성 실패
```json
{
  "detail": "다운로드 링크 생성 실패: S3 연결 오류"
}
```

---

## 권한 관리

### 다운로드 가능 조건
1. **인증된 사용자**: JWT 토큰 필요
2. **같은 회사**: 본인 회사의 영상만 다운로드 가능
3. **완성된 영상**: 상태가 `completed`, `client_approved`, `admin_approved`, `published` 중 하나

### 권한 검증 흐름
```
1. JWT 토큰 검증
   ↓
2. 영상 조회
   ↓
3. 회사 ID 비교 (video.company_id == user.company_id)
   ↓
4. 영상 상태 확인 (completed 이상)
   ↓
5. 다운로드 링크 생성
```

---

## S3 Presigned URL

### 특징
- **유효 기간**: 7일 (604,800초)
- **자동 만료**: 7일 후 링크 무효화
- **재생성 가능**: API 재호출 시 새 링크 생성

### URL 형식
```
https://s3.amazonaws.com/bucket-name/videos/company_123/video_456.mp4?
X-Amz-Algorithm=AWS4-HMAC-SHA256&
X-Amz-Credential=...&
X-Amz-Date=20260122T100000Z&
X-Amz-Expires=604800&
X-Amz-SignedHeaders=host&
X-Amz-Signature=...
```

---

## 사용 예시

### 1. 기본 다운로드

```bash
curl -X GET "https://api.example.com/api/videos/123/download" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Python 예시

```python
import requests

video_id = 123
access_token = "YOUR_ACCESS_TOKEN"

response = requests.get(
    f"https://api.example.com/api/videos/{video_id}/download",
    headers={"Authorization": f"Bearer {access_token}"}
)

if response.status_code == 200:
    data = response.json()
    
    print(f"영상 제목: {data['title']}")
    print(f"파일 크기: {data['file_size_mb']} MB")
    print(f"영상 길이: {data['duration_seconds']}초")
    print(f"제작 비용: ${data['production_cost_usd']}")
    print(f"다운로드 링크: {data['download_url']}")
    print(f"링크 만료: {data['download_expires_at']}")
    
    # 파일 다운로드
    video_response = requests.get(data['download_url'])
    with open('video.mp4', 'wb') as f:
        f.write(video_response.content)
    
    print("다운로드 완료!")
else:
    print(f"에러: {response.json()['detail']}")
```

### 3. JavaScript 예시

```javascript
const videoId = 123;
const accessToken = "YOUR_ACCESS_TOKEN";

fetch(`https://api.example.com/api/videos/${videoId}/download`, {
  headers: {
    "Authorization": `Bearer ${accessToken}`
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(`영상 제목: ${data.title}`);
    console.log(`파일 크기: ${data.file_size_mb} MB`);
    console.log(`영상 길이: ${data.duration_seconds}초`);
    console.log(`제작 비용: $${data.production_cost_usd}`);
    
    // 다운로드 링크를 새 탭에서 열기
    window.open(data.download_url, '_blank');
  })
  .catch(error => console.error('에러:', error));
```

---

## 프론트엔드 연동 가이드

### 1. 다운로드 버튼 구현

```javascript
async function downloadVideo(videoId) {
  const token = localStorage.getItem('access_token');
  
  try {
    // 1. 다운로드 링크 조회
    const response = await fetch(
      `https://api.example.com/api/videos/${videoId}/download`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    if (!response.ok) {
      throw new Error('다운로드 링크 생성 실패');
    }
    
    const data = await response.json();
    
    // 2. 메타데이터 표시
    displayVideoInfo(data);
    
    // 3. 다운로드 시작
    const link = document.createElement('a');
    link.href = data.download_url;
    link.download = `${data.title}.${data.format}`;
    link.click();
    
  } catch (error) {
    console.error('다운로드 실패:', error);
    alert('다운로드에 실패했습니다.');
  }
}

function displayVideoInfo(data) {
  document.getElementById('video-title').textContent = data.title;
  document.getElementById('file-size').textContent = `${data.file_size_mb} MB`;
  document.getElementById('duration').textContent = `${data.duration_seconds}초`;
  document.getElementById('cost').textContent = `$${data.production_cost_usd}`;
  document.getElementById('processing-time').textContent = `${data.processing_time_minutes}분`;
}
```

### 2. 썸네일 미리보기

```javascript
async function showThumbnail(videoId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `https://api.example.com/api/videos/${videoId}/download`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  const data = await response.json();
  
  // 썸네일 표시
  const img = document.getElementById('thumbnail');
  img.src = data.thumbnail_url;
}
```

---

## 주의사항

1. **링크 만료**: 7일 후 링크가 만료되므로, 장기 보관용으로는 부적합
2. **재생성 필요**: 만료된 링크는 API를 다시 호출하여 재생성
3. **권한 확인**: 다른 회사의 영상은 다운로드 불가
4. **상태 확인**: `completed` 이상의 상태만 다운로드 가능
5. **대역폭**: 대용량 파일 다운로드 시 네트워크 대역폭 고려

---

## 관련 API

- [영상 승인 API](./VideoApprovalAPI_v1.md) - 영상 승인/거부
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
