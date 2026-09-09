# EC2 Docker 배포 가이드

## 목차
1. [EC2 인스턴스 생성](#1단계-ec2-인스턴스-생성)
2. [EC2 접속](#2단계-ec2-접속)
3. [서버 초기 설정](#3단계-서버-초기-설정)
4. [코드 배포](#4단계-코드-배포)
5. [Docker 빌드 & 실행](#5단계-docker-빌드--실행)
6. [헬스체크](#6단계-헬스체크)
7. [CloudFront 설정 (CORS 해결)](#7단계-cloudfront-설정-cors-해결)
8. [Vercel 환경변수 설정](#8단계-vercel-환경변수-설정)
9. [트러블슈팅](#트러블슈팅)
10. [유용한 명령어](#유용한-명령어)

---

## 1단계: EC2 인스턴스 생성
AWS Console → EC2 → Launch Instance

1. 이름: meme-backend (원하는 이름)
2. AMI 선택:
- Ubuntu Server 22.04 LTS (추천)
- 또는 Amazon Linux 2023
3. 인스턴스 타입:
- t3.small (2GB RAM) - $15/월 - 추천
- t3.micro (1GB RAM) - $7.5/월 - 빡빡함
- t3.medium (4GB RAM) - $30/월 - 여유
4. 키 페어:
- 새로 생성 또는 기존 키 선택
- .pem 파일 다운로드 (잘 보관!)
5. 네트워크 설정:
- ✅ SSH (22) - 내 IP만
- ✅ HTTP (80) - 0.0.0.0/0
- ✅ HTTPS (443) - 0.0.0.0/0
- ✅ Custom TCP (8000) - 0.0.0.0/0
6. 스토리지: 20GB (기본값)
7. Launch Instance 클릭

## 2단계: EC2 접속
```
# Windows (PowerShell)
ssh -i "meme-fluencer.pem" ubuntu@3.36.129.41

# 권한 에러 나면
icacls "your-key.pem" /inheritance:r
icacls "your-key.pem" /grant:r "%username%:R"
```

## 3단계: 서버 초기 설정
```
# 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
sudo apt install -y docker.io docker-compose

# Docker 권한 설정
sudo usermod -aG docker ubuntu
newgrp docker

# Git 설치
sudo apt install -y git

# 확인
docker --version
docker-compose --version
```

## 4단계: 코드 배포
```bash
# Git clone
git clone https://github.com/SKN19-Final-4team/monorepo.git
cd monorepo/backend

# .env 파일 생성
nano .env
```

### .env 파일 필수 내용:
```env
# ==============================================
# 필수 환경 변수
# ==============================================

# Database (Lightsail PostgreSQL)
DATABASE_URL=postgresql://postgres:pass1234@3.35.238.161/meme-fluencer

# JWT Settings
JWT_SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=admeme-media-dev

# Google OAuth (YouTube API)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# CORS 설정 (중요!)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://d3akm36fp2lv3d.cloudfront.net,https://admeme-frontend.vercel.app,https://admeme-frontend-p1bqj7cns-hyojungjs-projects.vercel.app

# AI Pipeline 설정
AI_PIPELINE_DIRECT_MODE=true
AI_PIPELINE_MOCK_MODE=false

# 기타 AI 서비스 API Keys
NANO_BANANA_API_KEY=...
ELEVENLABS_API_KEY=...
COMFY_COMFYUI_BASE_URL=http://103.196.86.187:39370
```

**저장**: `Ctrl+X` → `Y` → `Enter`

## 5단계: Docker 빌드 & 실행
```bash
# 빌드 & 실행
docker-compose up -d --build

# 로그 확인 (서비스 이름은 'api')
docker-compose logs api

# 실시간 로그
docker logs -f meme-api

# 상태 확인
docker-compose ps
```

**예상 출력:**
```
Name                Command                  State                        Ports
---------------------------------------------------------------------------------------------------
meme-api   uv run uvicorn app.main:ap ...   Up (healthy)   0.0.0.0:8000->8000/tcp,:::8000->8000/tcp
```
## 6단계: 헬스체크
```bash
# EC2 내부에서
curl http://localhost:8000/health

# 예상 응답
{"status":"healthy","version":"4.0.0"}

# 외부에서 (로컬 PC)
curl http://your-ec2-public-ip:8000/health
```

### CORS 환경 변수 확인
```bash
# 컨테이너에 CORS 설정이 제대로 전달되었는지 확인
docker-compose exec api env | grep CORS

# 예상 출력
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://d3akm36fp2lv3d.cloudfront.net,...
```

### CORS Preflight 테스트
```bash
# OPTIONS 요청 테스트 (백엔드 직접)
curl -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: https://admeme-frontend-p1bqj7cns-hyojungjs-projects.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v

# 응답에 다음 헤더들이 있어야 함:
# access-control-allow-origin: https://admeme-frontend-p1bqj7cns-hyojungjs-projects.vercel.app
# access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
# access-control-allow-credentials: true
```
## 7단계: CloudFront 설정 (CORS 해결)

**중요**: 백엔드가 정상 작동해도 CloudFront 설정이 잘못되면 CORS 에러가 발생합니다!

### CloudFront 설정 방법

1. **AWS Console → CloudFront → Distributions**

2. **해당 Distribution 선택** (예: d3akm36fp2lv3d.cloudfront.net)

3. **Behaviors 탭 → Default (*) behavior 선택 → Edit**

4. **다음 설정 변경:**

   **Allowed HTTP methods:**
   - ✅ `GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE` 선택
   
   **Cache key and origin requests:**
   - **Cache policy**: `CachingDisabled` 선택 (개발 중)
     - 또는 커스텀 정책으로 TTL=0 설정
   - **Origin request policy**: `AllViewer` 선택
     - 또는 커스텀 정책에 다음 헤더 포함:
       - `Origin`
       - `Access-Control-Request-Method`
       - `Access-Control-Request-Headers`

5. **Save changes**

6. **Invalidations 탭 → Create invalidation**
   - Object paths: `/*`
   - Create invalidation

7. **5-10분 대기** (설정 전파 시간)

### CloudFront CORS 테스트

```bash
# CloudFront를 통한 OPTIONS 요청 테스트
curl -X OPTIONS https://d3akm36fp2lv3d.cloudfront.net/api/v1/auth/login \
  -H "Origin: https://admeme-frontend-p1bqj7cns-hyojungjs-projects.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v

# 응답에 CORS 헤더가 있어야 함
```

### Origin 설정 확인

CloudFront Origin이 EC2를 올바르게 가리키는지 확인:
- **Origin domain**: EC2 Public IP 또는 도메인
- **Protocol**: HTTP (포트 8000)
- **Origin path**: 비워두기

---

## 8단계: Vercel 환경변수 설정
## 8단계: Vercel 환경변수 설정

Vercel Dashboard → Your Project → Settings → Environment Variables

```env
Name: NEXT_PUBLIC_API_URL
Value: https://d3akm36fp2lv3d.cloudfront.net
```

**주의**: CloudFront 도메인을 사용하세요 (EC2 IP 직접 사용 X)

---

## 트러블슈팅

### 1. CORS 에러 발생 시

**증상:**
```
Access to fetch at 'https://d3akm36fp2lv3d.cloudfront.net/api/v1/auth/login' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

**해결 방법:**

1. **백엔드 CORS 설정 확인**
```bash
# EC2에서 실행
docker-compose exec api env | grep CORS

# CORS_ORIGINS가 비어있으면 .env 파일 확인
cat .env | grep CORS

# 컨테이너 재시작
docker-compose down
docker-compose up -d
```

2. **백엔드 CORS 테스트**
```bash
curl -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: https://your-frontend-domain.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

3. **CloudFront 설정 확인**
   - Allowed HTTP methods에 OPTIONS 포함되어 있는지
   - Cache policy가 CachingDisabled인지
   - Origin request policy가 AllViewer인지

4. **CloudFront 캐시 무효화**
```bash
# AWS CLI 사용 시
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### 2. 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker logs meme-api

# 일반적인 원인:
# - .env 파일 누락
# - 환경 변수 오타
# - 포트 충돌 (8000번 포트가 이미 사용 중)

# 포트 확인
sudo lsof -i :8000

# 강제 재시작
docker-compose down
docker-compose up -d --build
```

### 3. 환경 변수가 컨테이너에 전달되지 않을 때

**원인**: `.dockerignore`에 `.env`가 포함되어 있음

**해결**: `docker-compose.yml`에서 `env_file` 사용 (이미 설정됨)

```yaml
services:
  api:
    env_file:
      - .env
    environment:
      - CORS_ORIGINS=${CORS_ORIGINS}
```

### 4. Database 연결 실패

```bash
# PostgreSQL 연결 테스트
docker-compose exec api python -c "
from app.db.session import engine
try:
    with engine.connect() as conn:
        print('✓ Database connected')
except Exception as e:
    print(f'✗ Database error: {e}')
"
```

### 5. Vercel 프리뷰 도메인 CORS 에러

Vercel은 배포마다 새로운 프리뷰 도메인을 생성합니다.

**해결**: 백엔드 코드에서 Vercel 도메인 패턴을 동적으로 허용 (이미 구현됨)

```python
# app/main.py에 이미 구현되어 있음
if origin and origin.endswith(".vercel.app"):
    # 자동으로 허용
```

---

## 유용한 명령어
## 유용한 명령어

### Docker 관리
```bash
# 로그 보기 (최근 100줄)
docker logs meme-api | tail -100

# 실시간 로그
docker logs -f meme-api

# 컨테이너 상태 확인
docker-compose ps

# 재시작
docker-compose restart

# 중지
docker-compose down

# 재빌드 (코드 변경 시)
docker-compose down
docker-compose up -d --build

# 컨테이너 내부 접속
docker-compose exec api bash

# 특정 명령어 실행
docker-compose exec api python -c "print('Hello')"
```

### 시스템 모니터링
```bash
# 디스크 용량 확인
df -h

# 메모리 확인
free -h

# Docker 디스크 사용량
docker system df

# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a
```

### Git 업데이트
```bash
cd ~/monorepo/backend

# 최신 코드 가져오기
git pull

# 재배포
docker-compose down
docker-compose up -d --build
```

### 환경 변수 관리
```bash
# .env 파일 편집
nano .env

# 환경 변수 확인
docker-compose exec api env | grep CORS
docker-compose exec api env | grep DATABASE

# .env 변경 후 반드시 재시작
docker-compose restart
```

---

## 자동 재시작 설정

`docker-compose.yml`에 이미 설정되어 있음:
```yaml
restart: unless-stopped
```

EC2 재부팅 시 자동으로 컨테이너가 시작됩니다!

### Docker 서비스 자동 시작 확인
```bash
# Docker 서비스 상태 확인
sudo systemctl status docker

# 부팅 시 자동 시작 활성화
sudo systemctl enable docker
```

---

## 보안 체크리스트

- [ ] EC2 Security Group에서 SSH(22)는 내 IP만 허용
- [ ] .env 파일에 민감한 정보 포함 (Git에 커밋 X)
- [ ] JWT_SECRET_KEY는 강력한 랜덤 문자열 사용
- [ ] Database는 Private Subnet 또는 IP 제한
- [ ] CloudFront를 통해서만 접근 (EC2 IP 직접 노출 X)
- [ ] 정기적인 패키지 업데이트: `sudo apt update && sudo apt upgrade`

---

## 성능 최적화

### 1. Docker 이미지 최적화
- 이미 `python:3.11-slim` 사용 중 ✓
- Multi-stage build 고려 (필요시)

### 2. 메모리 모니터링
```bash
# 컨테이너 리소스 사용량
docker stats meme-api

# 메모리 부족 시 t3.medium으로 업그레이드
```

### 3. 로그 로테이션
```bash
# Docker 로그 크기 제한 (docker-compose.yml에 추가)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## 참고 자료

- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [AWS CloudFront CORS 설정](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/header-caching.html)
- [Vercel 환경 변수](https://vercel.com/docs/concepts/projects/environment-variables)

