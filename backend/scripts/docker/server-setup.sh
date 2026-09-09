#!/bin/bash

# ==============================================
# AWS Lightsail 서버 초기 설정 스크립트
# ==============================================

set -e  # 에러 발생 시 스크립트 중단

echo "=========================================="
echo "서버 초기 설정을 시작합니다..."
echo "=========================================="

# 1. 시스템 업데이트
echo ""
echo "[1/6] 시스템 업데이트 중..."
sudo apt update
sudo apt upgrade -y

# 2. 필수 패키지 설치
echo ""
echo "[2/6] 필수 패키지 설치 중..."
sudo apt install -y \
    git \
    curl \
    vim \
    wget \
    ca-certificates \
    gnupg \
    lsb-release

# 3. Docker 설치
echo ""
echo "[3/6] Docker 설치 중..."

# Docker GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 저장소 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

echo "Docker 설치 완료: $(docker --version)"

# 4. Docker Compose 설치
echo ""
echo "[4/6] Docker Compose 설치 중..."

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "Docker Compose 설치 완료: $(docker-compose --version)"

# 5. 방화벽 설정
echo ""
echo "[5/6] 방화벽 설정 중..."

sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # FastAPI

echo "방화벽 설정 완료"

# 6. 디렉토리 생성
echo ""
echo "[6/6] 프로젝트 디렉토리 생성 중..."

mkdir -p ~/backend
mkdir -p ~/logs

echo "디렉토리 생성 완료"

# 완료 메시지
echo ""
echo "=========================================="
echo "서버 초기 설정이 완료되었습니다"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 로그아웃 후 재로그인 (Docker 그룹 적용)"
echo "   exit"
echo ""
echo "2. Git 저장소 클론"
echo "   cd ~/backend"
echo "   git clone https://github.com/your-username/your-repo.git ."
echo ""
echo "3. 환경 변수 설정"
echo "   nano .env"
echo ""
echo "4. Docker 컨테이너 실행"
echo "   docker-compose up -d"
echo ""
echo "=========================================="
