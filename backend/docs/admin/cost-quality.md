# 비용 및 품질 관리 API

Admin이 플랫폼의 비용과 영상 품질을 모니터링하고 관리할 수 있는 API입니다.

## 인증

```http
Authorization: Bearer {admin_access_token}
```

Admin 권한 필요.

---

## 1. 회사별 월별 비용 리포트

각 회사의 월별 비용을 조회합니다.

**Endpoint:** `GET /api/v1/admin/costs/companies`

**Query Parameters:**
- `year` (required): 연도 (예: 2024)
- `month` (required): 월 (1-12)
- `company_id` (optional): 특정 회사만 조회
- `sort_by` (optional, default: `total_cost`): 정렬 기준
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response:**
```json
{
  "period": {
    "year": 2024,
    "month": 1
  },
  "total_companies": 72,
  "companies": [
    {
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "costs": {
        "character_generation": 125000,
        "voice_synthesis": 85000,
        "video_rendering": 195000,
        "storage": 45000,
        "api_calls": 32000,
        "total": 482000
      },
      "usage": {
        "total_videos": 45,
        "total_characters": 12,
        "total_duration_minutes": 2700,
        "storage_gb": 125.5
      },
      "average_cost_per_video": 10711,
      "comparison": {
        "previous_month_total": 425000,
        "growth_rate": 13.4
      }
    },
    {
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "costs": {
        "character_generation": 98000,
        "voice_synthesis": 72000,
        "video_rendering": 165000,
        "storage": 38000,
        "api_calls": 28000,
        "total": 401000
      },
      "usage": {
        "total_videos": 38,
        "total_characters": 10,
        "total_duration_minutes": 2280,
        "storage_gb": 105.2
      },
      "average_cost_per_video": 10553,
      "comparison": {
        "previous_month_total": 380000,
        "growth_rate": 5.5
      }
    }
  ],
  "summary": {
    "total_cost_all_companies": 15420000,
    "average_cost_per_company": 214167,
    "highest_cost_company": {
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "total_cost": 482000
    }
  }
}
```

---

## 2. 전체 비용 통계

플랫폼 전체의 비용 통계를 조회합니다.

**Endpoint:** `GET /api/v1/admin/costs/statistics`

