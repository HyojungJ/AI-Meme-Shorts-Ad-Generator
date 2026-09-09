# Docker 배포 환경 구축 작업 내역

## 작업 일자
2026년 2월 2일

## 작업 개요
FastAPI 백엔드 서버를 AWS Lightsail에 Docker로 배포하기 위한 환경 구축 및 설정 완료

---

## 1. Docker 환경 설정

### 1-1. 완료된 작업
- ✅ `Dockerfile` 작성 (Python 3.11, uv 패키지 매니저 사용)
- ✅ `docker-compose.yml` 작성 (로컬 테스트용)
- ✅ `.dockerignore` 작성
- ✅ 컨테이너 헬스체크 설정
- ✅ 원격 Lightsail DB 연결 설정

### 1-2. Docker 이미지 구성
```dockerfile
FROM python:3.11-slim
- uv 패키지 매니저 사용
- pyproject.toml + uv.lock으로 의존성 관리
- 포트: 8000
- 헬스체크: /health 엔드포인트
```

### 1-3. 로컬 테스트 완료
```bash
docker-compose up
# 결과: 서버 정상 실행, 헬스체크 통과
```

---

## 2. 환경 변수 관리

### 2-1. .env 파일 정리
**제거된 중복 항목:**
- `DB_URL` 삭제 (DATABASE_URL로 통합)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` 삭제

**제거된 미사용 환경 변수:**
- `LANGSMITH_*` (모니터링, 미사용)
- `PINECONE_API_KEY` (Vector DB, 미사용)
- `HUGGINGFACEHUB_API_TOKEN` (미사용)
- `TAVILY_API_KEY` (검색 API, 미사용)

**코드 수정:**
- `app/core/config.py`: 미사용 환경 변수 제거
- `scripts/database_user.py`: DATABASE_URL 우선 사용, DB_URL fallback
- `scripts/auth/v1/database.py`: DATABASE_URL 우선 사용
- `scripts/auth/v2/database.py`: DATABASE_URL 우선 사용

### 2-2. 최종 환경 변수 구조
```
필수 환경 변수:
- DATABASE_URL (PostgreSQL)
- JWT_SECRET_KEY
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (YouTube API)
- OPENAI_API_KEY

AI 서비스:
- NANO_BANANA_* (이미지 생성)
- ELEVENLABS_* (음성 생성)
- COMFY_* (영상 생성)

개발/디버깅:
- DEBUG, MOCK_MODE
- AI_PIPELINE_MOCK_MODE, AI_PIPELINE_DIRECT_MODE
```

### 2-3. 문서 작성
- ✅ `.env.example` 업데이트
- ✅ `docs/docker/20260202_ENV_SETUP_GUIDE.md` 작성

---

## 3. 의존성 관리

### 3-1. pyproject.toml 수정
**추가된 패키지:**
- `oauth2client>=4.1.3` (YouTube OAuth 인증용)

**중복 제거:**
- `google-api-python-client` 중복 항목 제거
- `pytrends` 중복 항목 제거

### 3-2. uv.lock 업데이트
```bash
uv lock
# 결과: oauth2client 및 의존성 패키지 추가됨
```

---

## 4. AWS Lightsail 서버 설정

### 4-1. 인스턴스 생성
- **리전:** ap-northeast-2 (서울)
- **플랫폼:** Ubuntu 22.04 LTS
- **플랜:** $10/월 (2GB RAM, 1 vCPU, 60GB SSD)
- **고정 IP:** 3.38.234.125

### 4-2. SSH 키 설정
- **키 파일:** `admeme.pem`
- **위치:** `C:\Users\kouls\Downloads\`
- **접속 테스트:** ✅ 성공

```bash
ssh -i C:\Users\kouls\Downloads\admeme.pem ubuntu@3.38.234.125
```

### 4-3. 방화벽 설정
```bash
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # FastAPI
```

### 4-4. 서버 초기 설정 완료
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 버전 확인
docker --version        # Docker version 29.2.0
docker-compose --version # Docker Compose version v5.0.2
```

### 4-5. 프로젝트 배포
```bash
# Git 저장소 클론
cd ~
git clone https://github.com/SKN19-Final-4team/backend.git backend
cd backend

# feature 브랜치로 변경 (Docker 파일 포함)
git checkout feature/39-docker-env

# .env 파일 생성 및 설정
nano .env
# (로컬 .env 내용 복사 후 붙여넣기)
chmod 600 .env
```

### 4-6. 문서 작성
- ✅ `docs/docker/20260202_LIGHTSAIL_SETUP_GUIDE.md` 작성
- ✅ `scripts/server-setup.sh` 자동화 스크립트 작성

---

## 5. Git 브랜치 관리

### 5-1. 브랜치 구조
- **작업 브랜치:** `feature/39-docker-env`
- **타겟 브랜치:** `main`

### 5-2. 커밋 내역
- Docker 환경 설정 파일 추가
- 환경 변수 정리 및 중복 제거
- 의존성 패키지 추가 (oauth2client)
- 배포 가이드 문서 작성
- 서버 초기 설정 스크립트 작성

### 5-3. Push 완료
```bash
git push -u origin feature/39-docker-env
```

---

