# Meme Influencer API

밈 기반 광고 영상 자동 생성 플랫폼 백엔드 API

## 버전 정보
- **마이그레이션 버전**: dc27a30675c3
- **데이터베이스**: PostgreSQL 14.20
- **총 테이블 수**: 24개

## 프로젝트 구조

```
backend/
├── app/                      # 메인 애플리케이션
│   ├── main.py              # FastAPI 엔트리포인트 (60+ routes)
│   ├── core/                # 핵심 설정
│   │   ├── config.py        # 환경 변수 및 전역 설정
│   │   └── security.py      # JWT, 비밀번호 해싱
│   ├── db/                  # 데이터베이스
│   │   ├── base.py          # SQLAlchemy Base
│   │   └── session.py       # DB 연결 및 세션
│   ├── models/              # SQLAlchemy 모델 (24개 테이블)
│   │   ├── account.py       # Account, Client, Admin
│   │   ├── company.py       # Company, CompanyMember, CompanyCharacter
│   │   ├── meme.py          # Meme, MemeExample
│   │   ├── ad_request.py    # AdRequest
│   │   ├── scenario.py      # ScenarioScript
│   │   ├── asset.py         # SceneAsset, VoiceGeneration, ImageGeneration, SceneVideo
│   │   ├── video.py         # Video
│   │   ├── workflow.py      # WorkflowExecution, WorkflowStage
│   │   ├── youtube.py       # AdminYoutubeChannel, AdminVideoPost
│   │   └── analytics.py     # PerformanceMetric, PromptVersion, PromptUsageLog, RetryQueue
│   ├── schemas/             # Pydantic 스키마
│   │   ├── auth.py          # 인증 관련
│   │   ├── users.py         # 사용자 관리
│   │   ├── video.py         # 영상 관련
│   │   ├── scenario.py      # 시나리오 관련
│   │   ├── admin.py         # Admin 관련
│   │   ├── analytics.py     # 성과 분석
│   │   ├── costs.py         # 비용 관리
│   │   └── quality.py       # 품질 관리
│   ├── crud/                # DB 작업 로직
│   │   ├── auth.py          # 인증 CRUD (Client, Admin 비밀번호 로그인)
│   │   ├── users.py         # 사용자 관리 CRUD
│   │   ├── video.py         # 영상 CRUD
│   │   ├── scenario.py      # 시나리오 CRUD
│   │   ├── status.py        # 상태 추적 CRUD
│   │   ├── final.py         # 영상 다운로드 CRUD
│   │   ├── admin.py         # Admin CRUD
│   │   ├── analytics.py     # 성과 분석 CRUD
│   │   ├── costs.py         # 비용 관리 CRUD
│   │   └── quality.py       # 품질 관리 CRUD
│   └── api/v1/endpoints/    # API v1 엔드포인트
│       ├── auth.py          # 인증 API (회원가입, 로그인, 토큰 관리)
│       ├── users.py         # 사용자 관리 API
│       ├── video.py         # 영상 생성 API
│       ├── status.py        # 상태 추적 API
│       ├── scenario.py      # 시나리오 검수 API
│       ├── final.py         # 영상 다운로드 API
│       ├── admin.py         # Admin 관리 API
│       ├── analytics.py     # 성과 분석 API
│       ├── costs.py         # 비용 관리 API
│       └── quality.py       # 품질 관리 API
│
├── alembic/                 # 데이터베이스 마이그레이션
│   ├── versions/            # 마이그레이션 파일
│   │   └── 20260125_2248_dc27a30675c3_initial_schema_with_all_tables.py
│   ├── env.py              # Alembic 환경 설정
│   └── script.py.mako      # 마이그레이션 템플릿
│
├── docs/                    # API 문서
│   ├── auth/               # 인증 API 문서
│   ├── generation/         # 영상 생성 API 문서
│   ├── scenario/           # 시나리오 API 문서
│   ├── status/             # 상태 추적 API 문서
│   ├── final/              # 영상 다운로드 API 문서
│   ├── admin/              # Admin API 문서
│   ├── db_env/             # 데이터베이스 및 환경 설정 문서
│   │   └── DATABASE_MIGRATION_GUIDE.md
│   ├── COMPLETE_SCHEMA.sql # 전체 데이터베이스 스키마 (단일 진실 공급원)
│   └── API_SPECIFICATION.md
│
├── scripts/                 # 레거시 백업 (사용 안 함)
│   └── README_LEGACY.md    # 레거시 설명
│
├── .env                     # 환경 변수
├── .env.example            # 환경 변수 예시
├── .gitignore
├── alembic.ini             # Alembic 설정
├── pyproject.toml          # 프로젝트 설정
├── uv.lock
└── README.md
```

