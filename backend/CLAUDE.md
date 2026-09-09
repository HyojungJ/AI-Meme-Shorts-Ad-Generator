# Meme-fluencer Backend

밈 영상 자동 생성 SaaS 플랫폼의 API 서버.

## 프로젝트 개요

사용자가 캐릭터와 밈을 선택하면 AI가 시나리오를 생성하고 영상을 자동 생성하는 서비스.

```
meme-fluencer/
├── AI/          ← 밈 수집 + 시나리오 + 영상 생성 파이프라인
├── backend/     ← 현재 repo (FastAPI API 서버)
└── frontend/    ← Next.js 웹 앱
```

## 팀 역할 (5명)

| 담당 | 역할 | Repo |
|------|------|------|
| 파이프라인 | MemeAgent, Orchestrator, MLOps, 자동화, 통합테스트 | AI |
| 시나리오 | ScenarioAgent, 파인튜닝, 시나리오 검증 | AI |
| 영상 | VideoGenerator, TTS, Sora, FFmpeg, 영상 검증 | AI |
| 백엔드 | FastAPI, 인증, DB, Celery, AI 연동 | backend |
| 프론트 | Next.js, UI/UX | frontend |

### 백엔드 담당 (본 repo)
- FastAPI: 라우터 (auth, users, characters, memes, generate)
- 인증: Firebase Admin SDK, JWT 검증
- DB: 스키마 설계, 마이그레이션, Repository 패턴
- 비동기: Redis, Celery Worker, 작업 상태 관리
- AI 연동: content_pipeline 호출, S3 업로드
- API 문서: Swagger/OpenAPI

## 실행

```bash
uv run uvicorn main:app --reload
```

## 코드 스타일

### 금지
- 뻔한 docstring
- 불필요한 주석
- 과도한 에러 핸들링
- 추상화 과잉 (BaseService, AbstractFactory 등)
- Response 모델 남발 (단순 dict면 dict 써)
- 모든 엔드포인트에 로깅

### 필수
- 기존 코드 스타일 따라가기
- FastAPI 라우터는 기능별 분리
- Pydantic 모델은 필요한 필드만
- DB 쿼리는 Repository 패턴

### 예시

```python
# 하지 마
@router.get("/memes/{meme_id}", response_model=MemeResponse)
async def get_meme_by_id(
    meme_id: int,
    db: Session = Depends(get_db)
) -> MemeResponse:
    """
    주어진 ID로 밈을 조회합니다.
    """
    try:
        meme = db.query(Meme).filter(Meme.id == meme_id).first()
        if not meme:
            raise HTTPException(404, "Meme not found")
        logger.info(f"Retrieved meme {meme_id}")
        return MemeResponse.from_orm(meme)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

# 이렇게 해
@router.get("/memes/{meme_id}")
def get_meme(meme_id: int, db: Session = Depends(get_db)):
    meme = db.query(Meme).filter(Meme.id == meme_id).first()
    if not meme:
        raise HTTPException(404)
    return meme
```

## 구조

```
backend/
├── api/            # FastAPI 라우터
├── db/             # DB 연결, Repository
├── scenario/       # 시나리오 생성
└── video/          # 영상 생성 (예정)
```

## DB

- Host: 3.35.238.161:5432
- Schema: memedb
