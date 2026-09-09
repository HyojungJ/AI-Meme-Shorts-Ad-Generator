# 데이터베이스 마이그레이션 가이드

## 개요
이 문서는 Alembic을 사용한 데이터베이스 마이그레이션 과정과 환경 설정 검증 방법을 설명합니다.

## 마이그레이션 정보

### 마이그레이션 버전
- **Revision ID**: `dc27a30675c3`
- **생성 날짜**: 2026-01-25 22:48:26
- **설명**: initial_schema_with_all_tables

### 데이터베이스 정보
- **DBMS**: PostgreSQL 14.20
- **총 테이블 수**: 24개 (alembic_version 포함)
- **스키마 기준**: `docs/COMPLETE_SCHEMA.sql`

## 마이그레이션 실행 과정

### 1. 사전 준비

#### 필수 패키지 설치
```bash
uv sync
```

설치되는 주요 패키지:
- `alembic>=1.13.0` - 데이터베이스 마이그레이션 도구
- `psycopg2-binary>=2.9.9` - PostgreSQL 드라이버
- `sqlalchemy>=2.0.0` - ORM

#### 환경변수 확인
`.env` 파일에 다음 변수가 설정되어 있어야 합니다:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### 2. 마이그레이션 파일 생성

```bash
uv run alembic revision --autogenerate -m "initial_schema_with_all_tables"
```

**생성된 파일**:
```
alembic/versions/20260125_2248_dc27a30675c3_initial_schema_with_all_tables.py
```

### 3. 마이그레이션 적용

```bash
uv run alembic upgrade head
```

**실행 결과**:
```
INFO  [alembic.runtime.migration] Running upgrade  -> dc27a30675c3, initial_schema_with_all_tables
```

### 4. 마이그레이션 상태 확인

```bash
uv run alembic current
```

**출력**:
```
dc27a30675c3 (head)
```

## 마이그레이션 변경 사항

### 인덱스 이름 변경
기존 데이터베이스의 인덱스 이름을 SQLAlchemy 모델의 명명 규칙에 맞게 변경했습니다.

#### 변경 패턴
- `idx_*` → `ix_*` (SQLAlchemy 기본 명명 규칙)
- `video_projects` → `ad_requests` (테이블명 변경 반영)

#### 주요 변경 사항

**ad_requests 테이블**:
```
idx_ad_requests_account       → ix_ad_requests_account_id
idx_ad_requests_company       → ix_ad_requests_company_id
idx_ad_requests_status        → ix_ad_requests_status
idx_video_projects_character  → ix_ad_requests_character_id
idx_video_projects_created    → ix_ad_requests_created_at
idx_video_projects_user       → ix_ad_requests_account_id
```

**videos 테이블**:
```
idx_videos_company  → ix_videos_company_id
idx_videos_created  → ix_videos_created_at
idx_videos_project  → ix_videos_ad_id
idx_videos_status   → ix_videos_status
```

**workflow_execution 테이블**:
```
idx_workflow_created     → ix_workflow_execution_created_at
idx_workflow_project_id  → ix_workflow_execution_ad_id
idx_workflow_status      → ix_workflow_execution_status
```

**memes 테이블**:
```
idx_memes_name   → ix_memes_meme_name (unique 제약조건 유지)
idx_memes_status → ix_memes_status
```

**performance_metrics 테이블**:
```
idx_performance_metrics_daily_unique  → 표현식 변경 (date(captured_at) → captured_at)
idx_performance_metrics_captured      → ix_performance_metrics_captured_at
idx_performance_metrics_post          → ix_performance_metrics_post_id
idx_performance_metrics_snapshot      → ix_performance_metrics_snapshot_type
idx_performance_metrics_video         → ix_performance_metrics_video_id
```

### 제약조건 변경

**prompt_versions 테이블**:
```sql
-- UNIQUE 제약조건을 인덱스로 변경
DROP CONSTRAINT uq_prompt_name_version
CREATE INDEX uq_prompt_name_version ON prompt_versions (prompt_name, version) UNIQUE
```

**memes 테이블**:
```sql
-- UNIQUE 제약조건을 인덱스로 변경
DROP CONSTRAINT memes_meme_name_key
CREATE INDEX ix_memes_meme_name ON memes (meme_name) UNIQUE
```

## 환경 설정 검증

### 필수 환경변수 목록

#### 애플리케이션 설정
```bash
APP_NAME=Meme Influencer API
APP_VERSION=4.0.0
DEBUG=True  # 개발 환경에서만 True
```

#### 데이터베이스
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

#### JWT 인증
```bash
JWT_SECRET_KEY=your-secret-key-here-use-strong-random-string
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### AWS S3
```bash
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=your-s3-bucket-name
```

#### OpenAI
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

#### Google OAuth (YouTube 자동 포스팅용)
```bash
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### 기타 API (선택)
```bash
PINECONE_API_KEY=your-pinecone-api-key-here
LANGSMITH_API_KEY=your-langsmith-api-key-here
HUGGINGFACEHUB_API_TOKEN=your-huggingface-token-here
TAVILY_API_KEY=your-tavily-api-key-here
```

