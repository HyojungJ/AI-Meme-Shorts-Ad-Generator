# 성과 분석 API

Admin이 전체 플랫폼의 영상 성과를 분석하고 모니터링할 수 있는 API입니다.

## 인증

```http
Authorization: Bearer {admin_access_token}
```

Admin 권한 필요.

---

## 1. 전체 대시보드

플랫폼 전체의 주요 지표를 한눈에 확인합니다.

**Endpoint:** `GET /api/v1/admin/analytics/dashboard`

**Query Parameters:**
- `date_from` (optional): 시작 날짜 (ISO 8601, 예: `2024-01-01`)
- `date_to` (optional): 종료 날짜 (ISO 8601, 예: `2024-01-31`)

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "summary": {
    "total_videos": 1250,
    "total_views": 5420000,
    "total_likes": 342000,
    "total_comments": 28500,
    "total_shares": 15200,
    "average_engagement_rate": 7.2,
    "average_view_duration_seconds": 45.3,
    "total_companies": 85,
    "active_companies": 72
  },
  "trends": {
    "views_growth": 15.3,
    "engagement_growth": 8.7,
    "video_count_growth": 12.1
  },
  "top_performing_videos": [
    {
      "video_id": 456,
      "title": "신제품 런칭 광고",
      "company_name": "ABC 마케팅",
      "views": 125000,
      "engagement_rate": 12.5,
      "published_at": "2024-01-15T10:00:00Z"
    }
  ],
  "top_companies": [
    {
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "total_videos": 45,
      "total_views": 850000,
      "average_engagement_rate": 9.8
    }
  ]
}
```

---

## 2. 밈별 성과 비교

어떤 밈이 가장 효과적인지 비교 분석합니다.

**Endpoint:** `GET /api/v1/admin/analytics/memes`

**Query Parameters:**
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `sort_by` (optional): 정렬 기준 (`views`, `engagement_rate`, `video_count`)
- `limit` (optional, default: 20): 결과 개수

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "memes": [
    {
      "meme_id": 12,
      "meme_name": "Distracted Boyfriend",
      "category": "관계",
      "usage_count": 145,
      "total_views": 1250000,
      "average_views_per_video": 8620,
      "average_engagement_rate": 8.9,
      "average_view_duration": 48.5,
      "top_performing_video": {
        "video_id": 789,
        "title": "신제품 vs 구제품",
        "views": 95000,
        "engagement_rate": 14.2
      }
    },
    {
      "meme_id": 8,
      "meme_name": "Drake Hotline Bling",
      "category": "선택",
      "usage_count": 132,
      "total_views": 1100000,
      "average_views_per_video": 8333,
      "average_engagement_rate": 7.8,
      "average_view_duration": 42.1,
      "top_performing_video": {
        "video_id": 654,
        "title": "구독 vs 좋아요",
        "views": 88000,
        "engagement_rate": 12.5
      }
    }
  ],
  "total_memes_used": 45
}
```

---

## 3. 카테고리별 성과 분석

밈 카테고리별 성과를 분석합니다.

**Endpoint:** `GET /api/v1/admin/analytics/categories`

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
  "categories": [
    {
      "category": "관계",
      "video_count": 285,
      "total_views": 2100000,
      "average_engagement_rate": 8.5,
      "top_memes": [
        {
          "meme_name": "Distracted Boyfriend",
          "usage_count": 145,
          "average_engagement_rate": 8.9
        },
        {
          "meme_name": "Woman Yelling at Cat",
          "usage_count": 98,
          "average_engagement_rate": 7.8
        }
      ]
    },
    {
      "category": "선택",
      "video_count": 245,
      "total_views": 1850000,
      "average_engagement_rate": 7.9,
      "top_memes": [
        {
          "meme_name": "Drake Hotline Bling",
          "usage_count": 132,
          "average_engagement_rate": 7.8
        },
        {
          "meme_name": "Two Buttons",
          "usage_count": 87,
          "average_engagement_rate": 8.1
        }
      ]
    },
    {
      "category": "반응",
      "video_count": 198,
      "total_views": 1420000,
      "average_engagement_rate": 9.2,
      "top_memes": [
        {
          "meme_name": "Surprised Pikachu",
          "usage_count": 112,
          "average_engagement_rate": 9.5
        }
      ]
    }
  ]
}
```

---

## 4. 시계열 성과 추이

날짜별 성과 추이를 확인합니다.

**Endpoint:** `GET /api/v1/admin/analytics/trends`

**Query Parameters:**
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `granularity` (optional, default: `day`): 집계 단위 (`day`, `week`, `month`)
- `metric` (optional, default: `views`): 지표 (`views`, `engagement_rate`, `video_count`)

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "granularity": "day",
  "metric": "views",
  "data_points": [
    {
      "date": "2024-01-01",
      "value": 145000,
      "video_count": 38
    },
    {
      "date": "2024-01-02",
      "value": 152000,
      "video_count": 42
    },
    {
      "date": "2024-01-03",
      "value": 138000,
      "video_count": 35
    }
  ],
  "summary": {
    "total": 4520000,
    "average": 145806,
    "peak": {
      "date": "2024-01-15",
      "value": 198000
    },
    "lowest": {
      "date": "2024-01-07",
      "value": 112000
    }
  }
}
```

---

## 5. 성과 데이터 내보내기

분석 데이터를 CSV 또는 Excel 파일로 내보냅니다.

**Endpoint:** `POST /api/v1/admin/analytics/export`

