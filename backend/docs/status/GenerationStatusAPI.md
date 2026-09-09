# 영상 제작 상태 조회 API V3

## 개요

영상 제작 워크플로우의 각 단계를 추적하고, 사용자에게 상세한 진행 상황을 제공하는 API입니다.

**주요 기능:**
- 워크플로우 단계별 상세 정보 조회
- 완료된 단계의 소요 시간 확인
- 현재 진행 중인 단계 확인
- 대기 중인 단계 목록 확인
- 예상 완료 시간 자동 계산

---

## API 엔드포인트

### GET /api/videos/status/{execution_id}

워크플로우의 상세 상태를 조회합니다.

#### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| execution_id | UUID | ✅ | 워크플로우 고유 ID |

#### 요청 헤더

```
Authorization: Bearer {access_token}
```

#### 응답 (200 OK)

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": 123,
  "status": "processing",
  "current_stage": "음성 합성",
  "progress_percentage": 60,
  "stages": [
    {
      "stage_name": "프로젝트 생성",
      "stage_order": 1,
      "status": "completed",
      "started_at": "2026-01-22T10:00:00+00:00",
      "completed_at": "2026-01-22T10:00:05+00:00",
      "duration_seconds": 5,
      "error_message": null
    },
    {
      "stage_name": "캐릭터 생성",
      "stage_order": 2,
      "status": "completed",
      "started_at": "2026-01-22T10:00:05+00:00",
      "completed_at": "2026-01-22T10:02:30+00:00",
      "duration_seconds": 145,
      "error_message": null
    },
    {
      "stage_name": "시나리오 생성",
      "stage_order": 3,
      "status": "completed",
      "started_at": "2026-01-22T10:02:30+00:00",
      "completed_at": "2026-01-22T10:03:00+00:00",
      "duration_seconds": 30,
      "error_message": null
    },
    {
      "stage_name": "음성 합성",
      "stage_order": 4,
      "status": "processing",
      "started_at": "2026-01-22T10:03:00+00:00",
      "completed_at": null,
      "duration_seconds": null,
      "error_message": null
    },
    {
      "stage_name": "영상 렌더링",
      "stage_order": 5,
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "duration_seconds": null,
      "error_message": null
    },
    {
      "stage_name": "품질 검증",
      "stage_order": 6,
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "duration_seconds": null,
      "error_message": null
    },
    {
      "stage_name": "S3 업로드",
      "stage_order": 7,
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "duration_seconds": null,
      "error_message": null
    }
  ],
  "estimated_completion_time": "2026-01-22T10:08:00+00:00",
  "estimated_remaining_seconds": 300,
  "total_cost_usd": 2.5,
  "retry_count": 0,
  "error_message": null,
  "created_at": "2026-01-22T10:00:00+00:00",
  "completed_at": null
}
```

#### 응답 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| execution_id | string | 워크플로우 고유 ID (UUID) |
| project_id | integer | 프로젝트 ID |
| status | string | 워크플로우 전체 상태 (created, generating_character, pending_approval, processing, completed, failed, cancelled) |
| current_stage | string | 현재 진행 중인 단계명 |
| progress_percentage | integer | 전체 진행률 (0-100) |
| stages | array | 단계별 상세 정보 배열 |
| stages[].stage_name | string | 단계명 |
| stages[].stage_order | integer | 단계 순서 |
| stages[].status | string | 단계 상태 (pending, processing, completed, failed, skipped) |
| stages[].started_at | string | 단계 시작 시각 (ISO 8601) |
| stages[].completed_at | string | 단계 완료 시각 (ISO 8601) |
| stages[].duration_seconds | integer | 단계 소요 시간 (초) |
| stages[].error_message | string | 에러 메시지 (실패 시) |
| estimated_completion_time | string | 예상 완료 시각 (ISO 8601) |
| estimated_remaining_seconds | integer | 예상 남은 시간 (초) |
| total_cost_usd | float | 총 비용 (USD) |
| retry_count | integer | 재시도 횟수 |
| error_message | string | 워크플로우 에러 메시지 |
| created_at | string | 워크플로우 생성 시각 (ISO 8601) |
| completed_at | string | 워크플로우 완료 시각 (ISO 8601) |

#### 에러 응답

**400 Bad Request** - 잘못된 execution_id 형식
```json
{
  "detail": "유효하지 않은 Execution ID 형식입니다"
}
```

**403 Forbidden** - 권한 없음
```json
{
  "detail": "접근 권한이 없습니다"
}
```

**404 Not Found** - 워크플로우를 찾을 수 없음
```json
{
  "detail": "해당 Execution ID를 찾을 수 없습니다"
}
```

---

## 워크플로우 단계

영상 제작 워크플로우는 총 7개의 단계로 구성됩니다:

| 순서 | 단계명 | 설명 | 예상 소요 시간 |
|------|--------|------|----------------|
| 1 | 프로젝트 생성 | 프로젝트 및 워크플로우 초기화 | 5초 |
| 2 | 캐릭터 생성 | AI를 통한 캐릭터 이미지/음성 생성 | 2-3분 |
| 3 | 시나리오 생성 | LLM을 통한 영상 시나리오 작성 | 30초 |
| 4 | 음성 합성 | TTS를 통한 음성 생성 | 1-2분 |
| 5 | 영상 렌더링 | 최종 영상 제작 | 3-5분 |
| 6 | 품질 검증 | 생성된 영상 품질 확인 | 30초 |
| 7 | S3 업로드 | 완성된 영상 S3 업로드 | 1분 |

**총 예상 소요 시간:** 약 8-12분

---

## 단계 상태

각 단계는 다음 상태 중 하나를 가집니다:

| 상태 | 설명 |
|------|------|
| pending | 대기 중 (아직 시작 안 됨) |
| processing | 진행 중 |
| completed | 완료 |
| failed | 실패 |
| skipped | 건너뜀 |

---

## 예상 완료 시간 계산 로직

예상 완료 시간은 다음과 같이 계산됩니다:

1. **완료된 단계들의 평균 소요 시간 계산**
   ```
   평균 소요 시간 = (완료된 단계들의 총 소요 시간) / (완료된 단계 수)
   ```

2. **남은 단계 수 계산**
   ```
   남은 단계 수 = pending 상태 단계 수 + processing 상태 단계 수
   ```

3. **예상 남은 시간 계산**
   ```
   예상 남은 시간 = 평균 소요 시간 × 남은 단계 수
   ```

4. **예상 완료 시각 계산**
   ```
   예상 완료 시각 = 현재 시각 + 예상 남은 시간
   ```

**특수 케이스:**
- 완료된 단계가 없는 경우: 회사별 평균 처리 시간 사용
- 워크플로우가 이미 완료된 경우: `estimated_remaining_seconds = 0`

---

## 사용 예시

### 1. 기본 상태 조회

```bash
curl -X GET "https://api.example.com/api/videos/status/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Python 예시

