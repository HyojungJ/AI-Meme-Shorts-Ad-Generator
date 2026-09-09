# Python 3.11 slim 이미지 사용 (용량 최소화)
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    ffmpeg \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Chrome 설치 (YouTube 업로드용) - 최신 방식
RUN wget -q -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome-stable_current_amd64.deb \
    && rm /tmp/google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Python 의존성 파일 복사
COPY backend/pyproject.toml backend/uv.lock ./

# AI 패키지 복사 (editable 의존성)
COPY AI /AI

# uv.lock에 고정된 버전으로 의존성 설치
RUN uv sync --frozen --no-dev

# 애플리케이션 코드 복사
COPY backend/ .

# YouTube 인증 토큰 복사 (gitignore되어 있지만 Docker에는 필요)
# 빌드 컨텍스트가 상위 폴더이므로 backend/ 경로 사용
RUN if [ -f token.pickle ]; then echo "token.pickle found"; else echo "token.pickle not found"; fi
RUN if [ -f token_analytics.pickle ]; then echo "token_analytics.pickle found"; else echo "token_analytics.pickle not found"; fi

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 포트 노출
EXPOSE 8000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Uvicorn으로 FastAPI 실행
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
