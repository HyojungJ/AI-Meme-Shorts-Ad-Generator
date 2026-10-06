# Meme Influencer - 프로젝트 종합 정리

## 1. 프로젝트 목표

한국 인터넷 밈을 활용한 광고 숏폼 영상을 AI로 자동 생성하는 SaaS 플랫폼.
기업이 제품 정보만 입력하면 밈 추천 → 캐릭터/음성 생성 → 시나리오 작성 → 영상 생성 → YouTube 게시까지 전 과정을 자동화하여, Z세대 타겟 마케팅 비용을 절감하고 제작 시간을 수일에서 5분으로 단축하는 것이 목표.

---

## 2. 활용 기술

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 14 (App Router) | React 프레임워크 |
| React | 18 | UI 라이브러리 |
| TypeScript | 5 | 타입 안전성 |
| TailwindCSS | 3 | 스타일링 |
| Recharts | 3 | 성과 분석 차트 |
| react-hook-form | 7 | 폼 관리 |
| react-dropzone | 14 | 파일 업로드 |
| Jest + React Testing Library | 30 | 테스트 |

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| FastAPI | 0.115+ | REST API 프레임워크 |
| Python | 3.11 | 백엔드 언어 |
| SQLAlchemy | 2.0 | ORM |
| Alembic | 1.13 | DB 마이그레이션 |
| python-jose | 3.5 | JWT 인증 |
| bcrypt | 5.0 | 비밀번호 해싱 |
| Uvicorn | 0.40 | ASGI 서버 |
| psycopg2-binary | 2.9 | PostgreSQL 드라이버 |
| boto3 | 1.42+ | AWS S3 연동 |

### AI/ML
| 기술 | 버전 | 용도 |
|------|------|------|
| LangGraph | 1.0 | AI 워크플로우 오케스트레이션 |
| LangChain | 1.2 | LLM 체인 구성 |
| OpenAI GPT-4o | - | 시나리오 생성, 밈 분석 |
| OpenAI GPT-4o-mini | - | 캐릭터 프롬프트 추천 |
| GPT-4o Vision | - | 이미지 검수 (수정 반영도 검증) |
| Google Gemini 2.0 Flash | - | 캐릭터 이미지 생성 |
| Gemini 2.5 Pro | - | 영상 검수 (VLM 자동 검증) |
| ElevenLabs | v3 | 음성 생성 (Voice Design) |
| Qwen TTS | 0.0.5 | 음성 생성 (대안, PyTorch 2.8 + Transformers 4.57) |
| dragonkue/BGE-m3-ko | - | 밈 추천 (한국어 임베딩 + 코사인 유사도) |
| ComfyUI + LTX Video | - | 숏폼 영상 생성 |
| A.x-4.0 (파인튜닝) | - | 시나리오 생성 특화 모델 |
| librosa | 0.10 | 오디오 분석 |
| Pillow / OpenCV | 10.0 / 4.8 | 이미지/영상 처리 |
| FFmpeg | - | 영상 병합 (크로스페이드) |

### Infrastructure
| 서비스 | 용도 |
|--------|------|
| AWS EC2 (t3.xlarge) | 백엔드 호스팅 (Docker) |
| AWS Lightsail PostgreSQL | 데이터베이스 (24개 테이블) |
| AWS S3 | 파일 스토리지 (이미지/음성/영상) |
| AWS CloudFront | CDN + HTTPS |
| Vercel | 프론트엔드 호스팅 (자동 배포) |
| RunPod Serverless | ComfyUI 영상 생성 + A.x-4.0 시나리오 모델 GPU 서버 |
| Docker + docker-compose | 백엔드 컨테이너화 |
| uv | Python 패키지 관리 |

### External APIs
| API | 용도 |
|-----|------|
| YouTube Data API v3 | 밈 영상 검색, 완성 영상 업로드 |
| Naver Search API | 밈 정보 수집 (블로그, 뉴스) |

---

## 3. 개발 환경

