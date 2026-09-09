# Backend 코드 리뷰 리포트

**리뷰 일시**: 2026-02-08
**리뷰 범위**: `backend/app/` 전체 (main.py, models, schemas, crud, services, api endpoints, core, db, tests)
**리뷰어**: Backend Engineer (Claude)

---

## 1. API 설계

### 현재 상태
- FastAPI 기반, `/api/v1/` 프리픽스로 버전 관리
- 16개 라우터 모듈 (auth, video, content_pipeline, admin, memes, analytics 등)
- OpenAPI/Swagger 자동 문서화 + Bearer 인증 스키마 커스터마이징

### 발견된 문제점

**`main.py:104-108` — 라우터 프리픽스 충돌 및 혼란**
- 심각도: 🟡 Warning
- `video.router`는 `/api/v1/videos`에, `content_pipeline.router`는 `/api/v1/video`에 등록됨
- `final.router`와 `scenario.router`도 모두 `/api/v1/videos`에 등록
- 같은 리소스에 대한 엔드포인트가 `/videos`와 `/video` 두 곳에 분산되어 있어 API 소비자 혼란
- **개선**: content_pipeline도 `/api/v1/videos` 하위로 통합하거나, 명확한 네이밍 규칙 수립

**`content_pipeline.py` — 파일 크기 과다 (1605줄)**
- 심각도: 🟡 Warning
- 단일 파일에 20개 이상의 엔드포인트 + 10개의 백그라운드 함수가 혼재
- 생성(generate), 미리보기(preview), 승인(approve), 수정(revise), 상태 조회(status) 등 모든 것이 하나의 파일
- **개선**: 기능별로 분리 (예: `content_generate.py`, `content_preview.py`, `content_approve.py`)

**`video.py` 엔드포인트 — 레거시 호환 파라미터 과다**
- 심각도: 🟢 Info
- `generate_video()` 함수에 `product_description`/`product_highlight`, `product_url`/`item_url`, `product_image`/`product_images` 등 중복 파라미터
- `video.py:236-251` 참조
- **개선**: API 버전 업 시 레거시 파라미터 정리, 또는 별도의 adapter 레이어 구성

**`memes.py:21-56` — Pydantic 스키마가 엔드포인트 파일에 정의됨**
- 심각도: 🟢 Info
- `MemeListItem`, `MemeListResponse`, `MemeSortRequest` 등이 `schemas/` 디렉토리 대신 엔드포인트 파일에 직접 정의
- **개선**: `app/schemas/meme.py`로 이동하여 일관성 유지

---

## 2. 데이터베이스

### 현재 상태
- SQLAlchemy ORM + PostgreSQL (psycopg2)
- `declarative_base()` 사용 (레거시 API)
- Alembic 마이그레이션 8개 버전 관리
- 모델 10개 파일, 인덱스 및 CheckConstraint 적극 활용
- GIN 인덱스 (memes.origin, scenario_scripts.scenes), 부분 인덱스 활용

### 발견된 문제점

**`db/base.py:6` — 레거시 declarative_base() 사용**
- 심각도: 🟢 Info
- `from sqlalchemy.ext.declarative import declarative_base`는 SQLAlchemy 2.0에서 deprecated
- SQLAlchemy 2.0+에서는 `from sqlalchemy.orm import DeclarativeBase` 사용 권장
- **개선**: `class Base(DeclarativeBase): pass`로 변경

**`db/session.py:11-18` — DATABASE_URL이 None일 때 크래시**
- 심각도: 🔴 Critical
- `settings.DATABASE_URL`이 None이면 `create_engine(None)`으로 앱 시작 시 크래시
- MOCK_MODE에서도 DB 엔진이 생성되려고 시도
- **개선**: MOCK_MODE일 때 엔진 생성 스킵하거나, URL 검증 추가

