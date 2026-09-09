# AWS Lightsail 서버 설정 가이드

## 개요

AWS Lightsail에 FastAPI 백엔드 서버를 배포하는 전체 과정을 설명합니다.

## 1. Lightsail 인스턴스 생성

### 1-1. AWS Lightsail 콘솔 접속

1. [AWS Lightsail 콘솔](https://lightsail.aws.amazon.com/) 접속
2. 로그인

### 1-2. 인스턴스 생성

1. **"인스턴스 생성" 버튼 클릭**

2. **인스턴스 위치 선택**
   - 리전: `서울 (ap-northeast-2)`
   - 가용 영역: 기본값

3. **플랫폼 선택**
   - `Linux/Unix` 선택

4. **블루프린트 선택**
   - `OS 전용` 탭 선택
   - `Ubuntu 22.04 LTS` 선택

5. **인스턴스 플랜 선택**
   - 권장: `$10/월` (2GB RAM, 1 vCPU, 60GB SSD)
   - 최소: `$5/월` (1GB RAM) - 테스트용

6. **인스턴스 이름 지정**
   - 예: `meme-backend-server`

7. **"인스턴스 생성" 클릭**

### 1-3. 고정 IP 할당 (선택사항)

1. 인스턴스 생성 후 `네트워킹` 탭 클릭
2. `고정 IP 생성` 클릭
3. 인스턴스에 연결
4. IP 주소 메모 (예: `3.35.238.161`)

## 2. SSH 키 설정

### 2-1. SSH 키 다운로드

1. Lightsail 콘솔에서 `계정` 메뉴 클릭
2. `SSH 키` 탭 클릭
3. 리전 선택 (`ap-northeast-2`)
4. `기본 키 다운로드` 클릭
5. 파일 저장 (예: `LightsailDefaultKey-ap-northeast-2.pem`)

### 2-2. SSH 키 권한 설정 (Windows)

PowerShell에서:

```powershell
# 키 파일 위치로 이동
cd C:\Users\YourName\.ssh

# 파일 권한 확인
icacls LightsailDefaultKey-ap-northeast-2.pem

# 권한 설정 (필요시)
icacls LightsailDefaultKey-ap-northeast-2.pem /inheritance:r
icacls LightsailDefaultKey-ap-northeast-2.pem /grant:r "%USERNAME%:R"
```

### 2-3. SSH 접속 테스트

```bash
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-2.pem ubuntu@YOUR_SERVER_IP
```

성공하면 서버 터미널에 접속됩니다.

## 3. 방화벽 설정

### 3-1. Lightsail 방화벽 규칙 추가

1. Lightsail 콘솔에서 인스턴스 클릭
2. `네트워킹` 탭 클릭
3. `IPv4 방화벽` 섹션에서 규칙 추가:

| 애플리케이션 | 프로토콜 | 포트 범위 | 설명 |
|-------------|---------|----------|------|
| SSH | TCP | 22 | SSH 접속 |
| HTTP | TCP | 80 | HTTP (Nginx) |
| HTTPS | TCP | 443 | HTTPS (SSL) |
| Custom | TCP | 8000 | FastAPI (개발용) |

4. 각 규칙에 대해 `+ 규칙 추가` 클릭

### 3-2. 방화벽 확인

```bash
# 서버에서 확인
sudo ufw status

# 비활성화되어 있으면 활성화
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
```

## 4. 서버 초기 설정

### 4-1. 서버 접속

```bash
ssh -i ~/.ssh/LightsailDefaultKey-ap-northeast-2.pem ubuntu@YOUR_SERVER_IP
```

### 4-2. 시스템 업데이트

```bash
# 패키지 목록 업데이트
sudo apt update

# 패키지 업그레이드
sudo apt upgrade -y
```

### 4-3. 필수 패키지 설치

```bash
# Git 설치
sudo apt install -y git

# Curl 설치
sudo apt install -y curl

# Vim 설치 (선택사항)
sudo apt install -y vim
```

### 4-4. Docker 설치

```bash
# Docker 설치 스크립트 다운로드 및 실행
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 변경사항 적용 (재로그인 필요)
newgrp docker

# Docker 버전 확인
docker --version
```

### 4-5. Docker Compose 설치

```bash
# Docker Compose 최신 버전 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 실행 권한 부여
sudo chmod +x /usr/local/bin/docker-compose

# 버전 확인
docker-compose --version
```

### 4-6. 자동화 스크립트 사용 (선택사항)

위 과정을 자동화한 스크립트:

```bash
# 스크립트 다운로드
curl -o setup.sh https://raw.githubusercontent.com/your-repo/backend/main/scripts/server-setup.sh

# 실행 권한 부여
chmod +x setup.sh

# 실행
./setup.sh
```

## 5. 프로젝트 배포

### 5-1. Git 저장소 클론

```bash
# 홈 디렉토리로 이동
cd ~

# Git 저장소 클론
git clone https://github.com/your-username/your-repo.git backend

# 프로젝트 디렉토리로 이동
cd backend
```

### 5-2. 환경 변수 설정

```bash
# .env 파일 생성
nano .env
```

`.env.example`을 참고해서 실제 값 입력:

```env
DATABASE_URL=postgresql://postgres:password@3.35.238.161:5432/meme-fluencer
JWT_SECRET_KEY=your-production-secret-key
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=admeme-media-dev
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
OPENAI_API_KEY=your-openai-key
DEBUG=false
```

**주의사항:**
- `DATABASE_URL`: Lightsail DB 엔드포인트 사용
- `DEBUG`: 반드시 `false`로 설정
- `JWT_SECRET_KEY`: 강력한 랜덤 키 생성

```bash
# 파일 권한 설정 (보안)
chmod 600 .env

# 저장 및 종료 (Ctrl + X, Y, Enter)
```

### 5-3. Docker 이미지 빌드

```bash
# Docker 이미지 빌드
docker-compose build

# 빌드 확인
docker images
```

### 5-4. Docker 컨테이너 실행

```bash
# 백그라운드로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 상태 확인
docker ps
```

### 5-5. 서비스 확인

```bash
# 헬스체크
curl http://localhost:8000/health

# API 문서 확인 (브라우저)
http://YOUR_SERVER_IP:8000/docs
```

## 6. 자동 시작 설정

### 6-1. Systemd 서비스 생성

서버 재부팅 시 자동으로 Docker 컨테이너 시작:

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/meme-backend.service
```

내용:

```ini
[Unit]
Description=Meme Backend API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/backend
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

### 6-2. 서비스 활성화

```bash
# 서비스 활성화
sudo systemctl enable meme-backend.service

# 서비스 시작
sudo systemctl start meme-backend.service

# 서비스 상태 확인
sudo systemctl status meme-backend.service
```

## 7. 모니터링 및 관리

### 7-1. 로그 확인

```bash
# Docker 로그 실시간 확인
docker-compose logs -f

# 최근 100줄만 확인
docker-compose logs --tail=100

# 특정 서비스 로그만 확인
docker-compose logs -f api
```

### 7-2. 컨테이너 관리

```bash
# 컨테이너 재시작
docker-compose restart

# 컨테이너 중지
docker-compose stop

# 컨테이너 시작
docker-compose start

# 컨테이너 삭제 (데이터 유지)
docker-compose down

# 컨테이너 및 볼륨 삭제 (데이터 삭제)
docker-compose down -v
```

### 7-3. 업데이트 배포

```bash
# Git 최신 코드 가져오기
git pull origin main

# Docker 이미지 재빌드
docker-compose build

# 컨테이너 재시작
docker-compose up -d

# 또는 한 번에
git pull && docker-compose build && docker-compose up -d
```

### 7-4. 디스크 공간 관리

```bash
# 디스크 사용량 확인
df -h

# Docker 디스크 사용량 확인
docker system df

# 사용하지 않는 이미지/컨테이너 정리
docker system prune -a
```

## 8. 보안 설정

### 8-1. SSH 보안 강화

```bash
# SSH 설정 파일 편집
sudo nano /etc/ssh/sshd_config
```

권장 설정:

```
# 루트 로그인 비활성화
PermitRootLogin no

# 비밀번호 인증 비활성화 (키 인증만 허용)
PasswordAuthentication no

# 포트 변경 (선택사항)
Port 2222
```

```bash
# SSH 서비스 재시작
sudo systemctl restart sshd
```

### 8-2. Fail2Ban 설치 (무차별 대입 공격 방지)

```bash
# Fail2Ban 설치
sudo apt install -y fail2ban

# 서비스 시작
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# 상태 확인
sudo fail2ban-client status
```

### 8-3. 자동 보안 업데이트

```bash
# Unattended Upgrades 설치
sudo apt install -y unattended-upgrades

# 활성화
sudo dpkg-reconfigure -plow unattended-upgrades
```

## 9. 트러블슈팅

### 9-1. Docker 컨테이너가 시작되지 않을 때

```bash
# 로그 확인
docker-compose logs

# 컨테이너 상태 확인
docker ps -a

# 이미지 재빌드
docker-compose build --no-cache
docker-compose up -d
```

### 9-2. 데이터베이스 연결 오류

```bash
# 데이터베이스 연결 테스트
docker exec -it meme-api bash
apt-get update && apt-get install -y postgresql-client
psql $DATABASE_URL

# Lightsail DB 보안 그룹 확인
# - 서버 IP가 허용되어 있는지 확인
```

### 9-3. 포트가 이미 사용 중일 때

```bash
# 포트 사용 확인
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 <PID>
```

### 9-4. 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# Docker 정리
docker system prune -a --volumes

# 로그 파일 정리
sudo journalctl --vacuum-time=7d
```

## 10. 체크리스트

배포 전 확인 사항:

- [ ] Lightsail 인스턴스 생성 완료
- [ ] 고정 IP 할당 완료
- [ ] SSH 키 다운로드 및 권한 설정 완료
- [ ] 방화벽 규칙 추가 완료 (22, 80, 443, 8000)
- [ ] Docker 및 Docker Compose 설치 완료
- [ ] Git 저장소 클론 완료
- [ ] `.env` 파일 설정 완료
- [ ] Docker 이미지 빌드 완료
- [ ] 컨테이너 실행 및 헬스체크 통과
- [ ] 자동 시작 설정 완료
- [ ] 보안 설정 완료

## 참고 자료

- [AWS Lightsail 문서](https://docs.aws.amazon.com/lightsail/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Ubuntu 서버 가이드](https://ubuntu.com/server/docs)
