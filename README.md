# 🎬 AI 기반 밈 숏폼 광고 영상 자동 생성 플랫폼

기업이 제품 정보만 입력하면 밈 추천부터 캐릭터·음성·시나리오·영상 생성과 YouTube 게시까지,
**광고 숏폼 제작 전 과정을 약 5분 안에 자동화하는 AI SaaS 플랫폼**입니다.

> **프로젝트 성격**
> AI 파이프라인, 백엔드 아키텍처, 프론트엔드와 데이터·파인튜닝 파이프라인을 하나로 연결한 개인 포트폴리오 프로젝트입니다.
> 여러 저장소로 나뉘어 있던 결과물을 하나의 시스템으로 통합하고, 최신 코드를 정본으로 선별해 구조를 리팩토링했습니다.

---

## 📌 한눈에 보기

| 항목 | 내용 |
|------|------|
| 목표 | 수일 걸리던 Z세대 타깃 숏폼 광고 제작을 약 5분으로 단축 |
| 입력 | 기업·제품 정보와 생성 옵션 |
| 출력 | 밈 기반 캐릭터, 음성, 시나리오, 숏폼 영상, YouTube 게시 결과 |
| AI 워크플로우 | 밈 수집·추천 → 캐릭터 → 음성 → 시나리오 → 영상 → 검수·게시 |
| 백엔드 | FastAPI, SQLAlchemy, PostgreSQL, 비동기 작업 상태 관리 |
| 인프라 | AWS EC2·Lightsail·S3·CloudFront, RunPod Serverless, Vercel |
| 핵심 성과 | 제작 시간 수일 → 약 5분, 8개 저장소 → 단일 레포, 37GB → 100MB대 |
| 사용 기술 | Python, LangGraph, FastAPI, SQLAlchemy, PostgreSQL, AWS, Next.js, Gemini, GPT-4o, ElevenLabs, Qwen TTS, ComfyUI/LTX Video, BGE-m3-ko |

---

## 🗂️ 저장소 구조

```
AI-Meme-Shorts-Ad-Generator
│
├─ backend/               # FastAPI 백엔드·AI 워크플로우 오케스트레이션
│   ├─ app/
│   │   ├─ api/           #   인증·밈·시나리오·영상·분석 API
│   │   ├─ core/          #   설정·JWT 보안·예외 처리
│   │   ├─ crud/          #   DB 접근 계층
│   │   ├─ db/            #   PostgreSQL 세션·커넥션
│   │   ├─ models/        #   SQLAlchemy ORM 모델 (24개 테이블)
│   │   ├─ schemas/       #   Pydantic 요청·응답 스키마
│   │   └─ services/      #   비즈니스 로직·AI Pipeline Client
│   ├─ alembic/           #   DB 마이그레이션
│   └─ Dockerfile, docker-compose.yml
│
├─ ai/                    # LangGraph 기반 AI 파이프라인
│   ├─ meme_collector/    #   Multi-Agent 밈 수집·분석·검증
│   ├─ content_pipeline/  #   image · voice · scenario · video 생성
│   ├─ finetune/          #   파인튜닝 관련 코드
│   └─ notebooks/         #   AI 실험 노트북
│
├─ frontend/              # Next.js 14 웹 애플리케이션
│   └─ src/
│       ├─ app/           #   인증·사용자·관리자·분석 화면
│       ├─ components/    #   UI 컴포넌트
│       └─ contexts/ hooks/ lib/ types/
│
├─ data-pipeline/         # 밈 크롤링·데이터셋 구축·전처리
│   ├─ scripts/           #   crawling · preprocessing · analysis · agent
│   └─ data/              #   raw / processed 데이터
│
├─ content-generator/     # 시나리오·페르소나 LLM 파인튜닝
│   └─ backend/           #   text_finetuning · rag · vectorDB
│
└─ docs/                  # 설계·배포·테스트·초기 기획 문서
```

