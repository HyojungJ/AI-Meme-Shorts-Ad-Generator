# API 변경 사항 (2026-01-26)

## 1. 회원가입 API - 같은 회사명 처리 개선

**변경 내용:**
- 같은 회사명으로 회원가입 시 새로운 Company를 생성하지 않고 기존 Company 재사용
- `get_or_create_company()` 함수 추가

**영향:**
- 같은 회사의 여러 사용자가 동일한 `company_id`를 공유

**파일:**
- `app/crud/auth.py`

---

## 2. 회원가입 API - role 필드 추가

**변경 내용:**
- 회원가입 시 `role` 필드 입력 받음 (manager/member)
- 기본값: "manager"

**요청 예시:**
```json
POST /api/v1/auth/signup
{
  "email": "user@example.com",
  "password": "password123",
  "company_name": "테스트회사",
  "member_name": "홍길동",
  "department": "마케팅팀",
  "role": "manager"
}
```

**파일:**
- `app/schemas/auth.py`
- `app/api/v1/endpoints/auth.py`
- `app/crud/auth.py`

---

## 3. 프로필 수정 API - 회사명 수정 기능 추가

**변경 내용:**
- 회원정보 수정 시 회사명도 수정 가능

**요청 예시:**
```json
PATCH /api/v1/auth/me
{
  "member_name": "홍길동",
  "department": "마케팅팀",
  "company_name": "새로운회사명"
}
```

**파일:**
- `app/schemas/auth.py` - `UpdateUserRequest`에 `company_name` 필드 추가
- `app/crud/auth.py` - `update_user_profile()` 함수에 회사명 수정 로직 추가
- `app/api/v1/endpoints/auth.py`

---

## 4. 내 프로젝트 목록 조회 API - 중복 제거

**변경 내용:**
- `/api/v1/videos/my-projects` 삭제 (중복)
- `/api/v1/status/my-projects`만 사용

**엔드포인트:**
```
GET /api/v1/status/my-projects?offset=0&limit=10&status=processing
```

**쿼리 파라미터:**
- `offset`: 시작 위치 (기본값: 0)
- `limit`: 조회 개수 (기본값: 10)
- `status`: 상태 필터 (선택)

**주의:**
- ❌ `page`, `per_page` 파라미터 사용 불가
- ✅ `offset`, `limit` 파라미터 사용

**파일:**
- `app/api/v1/endpoints/video.py` - 중복 엔드포인트 삭제
- `app/api/v1/endpoints/status.py` - `error_message` 필드 추가

---

## 5. 시나리오 검수 방식 변경

**변경 내용:**
- 2개 시나리오 후보 선택 → 1개 시나리오의 씬별 수정 요청 방식으로 변경

**시나리오 조회:**
```
GET /api/v1/videos/{job_id}/scenarios
```

**응답 예시:**
```json
{
  "job_id": "uuid",
  "scenario": {
    "script_id": 1,
    "ad_id": 5,
    "title": "시나리오 제목",
    "description": "설명",
    "scenes": [
      {
        "scene_number": 1,
        "scene_key": "intro",
        "text": "인트로 텍스트",
        "duration": 3.0
      },
      {
        "scene_number": 2,
        "scene_key": "main",
        "text": "메인 텍스트",
        "duration": 10.0
      }
    ],
    "total_duration": 15.0,
    "approval_status": "pending",
    "generation_type": "initial",
    "review_result": null,
    "used_templates": ["template_funny"],
    "created_at": "2026-01-26T..."
  }
}
```

**시나리오 승인:**
```
POST /api/v1/videos/{job_id}/scenarios/{script_id}/approve
```

**시나리오 수정 요청 (씬별):**
```
POST /api/v1/videos/{job_id}/scenarios/{script_id}/revise
{
  "scene_revisions": [
    {
      "scene_number": 1,
      "revision_notes": "더 재미있게 수정해주세요"
    },
    {
      "scene_number": 3,
      "revision_notes": "짧게 줄여주세요"
    }
  ],
  "general_notes": "전체적으로 밝은 톤으로"
}
```

**파일:**
- `app/schemas/scenario.py` - `ScenarioResponse`, `SceneInfo` 추가
- `app/crud/scenario.py` - `get_scenario_by_job()`, `request_scenario_revision()` 수정
- `app/api/v1/endpoints/scenario.py`

---

## 6. scenario_scripts 테이블 - 새 컬럼 추가

**추가된 컬럼:**
1. `generation_type` (VARCHAR(50)): 초안/재생성 구분
   - 'initial': 처음 생성된 시나리오 (기본값)
   - 'regenerated': 재생성된 시나리오