**`company.py:68` — mutable default 값**
- 심각도: 🟡 Warning
- `generation_metadata = Column(JSONB, default={})` — 빈 dict가 모든 인스턴스에서 공유될 수 있음
- `meme.py:21`, `meme.py:25`, `asset.py:53`, `asset.py:77`, `asset.py:100` 등 여러 곳에서 동일 패턴
- **개선**: `default=dict` (callable) 또는 `server_default=text("'{}'::jsonb")` 사용

**N+1 쿼리 가능성**
- 심각도: 🟡 Warning
- `video.py:170-205` (get_video_detail) — `ad_request.company.company_name`을 통한 lazy loading
- `admin.py:61` — company_ids를 별도 쿼리로 가져오지만, ad_request별로 company 접근할 때 N+1 발생 가능
- **개선**: `joinedload()` 또는 `selectinload()` 사용, 또는 현재 admin.py처럼 batch 쿼리 패턴 일관 적용

**CRUD 파일 내 반복적 import**
- 심각도: 🟢 Info
- `crud/video.py`에서 `from app.models.scenario import ScenarioScript`가 함수마다 반복 (411, 414, 419, 427, 429, 435, 459, 462, 478, 482행)
- **개선**: 파일 상단에서 한 번만 import

---

## 3. 에러 핸들링

### 현재 상태
- HTTPException으로 일관된 에러 응답
- CLAUDE.md 코딩 스타일에 따라 과도한 try/catch 지양
- 백그라운드 태스크에서 `_bg_safe_rollback()` 패턴으로 상태 복구

### 발견된 문제점

**`content_pipeline.py:86-99` — 백그라운드 에러 복구 로직의 triple-nested try/except**
- 심각도: 🟡 Warning
- `_bg_safe_rollback()`: rollback -> update_ad_status(fallback) -> 실패 시 다시 update_ad_status('failed') -> 다시 실패 시 rollback
- 복잡하지만 의도적 설계 (분산 시스템의 상태 복구). 다만 모든 백그라운드 함수에서 수동으로 호출해야 함
- **개선**: 데코레이터 또는 컨텍스트 매니저로 패턴 추출

**`video.py:538` — bare except 사용**
- 심각도: 🟡 Warning
- `except: pass` — 어떤 예외가 발생해도 무시. 실패한 상태 업데이트를 디버깅할 수 없음
- **개선**: 최소한 `except Exception: logger.error(...)` 으로 변경

**`admin.py:300-307` — YouTube 업로드 실패 시 에러를 삼킴**
- 심각도: 🟡 Warning
- `upload_status = 2`로 설정하지만 사용자에게 정확한 에러 메시지 미전달
- 그리고 `post.upload_status`는 모델에 정의되지 않은 필드 (`AdminVideoPost`에 `upload_status` 컬럼 없음)
- `video.youtube_upload_status`도 `Video` 모델에 없는 필드
- **개선**: 존재하지 않는 컬럼 참조 제거, 에러 메시지를 `post.error_message`에 저장

**`video.py:688-696` — 에러 메시지에 내부 정보 노출**
- 심각도: 🟡 Warning
- `detail=f"AI 파이프라인 통신 오류: {str(e)}"` — 내부 스택 트레이스가 클라이언트에 노출될 수 있음
- `video.py:694`, `video.py:750`, `video.py:814`, `video.py:977` 등 여러 곳
- **개선**: 로그에 상세 에러, 클라이언트에는 일반적 메시지

---

## 4. 인증/인가

### 현재 상태
- JWT (python-jose) 기반 Access/Refresh Token 인증
- bcrypt 비밀번호 해싱
- Fernet 대칭 암호화로 OAuth 토큰 저장
- `get_current_user()` 함수로 인증 미들웨어 구현

### 발견된 문제점

**`security.py:40,56` — datetime.utcnow() deprecated**
- 심각도: 🟢 Info
- Python 3.12+에서 `datetime.utcnow()`는 deprecated
- **개선**: `datetime.now(timezone.utc)` 사용 (전체 코드베이스 적용 필요)