```python
import requests

execution_id = "550e8400-e29b-41d4-a716-446655440000"
access_token = "YOUR_ACCESS_TOKEN"

response = requests.get(
    f"https://api.example.com/api/videos/status/{execution_id}",
    headers={"Authorization": f"Bearer {access_token}"}
)

if response.status_code == 200:
    data = response.json()
    
    print(f"전체 진행률: {data['progress_percentage']}%")
    print(f"현재 단계: {data['current_stage']}")
    print(f"예상 완료 시간: {data['estimated_completion_time']}")
    
    # 완료된 단계 출력
    completed_stages = [s for s in data['stages'] if s['status'] == 'completed']
    print(f"\n완료된 단계: {len(completed_stages)}개")
    for stage in completed_stages:
        print(f"  - {stage['stage_name']}: {stage['duration_seconds']}초 소요")
    
    # 대기 중인 단계 출력
    pending_stages = [s for s in data['stages'] if s['status'] == 'pending']
    print(f"\n대기 중인 단계: {len(pending_stages)}개")
    for stage in pending_stages:
        print(f"  - {stage['stage_name']}")
```

### 3. JavaScript 예시

```javascript
const executionId = "550e8400-e29b-41d4-a716-446655440000";
const accessToken = "YOUR_ACCESS_TOKEN";

fetch(`https://api.example.com/api/videos/status/${executionId}`, {
  headers: {
    "Authorization": `Bearer ${accessToken}`
  }
})
  .then(response => response.json())
  .then(data => {
    console.log(`전체 진행률: ${data.progress_percentage}%`);
    console.log(`현재 단계: ${data.current_stage}`);
    console.log(`예상 완료 시간: ${data.estimated_completion_time}`);
    
    // 단계별 정보 출력
    data.stages.forEach(stage => {
      console.log(`${stage.stage_name}: ${stage.status}`);
      if (stage.duration_seconds) {
        console.log(`  소요 시간: ${stage.duration_seconds}초`);
      }
    });
  });
```

---

## 주의사항

1. **권한 확인**: 같은 회사의 워크플로우만 조회 가능합니다.
2. **실시간 업데이트**: 단계 상태는 파이프라인에서 실시간으로 업데이트됩니다.
3. **예상 시간 정확도**: 예상 완료 시간은 평균 기반 추정치이며, 실제 소요 시간과 다를 수 있습니다.
4. **에러 처리**: 단계 실패 시 `error_message` 필드에서 상세 원인을 확인할 수 있습니다.

---

## 관련 API

- [영상 제작 요청 API](../generation/VideoGenerationAPI_v3.md) - 영상 생성 요청
- [내 프로젝트 목록 API](../generation/VideoGenerationAPI_v3.md#5-내-프로젝트-목록-조회) - 프로젝트 목록 조회

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-01-22 | 초기 버전 작성 |

---

## 문의

API 관련 문의사항은 개발팀에 문의해주세요.