| 항목 | 내용 |
|------|------|
| 레포지토리 | Monorepo (AI + backend + frontend) |
| GitHub | https://github.com/SKN19-Final-4team/monorepo |
| Python 버전 | 3.11 |
| Node.js 버전 | 18.x |
| 패키지 관리 | uv (Python), npm (Node.js) |
| DB | PostgreSQL 15 (AWS Lightsail, `3.35.238.161`) |
| 백엔드 서버 | EC2 `3.36.129.41`, Docker 컨테이너 |
| 프론트엔드 | Vercel (https://admeme-frontend.vercel.app) |
| CDN | CloudFront (https://d3akm36fp2lv3d.cloudfront.net) |
| AI 모델 서버 | RunPod Serverless (ComfyUI, A.x-4.0) |
| 배포 방식 | Frontend: Vercel 자동 배포 / Backend: SSH + git pull + docker-compose |

---

## 4. 구현 기능

### 4.1 밈 수집 시스템 (Meme Collector)
- LangGraph 기반 Multi-Agent 아키텍처 (Supervisor → Text/Media/Usage Researcher → Analyzer → Verifier)
- ReAct 패턴으로 나무위키, 네이버, YouTube 자동 크롤링
- Gemini Vision으로 밈 영상 분석 및 motion_prompt 생성
- Reflexion 패턴으로 품질 검증 (100점 만점, 80점 이상 PASS)
- 밈 타입 분류 (quotable / performable / hybrid)
- BGE-m3-ko 임베딩 기반 밈 추천 (제품-밈 유사도 매칭)

### 4.2 광고 영상 생성 파이프라인
- 2단계 검수 시스템 (Asset 생성 → Content 생성)
- GPT-4o-mini로 제품 기반 캐릭터 프롬프트 자동 추천
- Gemini 2.0 Flash로 캐릭터 이미지 생성
- ElevenLabs / Qwen TTS로 캐릭터 음성 생성
- GPT-4o (+ A.x-4.0 파인튜닝 모델)로 5단 구조 시나리오 생성
- ComfyUI + LTX Video로 씬별 영상 생성 (RunPod Serverless)
- FFmpeg 크로스페이드 병합
- 전체 워크플로우 약 4~5분 소요

### 4.3 AI 검수 시스템
- 이미지 검수: GPT-4o Vision으로 원본 vs 재생성 이미지 비교 (50점 미만 자동 재시도, 최대 2회)
- 영상 검수: Gemini 2.5 Pro로 영상 품질 자동 검증
- 검증 결과 DB 저장 (character.generation_metadata, video.review_result)

### 4.4 사용자 검수 시스템
- 캐릭터/음성 승인·거부·수정 요청
- 시나리오 씬별 수정 요청
- 영상 승인·거부·재생성 요청
- 피드백 기반 재생성 (수정 요청 사항 반영)

### 4.5 사용자 인증 및 권한
- JWT 인증 (Access Token 24시간 + Refresh Token 7일)
- Client / Admin 역할 분리
- bcrypt 비밀번호 해싱

### 4.6 실시간 상태 업데이트
- REST Polling 방식 (3초 간격) — CloudFront HTTP/2 호환
- 워크플로우 진행률 표시 (0~100%)
- 상태 전환 시 토스트 알림

### 4.7 Admin 기능
- 전체 영상 관리 (모든 회사)
- YouTube OAuth 2.0 자동 게시
- 워크플로우 모니터링 및 재시도
- 비용/품질 관리 대시보드

### 4.8 성과 분석
- Client: 내 영상 조회수, 참여율, 밈별 성과 비교
- Admin: 전체 회사 성과, 밈 효과성, ROI 분석
- Recharts 기반 시각화 (주간/월간/분기 트렌드)

### 4.9 배포 및 인프라
- Docker 컨테이너화 (AI 폴더 포함 빌드)
- DynamicCORSMiddleware (Vercel 프리뷰 URL 동적 허용)
- CloudFront CDN + S3 스토리지
- Alembic DB 마이그레이션 관리

---

## 5. 내 역할 (김종민)

### Backend 전체 설계 및 구현
- FastAPI 기반 REST API 설계 (60+ 엔드포인트)
- SQLAlchemy 2.0 ORM 모델 설계 (24개 테이블)
- JWT 인증 시스템 (Client/Admin 권한 분리)
- Alembic 마이그레이션 관리
- Pydantic 스키마 설계 및 입력 검증

### AI 파이프라인 통합 (Backend ↔ AI 연동)
- AI 파이프라인 클라이언트 아키텍처 설계 (Base → Direct / HTTP / Mock 3중 구조)
- Backend에서 AI 함수 직접 호출 (Direct 모드) 구현
- 백그라운드 태스크로 비동기 생성 처리 (캐릭터/음성/시나리오/영상)
- 워크플로우 상태 관리 및 진행률 추적
- 검수 결과 DB 저장 로직 구현 (영상 auto_review, 이미지 auto_review)

### AI 파이프라인 개발 (Content Pipeline)
- 밈 수집 Multi-Agent 시스템 설계 및 구현 (LangGraph)
  - Supervisor, Text/Media/Usage Researcher, Analyzer, Verifier 노드
  - 나무위키/네이버/YouTube 크롤링 도구 개발
  - Gemini Vision 영상 분석 도구 개발
  - Reflexion 패턴 품질 검증 시스템
- 콘텐츠 생성 파이프라인 설계 및 구현
  - 캐릭터 이미지 생성 (Gemini 2.0 Flash + nanobanana)
  - 음성 생성 (ElevenLabs Voice Design + Qwen TTS 대안 구현)
  - 영상 생성 (ComfyUI LTX Video + RunPod Serverless 연동)
  - 영상 병합 (FFmpeg 크로스페이드)
  - 씬 이미지 합성 (캐릭터 + 제품 이미지)
- AI 검수 시스템 구현
  - GPT-4o Vision 이미지 검수 (수정 반영도 자동 검증 + 재시도)
  - Gemini 2.5 Pro 영상 검수 (품질 자동 검증)
- BGE-m3-ko 기반 밈 추천 시스템 구현
- GPT-4o-mini 기반 캐릭터 프롬프트 추천 구현

### 배포 및 인프라
- AWS EC2 Docker 배포 환경 구축
- Dockerfile / docker-compose.yml 설계 (AI 폴더 포함 빌드 컨텍스트)
- CloudFront CDN 설정 및 DynamicCORSMiddleware 구현
- S3 스토리지 연동 (이미지/음성/영상 업로드)
- RunPod Serverless 연동 (ComfyUI, A.x-4.0)
- DB CHECK 제약조건 이슈 해결, 상태 동기화 버그 수정 등 운영 이슈 대응

### 문서화
- Application Report 작성
- Deployment Architecture 문서 작성
- EC2 Docker Deploy Guide 작성
- 테스트 계획서 및 결과 보고서 작성