**`security.py:84-97` — get_current_user가 FastAPI Depends가 아닌 수동 호출**
- 심각도: 🟡 Warning
- `get_current_user(request)`를 각 엔드포인트에서 수동 호출 (`await get_current_user(request)`)
- FastAPI의 `Depends(get_current_user)` 패턴을 사용하면 OpenAPI 문서에 자동 반영되고, 코드가 간결해짐
- **개선**: `current_user: dict = Depends(get_current_user)` 패턴으로 통일

**`auth.py:420-431` — 개발 모드 토큰 노출**
- 심각도: 🔴 Critical
- 비밀번호 재설정 토큰이 MOCK_MODE에서 응답에 포함됨
- MOCK_MODE가 프로덕션에서 켜져 있으면 보안 위험
- `auth.py:425-431` 참조
- **개선**: MOCK_MODE가 아닌 DEBUG 모드로 제한, 또는 프로덕션 환경 변수 검증 강화

**`security.py:121-127` — JWT_SECRET_KEY를 Fernet 키로 재사용**
- 심각도: 🟡 Warning
- `_get_encryption_key()`가 JWT_SECRET_KEY를 SHA256 해시하여 Fernet 키로 사용
- 키 분리 원칙 위반 (하나의 시크릿이 여러 목적으로 사용됨)
- **개선**: OAuth 토큰 암호화용 별도 키 (ENCRYPTION_KEY) 환경 변수 추가

**권한 체크 불일치**
- 심각도: 🟡 Warning
- `content_pipeline.py:540` — admin이면 company_id 무관하게 접근 허용
- `video.py:133-135` — 동일 패턴
- 하지만 `video.py:558` — `character.company_id != user_info["company_id"]`로만 체크 (admin 무시)
- **개선**: 통일된 권한 체크 유틸리티 함수로 추출

**Refresh Token 갱신 시 Token Rotation 미적용**
- 심각도: 🟡 Warning
- `auth.py:289-343` — `/refresh` 엔드포인트에서 새 Access Token만 발급, Refresh Token은 재사용
- Refresh Token 탈취 시 무제한 재사용 가능
- **개선**: Refresh Token도 매번 새로 발급 (Token Rotation)

---

## 5. 서비스 레이어

### 현재 상태
- AI Pipeline: Mock, Direct, HTTP 3가지 모드 지원
- S3 서비스: presigned URL 생성, 파일 업로드/삭제
- YouTube: OAuth 인증 + 영상 업로드 + 분석 데이터 수집

### 발견된 문제점

**`ai_pipeline_direct.py:23-24` — sys.path 조작**
- 심각도: 🟡 Warning
- `sys.path.insert(0, str(_ai_path))` — AI 패키지 경로를 런타임에 추가
- 패키지 간 import 충돌 가능성
- **개선**: pyproject.toml의 `tool.uv.sources`로 이미 경로 설정됨. sys.path 조작이 정말 필요한지 재검토

**`content_pipeline.py:56-62` — asyncio.new_event_loop() 안티패턴**
- 심각도: 🔴 Critical
- `_run_async()`가 매 호출마다 새 이벤트 루프를 생성하고 닫음
- BackgroundTasks 내에서 호출되므로 FastAPI의 이벤트 루프와 충돌 가능
- CPU 오버헤드 및 리소스 누수 위험
- **개선**: `asyncio.run()` 사용하거나, AI 함수를 동기 함수로 변경하거나, `anyio.from_thread.run()` 사용

**`admin.py:217-297` — YouTube 업로드 로직이 엔드포인트에 직접 구현**
- 심각도: 🟡 Warning
- S3 다운로드 -> 임시 파일 -> YouTube 업로드 -> 정리 로직이 약 80줄에 걸쳐 엔드포인트 핸들러에 인라인
- boto3 클라이언트를 매번 새로 생성 (s3_service.py의 기존 클라이언트 미사용)
- S3 URL 파싱 로직이 `s3_service.py:133-147`의 `_parse_s3_url()`과 중복
- **개선**: `services/youtube_service.py`로 추출

