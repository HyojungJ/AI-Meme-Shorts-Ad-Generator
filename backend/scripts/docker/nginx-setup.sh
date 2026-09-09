#!/bin/bash

# ==============================================
# Nginx 자동 설정 스크립트
# ==============================================

set -e  # 에러 발생 시 스크립트 중단

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Nginx 설정을 시작합니다..."
echo "=========================================="

# 도메인 입력 받기
echo ""
read -p "도메인을 입력하세요 (예: example.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ 도메인을 입력해야 합니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 도메인: $DOMAIN${NC}"

# 1. Nginx 설치
echo ""
echo "[1/5] Nginx 설치 중..."
sudo apt update
sudo apt install -y nginx

echo -e "${GREEN}✅ Nginx 설치 완료: $(nginx -v 2>&1)${NC}"

# 2. Nginx 시작 및 활성화
echo ""
echo "[2/5] Nginx 시작 중..."
sudo systemctl start nginx
sudo systemctl enable nginx

echo -e "${GREEN}✅ Nginx 시작 완료${NC}"

# 3. 방화벽 설정
echo ""
echo "[3/5] 방화벽 설정 중..."
sudo ufw allow 'Nginx Full'

echo -e "${GREEN}✅ 방화벽 설정 완료${NC}"

# 4. Nginx 설정 파일 생성
echo ""
echo "[4/5] Nginx 설정 파일 생성 중..."

sudo tee /etc/nginx/sites-available/fastapi > /dev/null <<EOF
# Rate limiting 설정
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # 로그 설정
    access_log /var/log/nginx/fastapi_access.log;
    error_log /var/log/nginx/fastapi_error.log;

    # 클라이언트 최대 업로드 크기
    client_max_body_size 100M;

    # FastAPI로 프록시
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # 헤더 설정
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket 지원
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 정적 파일 캐싱
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        proxy_pass http://localhost:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 심볼릭 링크 생성
sudo ln -sf /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/

# 기본 설정 비활성화
sudo rm -f /etc/nginx/sites-enabled/default

# 설정 파일 문법 검사
if sudo nginx -t; then
    echo -e "${GREEN}✅ Nginx 설정 파일 생성 완료${NC}"
else
    echo -e "${RED}❌ Nginx 설정 파일 오류${NC}"
    exit 1
fi

# Nginx 재시작
sudo systemctl restart nginx

# 5. SSL 인증서 설정 (선택사항)
echo ""
echo "[5/5] SSL 인증서 설정..."
read -p "SSL 인증서를 설정하시겠습니까? (y/n): " SSL_CHOICE

if [ "$SSL_CHOICE" = "y" ] || [ "$SSL_CHOICE" = "Y" ]; then
    echo ""
    echo "Certbot 설치 중..."
    sudo apt install -y certbot python3-certbot-nginx
    
    echo ""
    echo "SSL 인증서 발급 중..."
    echo -e "${YELLOW}⚠️  이메일 주소와 약관 동의가 필요합니다.${NC}"
    
    sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSL 인증서 설정 완료${NC}"
        
        # 자동 갱신 테스트
        echo ""
        echo "자동 갱신 테스트 중..."
        sudo certbot renew --dry-run
        
        echo -e "${GREEN}✅ 자동 갱신 설정 완료${NC}"
    else
        echo -e "${RED}❌ SSL 인증서 발급 실패${NC}"
        echo -e "${YELLOW}⚠️  DNS 설정을 확인하고 다시 시도하세요.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SSL 인증서 설정을 건너뜁니다.${NC}"
    echo -e "${YELLOW}⚠️  나중에 'sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN' 명령으로 설정할 수 있습니다.${NC}"
fi

# 완료 메시지
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Nginx 설정이 완료되었습니다!${NC}"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. DNS 설정 확인"
echo "   - A 레코드: @ → YOUR_SERVER_IP"
echo "   - A 레코드: www → YOUR_SERVER_IP"
echo ""
echo "2. FastAPI 서버 실행"
echo "   cd ~/backend"
echo "   docker-compose up -d"
echo ""
echo "3. 브라우저에서 확인"
if [ "$SSL_CHOICE" = "y" ] || [ "$SSL_CHOICE" = "Y" ]; then
    echo "   https://$DOMAIN/docs"
else
    echo "   http://$DOMAIN/docs"
fi
echo ""
echo "4. 로그 확인"
echo "   sudo tail -f /var/log/nginx/fastapi_access.log"
echo "   sudo tail -f /var/log/nginx/fastapi_error.log"
echo ""
echo "=========================================="
