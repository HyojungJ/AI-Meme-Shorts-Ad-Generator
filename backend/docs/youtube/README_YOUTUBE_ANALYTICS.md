# YouTube Analytics 데이터 수집 가이드

YouTube에 업로드된 영상의 성과 데이터를 자동으로 수집하여 프론트엔드에서 확인할 수 있도록 합니다.

## 📋 개요

- **목적**: YouTube Analytics API를 통해 영상 성과 데이터(조회수, 좋아요, 댓글 등)를 수집
- **저장 위치**: `performance_metrics` 테이블
- **프론트엔드**: 클라이언트 대시보드(`/main`)와 관리자 분석 페이지(`/admin/analytics`)에서 확인 가능

## 🔧 설정

### 1. Google Cloud Console 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 프로젝트 선택 또는 생성
3. **API 및 서비스 > 라이브러리**로 이동
4. 다음 API를 활성화:
   - YouTube Data API v3
   - YouTube Analytics API
5. **API 및 서비스 > 사용자 인증 정보**로 이동
6. **OAuth 2.0 클라이언트 ID** 생성:
   - 애플리케이션 유형: 데스크톱 앱
   - 이름: YouTube Analytics Collector
7. 클라이언트 ID와 클라이언트 보안 비밀번호를 복사

### 2. 환경 변수 설정

`backend/.env` 파일에 추가:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. 필요한 패키지 설치

```bash
cd backend
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client schedule
```

또는 `pyproject.toml`에 추가 후:

```bash
uv sync
```

## 🚀 사용 방법

### 수동 실행

#### 1. 특정 영상의 성과 데이터 수집 (테스트용)

```bash
cd backend
python scripts/youtube_analytics_collector.py --video-id 123
```

- `--video-id`: Video 테이블의 video_id
- `--days`: 며칠 전부터 데이터를 수집할지 (기본값: 30일)

예시:
```bash
# 최근 7일간의 데이터 수집
python scripts/youtube_analytics_collector.py --video-id 123 --days 7
```

#### 2. 모든 게시된 영상의 성과 데이터 수집

```bash
cd backend
python scripts/youtube_analytics_collector.py --all
```

- `--days`: 며칠 전부터 데이터를 수집할지 (기본값: 1일)

예시:
```bash
# 최근 7일간의 모든 영상 데이터 수집
python scripts/youtube_analytics_collector.py --all --days 7
```

### 자동 실행 (스케줄러)

매일 오전 9시에 자동으로 데이터를 수집하도록 설정:

```bash
cd backend
python scripts/schedule_analytics_collection.py
```

- 백그라운드에서 계속 실행됨
- Ctrl+C로 종료 가능
- 프로덕션 환경에서는 systemd 또는 supervisor로 관리 권장

#### systemd 서비스 설정 (Linux)

`/etc/systemd/system/youtube-analytics.service` 파일 생성:

```ini
[Unit]
Description=YouTube Analytics Data Collector
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/.venv/bin"
ExecStart=/path/to/backend/.venv/bin/python scripts/schedule_analytics_collection.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable youtube-analytics
sudo systemctl start youtube-analytics
sudo systemctl status youtube-analytics
```

## 📊 데이터 확인

### 프론트엔드에서 확인

1. **클라이언트 대시보드** (`/main`):
   - 내 회사의 영상 성과 요약
   - 조회수 추이 그래프
   - 반응률 추이 그래프
   - 최근 영상 목록 및 성과

2. **관리자 분석 페이지** (`/admin/analytics`):
   - 전체 플랫폼 성과 대시보드
   - 밈별 성과 분석
   - 카테고리별 성과 분석
   - 시계열 트렌드 분석

### API 엔드포인트

#### 클라이언트용
- `GET /api/v1/analytics/dashboard` - 내 회사 성과 대시보드
- `GET /api/v1/analytics/videos/{video_id}` - 특정 영상 성과 조회
- `GET /api/v1/analytics/summary` - 간단 요약 통계

#### 관리자용
- `GET /api/v1/admin/analytics/dashboard` - 전체 대시보드
- `GET /api/v1/admin/analytics/memes` - 밈별 성과
- `GET /api/v1/admin/analytics/categories` - 카테고리별 성과
- `GET /api/v1/admin/analytics/trends` - 시계열 트렌드

### 데이터베이스에서 직접 확인

```sql
-- 최근 수집된 성과 데이터 확인
SELECT 
    pm.metric_id,
    v.title,
    pm.views,
    pm.likes,
    pm.comments,
    pm.engagement_rate,
    pm.captured_at
FROM performance_metrics pm
JOIN videos v ON pm.video_id = v.video_id
ORDER BY pm.captured_at DESC
LIMIT 10;

-- 특정 영상의 성과 추이
SELECT 
    captured_at,
    views,
    likes,
    comments,
    engagement_rate
FROM performance_metrics
WHERE video_id = 123
ORDER BY captured_at DESC;
```

## 🔍 트러블슈팅

### 1. 인증 오류

**문제**: `ValueError: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set`

**해결**:
- `.env` 파일에 `GOOGLE_CLIENT_ID`와 `GOOGLE_CLIENT_SECRET`가 설정되어 있는지 확인
- 환경 변수가 제대로 로드되는지 확인

### 2. API 권한 오류

**문제**: `HttpError 403: Forbidden`

**해결**:
- Google Cloud Console에서 YouTube Analytics API가 활성화되어 있는지 확인
- OAuth 동의 화면에서 필요한 스코프가 추가되어 있는지 확인
- `token_analytics.pickle` 파일을 삭제하고 다시 인증

### 3. 데이터가 없음

**문제**: YouTube Analytics API에서 데이터를 가져올 수 없음

**해결**:
- YouTube Analytics는 실시간이 아니라 24-48시간 지연됨
- 영상이 실제로 YouTube에 게시되어 있는지 확인
- `youtube_video_id`가 올바르게 저장되어 있는지 확인

### 4. 중복 데이터

**문제**: 같은 날짜에 여러 번 데이터가 저장됨

**해결**:
- `performance_metrics` 테이블에는 `idx_performance_metrics_daily_unique` 인덱스가 있어 daily snapshot은 중복 방지됨
- 하지만 realtime snapshot은 중복 가능
- 필요시 스크립트 실행 전에 기존 데이터 확인

## 📝 주의사항

1. **YouTube Analytics API 할당량**:
   - 일일 할당량: 10,000 쿼리
   - 영상당 1개의 쿼리 사용
   - 영상이 많을 경우 할당량 초과 가능성 있음

2. **데이터 지연**:
   - YouTube Analytics 데이터는 24-48시간 지연됨
   - 실시간 데이터가 필요한 경우 YouTube Data API v3 사용 고려

3. **인증 토큰**:
   - `token_analytics.pickle` 파일은 민감 정보이므로 `.gitignore`에 추가
   - 프로덕션 환경에서는 서비스 계정 사용 권장

4. **성능**:
   - 영상이 많을 경우 수집 시간이 오래 걸릴 수 있음
   - 배치 처리 또는 비동기 처리 고려

## 🔄 다음 단계

1. **실시간 데이터 수집**: YouTube Data API v3를 사용하여 더 빠른 데이터 수집
2. **알림 기능**: 특정 조건(조회수 급증 등)에 알림 전송
3. **예측 분석**: 머신러닝을 사용한 성과 예측
4. **자동 최적화**: 성과 데이터 기반 자동 밈 추천
