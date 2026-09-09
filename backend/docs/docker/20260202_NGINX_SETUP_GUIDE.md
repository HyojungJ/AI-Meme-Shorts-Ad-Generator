# Nginx 설정 가이드

## 개요

Nginx를 리버스 프록시로 설정하여 FastAPI 서버로 요청을 전달하고, SSL 인증서를 적용하는 방법을 설명합니다.

---

## 1. Nginx 설치

### 1-1. 서버에 SSH 접속

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_SERVER_IP
```

### 1-2. Nginx 설치

```bash
# 패키지 업데이트
sudo apt update

# Nginx 설치
sudo apt install -y nginx

# 버전 확인
nginx -v

# Nginx 시작
sudo systemctl start nginx
sudo systemctl enable nginx

# 상태 확인
sudo systemctl status nginx
```

### 1-3. 방화벽 설정 확인

```bash
# HTTP, HTTPS 포트 열려있는지 확인
sudo ufw status

# 없으면 추가
sudo ufw allow 'Nginx Full'
```

### 1-4. 기본 페이지 확인

브라우저에서 `http://YOUR_SERVER_IP` 접속
→ "Welcome to nginx!" 페이지 보이면 성공

---

## 2. Nginx 리버스 프록시 설정

### 2-1. 설정 파일 생성

```bash
# 설정 파일 생성
sudo nano /etc/nginx/sites-available/fastapi
```

### 2-2. 설정 내용 입력

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;

    # 로그 설정
    access_log /var/log/nginx/fastapi_access.log;
    error_log /var/log/nginx/fastapi_error.log;

    # 클라이언트 최대 업로드 크기
    client_max_body_size 100M;

    # FastAPI로 프록시
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        # 헤더 설정
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 지원 (필요시)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 정적 파일 캐싱 (선택사항)
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        proxy_pass http://localhost:8000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**주의:** `YOUR_DOMAIN.com`을 실제 도메인으로 변경

### 2-3. 설정 파일 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/

# 기본 설정 비활성화 (선택사항)
sudo rm /etc/nginx/sites-enabled/default

# 설정 파일 문법 검사
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 2-4. 테스트

```bash
# FastAPI 서버 실행 확인
docker ps

# 브라우저에서 접속
http://YOUR_DOMAIN.com/docs
```

---

## 3. SSL 인증서 설정 (Let's Encrypt)

### 3-1. Certbot 설치

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx
```

### 3-2. SSL 인증서 발급

```bash
# 인증서 발급 및 자동 설정
sudo certbot --nginx -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# 이메일 입력 (인증서 만료 알림용)
# 약관 동의 (Y)
# 이메일 수신 동의 (선택)
```

### 3-3. 자동 갱신 설정

```bash
# 자동 갱신 테스트
sudo certbot renew --dry-run

# Cron 작업 확인 (자동으로 설정됨)
sudo systemctl status certbot.timer
```

### 3-4. 설정 확인

Certbot이 자동으로 Nginx 설정을 수정합니다:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;
    
    # HTTP를 HTTPS로 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;

    # SSL 인증서
    ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 나머지 설정은 동일
    location / {
        proxy_pass http://localhost:8000;
        # ...
    }
}
```

### 3-5. HTTPS 테스트

```bash
# 브라우저에서 접속
https://YOUR_DOMAIN.com/docs

# SSL 등급 확인
https://www.ssllabs.com/ssltest/
```

---

## 4. 도메인 연결

### 4-1. 도메인 구매

