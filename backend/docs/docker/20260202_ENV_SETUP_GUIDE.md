# 환경 변수 설정 가이드

## 개요

Docker 컨테이너에서 FastAPI 애플리케이션을 실행하기 위한 환경 변수 설정 방법을 설명합니다.

## 로컬 개발 환경

### 1. .env 파일 생성

프로젝트 루트에 `.env` 파일을 생성합니다.

```bash
# .env.example을 복사해서 시작
cp .env.example .env
```

### 2. 필수 환경 변수 설정

`.env` 파일을 열어서 실제 값으로 수정합니다:

```env
# 데이터베이스
DATABASE_URL=postgresql://username:password@host:port/database_name

# JWT
JWT_SECRET_KEY=your-strong-secret-key-here

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=your-bucket-name

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key
```

### 3. Docker Compose 실행

```bash
# 컨테이너 빌드 및 실행
docker-compose up

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

`docker-compose.yml`의 `env_file: - .env` 설정이 자동으로 환경 변수를 컨테이너에 전달합니다.

## 서버 배포 환경 (Lightsail)

### 방법 1: .env 파일 업로드 (권장)

#### 1-1. 서버에 .env 파일 생성

```bash
# SSH로 서버 접속
ssh -i your-key.pem ubuntu@your-server-ip

# 프로젝트 디렉토리로 이동
cd /home/ubuntu/backend

# .env 파일 생성
nano .env
```

#### 1-2. 환경 변수 입력

로컬의 `.env` 파일 내용을 복사해서 붙여넣습니다.

**주의사항:**
- `DATABASE_URL`: Lightsail DB 엔드포인트로 변경
- `DEBUG`: `false`로 설정
- `COMFY_WORKFLOW_PATH`: 서버 경로로 변경
- `COMFY_SSH_KEY`: 서버 경로로 변경

#### 1-3. 파일 권한 설정

```bash
# .env 파일 권한 제한 (보안)
chmod 600 .env

# 소유자 확인
ls -la .env
```

#### 1-4. Docker Compose 실행

```bash
docker-compose up -d
```

### 방법 2: 환경 변수 직접 설정

#### 2-1. docker-compose.yml 수정

```yaml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      # ... 나머지 환경 변수
```

#### 2-2. 서버 환경 변수 설정

```bash
# ~/.bashrc 또는 ~/.profile에 추가
export DATABASE_URL="postgresql://..."
export JWT_SECRET_KEY="..."

# 적용
source ~/.bashrc
```

#### 2-3. Docker Compose 실행

```bash
docker-compose up -d
```

### 방법 3: Docker Secrets (프로덕션 권장)

민감한 정보를 Docker Secrets로 관리합니다.

```bash
# Secret 생성
echo "your-secret-value" | docker secret create db_password -

# docker-compose.yml에서 사용
secrets:
  db_password:
    external: true
```

## 환경 변수 검증

### 컨테이너 내부 환경 변수 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 환경 변수 확인
docker exec meme-api env | grep DATABASE_URL

# 또는 컨테이너 내부 접속
docker exec -it meme-api bash
echo $DATABASE_URL
```

### API 헬스체크

```bash
# 헬스체크 엔드포인트 호출
curl http://localhost:8000/health

# 응답 예시
{
  "status": "healthy",
  "database": "connected",
  "s3": "connected"
}
```

## 보안 권장 사항

### 1. .env 파일 보안

```bash
# 파일 권한 제한
chmod 600 .env

# Git에서 제외 (.gitignore에 추가됨)
# .env
# .env.local
```

### 2. 민감한 정보 관리

- `.env` 파일을 Git에 커밋하지 않기
- `.env.example`에는 실제 값 넣지 않기
- 프로덕션 환경에서는 AWS Secrets Manager 또는 Docker Secrets 사용

### 3. JWT Secret Key 생성

강력한 랜덤 키 생성:

```bash
# Python으로 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL로 생성
openssl rand -base64 32
```

### 4. 환경별 설정 분리

```bash
# 개발 환경
.env.development

# 스테이징 환경
.env.staging

# 프로덕션 환경
.env.production
```

## 트러블슈팅

### 환경 변수가 로드되지 않을 때

1. **파일 경로 확인**
   ```bash
   ls -la .env
   ```

2. **파일 인코딩 확인**
   - UTF-8 인코딩 사용
   - BOM 없이 저장

3. **Docker Compose 재시작**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **캐시 제거 후 재빌드**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### DATABASE_URL 연결 오류

1. **Lightsail DB 보안 그룹 확인**
   - 서버 IP가 허용되어 있는지 확인

2. **연결 문자열 형식 확인**
   ```
   postgresql://username:password@host:port/database
   ```

3. **네트워크 연결 테스트**
   ```bash
   # 컨테이너 내부에서 테스트
   docker exec -it meme-api bash
   apt-get update && apt-get install -y postgresql-client
   psql $DATABASE_URL
   ```

### AWS S3 연결 오류

1. **IAM 권한 확인**
   - S3 읽기/쓰기 권한 확인

2. **리전 확인**
   ```env
   AWS_REGION=ap-northeast-2
   S3_BUCKET_NAME=your-bucket-name
   ```

3. **연결 테스트**
   ```bash
   docker exec -it meme-api python -c "
   from app.services.s3_service import test_s3_connection
   print(test_s3_connection())
   "
   ```

## 환경 변수 목록

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | JWT 토큰 암호화 키 | `random-32-char-string` |
| `AWS_ACCESS_KEY_ID` | AWS 액세스 키 | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS 시크릿 키 | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `S3_BUCKET_NAME` | S3 버킷 이름 | `admeme-media-dev` |
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 시크릿 | `GOCSPX-xxx` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-xxx` |

### 선택적 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DEBUG` | 디버그 모드 | `false` |
| `MOCK_MODE` | Mock 모드 (테스트용) | `false` |
| `AI_PIPELINE_MOCK_MODE` | AI 파이프라인 Mock 모드 | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT 토큰 만료 시간 (분) | `1440` |

## 참고 자료

- [Docker Compose 환경 변수 문서](https://docs.docker.com/compose/environment-variables/)
- [FastAPI 설정 관리](https://fastapi.tiangolo.com/advanced/settings/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
