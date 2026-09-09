# 시나리오 검수 및 승인 API v1

## 개요

영상 생성 과정에서 생성된 2개의 시나리오 후보를 조회하고, 선택/승인하거나 수정 요청하는 API입니다.

**작업 기간**: 2026-01-22  
**위치**: `scripts/scenario/v1/`

---

## 시스템 구조

```
시나리오 생성 (2개 후보)
  ↓
검수 요청 알림 발송
  ↓
고객 조회 및 검토
  ↓
선택 1: 승인 → 파이프라인 트리거
선택 2: 수정 요청 → 재생성 (최대 3회)
선택 3: 24시간 미응답 → 자동 승인
```

---

## API 엔드포인트

### 1. GET /api/videos/{job_id}/scenarios

시나리오 후보 전체 조회 (2개)

**경로 파라미터**
- `job_id` (UUID): 워크플로우 실행 ID

**응답**

```json
{
  "job_id": "uuid",
  "project_id": 123,
  "status": "pending_review",
  "scenarios": [
    {
      "script_id": 1,
      "title": "영상 제목",
      "description": "요약 설명",
      "hashtags": ["#해시태그1", "#해시태그2"],
      "total_duration": 18.5,
      "meme": {
        "meme_id": 1,
        "meme_name": "밈 이름",
        "definition": "밈 정의",
        "key_phrase": "핵심 문구"
      },
      "scenes": [
        {
          "scene_key": "intro",
          "dialogue": "대사 내용",
          "duration": 5.0,
          "visual_description": "시각적 설명"
        }
      ],
      "created_at": "2026-01-22T10:00:00Z"
    }
  ],
  "approval_deadline": "2026-01-23T10:00:00Z"
}
```

### 2. POST /api/videos/{job_id}/scenarios/{script_id}/approve

시나리오 승인 및 파이프라인 트리거

**경로 파라미터**
- `job_id` (UUID): 워크플로우 실행 ID
- `script_id` (int): 선택한 시나리오 ID

**응답**

```json
{
  "message": "시나리오가 승인되었습니다. 영상 제작을 시작합니다.",
  "script_id": 1,
  "approval_status": "approved",
  "approved_at": "2026-01-22T10:30:00Z",
  "next_stage": "audio_generation"
}
```

### 3. POST /api/videos/{job_id}/scenarios/{script_id}/revise

시나리오 수정 요청 (씬별)

**경로 파라미터**
- `job_id` (UUID): 워크플로우 실행 ID
- `script_id` (int): 수정 요청할 시나리오 ID

**요청 본문**

```json
{
  "scene_revisions": [
    {
      "scene_number": 1,
      "revision_notes": "첫 번째 씬의 배경을 더 밝게 해주세요"
    },
    {
      "scene_number": 3,
      "revision_notes": "세 번째 씬의 대사를 더 짧게 줄여주세요"
    }
  ],
  "general_notes": "전체적으로 템포를 빠르게 해주세요 (선택사항)"
}
```

**필드 설명**
- `scene_revisions` (배열, 필수): 씬별 수정 요청 목록 (최소 1개)
  - `scene_number` (int, 1-4): 수정할 씬 번호
  - `revision_notes` (string): 해당 씬의 수정 요청 내용
- `general_notes` (string, 선택): 전체 시나리오에 대한 추가 의견

**응답**

```json
{
  "script_id": 1,
  "ad_id": 123,
  "status": "revision_requested",
  "message": "2개 씬에 대한 수정이 요청되었습니다"
}
```

**제한사항**
- 최대 3회까지 수정 요청 가능
- 3회 초과 시 400 에러 반환
- `scene_number`는 1-4 범위 내여야 함
- 최소 1개 이상의 씬 수정 요청 필요

---

## 데이터베이스

### scenario_scripts 테이블 활용

```sql
-- 승인 관련 필드
approval_status VARCHAR(20) DEFAULT 'pending'
  -- 'pending': 검수 대기
  -- 'approved': 승인됨
  -- 'rejected': 거부됨
  -- 'auto_approved': 자동 승인됨

approval_requested_at TIMESTAMP  -- 검수 요청 시간
approved_at TIMESTAMP            -- 승인 시간
approved_by_account_id INT       -- 승인자 ID
```

### workflow_execution 테이블 활용

```sql
-- 상태 관리
status VARCHAR(50)
  -- 'pending_review': 시나리오 검수 대기
  -- 'approved': 승인 완료
  -- 'processing': 영상 제작 중

retry_count INT DEFAULT 0  -- 수정 요청 횟수 (최대 3)
```

---

## 자동화 및 알림

### 1. 검수 요청 알림

시나리오 생성 완료 시:
- 이메일 알림 발송
- 인앱 알림 발송
- 승인 기한 안내 (24시간)

### 2. 자동 승인 스케줄러

24시간 내 미응답 시:
- `approval_status`를 `auto_approved`로 변경
- 첫 번째 시나리오 자동 선택
- 파이프라인 자동 트리거

### 3. 수정 요청 처리

수정 요청 시:
- `retry_count` 증가
- 피드백 저장
- 시나리오 재생성 워크플로우 실행
- 3회 초과 시 실패 처리 및 알림

---

## 주요 파일

### scripts/scenario/v1/scenario_routes.py

API 엔드포인트 정의

주요 함수:
- `get_scenarios()`: 시나리오 후보 조회
- `approve_scenario()`: 시나리오 승인
- `revise_scenario()`: 수정 요청

### scripts/scenario/v1/database.py

데이터베이스 함수

주요 함수:
- `get_scenarios_by_job()`: job_id로 시나리오 조회
- `approve_scenario_by_id()`: 시나리오 승인 처리
- `reject_other_scenarios()`: 다른 후보 거부 처리
- `increment_revision_count()`: 수정 횟수 증가

---

## 테스트 방법

### 1. 시나리오 조회

```python
import requests

headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    f'http://localhost:8000/api/videos/{job_id}/scenarios',
    headers=headers
)
print(response.json())
```

### 2. 시나리오 승인

```python
response = requests.post(
    f'http://localhost:8000/api/videos/{job_id}/scenarios/{script_id}/approve',
    headers=headers
)
print(response.json())
```

### 3. 수정 요청

```python
response = requests.post(
    f'http://localhost:8000/api/videos/{job_id}/scenarios/{script_id}/revise',
    headers=headers,
    json={
        'scene_revisions': [
            {
                'scene_number': 1,
                'revision_notes': '첫 번째 씬의 배경을 더 밝게 해주세요'
            },
            {
                'scene_number': 3,
                'revision_notes': '세 번째 씬의 대사를 더 짧게 줄여주세요'
            }
        ],
        'general_notes': '전체적으로 템포를 빠르게 해주세요'
    }
)
print(response.json())
```

---

## 에러 코드

- `400`: 잘못된 요청 (최대 수정 횟수 초과 등)
- `403`: 권한 없음
- `404`: 시나리오를 찾을 수 없음
- `409`: 이미 처리된 시나리오

---

## 제한사항

- 최대 수정 요청 횟수: 3회
- 자동 승인 기한: 24시간
- 한 번 승인된 시나리오는 취소 불가