2. `review_result` (JSONB): 사용자 피드백 저장
   ```json
   {
     "latest": {
       "scene_revisions": [...],
       "general_notes": "...",
       "requested_at": "2026-01-26T..."
     },
     "history": [...]
   }
   ```

3. `used_templates` (TEXT[]): 사용된 템플릿 목록

**마이그레이션:**
```bash
alembic revision --autogenerate -m "add_scenario_fields"
alembic upgrade head
```

**파일:**
- `app/models/scenario.py`
- `app/schemas/scenario.py`
- `app/crud/scenario.py` - `create_scenario()` 함수 추가
- `alembic/versions/20260126_1438_e02bb8c83b9d_add_scenario_fields.py`

---

## 7. 품질 관리 API - 실제 DB 테이블 사용

**변경 내용:**
- Mock 구현에서 실제 `prompt_usage_logs` 테이블 사용으로 변경
- `validation_id` = `log_id`
- 품질 검증 실패 = `success = false` 또는 `quality_score < 3.0`

**품질 검증 실패 목록 조회:**
```
GET /api/v1/admin/quality/validation-failures?offset=0&limit=20
```

**품질 검증 재시도:**
```
POST /api/v1/admin/quality/validation-failures/{validation_id}/retry
{
  "force_reprocess": true,
  "skip_checks": ["check1"],
  "note": "재시도 사유"
}
```

**품질 검증 승인:**
```
POST /api/v1/admin/quality/validation-failures/{validation_id}/approve
{
  "approved_by": "admin@example.com",
  "reason": "수동 승인 사유",
  "override_checks": ["check1", "check2"]
}
```

**파일:**
- `app/crud/quality.py`
- `app/models/analytics.py`

---

## 8. Admin API 수정 사항

### 8.1 영상 목록 조회 - 필수 필드 추가
- `company_name`, `duration_seconds`, `file_size_mb` 필드 추가

### 8.2 YouTube 게시 승인 - 필드명 수정
- `title` → `yt_title`
- `description` → `yt_description`
- `scheduled_at` 문자열을 datetime으로 파싱

### 8.3 게시 보류 API 구현
```
POST /api/v1/admin/videos/{video_id}/hold
```

### 8.4 워크플로우 상세 로그 API 구현
```
GET /api/v1/admin/workflows/{execution_id}/logs
```

### 8.5 사용자 삭제 API 수정
- `'deleted': True` → `'status': 'deleted'`

**파일:**
- `app/api/v1/endpoints/admin.py`
- `app/crud/users.py`

---

## 프론트엔드 연동 시 주의사항

### 1. 환경 변수 설정
```env
# .env.local
NEXT_PUBLIC_MOCK_MODE=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. API 엔드포인트 변경
- ❌ `/api/v1/videos/my-projects`
- ✅ `/api/v1/status/my-projects`

### 3. 쿼리 파라미터
- ❌ `?page=1&per_page=10`
- ✅ `?offset=0&limit=10`

### 4. 영상 생성 API
- `Content-Type: multipart/form-data`
- `product_images` 필드 필수 (파일 업로드)

### 5. CORS 설정
- 이미 `localhost:3000` 허용됨
- 추가 설정 불필요

---

## 테스트 데이터

### prompt_usage_logs 테스트 데이터
```sql
-- prompt_versions 추가
INSERT INTO prompt_versions (prompt_name, version, content, is_active)
VALUES 
('scenario_generation', 'v1.0', '시나리오 생성 프롬프트', true),
('video_generation', 'v1.0', '영상 생성 프롬프트', true);

-- prompt_usage_logs 추가 (품질 검증 실패 케이스)
INSERT INTO prompt_usage_logs (version_id, ad_id, latency_ms, token_usage, quality_score, success, error_log, created_at)
VALUES 
(1, 5, 5000, '{"prompt_tokens": 100, "completion_tokens": 50}', NULL, false, 'AI 파이프라인 타임아웃', NOW() - INTERVAL '2 hours'),
(1, 5, 2000, '{"prompt_tokens": 150, "completion_tokens": 80}', 2.5, true, NULL, NOW() - INTERVAL '30 minutes');
```

---

## 마이그레이션 이력

1. `20260125_2248_dc27a30675c3_initial_schema_with_all_tables.py` - 초기 스키마
2. `20260126_1438_e02bb8c83b9d_add_scenario_fields.py` - 시나리오 필드 추가

---

## 다음 작업 예정

1. AI 파이프라인 연동 (`AI_PIPELINE_URL` 설정 필요)
2. S3 파일 업로드 구현
3. 이메일 발송 기능 구현 (비밀번호 재설정)
4. 실시간 워크플로우 상태 업데이트 (WebSocket)