**Query Parameters:**
- `date_from` (required): 시작 날짜 (ISO 8601)
- `date_to` (required): 종료 날짜 (ISO 8601)
- `granularity` (optional, default: `month`): 집계 단위 (`day`, `week`, `month`)

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "total_costs": {
    "character_generation": 3250000,
    "voice_synthesis": 2180000,
    "video_rendering": 5420000,
    "storage": 1250000,
    "api_calls": 890000,
    "total": 12990000
  },
  "cost_breakdown_percentage": {
    "character_generation": 25.0,
    "voice_synthesis": 16.8,
    "video_rendering": 41.7,
    "storage": 9.6,
    "api_calls": 6.9
  },
  "usage_statistics": {
    "total_videos": 1250,
    "total_characters": 285,
    "total_duration_minutes": 75000,
    "total_storage_gb": 3420,
    "total_api_calls": 125000
  },
  "averages": {
    "cost_per_video": 10392,
    "cost_per_minute": 173,
    "cost_per_character": 45579
  },
  "trends": [
    {
      "date": "2024-01-01",
      "total_cost": 385000,
      "video_count": 38
    },
    {
      "date": "2024-01-02",
      "total_cost": 412000,
      "video_count": 42
    }
  ],
  "comparison": {
    "previous_period_total": 11250000,
    "growth_rate": 15.5,
    "cost_efficiency_improvement": -2.3
  }
}
```

---

## 3. 비용 상세 내역

특정 기간의 상세 비용 내역을 조회합니다.

**Endpoint:** `GET /api/v1/admin/costs/details`

**Query Parameters:**
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `company_id` (optional): 특정 회사만 조회
- `cost_type` (optional): 비용 유형 필터
- `offset` (optional, default: 0)
- `limit` (optional, default: 50, max: 200)

**Response:**
```json
{
  "total_count": 1250,
  "offset": 0,
  "limit": 50,
  "details": [
    {
      "cost_id": 98765,
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "video_id": 456,
      "video_title": "신제품 런칭 광고",
      "cost_type": "video_rendering",
      "amount": 12500,
      "details": {
        "duration_seconds": 60,
        "resolution": "1080p",
        "processing_time_minutes": 15.5
      },
      "created_at": "2024-01-23T10:30:00Z"
    },
    {
      "cost_id": 98764,
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "video_id": 456,
      "video_title": "신제품 런칭 광고",
      "cost_type": "voice_synthesis",
      "amount": 3200,
      "details": {
        "character_count": 850,
        "voice_model": "premium"
      },
      "created_at": "2024-01-23T10:15:00Z"
    }
  ]
}
```

---

## 4. 품질 점수 낮은 영상 목록

품질 점수가 낮은 영상을 조회합니다.

**Endpoint:** `GET /api/v1/admin/quality/low-score-videos`

**Query Parameters:**
- `threshold` (optional, default: 70): 품질 점수 임계값 (0-100)
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `sort_by` (optional, default: `quality_score`): 정렬 기준
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response:**
```json
{
  "threshold": 70,
  "total_count": 45,
  "offset": 0,
  "limit": 20,
  "videos": [
    {
      "video_id": 789,
      "title": "여름 시즌 프로모션",
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "quality_score": 58,
      "quality_issues": [
        {
          "category": "audio",
          "issue": "음성 품질 낮음",
          "severity": "high",
          "details": "배경 노이즈 감지됨"
        },
        {
          "category": "video",
          "issue": "프레임 드롭",
          "severity": "medium",
          "details": "15-20초 구간에서 프레임 드롭 발생"
        },
        {
          "category": "content",
          "issue": "자막 싱크 불일치",
          "severity": "low",
          "details": "음성과 자막 0.5초 차이"
        }
      ],
      "status": "completed",
      "created_at": "2024-01-22T14:30:00Z",
      "client_approved": false,
      "views": 12500,
      "engagement_rate": 4.2
    },
    {
      "video_id": 790,
      "title": "신상품 소개",
      "company_id": 12,
      "company_name": "DEF 커머스",
      "quality_score": 65,
      "quality_issues": [
        {
          "category": "video",
          "issue": "해상도 낮음",
          "severity": "medium",
          "details": "일부 구간 720p 이하"
        }
      ],
      "status": "completed",
      "created_at": "2024-01-21T16:45:00Z",
      "client_approved": true,
      "views": 8500,
      "engagement_rate": 5.8
    }
  ],
  "summary": {
    "average_quality_score": 62.5,
    "most_common_issues": [
      {
        "category": "audio",
        "count": 28
      },
      {
        "category": "video",
        "count": 22
      },
      {
        "category": "content",
        "count": 15
      }
    ]
  }
}
```

---

## 5. 자동 품질 검증 실패 목록

자동 품질 검증에 실패한 영상을 조회합니다.

**Endpoint:** `GET /api/v1/admin/quality/validation-failures`

**Query Parameters:**
- `failure_type` (optional): 실패 유형 필터 (`audio_quality`, `video_quality`, `content_policy`, `technical`)
- `date_from` (optional): 시작 날짜
- `date_to` (optional): 종료 날짜
- `status` (optional): 처리 상태 (`pending`, `reviewed`, `resolved`)
- `offset` (optional, default: 0)
- `limit` (optional, default: 20, max: 100)

**Response:**
```json
{
  "total_count": 32,
  "offset": 0,
  "limit": 20,
  "failures": [
    {
      "validation_id": 5678,
      "video_id": 791,
      "title": "겨울 세일 광고",
      "company_id": 15,
      "company_name": "GHI 쇼핑몰",
      "failure_type": "audio_quality",
      "failure_reason": "음성 볼륨이 너무 낮음 (평균 -35dB)",
      "severity": "high",
      "validation_details": {
        "audio_level_db": -35,
        "threshold_db": -20,
        "noise_level": "high",
        "clarity_score": 45
      },
      "status": "pending",
      "retry_count": 0,
      "created_at": "2024-01-23T11:00:00Z",
      "reviewed_at": null,
      "resolved_at": null
    },
    {
      "validation_id": 5677,
      "video_id": 792,
      "title": "신메뉴 출시",
      "company_id": 18,
      "company_name": "JKL 레스토랑",
      "failure_type": "content_policy",
      "failure_reason": "부적절한 콘텐츠 감지",
      "severity": "critical",
      "validation_details": {
        "flagged_content": "inappropriate_language",
        "confidence": 0.92,
        "timestamp": "00:15-00:18"
      },
      "status": "reviewed",
      "retry_count": 0,
      "created_at": "2024-01-23T10:30:00Z",
      "reviewed_at": "2024-01-23T11:15:00Z",
      "reviewed_by": "admin@example.com",
      "review_note": "오탐지 확인, 승인 처리",
      "resolved_at": null
    }
  ],
  "summary": {
    "by_failure_type": {
      "audio_quality": 12,
      "video_quality": 8,
      "content_policy": 7,
      "technical": 5
    },
    "by_status": {
      "pending": 18,
      "reviewed": 10,
      "resolved": 4
    },
    "by_severity": {
      "critical": 5,
      "high": 12,
      "medium": 10,
      "low": 5
    }
  }
}
```

---

## 6. 품질 검증 재시도

실패한 품질 검증을 재시도합니다.

**Endpoint:** `POST /api/v1/admin/quality/validation/{validation_id}/retry`

**Path Parameters:**
- `validation_id`: 검증 ID

**Request Body:**
```json
{
  "force_reprocess": true,
  "skip_checks": ["content_policy"],
  "note": "음성 재생성 후 재검증"
}
```

**Response:**
```json
{
  "validation_id": 5678,
  "video_id": 791,
  "status": "processing",
  "retry_count": 1,
  "message": "품질 검증이 재시도되었습니다",
  "estimated_completion": "2024-01-23T11:30:00Z"
}
```

---

## 7. 품질 검증 승인

실패한 검증을 수동으로 승인합니다.

**Endpoint:** `POST /api/v1/admin/quality/validation/{validation_id}/approve`

**Path Parameters:**
- `validation_id`: 검증 ID

**Request Body:**
```json
{
  "reason": "오탐지 확인, 실제 콘텐츠는 문제 없음",
  "override_checks": ["content_policy"]
}
```

**Response:**
```json
{
  "validation_id": 5677,
  "video_id": 792,
  "status": "approved",
  "approved_by": "admin@example.com",
  "approved_at": "2024-01-23T11:20:00Z",
  "message": "품질 검증이 승인되었습니다"
}
```

---

## 8. 비용 최적화 제안

비용 절감을 위한 제안을 제공합니다.

**Endpoint:** `GET /api/v1/admin/costs/optimization-suggestions`

**Query Parameters:**
- `company_id` (optional): 특정 회사만 조회
- `min_savings` (optional, default: 10000): 최소 절감 금액

**Response:**
```json
{
  "total_potential_savings": 1250000,
  "suggestions": [
    {
      "suggestion_id": 1,
      "company_id": 5,
      "company_name": "ABC 마케팅",
      "category": "storage",
      "title": "오래된 영상 아카이빙",
      "description": "6개월 이상 조회되지 않은 영상을 저비용 스토리지로 이동",
      "current_cost": 45000,
      "optimized_cost": 12000,
      "potential_savings": 33000,
      "savings_percentage": 73.3,
      "implementation_effort": "low",
      "affected_videos": 28
    },
    {
      "suggestion_id": 2,
      "company_id": 8,
      "company_name": "XYZ 브랜드",
      "category": "video_rendering",
      "title": "해상도 최적화",
      "description": "60초 이하 짧은 영상은 720p로 렌더링",
      "current_cost": 165000,
      "optimized_cost": 125000,
      "potential_savings": 40000,
      "savings_percentage": 24.2,
      "implementation_effort": "medium",
      "affected_videos": 22
    },
    {
      "suggestion_id": 3,
      "company_id": 12,
      "company_name": "DEF 커머스",
      "category": "character_generation",
      "title": "캐릭터 재사용",
      "description": "유사한 캐릭터 요청 시 기존 캐릭터 재사용",
      "current_cost": 98000,
      "optimized_cost": 65000,
      "potential_savings": 33000,
      "savings_percentage": 33.7,
      "implementation_effort": "high",
      "affected_videos": 15
    }
  ]
}
```

---

## 9. 품질 트렌드 분석

시간에 따른 품질 트렌드를 분석합니다.

**Endpoint:** `GET /api/v1/admin/quality/trends`

**Query Parameters:**
- `date_from` (required): 시작 날짜
- `date_to` (required): 종료 날짜
- `granularity` (optional, default: `week`): 집계 단위

**Response:**
```json
{
  "period": {
    "from": "2024-01-01",
    "to": "2024-01-31"
  },
  "granularity": "week",
  "trends": [
    {
      "period": "2024-W01",
      "average_quality_score": 82.5,
      "total_videos": 285,
      "validation_failures": 8,
      "failure_rate": 2.8,
      "most_common_issue": "audio_quality"
    },
    {
      "period": "2024-W02",
      "average_quality_score": 85.2,
      "total_videos": 298,
      "validation_failures": 6,
      "failure_rate": 2.0,
      "most_common_issue": "video_quality"
    },
    {
      "period": "2024-W03",
      "average_quality_score": 84.8,
      "total_videos": 312,
      "validation_failures": 9,
      "failure_rate": 2.9,
      "most_common_issue": "audio_quality"
    }
  ],
  "summary": {
    "average_quality_score": 84.2,
    "quality_improvement": 2.7,
    "average_failure_rate": 2.6,
    "failure_rate_improvement": -0.8
  }
}
```

---

## 사용 예시

### Python

```python
import requests