> 가상환경, `node_modules`, 생성 미디어, 약 18GB의 파인튜닝 체크포인트와 `.env`·OAuth 토큰 등 비밀 파일은 저장소에서 제외했습니다.
> 각 서비스의 환경 변수는 해당 폴더의 `.env.example`을 참고할 수 있습니다.

---

## 🧩 시스템 아키텍처

```
[Frontend — Next.js / Vercel]
          │  REST API + 3초 Polling
          ▼
[Backend — FastAPI / AWS EC2 Docker]
          │  JWT 인증 · 진행률 · 승인 상태 · 비용/품질 관리
          │
          ├─ AI Pipeline Client (Direct / HTTP / Mock)
          │        │
          │        ▼
          │   [AI — LangGraph]
          │     ├─ Meme Collector Multi-Agent
          │     └─ Content Pipeline
          │          ├─ Character — GPT-4o-mini + Gemini
          │          ├─ Voice     — ElevenLabs / Qwen TTS
          │          ├─ Scenario  — GPT-4o / 파인튜닝 모델
          │          └─ Video     — ComfyUI + LTX Video + FFmpeg
          │
          ├─ PostgreSQL — AWS Lightsail
          └─ Object Storage/CDN — AWS S3 + CloudFront

[data-pipeline] 크롤링·학습 데이터 구축
          │
          ▼
[content-generator] LLM 파인튜닝
          │
          ▼
[AI Scenario Pipeline]
```

---

## 🛠️ 기술 스택

- **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS, Recharts
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic, Pydantic, JWT, Uvicorn
- **AI / Orchestration**: LangGraph, LangChain, GPT-4o, GPT-4o-mini, Gemini 2.0 Flash, Gemini 2.5 Pro
- **Voice / Video**: ElevenLabs, Qwen TTS, ComfyUI, LTX Video, FFmpeg
- **Recommendation / Fine-tuning**: `dragonkue/BGE-m3-ko`, EEVE, A.x-4.0
- **Database / Storage**: PostgreSQL, AWS S3
- **Infrastructure**: AWS EC2, Lightsail, CloudFront, RunPod Serverless, Docker, Vercel

---

## 1. 개요

기업이 제품 정보만 입력하면 **밈 추천 → 캐릭터·음성 생성 → 시나리오 작성 → 영상 생성 → YouTube 게시**까지
전 과정을 약 5분 안에 자동으로 끝내는 AI SaaS를 만들었습니다.

기존에 수일씩 걸리던 Z세대 타깃 숏폼 광고 제작 과정을 단축하면서도,
AI 자동 검수와 사용자 승인 절차를 함께 적용해 생성 속도와 품질을 동시에 관리하는 것이 목표였습니다.

---

## 2. 담당 역할과 문제 해결 과정

### 1) 밈 수집 및 추천 파이프라인

LangGraph 기반 Multi-Agent 구조를 설계해 웹의 분산된 밈 정보를 자동으로 수집·분석하도록 했습니다.

- `Supervisor`가 전체 조사 계획과 에이전트 작업을 조정
- `Text Researcher`, `Media Researcher`, `Usage Researcher`가 나무위키·네이버·YouTube에서 정보 수집
- `Analyzer`가 밈의 의미, 사용 맥락과 동작 프롬프트를 구조화
- `Verifier`가 Reflexion 패턴으로 결과를 검증하고 기준 미달 시 재조사
- Gemini Vision으로 밈 영상을 분석해 동작 특성과 `motion_prompt` 추출
- 제품과 밈을 연결할 때 `BGE-m3-ko` 임베딩과 코사인 유사도로 추천

### 2) 콘텐츠 생성 오케스트레이션

서로 다른 생성 모델과 외부 API를 하나의 순차 워크플로우로 연결했습니다.