**`s3_service.py:17-27` — 모듈 로드 시 S3 클라이언트 즉시 초기화**
- 심각도: 🟢 Info
- 모듈 import 시점에 boto3 클라이언트가 생성됨
- AWS 자격 증명이 없으면 warning만 출력하고 `s3_client = None`
- 테스트 환경에서 불필요한 AWS 연결 시도
- **개선**: lazy initialization 패턴 적용

---

## 6. 테스트

### 현재 상태
- pytest + pytest-asyncio
- conftest.py에서 MOCK_MODE 환경 변수 설정
- FastAPI TestClient + DB mock 주입
- test_integration_mock.py: 6개 테스트 클래스 (약 460줄)
- test_client_signatures.py, test_database.py, test_analytics_api.py 존재

### 발견된 문제점

**테스트 커버리지 부족**
- 심각도: 🔴 Critical
- 인증 엔드포인트 (auth.py) 테스트 없음 — 회원가입, 로그인, 토큰 갱신, 비밀번호 재설정 미테스트
- 밈 목록 (memes.py) 테스트 없음
- Admin 엔드포인트 테스트 없음
- SSE 스트리밍 테스트 없음
- CRUD 레이어 단위 테스트 없음
- **개선**: 최소한 인증 플로우와 핵심 비즈니스 로직(광고 생성 -> 검수 -> 완료)의 E2E 테스트 추가

**`conftest.py:13` — 하드코딩된 DATABASE_URL**
- 심각도: 🟢 Info
- `DATABASE_URL = "sqlite:///test.db"` — SQLite 사용하지만 PostgreSQL 전용 기능(JSONB, ARRAY, GIN 인덱스)이 모델에 사용됨
- 실제 DB 연결 테스트 불가
- **개선**: testcontainers-python으로 PostgreSQL 컨테이너 사용 또는 별도 테스트 DB 환경 구성

**테스트와 실제 코드 간 불일치**
- 심각도: 🟡 Warning
- `test_integration_mock.py:174` — `assert data["status"] == "regenerated"` 이지만 실제 `content_pipeline.py:985`에서는 `status="regenerating"` 반환 (bg task 이므로)
- 테스트가 Mock 모드의 동기 응답을 기대하지만, 실제 코드는 백그라운드 태스크를 사용
- **개선**: 백그라운드 태스크 동작을 고려한 테스트 시나리오 재설계

---

## 7. 코드 품질

### 현재 상태
- CLAUDE.md 스타일 가이드 준수 (간결한 코드, 불필요한 docstring/주석 최소화)
- Pydantic v2 모델 사용
- 기능별 디렉토리 구조 (models, schemas, crud, services, api)

### 발견된 문제점

**`config.py:10-68` — Pydantic BaseSettings 미사용**
- 심각도: 🟡 Warning
- `class Settings`가 일반 클래스로, `os.getenv()`를 직접 호출
- 타입 검증 없음 (`DATABASE_URL`이 None이어도 에러 없이 진행)
- `.env` 파일 로딩을 `load_dotenv()`로 별도 수행
- pyproject.toml에 `pydantic-settings`가 이미 의존성에 포함됨
- **개선**: `from pydantic_settings import BaseSettings`로 변경하면 자동 .env 로딩 + 타입 검증

**`content_pipeline.py` — 백그라운드 함수의 DB 세션 패턴 중복**
- 심각도: 🟡 Warning
- `_bg_generate_character`, `_bg_generate_voice`, `_bg_revise_scenario` 등 10개 함수가 모두 동일 패턴:
  ```python
  db = SessionLocal()
  try:
      ...
  except Exception:
      _bg_safe_rollback(db, ...)
  finally:
      db.close()
  ```
- **개선**: 컨텍스트 매니저로 추출

**`video.py:62-84` — OpenAI 직접 호출**
- 심각도: 🟡 Warning
- `_rewrite_voice_description()`이 OpenAI API를 직접 호출
- AI 파이프라인 서비스 레이어를 우회
- 엔드포인트 파일에 LLM 로직이 인라인
- **개선**: AI 서비스 레이어로 이동