headers = {"Authorization": f"Bearer {admin_token}"}

# 회사별 월별 비용
costs = requests.get(
    "http://localhost:8000/api/v1/admin/costs/companies",
    headers=headers,
    params={"year": 2024, "month": 1}
).json()

for company in costs['companies']:
    print(f"{company['company_name']}: {company['costs']['total']:,}원")

# 전체 비용 통계
stats = requests.get(
    "http://localhost:8000/api/v1/admin/costs/statistics",
    headers=headers,
    params={
        "date_from": "2024-01-01",
        "date_to": "2024-01-31"
    }
).json()

print(f"총 비용: {stats['total_costs']['total']:,}원")
print(f"영상당 평균: {stats['averages']['cost_per_video']:,}원")

# 품질 점수 낮은 영상
low_quality = requests.get(
    "http://localhost:8000/api/v1/admin/quality/low-score-videos",
    headers=headers,
    params={"threshold": 70}
).json()

for video in low_quality['videos']:
    print(f"{video['title']}: 품질 점수 {video['quality_score']}")
    for issue in video['quality_issues']:
        print(f"  - {issue['category']}: {issue['issue']}")

# 품질 검증 실패 목록
failures = requests.get(
    "http://localhost:8000/api/v1/admin/quality/validation-failures",
    headers=headers,
    params={"status": "pending"}
).json()