## 실행 방법

### 1. 패키지 설치

```bash
# uv를 사용한 의존성 설치
uv sync
```

### 2. 환경 변수 설정

`.env.example` 파일을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

`.env` 파일에 실제 값 입력:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@host:port/database
DB_URL=postgresql://user:password@host:port/database

# JWT 인증
JWT_SECRET_KEY=your-secret-key-here-use-strong-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=your-s3-bucket-name

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Google OAuth (YouTube 자동 포스팅용, 사용자 로그인 아님)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# 기타
DEBUG=False
MOCK_MODE=false
```

### 3. 데이터베이스 마이그레이션

```bash
# 마이그레이션 파일 생성 (이미 생성됨)
uv run alembic revision --autogenerate -m "migration_name"

# 마이그레이션 적용
uv run alembic upgrade head

# 현재 마이그레이션 버전 확인
uv run alembic current
```

### 4. 서버 실행

```bash
# 개발 모드 (권장)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Windows 환경**: `127.0.0.1` 또는 `localhost` 사용 가능

### 5. API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **헬스 체크**: http://localhost:8000/health

## API 엔드포인트

### 인증 (Auth) - `/api/v1/auth`
- `POST /signup` - 회원가입 (Client, Admin 모두 비밀번호 기반)
- `POST /login` - 로그인
- `POST /logout` - 로그아웃
- `POST /refresh` - 토큰 갱신
- `GET /me` - 현재 사용자 정보
- `POST /password-reset/request` - 비밀번호 재설정 요청
- `POST /password-reset/confirm` - 비밀번호 재설정 확인

### 영상 생성 (Video) - `/api/v1/videos`
- `POST /generate` - 영상 제작 요청
- `GET /character/{character_id}` - 캐릭터 미리보기
- `POST /character/{character_id}/approve` - 캐릭터 승인/거부
- `GET /characters` - 회사 캐릭터 목록
- `GET /my-projects` - 내 프로젝트 목록

### 상태 추적 (Status) - `/api/v1/status`
- `GET /{execution_id}` - 워크플로우 기본 상태
- `GET /{execution_id}/detail` - 워크플로우 상세 상태
- `GET /my-projects` - 내 프로젝트 상태 목록

### 시나리오 검수 (Scenario) - `/api/v1/videos`
- `GET /{job_id}/scenarios` - 시나리오 후보 조회
- `POST /{job_id}/scenarios/{script_id}/approve` - 시나리오 승인
- `POST /{job_id}/scenarios/{script_id}/revise` - 시나리오 수정 요청

### 영상 다운로드 (Final) - `/api/v1/videos`
- `GET /{video_id}/download` - 영상 다운로드 링크
- `POST /{video_id}/approve` - 영상 승인
- `POST /{video_id}/reject` - 영상 거부

### Admin 관리 - `/api/v1/admin`
- `GET /videos/all` - 전체 영상 목록
- `GET /videos/pending` - 게시 대기 영상
- `POST /videos/{video_id}/publish` - YouTube 게시 승인
- `POST /videos/{video_id}/hold` - 게시 보류
- `GET /workflows` - 워크플로우 목록
- `GET /workflows/{execution_id}/logs` - 워크플로우 상세 로그
- `POST /workflows/{execution_id}/retry` - 워크플로우 재시도
- `POST /workflows/{execution_id}/cancel` - 워크플로우 취소

### 성과 분석 (Analytics) - `/api/v1/admin/analytics`
- `GET /dashboard` - 대시보드
- `GET /memes` - 밈 분석
- `GET /categories` - 카테고리 분석
- `GET /trends` - 트렌드 분석
- `POST /export` - 데이터 내보내기
- `GET /export/{export_id}` - 내보내기 결과 조회
- `GET /companies` - 회사별 분석