1. GPT-4o-mini로 제품 특성에 맞는 캐릭터 프롬프트 추천
2. Gemini 이미지 모델로 캐릭터 생성
3. ElevenLabs Voice Design 또는 Qwen TTS로 캐릭터 음성 생성
4. GPT-4o와 파인튜닝 모델로 5단 구조 광고 시나리오 작성
5. 캐릭터·제품 이미지를 합성해 씬 입력 이미지 생성
6. ComfyUI + LTX Video를 RunPod Serverless에서 실행해 씬별 영상 생성
7. FFmpeg 크로스페이드로 씬 영상과 오디오 병합
8. 완성 영상을 저장하고 YouTube 게시 단계로 전달

### 3) 자동·수동 검수 체계

생성 결과의 신뢰도를 높이기 위해 자동 검수와 사용자 검수를 함께 설계했습니다.

- **이미지 자동 검수**: GPT-4o Vision으로 원본 요구사항과 생성·수정 이미지를 비교
- **영상 자동 검수**: Gemini 2.5 Pro로 영상의 품질과 시나리오 반영 여부 검증
- 기준 미달 결과는 최대 재시도 횟수 내에서 자동 재생성
- 캐릭터·음성·시나리오·영상 단계별 사용자 승인, 거부, 수정 요청 지원
- 전체 워크플로우를 **Asset 생성 → Content 생성**의 두 단계로 분리해 검수 시점과 책임을 명확화

### 4) 비동기 백엔드 구축

FastAPI와 PostgreSQL을 중심으로 긴 미디어 생성 작업을 안정적으로 관리하는 백엔드를 구성했습니다.

- SQLAlchemy ORM 기반 24개 테이블과 Alembic 마이그레이션 관리
- AWS Lightsail PostgreSQL에 사용자·광고 요청·생성 자산·워크플로우 상태 저장
- 이미지·음성·영상을 S3에 저장하고 CloudFront CDN으로 제공
- AI Pipeline Client를 Direct / HTTP / Mock 세 가지 모드로 분리해 개발·배포 환경에 대응
- 4~5분 걸리는 생성 작업을 백그라운드로 실행하고 단계별 진행률과 승인 상태 관리
- Next.js 프론트엔드가 3초 간격으로 상태를 폴링해 진행 상황과 상태 전환을 사용자에게 표시

### 5) 레포지토리 통합 및 경량화

원래 여러 팀 저장소에 분산돼 있던 코드를 하나의 개인 포트폴리오 레포로 통합했습니다.

- 각각 별도 `.git`을 가진 8개 저장소를 하나로 통합
- `backend` / `ai` / `frontend` / `data-pipeline` / `content-generator` / `docs`로 의미 기반 재배치
- 중복·분기된 코드 중 프로덕션 하드닝과 최신 기능이 반영된 버전을 정본으로 채택
- 약 18GB의 파인튜닝 체크포인트, 가상환경, `node_modules`, 빌드 캐시와 비밀 파일 제거
- 통합 `.gitignore`와 서비스별 `.env.example`로 공개 저장소의 안전성 확보
- 전체 저장소 용량을 **약 37GB에서 100MB대**로 축소

---

## 3. 성과

- 숏폼 광고 제작 시간을 **수일에서 약 5분**으로 단축하는 End-to-End AI 생성 워크플로우 구축
- 밈 수집·추천부터 캐릭터·음성·시나리오·영상 생성과 YouTube 게시까지 자동화
- AI 자동 검수와 사용자 검수를 결합한 **2단계 Asset → Content 워크플로우** 완성
- 4~5분 장기 작업의 진행 상태를 백엔드에서 관리하고 프론트엔드에서 실시간에 가깝게 제공
- 8개로 흩어진 저장소를 재현 가능한 단일 구조로 통합하고 **37GB → 100MB대**로 경량화

---

## 4. 핵심 기능

