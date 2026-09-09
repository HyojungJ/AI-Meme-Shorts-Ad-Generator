# 배포 환경 아키텍처

## 통합 시스템 아키텍처 (CI/CD + 운영 환경)

```
                    ┌─────────────────────────────────┐
                    │     개발자 (Developer)          │
                    └─────────────────────────────────┘
                                    │
                                    │ git push
                                    ▼
                    ┌─────────────────────────────────┐
                    │   GitHub Repository             │
                    │   (monorepo)                    │
                    │                                 │
                    │   ├── frontend/  (Next.js)      │
                    │   ├── backend/   (FastAPI)      │
                    │   └── AI/        (LangGraph)    │
                    └─────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
            Webhook (자동)                   git pull (수동)
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Vercel CI/CD (자동)     │   │   EC2 수동 배포           │
    │                           │   │                           │
    │  1. Push 감지             │   │  1. SSH 접속              │
    │  2. npm install           │   │  2. git pull              │
    │  3. npm run build         │   │  3. docker-compose down   │
    │  4. Edge 배포             │   │  4. docker-compose up -d  │
    │  5. 프리뷰 URL (PR)       │   │  5. health check          │
    └───────────────────────────┘   └───────────────────────────┘
                    │                               │
                    │ 배포 완료                      │ 배포 완료
                    ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         프로덕션 환경                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌───────────────────────────────────┐   ┌───────────────────────────┐
│   사용자 (Client/Admin)           │   │   사용자 (Client/Admin)   │
└───────────────────────────────────┘   └───────────────────────────┘
                    │                               │
                    │ HTTPS Request                 │ HTTPS Request
                    ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Vercel Platform                           │   │
│  │  - App Router (React Server/Client Components)              │   │
│  │  - Edge Network (글로벌 CDN)                                 │   │
│  │  - 환경 변수: NEXT_PUBLIC_API_URL                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  URL: https://admeme-frontend.vercel.app                             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API Request (HTTPS)
                                    ▼
                                    │ JSON Response
                                    ▲
┌─────────────────────────────────────────────────────────────────────┐
│                    AWS CloudFront (CDN)                              │
│  - SSL/TLS 인증서                                                     │
│  - CORS 처리 (DynamicCORSMiddleware)                                 │
│  - Cache Policy: CachingDisabled (개발 중)                           │
│                                                                       │
│  URL: https://d3akm36fp2lv3d.cloudfront.net                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP Request
                                    ▼
                                    │ HTTP Response
                                    ▲
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI + Docker)                        │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AWS EC2 (t3.small, Ubuntu 22.04)               │   │
│  │                                                              │   │
│  │  ┌────────────────────────────────────────────────────┐    │   │
│  │  │         Docker Container (meme-api)                │    │   │
│  │  │                                                     │    │   │
│  │  │  - FastAPI (Uvicorn)                               │    │   │
│  │  │  - 60+ REST API 엔드포인트                          │    │   │
│  │  │  - JWT 인증                                         │    │   │
│  │  │  - AI 파이프라인 오케스트레이션                      │    │   │
│  │  │  - Port: 8000                                       │    │   │
│  │  └────────────────────────────────────────────────────┘    │   │
│  │                                                              │   │
│  │  IP: 3.36.129.41                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                │                   │                   │
                │                   │                   │
    ┌───────────┘                   │                   └───────────┐
    │                               │                               │
    │ SQL Query                     │ Upload/Download               │ API Request
    ▼                               ▼                               ▼
    │ Query Result                  │ File URL                      │ API Response
    ▲                               ▲                               ▲
┌─────────────┐          ┌──────────────────┐          ┌──────────────────┐
│  PostgreSQL │          │   AWS S3 Bucket  │          │  External APIs   │
│  (Lightsail)│          │                  │          │                  │
│             │          │  - 캐릭터 이미지  │          │  - OpenAI        │
│ - 24개 테이블│          │  - 음성 파일     │          │  - Google Gemini │
│ - Alembic   │          │  - 영상 파일     │          │  - ElevenLabs    │
│             │          │                  │          │  - YouTube API   │
│ Port: 5432  │          │  + CloudFront    │          │  - Naver API     │
└─────────────┘          │    CDN 연동      │          └──────────────────┘
                         └──────────────────┘
                                    │
                                    │ CDN Request
                                    ▼
                                    │ File Response
                                    ▲
                    ┌───────────────┴───────────────┐
                    │                               │
                    │ API Request                   │ API Request
                    ▼                               ▼
                    │ Video Response                │ Scenario Response
                    ▲                               ▲
        ┌──────────────────────┐      ┌──────────────────────┐
        │   RunPod Serverless  │      │   RunPod Serverless  │
        │                      │      │                      │
        │  ComfyUI + LTX Video │      │  A.x-4.0 (시나리오)  │
        │                      │      │                      │
        │  - 영상 생성 모델     │      │  - 파인튜닝 모델      │
        │  - GPU 인스턴스       │      │  - 시나리오 생성      │
        │  - 자동 스케일링      │      │  - 자동 스케일링      │
        │  - API 엔드포인트     │      │  - API 엔드포인트     │
        └──────────────────────┘      └──────────────────────┘
```