## 6. 다음 단계 (미완료)

### 6-1. Docker 빌드 및 실행
```bash
# 서버에서 실행 예정
cd ~/backend
docker-compose build
docker-compose up -d
```

### 6-2. Nginx 설정 (예정)
- 리버스 프록시 설정
- SSL 인증서 설정 (Let's Encrypt)
- 도메인 연결

### 6-3. 자동 배포 설정 (예정)
- GitHub Actions CI/CD
- 자동 빌드 및 배포

---

## 7. 서버 정보

### 7-1. 백엔드 서버
- **IP:** 3.38.234.125
- **OS:** Ubuntu 22.04 LTS
- **Docker:** 29.2.0
- **Docker Compose:** v5.0.2

### 7-2. 데이터베이스 서버 (기존)
- **IP:** 3.35.238.161
- **포트:** 5432
- **DB:** meme-fluencer

### 7-3. 네트워크 구조
```
[사용자]
   ↓
[백엔드 서버: 3.38.234.125]
   ↓ DATABASE_URL
[DB 서버: 3.35.238.161]
```

---

## 8. 참고 문서

### 8-1. 작성된 문서
- `docs/docker/20260202_ENV_SETUP_GUIDE.md` - 환경 변수 설정 가이드
- `docs/docker/20260202_LIGHTSAIL_SETUP_GUIDE.md` - Lightsail 서버 설정 가이드
- `docs/docker/20260202_NGINX_SETUP_GUIDE.md` - Nginx 설정 가이드
- `docs/docker/20260202_DEPLOYMENT_SUMMARY.md` - 전체 작업 내역 요약

### 8-2. 주요 파일
- `Dockerfile` - Docker 이미지 정의
- `docker-compose.yml` - Docker Compose 설정
- `.dockerignore` - Docker 빌드 제외 파일
- `.env.example` - 환경 변수 템플릿
- `pyproject.toml` - Python 의존성 정의
- `uv.lock` - 의존성 버전 고정

### 8-3. 스크립트
- `scripts/server-setup.sh` - 서버 초기 설정 자동화
- `scripts/nginx-setup.sh` - Nginx 설정 자동화


---

## 9. 트러블슈팅

### 9-1. SSH 접속 실패
**문제:** Permission denied (publickey)
**원인:** 잘못된 SSH 키 사용
**해결:** `admeme.pem` 키 사용

### 9-2. Git clone 인증 실패
**문제:** Password authentication is not supported
**원인:** GitHub Personal Access Token 필요
**해결:** 저장소를 Public으로 변경

### 9-3. docker-compose.yml 없음
**문제:** no configuration file provided
**원인:** main 브랜치에 Docker 파일 없음
**해결:** `feature/39-docker-env` 브랜치 사용

---

## 10. 체크리스트

### 완료된 작업
- [x] Dockerfile 작성
- [x] docker-compose.yml 작성
- [x] .dockerignore 작성
- [x] 환경 변수 정리 (.env, .env.example)
- [x] 의존성 패키지 추가 (oauth2client)
- [x] 로컬 Docker 테스트
- [x] Lightsail 인스턴스 생성
- [x] SSH 키 설정
- [x] 방화벽 설정
- [x] Docker 및 Docker Compose 설치
- [x] Git 저장소 클론
- [x] .env 파일 서버 업로드
- [x] 배포 가이드 문서 작성
- [x] Git push 완료

### 진행 중
- [ ] Pull Request 생성 및 merge
- [ ] 서버에서 Docker 빌드
- [ ] 서버에서 Docker 실행
- [ ] API 동작 확인

### 예정
- [x] Nginx 설정 가이드 작성
- [x] Nginx 자동 설정 스크립트 작성
- [ ] Nginx 설정 (서버에 적용)
- [ ] SSL 인증서 설정
- [ ] 도메인 연결
- [ ] 자동 배포 설정 (CI/CD)
- [ ] 모니터링 설정

---

## 11. Nginx 설정 (추가)

### 11-1. 문서 작성
- ✅ `docs/docker/20260202_NGINX_SETUP_GUIDE.md` 작성
  - Nginx 설치 가이드
  - 리버스 프록시 설정
  - SSL 인증서 설정 (Let's Encrypt)
  - 도메인 연결 방법
  - 보안 강화 설정
  - 성능 최적화
  - 트러블슈팅

### 11-2. 자동화 스크립트 작성
- ✅ `scripts/nginx-setup.sh` 작성
  - Nginx 자동 설치
  - 리버스 프록시 자동 설정
  - SSL 인증서 자동 발급 (선택)
  - 방화벽 자동 설정

### 11-3. 주요 기능
**리버스 프록시:**
```
[사용자] → [Nginx:80/443] → [Docker FastAPI:8000]
```

**보안 기능:**
- HTTPS 자동 리다이렉트
- Rate Limiting (DDoS 방어)
- 보안 헤더 추가
- IP 화이트리스트 (선택)

**성능 최적화:**
- Gzip 압축
- 정적 파일 캐싱
- Keep-alive 설정

---


## 작업자
- 작업자: Kiro AI Assistant
- 사용자: HyojungJ
- 프로젝트: SKN19-Final-4team/backend