| 기능 | 구현 내용 |
|------|-----------|
| 밈 수집 | LangGraph Multi-Agent + 웹·YouTube 리서치 + Reflexion 검증 |
| 밈 추천 | BGE-m3-ko 임베딩 기반 제품·밈 유사도 계산 |
| 캐릭터 | GPT-4o-mini 프롬프트 추천 + Gemini 이미지 생성 |
| 음성 | ElevenLabs Voice Design / Qwen TTS 대안 지원 |
| 시나리오 | GPT-4o 및 파인튜닝 모델 기반 5단 광고 대본 |
| 영상 | ComfyUI + LTX Video + FFmpeg 씬 병합 |
| AI 검수 | GPT-4o Vision 이미지 검수 + Gemini 2.5 Pro 영상 검수 |
| 사용자 검수 | 단계별 승인·거부·수정 요청과 피드백 기반 재생성 |
| 인증·권한 | JWT Access/Refresh Token, Client/Admin 역할 분리 |
| 상태 관리 | 백그라운드 작업 + 3초 Polling + 진행률·토스트 알림 |
| 성과 분석 | YouTube Analytics, 밈별·회사별 성과와 ROI 대시보드 |

---

## 5. 회고

AI를 서비스로 만드는 일은 모델 성능만의 문제가 아니었습니다.
캐릭터·음성·시나리오·영상 생성 단계를 어떤 순서로 연결하고,
실패했을 때 어떻게 재시도하고 검수할지 설계하는 것이 결과물의 품질을 좌우했습니다.

4~5분짜리 비동기 작업을 백엔드가 추적하고 프론트엔드가 폴링으로 진행률을 보여주는 구조를 만들면서,
**긴 작업을 사용자 경험으로 감싸는 방법**을 배웠습니다.
단순히 작업을 실행하는 것뿐 아니라 현재 단계, 실패 원인, 재시도와 승인 상태를 일관되게 관리해야
사용자가 시스템을 신뢰할 수 있다는 점도 확인했습니다.

또한 크롤링 → 데이터 전처리 → 파인튜닝 → AI 생성 → 백엔드 오케스트레이션 → 프론트엔드 제공으로 이어지는
데이터와 서비스 흐름 전체를 정리했습니다. 여러 저장소에 분산된 결과물을 하나의 일관된 시스템으로 재구성하면서,
대형 프로젝트에서는 코드 구현뿐 아니라 **경계 설정, 정본 관리, 보안과 재현성**도 중요하다는 것을 배웠습니다.

---

## 🚀 실행 방법

각 서비스는 독립적으로 실행하며, 환경 변수는 각 폴더의 `.env.example`을 복사해 `.env`로 구성합니다.

### Backend

```powershell
Set-Location backend
Copy-Item .env.example .env
uv sync
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

AI 파이프라인은 백엔드의 Direct 모드에서 직접 호출하거나 HTTP 모드로 분리해 실행할 수 있습니다.
밈 수집·콘텐츠 생성 실험은 `ai/notebooks/`, 데이터 구축 과정은 `data-pipeline/`,
파인튜닝 과정은 `content-generator/`를 참고할 수 있습니다.

> 파인튜닝 체크포인트, 생성 미디어, 외부 모델, 데이터베이스 접속 정보는 저장소에 포함하지 않았습니다.

---

## 📚 문서

- [`docs/Project_Summary.md`](docs/Project_Summary.md) — 전체 시스템과 기능 정리
- [`docs/Application_Report.md`](docs/Application_Report.md) — 애플리케이션 리포트
- [`docs/Deployment_Architecture.md`](docs/Deployment_Architecture.md) — 배포 아키텍처
- [`docs/EC2_Docker_Deploy_Guide.md`](docs/EC2_Docker_Deploy_Guide.md) — EC2·Docker 배포 가이드
- [`docs/Test_Plan.md`](docs/Test_Plan.md) — 테스트 계획
- [`docs/Test_Results_Report.md`](docs/Test_Results_Report.md) — 테스트 결과
- `docs/planning/` — 초기 기획과 주간 리포트
