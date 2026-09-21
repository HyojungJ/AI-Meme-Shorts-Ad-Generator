# 🎬 AI 기반 밈 숏폼 광고 영상 자동 생성 플랫폼
한국 인터넷 밈을 활용한 **광고 숏폼 영상을 AI로 자동 생성하는 SaaS 플랫폼**.
기업이 제품 정보만 입력하면 밈 추천 → 캐릭터·음성 생성 → 시나리오 작성 → 영상 생성 → YouTube 게시까지 전 과정을 자동화한다. 수일 걸리던 Z세대 타깃 숏폼 광고 제작을 약 5분으로 단축하는 것이 목표.

> **이 저장소에 대하여**
> 밈 수집 파이프라인, 콘텐츠 생성 AI, 백엔드 API, 프론트엔드, LLM 파인튜닝까지 — 원래 여러 저장소로 흩어져 있던 대형 프로젝트를 **하나의 레포로 통합하고 구조를 재정리한 포트폴리오 버전**이다. 각 서비스의 역할과 연결 관계를 이해하기 쉽도록 폴더 단위로 재배치하고, 대용량 산출물·비밀 파일을 걷어냈다.

---

## 📌 핵심 기능

| 기능 | 설명 |
|------|------|
| **밈 수집** | LangGraph Multi-Agent가 나무위키·네이버·YouTube를 크롤링, Gemini Vision으로 밈 영상 분석, 품질 검증(Reflexion)까지 자동화 |
| **밈 추천** | BGE-m3-ko 임베딩 기반 제품↔밈 유사도 매칭 |
| **캐릭터 생성** | GPT-4o-mini 프롬프트 추천 → Gemini 2.0 Flash 이미지 생성 |
| **음성 생성** | ElevenLabs Voice Design / Qwen TTS |
| **시나리오 생성** | GPT-4o (+ 파인튜닝 모델)로 5단 구조 광고 대본 작성 |
| **영상 생성** | ComfyUI + LTX Video (RunPod Serverless) → FFmpeg 크로스페이드 병합 |
| **AI 검수** | GPT-4o Vision 이미지 검수 + Gemini 2.5 Pro 영상 검수 (자동 재시도) |
| **사용자 검수** | 캐릭터·음성·시나리오·영상 단계별 승인/거부/수정 요청 |
| **성과 분석** | YouTube Analytics 연동, 밈별·회사별 성과 대시보드 (Recharts) |

전체 워크플로우 약 4~5분 소요, 2단계 검수(Asset 생성 → Content 생성) 구조.

---

## 🗂️ 저장소 구조

```
AI-Meme-Shorts-Ad-Generator
│
├─ backend/            # FastAPI 백엔드 (REST API, 인증, DB, AI 파이프라인 오케스트레이션)
│   ├─ app/
│   │   ├─ api/        #   엔드포인트 (auth, memes, scenario, final, analytics, sse ...)
│   │   ├─ core/       #   설정, 보안(JWT), 예외 처리
│   │   ├─ crud/       #   DB 액세스 계층
│   │   ├─ db/         #   세션, 커넥션
│   │   ├─ models/     #   SQLAlchemy 2.0 ORM (24개 테이블)
│   │   ├─ schemas/    #   Pydantic 스키마
│   │   └─ services/   #   비즈니스 로직 + AI 파이프라인 클라이언트
│   ├─ alembic/        #   DB 마이그레이션
│   └─ Dockerfile, docker-compose.yml
│
├─ ai/                 # AI 파이프라인 (LangGraph 기반)
│   ├─ meme_collector/ #   밈 수집 Multi-Agent (Supervisor/Researcher/Analyzer/Verifier)
│   ├─ content_pipeline/  # 콘텐츠 생성 (image · voice · scenario · video)
│   ├─ finetune/       #   파인튜닝 관련 스크립트
│   └─ notebooks/      #   실험 노트북
│
├─ frontend/           # Next.js 14 (App Router) 웹 앱
│   └─ src/
│       ├─ app/        #   라우트 (auth, dashboard/user, admin ...)
│       ├─ components/ #   UI 컴포넌트
│       ├─ contexts/ hooks/ lib/ types/
│
├─ data-pipeline/      # 밈 크롤링 + 데이터셋 구축 (파인튜닝 데이터 전처리)
│   ├─ scripts/        #   crawling · preprocessing · analysis · agent
│   └─ data/           #   raw / processed 데이터셋
│
├─ content-generator/  # LLM 텍스트 파인튜닝 (시나리오·페르소나 특화 모델)
│   └─ backend/        #   text_finetuning · rag · vectorDB
│
└─ docs/               # 설계·배포·테스트 문서 + 기획 문서(planning/)
```

> **포폴 정리 원칙**: 실행용 대용량(가상환경, `node_modules`, 파인튜닝 체크포인트 약 18GB, 생성 미디어)과 비밀 파일(`.env`, SSH 키, OAuth 토큰)은 `.gitignore`로 제외했다. 각 서비스의 필요한 환경 변수는 `*/.env.example` 참고. 이 정리로 저장소 용량이 **약 37GB → 100MB 대**로 줄었다.