#### 모드 설정
```bash
MOCK_MODE=False  # True로 설정 시 외부 API 호출 없이 Mock 데이터 사용
```

### 환경변수 검증 방법

Python 스크립트로 환경변수 설정 상태를 확인할 수 있습니다:

```python
from app.core.config import settings

# 필수 환경변수 확인
print(f"DATABASE_URL: {'✓ 설정됨' if settings.DATABASE_URL else '✗ 미설정'}")
print(f"JWT_SECRET_KEY: {'✓ 설정됨' if settings.JWT_SECRET_KEY else '✗ 미설정'}")
print(f"AWS_ACCESS_KEY_ID: {'✓ 설정됨' if settings.AWS_ACCESS_KEY_ID else '✗ 미설정'}")
print(f"OPENAI_API_KEY: {'✓ 설정됨' if settings.OPENAI_API_KEY else '✗ 미설정'}")
```

## 데이터베이스 연결 검증

### 연결 테스트

```python
from sqlalchemy import text
from app.db.session import engine

with engine.connect() as conn:
    # PostgreSQL 버전 확인
    result = conn.execute(text("SELECT version()"))
    print(result.scalar())
    
    # 테이블 목록 확인
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    print(f"총 {len(tables)}개 테이블")
    
    # Alembic 버전 확인
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    print(f"마이그레이션 버전: {result.scalar()}")
```

### 예상 출력
```
PostgreSQL 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1) on x86_64-pc-linux-gnu
총 24개 테이블
마이그레이션 버전: dc27a30675c3
```

## 테이블 목록

마이그레이션 후 생성된 테이블:

1. `accounts` - 계정 정보
2. `ad_requests` - 광고 영상 제작 요청
3. `admin_video_posts` - Admin YouTube 포스팅 기록
4. `admin_youtube_channels` - Admin YouTube 채널 정보
5. `admins` - Admin 계정
6. `alembic_version` - Alembic 마이그레이션 버전
7. `clients` - Client 계정
8. `companies` - 회사 정보
9. `company_characters` - 회사별 캐릭터
10. `company_members` - 회사 멤버
11. `image_generations` - 이미지 생성 기록
12. `meme_examples` - 밈 예시
13. `memes` - 밈 정보
14. `performance_metrics` - 성과 지표
15. `prompt_usage_logs` - 프롬프트 사용 로그
16. `prompt_versions` - 프롬프트 버전
17. `retry_queue` - 재시도 큐
18. `scenario_scripts` - 시나리오 스크립트
19. `scene_assets` - 씬 에셋
20. `scene_videos` - 씬 영상
21. `videos` - 최종 영상
22. `voice_generations` - 음성 생성 기록
23. `workflow_execution` - 워크플로우 실행 기록
24. `workflow_stages` - 워크플로우 단계

## API 서버 실행

### 개발 서버 실행
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 서버 실행
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API 문서 접근
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 헬스 체크
```bash
curl http://localhost:8000/health
```

**응답**:
```json
{
  "status": "healthy",
  "version": "4.0.0"
}
```

## 등록된 API 엔드포인트