**`video.py:138-139, 41-49` — print 디버그 + 조건부 import**
- 심각도: 🟢 Info
- `print(f"[VIDEO DETAIL] ad_id={ad_id}...")` — 프로덕션 코드에 print문
- MOCK_MODE에 따른 조건부 import (`scripts.generation.s3_handler_mock`)
- **개선**: logger 사용, mock import를 테스트 전용으로 분리

**`auth.py:52-73, 130-174` — Mock 모드 코드가 프로덕션 엔드포인트에 인라인**
- 심각도: 🟡 Warning
- signup, login 함수 내부에 `if settings.MOCK_MODE:` 블록이 약 20줄씩 차지
- 프로덕션 코드 가독성 저하
- **개선**: Mock 전용 서비스 레이어로 분리하거나, FastAPI dependency override 활용

**`main.py:14-30` — 조건부 import의 에러 처리**
- 심각도: 🟢 Info
- character_profiles import 실패 시 `character_profiles = None`으로 폴백
- 앱 시작 시 필수 모듈이 아닌 선택적 모듈의 실패를 정상적으로 처리
- 다만 에러 메시지에 이모지(`✗`) 사용은 로그 파서에 비친화적

**타입 힌팅 부분 적용**
- 심각도: 🟢 Info
- CRUD 함수 반환 타입이 대부분 미명시 (예: `def get_ad_request_by_id(db, ad_id)` → 반환 `Optional[AdRequest]` 미표기)
- **개선**: CLAUDE.md에서 불필요한 docstring을 금지하므로, 최소한 반환 타입만 추가

---

## 8. 기타 사항

### `pyproject.toml` — 프로젝트명 불일치
- 심각도: 🟢 Info
- `name = "meme-data"`이지만 실제 프로젝트는 "meme-fluencer"
- 크롤링, 데이터 처리, AI 모델 등 backend와 무관한 의존성이 대량 포함 (selenium, pandas, chromadb, langchain 등)
- **개선**: backend 전용 의존성과 AI 의존성 분리 검토

### Alembic 마이그레이션
- 심각도: 🟢 Info
- 8개 마이그레이션 파일이 순차적으로 관리됨
- 파일명에 날짜 포함으로 추적 용이
- 다만 모델 변경(content_generating status 등)이 마이그레이션에 잘 반영되어 있음

### SSE 엔드포인트
- 심각도: 🟡 Warning
- `sse.py:99` — JWT 토큰을 query parameter로 전달 (EventSource API 제약)
- URL에 토큰이 노출되어 서버 로그, 브라우저 히스토리에 기록될 수 있음
- **개선**: 단기 유효(수분) SSE 전용 토큰 발급 엔드포인트 추가

---

## 요약

| 카테고리 | 상태 | 주요 이슈 |
|---------|------|----------|
| API 설계 | 양호 | 라우터 프리픽스 혼란, content_pipeline 파일 크기 과다 |
| 데이터베이스 | 양호 | mutable default, DATABASE_URL None 크래시 |
| 에러 핸들링 | 보통 | bare except, 존재하지 않는 모델 필드 참조 |
| 인증/인가 | 보통 | 개발 토큰 노출, Refresh Token Rotation 미적용, 권한 체크 불일치 |
| 서비스 레이어 | 보통 | asyncio.new_event_loop 안티패턴, YouTube 로직 인라인 |
| 테스트 | 미흡 | 인증/밈/Admin 테스트 없음, 테스트-코드 불일치 |
| 코드 품질 | 양호 | CLAUDE.md 스타일 준수, 다만 Mock 코드 인라인 등 |

### 우선 순위 높은 개선 항목 (Critical)
1. `db/session.py` — DATABASE_URL None 방어 로직 추가
2. `content_pipeline.py:56-62` — `_run_async()` 이벤트 루프 안티패턴 개선
3. `auth.py:425-431` — 프로덕션 환경에서 재설정 토큰 노출 방지
4. 테스트 커버리지 확대 (인증 플로우, 핵심 비즈니스 로직)
5. `admin.py:300-307` — 존재하지 않는 모델 필드 참조 수정