---

## 🧩 시스템 아키텍처

```
[Frontend (Next.js / Vercel)]
        │  REST + Polling(3s)
        ▼
[Backend (FastAPI / EC2 Docker)] ──── JWT 인증, 워크플로우 상태 관리
        │
        ├─ AI Pipeline Client (Direct / HTTP / Mock 3중 구조)
        │        │
        │        ▼
        │   [AI (LangGraph)]
        │     ├─ 밈 수집 Multi-Agent
        │     └─ 콘텐츠 생성 (캐릭터 → 음성 → 시나리오 → 영상)
        │              │
        │              ├─ Gemini / GPT-4o / ElevenLabs / Qwen TTS
        │              └─ ComfyUI + LTX Video (RunPod Serverless)
        │
        ├─ PostgreSQL (AWS Lightsail, 24 tables)
        └─ AWS S3 + CloudFront (이미지·음성·영상 스토리지/CDN)

[data-pipeline] 밈 크롤링·데이터셋 → [content-generator] LLM 파인튜닝 → 시나리오 모델
```

---

## 🛠️ 기술 스택

**Frontend** — Next.js 14, React 18, TypeScript, TailwindCSS, Recharts, react-hook-form
**Backend** — FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic, JWT(python-jose), Uvicorn, boto3
**AI/ML** — LangGraph, LangChain, OpenAI GPT-4o / 4o-mini / Vision, Gemini 2.0 Flash / 2.5 Pro, ElevenLabs, Qwen TTS, BGE-m3-ko, ComfyUI + LTX Video, 파인튜닝(EEVE / A.x-4.0)
**Infra** — AWS EC2(Docker) / Lightsail PostgreSQL / S3 / CloudFront, Vercel, RunPod Serverless, uv

---

## 🚀 실행 (개발 환경)

각 서비스는 독립적으로 실행된다. 환경 변수는 각 폴더의 `.env.example`을 복사해 `.env`로 채운다.

```bash
# Backend (FastAPI)
cd backend
uv sync                         # 또는 pip install -e .
cp .env.example .env            # 값 채우기
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (Next.js)
cd frontend
npm install
npm run dev

# AI 파이프라인은 backend에서 Direct 모드로 호출되며,
# 밈 수집·콘텐츠 생성 실험은 ai/notebooks 참고
```

> 벡터 DB, 파인튜닝 모델, 생성 미디어 등 대용량 산출물은 저장소에 포함되지 않는다(재생성 또는 외부 스토리지 사용).

---

## 📚 문서

`docs/` 에 상세 문서가 있다.
- `Project_Summary.md` — 프로젝트 전체 종합 정리
- `Application_Report.md` — 애플리케이션 리포트
- `Deployment_Architecture.md`, `EC2_Docker_Deploy_Guide.md` — 배포 아키텍처·가이드
- `Test_Plan.md`, `Test_Results_Report.md` — 테스트 계획·결과
- `planning/` — 초기 기획·주간 리포트

---

## 💭 회고

밈 수집부터 영상 생성, 웹 서비스, 배포까지 하나의 파이프라인으로 엮인 대형 시스템을 다루면서 배운 것:

- **AI를 서비스로 만드는 일의 복잡함** — 모델 성능만이 아니라, 각 생성 단계(캐릭터·음성·시나리오·영상)를 어떤 순서로 연결하고, 실패 시 어떻게 재시도·검수할지 설계하는 것이 품질을 좌우했다.
- **오케스트레이션과 상태 관리** — 4~5분짜리 비동기 워크플로우를 백엔드가 추적하고, 프론트가 폴링으로 진행률을 보여주는 구조를 이해하며 "긴 작업을 사용자 경험으로 감싸는 법"을 익혔다.
- **AI 검수의 필요성** — 생성 결과를 GPT-4o Vision / Gemini로 자동 검증하고 재시도하는 2단계 검수가, 자동화 파이프라인의 신뢰도를 만드는 핵심이었다.
- **데이터의 상류부터 하류까지** — 크롤링(data-pipeline) → 파인튜닝(content-generator) → 서비스(backend/ai)로 이어지는 데이터 흐름 전체를 정리하며, 흩어진 저장소를 하나의 일관된 시스템으로 재구성했다.

### 정리하면서 개선한 점
- 8개로 흩어져 있던 저장소(각각 별도 `.git`)를 **하나의 포폴 레포로 통합**하고, 의미 기반 폴더(`backend` / `ai` / `frontend` / `data-pipeline` / `content-generator` / `docs`)로 재배치
- 통합 과정에서 갈라져 있던 중복 코드 중 **최신·완전한 버전을 정본으로 채택**
- 약 18GB의 파인튜닝 체크포인트, 각종 가상환경·`node_modules`, 비밀 파일을 `.gitignore`로 분리해 저장소를 코드 중심으로 정리 (**37GB → 100MB 대**)