### 사용자 관리 (Users) - `/api/v1/admin/users`
- `GET /` - 사용자 목록
- `GET /{account_id}` - 사용자 상세
- `PATCH /{account_id}/status` - 사용자 상태 변경
- `PATCH /{account_id}/role` - 사용자 권한 변경
- `GET /{account_id}/activity-logs` - 사용자 활동 로그
- `DELETE /{account_id}` - 사용자 삭제
- `GET /statistics/summary` - 사용자 통계
- `POST /bulk-action` - 일괄 작업

### 비용 관리 (Costs) - `/api/v1/admin/costs`
- `GET /companies` - 회사별 비용
- `GET /statistics` - 비용 통계
- `GET /details` - 비용 상세
- `GET /optimization-suggestions` - 최적화 제안

### 품질 관리 (Quality) - `/api/v1/admin/quality`
- `GET /low-score-videos` - 낮은 점수 영상
- `GET /validation-failures` - 검증 실패 목록
- `POST /validation/{validation_id}/retry` - 검증 재시도
- `POST /validation/{validation_id}/approve` - 검증 승인
- `GET /trends` - 품질 트렌드

## 데이터베이스 스키마

### 테이블 목록 (24개)

**계정 관리**:
- `accounts` - 통합 계정 정보
- `clients` - Client 계정 (비밀번호 로그인)
- `admins` - Admin 계정 (비밀번호 로그인)

**회사 관리**:
- `companies` - 회사 정보
- `company_members` - 회사 멤버
- `company_characters` - 회사별 캐릭터

**밈 관리**:
- `memes` - 밈 정보
- `meme_examples` - 밈 예시

**광고 제작**:
- `ad_requests` - 광고 영상 제작 요청
- `scenario_scripts` - 시나리오 스크립트
- `scene_assets` - 씬 에셋
- `voice_generations` - 음성 생성 기록
- `image_generations` - 이미지 생성 기록
- `scene_videos` - 씬 영상
- `videos` - 최종 영상

**워크플로우**:
- `workflow_execution` - 워크플로우 실행 기록
- `workflow_stages` - 워크플로우 단계
- `retry_queue` - 재시도 큐

**Admin 기능**:
- `admin_youtube_channels` - Admin YouTube 채널 (OAuth 정보)
- `admin_video_posts` - Admin YouTube 포스팅 기록

**분석 및 로깅**:
- `performance_metrics` - 성과 지표
- `prompt_versions` - 프롬프트 버전
- `prompt_usage_logs` - 프롬프트 사용 로그

**시스템**:
- `alembic_version` - 마이그레이션 버전

### 스키마 문서
전체 DDL 및 제약조건은 `docs/COMPLETE_SCHEMA.sql` 참조

### 마이그레이션 가이드
데이터베이스 마이그레이션 및 환경 설정은 `docs/db_env/DATABASE_MIGRATION_GUIDE.md` 참조

## 아키텍처

### 레이어 분리

1. **API Layer** (`app/api/v1/endpoints/`)
   - FastAPI 라우터 정의
   - 요청 검증 및 응답 반환
   - JWT 인증 처리

2. **Schema Layer** (`app/schemas/`)
   - Pydantic 모델로 요청/응답 검증
   - 타입 안정성 보장

3. **CRUD Layer** (`app/crud/`)
   - 데이터베이스 작업 로직
   - 비즈니스 로직 분리

4. **Model Layer** (`app/models/`)
   - SQLAlchemy ORM 모델
   - 데이터베이스 스키마 정의

5. **Core Layer** (`app/core/`)
   - 설정 관리 (환경변수)
   - 보안 (JWT, 비밀번호 해싱)

### 인증 방식

- **Client**: 비밀번호 기반 로그인 (JWT)
- **Admin**: 비밀번호 기반 로그인 (JWT)
- **Google OAuth**: YouTube 자동 포스팅 전용 (사용자 로그인 아님)

### 주요 특징

- FastAPI 표준 구조
- API 버전 관리 (`/api/v1/`)
- 도메인별 라우터 분리
- Alembic 마이그레이션
- JWT 기반 인증
- PostgreSQL 24개 테이블
- 워크플로우 상태 추적
- Admin 관리 기능 (성과 분석, 비용 관리, 품질 관리)