- [가비아](https://www.gabia.com/)
- [AWS Route 53](https://aws.amazon.com/route53/)
- [Cloudflare](https://www.cloudflare.com/)

### 4-2. DNS 설정

도메인 관리 페이지에서 A 레코드 추가:

| 타입 | 호스트 | 값 | TTL |
|------|--------|-----|-----|
| A | @ | YOUR_SERVER_IP | 3600 |
| A | www | YOUR_SERVER_IP | 3600 |

### 4-3. DNS 전파 확인

```bash
# DNS 조회
nslookup YOUR_DOMAIN.com

# 또는
dig YOUR_DOMAIN.com
```

DNS 전파는 최대 24~48시간 소요 (보통 몇 분~몇 시간)

---

## 5. 보안 강화

### 5-1. 추가 보안 헤더

```nginx
server {
    # ...

    # 보안 헤더 추가
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # ...
}
```

### 5-2. Rate Limiting (DDoS 방어)

```nginx
# /etc/nginx/nginx.conf의 http 블록에 추가
http {
    # ...

    # Rate limiting 설정
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # ...
}
```

```nginx
# /etc/nginx/sites-available/fastapi
server {
    # ...

    location / {
        # Rate limiting 적용
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        # ...
    }
}
```

### 5-3. IP 화이트리스트 (Admin 전용)

```nginx
# Admin API만 특정 IP에서 접근 가능
location /api/v1/admin {
    allow YOUR_OFFICE_IP;
    deny all;
    
    proxy_pass http://localhost:8000;
    # ...
}
```

---

## 6. 모니터링 및 로그

### 6-1. 로그 확인

```bash
# 액세스 로그
sudo tail -f /var/log/nginx/fastapi_access.log

# 에러 로그
sudo tail -f /var/log/nginx/fastapi_error.log

# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log
```

### 6-2. 로그 로테이션

```bash
# 로그 로테이션 설정 확인
cat /etc/logrotate.d/nginx
```

기본 설정으로 자동 로테이션됨 (일일 또는 주간)

---

## 7. 트러블슈팅

### 7-1. Nginx 시작 실패

```bash
# 설정 파일 문법 검사
sudo nginx -t

# 에러 로그 확인
sudo journalctl -u nginx -n 50

# 포트 충돌 확인
sudo lsof -i :80
sudo lsof -i :443
```

### 7-2. 502 Bad Gateway

**원인:** FastAPI 서버가 실행되지 않음

```bash
# Docker 컨테이너 확인
docker ps

# 컨테이너 로그 확인
docker-compose logs -f

# 컨테이너 재시작
docker-compose restart
```

### 7-3. SSL 인증서 발급 실패

**원인:** 도메인이 서버 IP를 가리키지 않음

```bash
# DNS 확인
nslookup YOUR_DOMAIN.com

# 80 포트 열려있는지 확인
sudo ufw status
```

### 7-4. 413 Request Entity Too Large

**원인:** 업로드 파일 크기 제한

```nginx
# /etc/nginx/sites-available/fastapi
server {
    # 크기 제한 증가
    client_max_body_size 500M;
}
```

```bash
# Nginx 재시작
sudo systemctl restart nginx
```

---

## 8. 성능 최적화

### 8-1. Gzip 압축

```nginx
# /etc/nginx/nginx.conf의 http 블록에 추가
http {
    # ...

    # Gzip 압축 활성화
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;
}
```

### 8-2. 캐싱 설정

```nginx
server {
    # ...

    # API 응답 캐싱 (선택적)
    location /api/v1/public {
        proxy_cache_valid 200 5m;
        proxy_cache_bypass $http_cache_control;
        add_header X-Cache-Status $upstream_cache_status;
        
        proxy_pass http://localhost:8000;
        # ...
    }
}
```

### 8-3. 연결 최적화

```nginx
# /etc/nginx/nginx.conf
http {
    # ...

    # Keep-alive 설정
    keepalive_timeout 65;
    keepalive_requests 100;

    # 버퍼 크기 최적화
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
}
```

---

## 9. 배포 체크리스트

### 배포 전 확인사항

- [ ] Nginx 설치 완료
- [ ] 리버스 프록시 설정 완료
- [ ] 도메인 DNS 설정 완료
- [ ] SSL 인증서 발급 완료
- [ ] HTTPS 리다이렉트 설정 완료
- [ ] 보안 헤더 추가 완료
- [ ] Rate limiting 설정 완료
- [ ] 로그 확인 가능
- [ ] FastAPI 서버 정상 작동
- [ ] API 문서 접근 가능 (https://domain.com/docs)

---

## 10. 설정 파일 예시 (완전판)

### /etc/nginx/sites-available/fastapi

```nginx
# Rate limiting 설정
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL 인증서
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 로그
    access_log /var/log/nginx/fastapi_access.log;
    error_log /var/log/nginx/fastapi_error.log;

    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # 업로드 크기 제한
    client_max_body_size 100M;

    # API 엔드포인트
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
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
```

---

## 참고 자료

- [Nginx 공식 문서](https://nginx.org/en/docs/)
- [Let's Encrypt 문서](https://letsencrypt.org/docs/)
- [Certbot 사용 가이드](https://certbot.eff.org/)
- [Nginx 보안 가이드](https://www.nginx.com/blog/mitigating-ddos-attacks-with-nginx-and-nginx-plus/)