### 인증 (Authentication)
- `POST /api/v1/auth/signup` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/logout` - 로그아웃
- `POST /api/v1/auth/refresh` - 토큰 갱신
- `GET /api/v1/auth/me` - 내 정보 조회
- `POST /api/v1/auth/password-reset/request` - 비밀번호 재설정 요청
- `POST /api/v1/auth/password-reset/confirm` - 비밀번호 재설정 확인

### 영상 생성 (Video Generation)
- `POST /api/v1/videos/generate` - 영상 생성 요청
- `GET /api/v1/videos/character/{character_id}` - 캐릭터 조회
- `POST /api/v1/videos/character/{character_id}/approve` - 캐릭터 승인
- `GET /api/v1/videos/characters` - 캐릭터 목록
- `GET /api/v1/videos/my-projects` - 내 프로젝트 목록

### 상태 추적 (Status Tracking)
- `GET /api/v1/status/{execution_id}` - 워크플로우 상태 조회
- `GET /api/v1/status/{execution_id}/detail` - 워크플로우 상세 조회
- `GET /api/v1/status/my-projects` - 내 프로젝트 상태 목록

### 영상 다운로드 (Video Download)
- `GET /api/v1/videos/{video_id}/download` - 영상 다운로드
- `POST /api/v1/videos/{video_id}/approve` - 영상 승인
- `POST /api/v1/videos/{video_id}/reject` - 영상 거부

### 시나리오 검수 (Scenario Review)
- `GET /api/v1/videos/{job_id}/scenarios` - 시나리오 목록
- `POST /api/v1/videos/{job_id}/scenarios/{script_id}/approve` - 시나리오 승인
- `POST /api/v1/videos/{job_id}/scenarios/{script_id}/revise` - 시나리오 수정 요청

### Admin 관리 (Admin Management)
- `GET /api/v1/admin/videos/all` - 전체 영상 목록
- `GET /api/v1/admin/videos/pending` - 대기 중인 영상
- `POST /api/v1/admin/videos/{video_id}/publish` - 영상 게시
- `POST /api/v1/admin/videos/{video_id}/hold` - 영상 보류
- `GET /api/v1/admin/workflows` - 워크플로우 목록
- `GET /api/v1/admin/workflows/{execution_id}/logs` - 워크플로우 로그
- `POST /api/v1/admin/workflows/{execution_id}/retry` - 워크플로우 재시도
- `POST /api/v1/admin/workflows/{execution_id}/cancel` - 워크플로우 취소

### 성과 분석 (Analytics)
- `GET /api/v1/admin/analytics/dashboard` - 대시보드
- `GET /api/v1/admin/analytics/memes` - 밈 분석
- `GET /api/v1/admin/analytics/categories` - 카테고리 분석
- `GET /api/v1/admin/analytics/trends` - 트렌드 분석
- `POST /api/v1/admin/analytics/export` - 데이터 내보내기
- `GET /api/v1/admin/analytics/export/{export_id}` - 내보내기 결과 조회
- `GET /api/v1/admin/analytics/companies` - 회사별 분석

### 사용자 관리 (User Management)
- `GET /api/v1/admin/users` - 사용자 목록
- `GET /api/v1/admin/users/{account_id}` - 사용자 상세
- `PATCH /api/v1/admin/users/{account_id}/status` - 사용자 상태 변경
- `PATCH /api/v1/admin/users/{account_id}/role` - 사용자 권한 변경
- `GET /api/v1/admin/users/{account_id}/activity-logs` - 사용자 활동 로그
- `DELETE /api/v1/admin/users/{account_id}` - 사용자 삭제
- `GET /api/v1/admin/users/statistics/summary` - 사용자 통계
- `POST /api/v1/admin/users/bulk-action` - 일괄 작업

### 비용 관리 (Cost Management)
- `GET /api/v1/admin/costs/companies` - 회사별 비용
- `GET /api/v1/admin/costs/statistics` - 비용 통계
- `GET /api/v1/admin/costs/details` - 비용 상세
- `GET /api/v1/admin/costs/optimization-suggestions` - 최적화 제안

### 품질 관리 (Quality Management)
- `GET /api/v1/admin/quality/low-score-videos` - 낮은 점수 영상
- `GET /api/v1/admin/quality/validation-failures` - 검증 실패 목록
- `POST /api/v1/admin/quality/validation/{validation_id}/retry` - 검증 재시도
- `POST /api/v1/admin/quality/validation/{validation_id}/approve` - 검증 승인
- `GET /api/v1/admin/quality/trends` - 품질 트렌드

## 트러블슈팅

### 문제 1: psycopg2 모듈을 찾을 수 없음
```
ModuleNotFoundError: No module named 'psycopg2'
```

**해결 방법**:
```bash
uv sync
```

### 문제 2: 데이터베이스 연결 실패
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**확인 사항**:
1. `.env` 파일의 `DATABASE_URL` 확인
2. 데이터베이스 서버 실행 상태 확인
3. 네트워크 연결 확인
4. 방화벽 설정 확인

### 문제 3: 마이그레이션 충돌
```
alembic.util.exc.CommandError: Target database is not up to date
```

**해결 방법**:
```bash
# 현재 버전 확인
uv run alembic current

# 최신 버전으로 업그레이드
uv run alembic upgrade head

# 또는 특정 버전으로 다운그레이드 후 재시도
uv run alembic downgrade base
uv run alembic upgrade head
```

### 문제 4: 환경변수 로드 실패
```
ValidationError: field required
```

**해결 방법**:
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `.env.example`을 참고하여 누락된 변수 추가
3. 환경변수 이름 오타 확인

## 참고 문서

- **스키마 정의**: `docs/COMPLETE_SCHEMA.sql`
- **Alembic 설정**: `alembic.ini`
- **Alembic 환경**: `alembic/env.py`
- **마이그레이션 파일**: `alembic/versions/`
- **모델 정의**: `app/models/`
- **데이터베이스 설정**: `app/db/session.py`
- **환경 설정**: `app/core/config.py`

## 주의사항

1. **프로덕션 환경에서는 반드시 백업 후 마이그레이션 실행**
2. **DEBUG 모드는 개발 환경에서만 True로 설정**
3. **JWT_SECRET_KEY는 강력한 랜덤 문자열 사용**
4. **데이터베이스 비밀번호는 절대 코드에 하드코딩하지 않기**
5. **Google OAuth는 YouTube 자동 포스팅용이며, 사용자 로그인에는 사용하지 않음**
6. **Admin과 Client 모두 비밀번호 기반 인증 사용**

## 다음 단계

1. ✅ 데이터베이스 마이그레이션 완료
2. ✅ 환경변수 설정 완료
3. ✅ API 서버 실행 테스트 완료
4. 🔄 실제 데이터로 API 엔드포인트 테스트
5. 🔄 프론트엔드 연동
6. 🔄 배포 준비