---

## 주요 구성 요소

### 1. Frontend (Vercel)
- **플랫폼**: Vercel
- **프레임워크**: Next.js 14 (App Router)
- **배포 방식**: Git Push 시 자동 배포
- **특징**:
  - Edge Network를 통한 글로벌 CDN
  - 서버리스 함수 자동 스케일링
  - 프리뷰 배포 (PR별 고유 URL)
- **URL**: https://admeme-frontend.vercel.app

### 2. CDN (AWS CloudFront)
- **역할**: Backend API 앞단 CDN
- **기능**:
  - SSL/TLS 인증서 관리
  - CORS 처리 (DynamicCORSMiddleware와 연동)
  - 정적 리소스 캐싱
- **Origin**: EC2 Public IP (http://3.36.129.41:8000)
- **URL**: https://d3akm36fp2lv3d.cloudfront.net

### 3. Backend (AWS EC2 + Docker)
- **인스턴스**: t3.small (2 vCPU, 2GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **컨테이너**: Docker (meme-api)
- **프레임워크**: FastAPI + Uvicorn
- **주요 기능**:
  - REST API 서버 (60+ 엔드포인트)
  - JWT 인증 및 권한 관리
  - AI 파이프라인 오케스트레이션
  - 워크플로우 관리
- **포트**: 8000

### 4. Database (AWS Lightsail PostgreSQL)
- **플랫폼**: AWS Lightsail
- **버전**: PostgreSQL 15
- **스토리지**: 40GB SSD
- **테이블**: 24개
- **마이그레이션**: Alembic
- **연결**: psycopg2-binary

### 5. Storage (AWS S3)
- **버킷**: admeme-media-dev
- **저장 파일**:
  - 캐릭터 이미지 (PNG)
  - 음성 파일 (MP3)
  - 영상 파일 (MP4)
- **CDN**: CloudFront 연동
- **접근 권한**: Public Read

### 6. AI 모델 서버 (RunPod Serverless)

#### 6.1 ComfyUI + LTX Video
- **플랫폼**: RunPod Serverless
- **모델**: LTX Video (영상 생성)
- **GPU**: 자동 할당 (사용량 기반)
- **특징**:
  - 서버리스 자동 스케일링
  - 사용한 만큼만 과금
  - API 엔드포인트 제공
- **용도**: 씬별 영상 생성

#### 6.2 A.x-4.0 (시나리오 생성 파인튜닝 모델)
- **플랫폼**: RunPod Serverless
- **모델**: A.x-4.0 (파인튜닝된 시나리오 생성 모델)
- **GPU**: 자동 할당 (사용량 기반)
- **특징**:
  - 한국 밈 특화 파인튜닝
  - 서버리스 자동 스케일링
  - API 엔드포인트 제공
- **용도**: 5단 구조 시나리오 생성

### 7. External APIs
- **OpenAI**: GPT-4o (밈 분석), GPT-4o-mini (프롬프트 추천)
- **Google Gemini**: 2.0 Flash (캐릭터 이미지 생성, 영상 분석)
- **ElevenLabs**: 음성 생성 (Voice Design)
- **YouTube Data API v3**: 밈 영상 검색, 영상 업로드
- **Naver Search API**: 밈 정보 수집

---

## 데이터 흐름

### 영상 생성 워크플로우

```
1. 사용자 요청 (Frontend)
   └─> Vercel → CloudFront → EC2 Backend

2. 캐릭터 프롬프트 생성 (Backend)
   └─> OpenAI GPT-4o-mini API

3. 캐릭터 이미지 생성 (Backend)
   └─> Google Gemini 2.0 Flash API
   └─> S3 업로드

4. 음성 디자인 (Backend)
   └─> ElevenLabs API (또는 Qwen TTS)
   └─> S3 업로드

5. 시나리오 생성 (Backend)
   └─> RunPod A.x-4.0 API (파인튜닝 모델)
   └─> PostgreSQL 저장

6. TTS 생성 (Backend)
   └─> ElevenLabs API (또는 Qwen TTS)
   └─> S3 업로드

7. 영상 생성 (Backend)
   └─> RunPod ComfyUI + LTX Video API
   └─> S3 업로드

8. 결과 반환 (Backend → Frontend)
   └─> CloudFront → Vercel → 사용자
```

---

## 배포 프로세스

### Frontend (Vercel) - 자동 배포

#### 1. 프로덕션 배포 (main 브랜치)
```bash
# 개발자 작업
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main

# Vercel 자동 실행 (Webhook)
# 1. GitHub Push 이벤트 감지
# 2. 빌드 시작
#    - npm install
#    - npm run build
# 3. 배포 (Edge Network)
# 4. 배포 완료 알림 (Slack/Email)

# 결과
# ✅ https://admeme-frontend.vercel.app (프로덕션)
```

#### 2. 프리뷰 배포 (Pull Request)
```bash
# 개발자 작업
git checkout -b feature/new-feature
git push origin feature/new-feature

# GitHub에서 PR 생성

# Vercel 자동 실행 (Webhook)
# 1. PR 생성 이벤트 감지
# 2. 프리뷰 빌드 시작
# 3. 고유 URL 생성
# 4. PR에 코멘트로 URL 추가

# 결과
# ✅ https://admeme-frontend-[hash].vercel.app (프리뷰)
```

#### 3. Vercel 설정
```yaml
# vercel.json (프로젝트 루트)
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "installCommand": "npm install",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://d3akm36fp2lv3d.cloudfront.net"
  }
}
```

### Backend (EC2 Docker) - 수동 배포

#### 1. 배포 스크립트
```bash
#!/bin/bash
# deploy.sh

echo "🚀 Backend 배포 시작..."

# 1. EC2 접속
ssh -i "key.pem" ubuntu@3.36.129.41 << 'EOF'

# 2. 코드 업데이트
cd ~/monorepo
echo "📥 Git Pull..."
git pull origin main

# 3. Docker 재시작
cd backend
echo "🐳 Docker 재빌드..."
docker-compose down
docker-compose up -d --build

# 4. 헬스 체크
echo "🏥 헬스 체크..."
sleep 10
curl -f http://localhost:8000/health || exit 1

echo "✅ 배포 완료!"
EOF
```

#### 2. 배포 실행
```bash
# 로컬에서 실행
./deploy.sh

# 또는 직접 실행
ssh -i "key.pem" ubuntu@3.36.129.41
cd ~/monorepo
git pull
cd backend
docker-compose down
docker-compose up -d --build
```

#### 3. 배포 확인
```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker logs -f meme-api

# API 테스트
curl https://d3akm36fp2lv3d.cloudfront.net/health
```

### RunPod Serverless - 수동 배포

#### 1. ComfyUI + LTX Video 배포
```bash
# RunPod Dashboard에서 작업

# 1. 템플릿 생성
# - Docker Image: comfyui/comfyui:latest
# - GPU: RTX 4090 (24GB VRAM)
# - 워크플로우 JSON 업로드

# 2. 엔드포인트 생성
# - Serverless 선택
# - API URL 발급: https://api.runpod.ai/v2/[endpoint-id]
# - API Key 발급

# 3. 환경 변수 등록 (Backend .env)
COMFY_COMFYUI_BASE_URL=https://api.runpod.ai/v2/[endpoint-id]
RUNPOD_API_KEY=your-api-key

# 4. 자동 스케일링 설정
# - Min Instances: 0 (비용 절감)
# - Max Instances: 5 (부하 대응)
# - Idle Timeout: 60초
```

#### 2. A.x-4.0 시나리오 모델 배포
```bash
# RunPod Dashboard에서 작업

# 1. 모델 업로드
# - 파인튜닝된 모델 가중치 업로드
# - 추론 스크립트 업로드

# 2. 엔드포인트 생성
# - Serverless 선택
# - API URL 발급: https://api.runpod.ai/v2/[scenario-endpoint-id]
# - API Key 발급

# 3. 환경 변수 등록 (Backend .env)
SCENARIO_MODEL_URL=https://api.runpod.ai/v2/[scenario-endpoint-id]
SCENARIO_API_KEY=your-api-key

# 4. 자동 스케일링 설정
# - Min Instances: 0
# - Max Instances: 3
# - Idle Timeout: 120초
```

---

## 배포 전략

### Frontend (Vercel)
| 전략 | 설명 |
|------|------|
| **자동 배포** | Git Push 시 자동 빌드 및 배포 |
| **프리뷰 배포** | PR별 고유 URL 생성 (테스트 용이) |
| **롤백** | Vercel Dashboard에서 이전 버전으로 즉시 롤백 |
| **A/B 테스트** | Vercel Edge Config로 트래픽 분산 가능 |

### Backend (EC2)
| 전략 | 설명 |
|------|------|
| **수동 배포** | SSH 접속 후 git pull + docker-compose |
| **블루-그린** | 향후 도입 예정 (무중단 배포) |
| **롤백** | git revert + docker-compose 재시작 |
| **헬스 체크** | 배포 후 /health 엔드포인트 확인 |

### RunPod (AI 모델)
| 전략 | 설명 |
|------|------|
| **수동 배포** | Dashboard에서 모델 업데이트 |
| **버전 관리** | 엔드포인트별 버전 태그 관리 |
| **롤백** | 이전 엔드포인트로 환경 변수 변경 |
| **A/B 테스트** | 두 엔드포인트 동시 운영 후 비교 |

---

## 보안 설정

### Network Security
- **EC2 Security Group**:
  - SSH (22): 관리자 IP만
  - HTTP (80): 0.0.0.0/0
  - HTTPS (443): 0.0.0.0/0
  - Custom TCP (8000): 0.0.0.0/0

- **CloudFront**:
  - SSL/TLS 인증서 (AWS Certificate Manager)
  - HTTPS Only

- **S3**:
  - Public Read (CloudFront Origin Access Identity)
  - Bucket Policy 설정

### Application Security
- **JWT 인증**: Access Token (24시간) + Refresh Token (7일)
- **비밀번호 해싱**: bcrypt (cost factor 12)
- **API Key 관리**: 환경 변수 (.env)
- **CORS**: DynamicCORSMiddleware (Vercel 도메인 자동 허용)

---

## 비용 구조

### 고정 비용
| 서비스 | 사양 | 월 비용 (예상) |
|--------|------|---------------|
| AWS EC2 (t3.small) | 2 vCPU, 2GB RAM | $15 |
| AWS Lightsail PostgreSQL | 1GB RAM, 40GB SSD | $15 |
| Vercel (Hobby) | 무제한 배포 | $0 |
| **합계** | | **$30** |

### 변동 비용 (사용량 기반)
| 서비스 | 과금 방식 | 예상 비용 |
|--------|----------|----------|
| AWS S3 | 스토리지 + 전송량 | $5-10/월 |
| AWS CloudFront | 데이터 전송량 | $5-10/월 |
| RunPod ComfyUI | GPU 사용 시간 | $0.5/시간 × 사용량 |
| RunPod A.x-4.0 | GPU 사용 시간 | $0.5/시간 × 사용량 |
| OpenAI API | 토큰 사용량 | $10-30/월 |
| Google Gemini API | 이미지 생성 횟수 | $5-15/월 |
| ElevenLabs API | 음성 생성 시간 | $10-20/월 |

**총 예상 비용**: **$80-130/월** (사용량에 따라 변동)

---

## 모니터링 및 로깅

### Application Logs
- **Backend**: Docker logs (`docker logs -f meme-api`)
- **Frontend**: Vercel Dashboard (실시간 로그)
- **RunPod**: RunPod Dashboard (API 호출 로그)

### Health Checks
- **Backend**: `GET /health` (30초 간격)
- **Database**: Connection Pool 모니터링
- **S3**: Bucket 용량 모니터링

### Alerts
- **EC2**: CPU/Memory 사용률 (CloudWatch)
- **Database**: Connection 수, 쿼리 성능
- **API**: 응답 시간, 에러율

---

## 확장 계획

### 단기 (1-3개월)
- [ ] EC2 Auto Scaling Group 구성
- [ ] RDS PostgreSQL로 마이그레이션 (고가용성)
- [ ] Redis 캐싱 도입 (밈 데이터, 세션)
- [ ] CloudWatch 대시보드 구축

### 중기 (3-6개월)
- [ ] Multi-Region 배포 (글로벌 확장)
- [ ] Kubernetes (EKS) 마이그레이션
- [ ] CI/CD 파이프라인 자동화 (GitHub Actions)
- [ ] 모니터링 강화 (Prometheus + Grafana)

### 장기 (6-12개월)
- [ ] Microservices 아키텍처 전환
- [ ] Event-Driven Architecture (SQS, SNS)
- [ ] Data Lake 구축 (S3 + Athena)
- [ ] ML 모델 자체 호스팅 (비용 절감)

---