## 개발 상태

### 완료된 작업
- ✅ 데이터베이스 스키마 정의 (24개 테이블)
- ✅ SQLAlchemy 모델 완전 구현
- ✅ Alembic 마이그레이션 설정 및 적용
- ✅ 인증 시스템 (Client, Admin 비밀번호 로그인)
- ✅ 영상 생성 API
- ✅ 상태 추적 API
- ✅ 시나리오 검수 API
- ✅ 영상 다운로드 API
- ✅ Admin 관리 API
- ✅ 성과 분석 API
- ✅ 사용자 관리 API
- ✅ 비용 관리 API
- ✅ 품질 관리 API
- ✅ API 문서 (Swagger UI, ReDoc)
- ✅ 환경 설정 및 검증

### 진행 중인 작업
- 🔄 실제 워크플로우 로직 구현
- 🔄 외부 API 연동 (OpenAI, AWS S3 등)
- 🔄 YouTube 자동 포스팅 기능
- 🔄 프론트엔드 연동

### 향후 계획
- 📋 단위 테스트 작성
- 📋 통합 테스트 작성
- 📋 성능 최적화
- 📋 배포 자동화

## 개발 가이드

## 개발 가이드

### 새 기능 추가 방법

1. **모델 정의** (`app/models/`)
   ```python
   from sqlalchemy import Column, Integer, String
   from app.db.base import Base
   
   class NewModel(Base):
       __tablename__ = "new_table"
       id = Column(Integer, primary_key=True)
       name = Column(String(100))
   ```

2. **스키마 정의** (`app/schemas/`)
   ```python
   from pydantic import BaseModel
   
   class NewModelCreate(BaseModel):
       name: str
   
   class NewModelResponse(BaseModel):
       id: int
       name: str
   ```

3. **CRUD 함수** (`app/crud/`)
   ```python
   from sqlalchemy.orm import Session
   from app.models.new_model import NewModel
   
   def create_new_model(db: Session, name: str):
       model = NewModel(name=name)
       db.add(model)
       db.commit()
       return model
   ```

4. **API 엔드포인트** (`app/api/v1/endpoints/`)
   ```python
   from fastapi import APIRouter, Depends
   from sqlalchemy.orm import Session
   from app.db.session import get_db
   
   router = APIRouter()
   
   @router.post("/new")
   def create_new(name: str, db: Session = Depends(get_db)):
       return create_new_model(db, name)
   ```

5. **라우터 등록** (`app/main.py`)
   ```python
   from app.api.v1.endpoints import new_endpoint
   
   app.include_router(
       new_endpoint.router,
       prefix="/api/v1/new",
       tags=["New Feature"]
   )
   ```

6. **마이그레이션 생성 및 적용**
   ```bash
   uv run alembic revision --autogenerate -m "add new_table"
   uv run alembic upgrade head
   ```

### 코드 스타일

- Python 3.11+ 사용
- Type hints 필수
- Pydantic 모델로 검증
- SQLAlchemy 2.0 스타일
- FastAPI 의존성 주입 활용

### 환경변수 추가

1. `.env.example`에 예시 추가
2. `app/core/config.py`의 `Settings` 클래스에 필드 추가
3. `docs/db_env/DATABASE_MIGRATION_GUIDE.md` 업데이트


## 문서

- **API 명세**: `docs/API_SPECIFICATION.md`
- **데이터베이스 스키마**: `docs/COMPLETE_SCHEMA.sql`
- **마이그레이션 가이드**: `docs/db_env/DATABASE_MIGRATION_GUIDE.md`
- **인증 API**: `docs/auth/`
- **영상 생성 API**: `docs/generation/`
- **시나리오 API**: `docs/scenario/`
- **상태 추적 API**: `docs/status/`
- **영상 다운로드 API**: `docs/final/`
- **Admin API**: `docs/admin/`

## 기술 스택

- **Framework**: FastAPI 0.128.0+
- **Database**: PostgreSQL 14.20
- **ORM**: SQLAlchemy 2.0+
- **Migration**: Alembic 1.13.0+
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Validation**: Pydantic 2.5+
- **Package Manager**: uv
- **Python**: 3.11+