**Request Body:**
```json
{
  "report_type": "dashboard",
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "format": "csv",
  "include_details": true,
  "filters": {
    "company_ids": [5, 8, 12],
    "meme_categories": ["관계", "선택"]
  }
}
```

**Fields:**
- `report_type`: 리포트 유형 (`dashboard`, `memes`, `categories`, `companies`, `videos`)
- `date_from`: 시작 날짜
- `date_to`: 종료 날짜
- `format`: 파일 형식 (`csv`, `excel`)
- `include_details`: 상세 데이터 포함 여부
- `filters`: 필터 조건 (optional)

**Response:**
```json
{
  "export_id": "exp_abc123def456",
  "status": "processing",
  "estimated_completion": "2024-01-23T10:05:00Z",
  "message": "데이터 내보내기가 시작되었습니다"
}
```

**내보내기 상태 확인:**

**Endpoint:** `GET /api/v1/admin/analytics/export/{export_id}`

**Response:**
```json
{
  "export_id": "exp_abc123def456",
  "status": "completed",
  "download_url": "https://s3.amazonaws.com/exports/analytics_2024-01-23.csv",
  "file_size_mb": 2.5,
  "expires_at": "2024-01-24T10:00:00Z",
  "created_at": "2024-01-23T10:00:00Z",
  "completed_at": "2024-01-23T10:04:32Z"
}
```

---

## 6. 회사별 성과 비교

회사별 성과를 비교 분석합니다.

**Endpoint:** `GET /api/v1/admin/analytics/companies`

**Query Parameters:**
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `sort_by` (optional, default: `total_views`): 정렬 기준
- `limit` (optional, default: 20): 결과 개수

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "companies": [
    {
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "total_videos": 45,
      "total_views": 850000,
      "total_engagement": 68000,
      "average_engagement_rate": 9.8,
      "average_views_per_video": 18888,
      "most_used_meme": "Distracted Boyfriend",
      "best_performing_video": {
        "video_id": 456,
        "title": "신제품 런칭",
        "views": 125000,
        "engagement_rate": 12.5
      }
    },
    {
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "total_videos": 38,
      "total_views": 720000,
      "total_engagement": 54000,
      "average_engagement_rate": 8.5,
      "average_views_per_video": 18947,
      "most_used_meme": "Drake Hotline Bling",
      "best_performing_video": {
        "video_id": 654,
        "title": "여름 시즌 프로모션",
        "views": 98000,
        "engagement_rate": 11.2
      }
    }
  ],
  "total_companies": 72
}
```

---

## 사용 예시

### Python

```python
import requests
from datetime import datetime, timedelta

headers = {"Authorization": f"Bearer {admin_token}"}

# 전체 대시보드 조회
dashboard = requests.get(
    "http://localhost:8000/api/v1/admin/analytics/dashboard",
    headers=headers,
    params={
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    }
).json()

print(f"총 조회수: {dashboard['summary']['total_views']:,}")
print(f"평균 참여율: {dashboard['summary']['average_engagement_rate']}%")

# 밈별 성과 비교
memes = requests.get(
    "http://localhost:8000/api/v1/admin/analytics/memes",
    headers=headers,
    params={
        "sort_by": "engagement_rate",
        "limit": 10
    }
).json()

for meme in memes['memes']:
    print(f"{meme['meme_name']}: {meme['average_engagement_rate']}%")

# 데이터 내보내기
export = requests.post(
    "http://localhost:8000/api/v1/admin/analytics/export",
    headers=headers,
    json={
        "report_type": "dashboard",
        "date_from": "2024-01-01",
        "date_to": "2024-01-31",
        "format": "csv"
    }
).json()

export_id = export['export_id']

# 내보내기 완료 대기
import time
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/admin/analytics/export/{export_id}",
        headers=headers
    ).json()
    
    if status['status'] == 'completed':
        print(f"다운로드: {status['download_url']}")
        break
    
    time.sleep(5)
```

### cURL

```bash
# 전체 대시보드
curl -X GET "http://localhost:8000/api/v1/admin/analytics/dashboard?date_from=2024-01-01&date_to=2024-01-31" \
  -H "Authorization: Bearer {admin_token}"

# 카테고리별 성과
curl -X GET "http://localhost:8000/api/v1/admin/analytics/categories" \
  -H "Authorization: Bearer {admin_token}"

# 데이터 내보내기
curl -X POST "http://localhost:8000/api/v1/admin/analytics/export" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "memes",
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "format": "excel"
  }'
```

---

## 주요 지표 설명

### 참여율 (Engagement Rate)
```
참여율 = (좋아요 + 댓글 + 공유) / 조회수 × 100
```

### 평균 시청 시간 (Average View Duration)
영상을 얼마나 오래 시청했는지 (초 단위)

### 성장률 (Growth Rate)
```
성장률 = (현재 기간 - 이전 기간) / 이전 기간 × 100
```

---

## 구현 상태

- ⏳ 전체 대시보드 (구현 예정)
- ⏳ 밈별 성과 비교 (구현 예정)
- ⏳ 카테고리별 성과 분석 (구현 예정)
- ⏳ 시계열 성과 추이 (구현 예정)
- ⏳ 성과 데이터 내보내기 (구현 예정)
- ⏳ 회사별 성과 비교 (구현 예정)

---

## 관련 파일

- API 엔드포인트: `app/api/v1/endpoints/analytics.py` (생성 예정)
- CRUD 로직: `app/crud/analytics.py` (생성 예정)
- 스키마: `app/schemas/analytics.py` (생성 예정)
- 모델: `app/models/video.py` (VideoPost, FinalVideo)