print(f"처리 대기 중: {failures['total_count']}건")

# 비용 최적화 제안
suggestions = requests.get(
    "http://localhost:8000/api/v1/admin/costs/optimization-suggestions",
    headers=headers
).json()

print(f"총 절감 가능 금액: {suggestions['total_potential_savings']:,}원")
for suggestion in suggestions['suggestions']:
    print(f"{suggestion['title']}: {suggestion['potential_savings']:,}원 절감 가능")
```

### cURL

```bash
# 회사별 비용
curl -X GET "http://localhost:8000/api/v1/admin/costs/companies?year=2024&month=1" \
  -H "Authorization: Bearer {admin_token}"

# 품질 점수 낮은 영상
curl -X GET "http://localhost:8000/api/v1/admin/quality/low-score-videos?threshold=70" \
  -H "Authorization: Bearer {admin_token}"

# 품질 검증 승인
curl -X POST "http://localhost:8000/api/v1/admin/quality/validation/5677/approve" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "오탐지 확인",
    "override_checks": ["content_policy"]
  }'
```

---

## 구현 상태

- ⏳ 회사별 월별 비용 리포트 (구현 예정)
- ⏳ 전체 비용 통계 (구현 예정)
- ⏳ 비용 상세 내역 (구현 예정)
- ⏳ 품질 점수 낮은 영상 목록 (구현 예정)
- ⏳ 자동 품질 검증 실패 목록 (구현 예정)
- ⏳ 품질 검증 재시도 (구현 예정)
- ⏳ 품질 검증 승인 (구현 예정)
- ⏳ 비용 최적화 제안 (구현 예정)
- ⏳ 품질 트렌드 분석 (구현 예정)

---

## 관련 파일

- API 엔드포인트: `app/api/v1/endpoints/costs.py`, `app/api/v1/endpoints/quality.py` (생성 예정)
- CRUD 로직: `app/crud/costs.py`, `app/crud/quality.py` (생성 예정)
- 스키마: `app/schemas/costs.py`, `app/schemas/quality.py` (생성 예정)
- 모델: `app/models/video.py` (FinalVideo, WorkflowExecution)
