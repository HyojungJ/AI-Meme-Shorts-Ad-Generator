# YouTube 영상 성과 분석 시스템 구축 완료 ✅

## 📋 구현 내용

YouTube에 업로드된 영상의 성과 데이터를 자동으로 수집하고 프론트엔드에서 확인할 수 있는 시스템을 구축했습니다.

## 🎯 주요 기능

### 1. 데이터 수집 스크립트
- **파일**: `backend/scripts/youtube_analytics_collector.py`
- **기능**:
  - YouTube Analytics API를 통해 영상 성과 데이터 수집
  - 조회수, 좋아요, 댓글, 공유, 시청 시간 등
  - `performance_metrics` 테이블에 자동 저장
  - 특정 영상 또는 전체 영상 수집 가능

### 2. 자동 스케줄러
- **파일**: `backend/scripts/schedule_analytics_collection.py`
- **기능**:
  - 매일 오전 9시 자동 실행
  - 백그라운드 서비스로 운영 가능
  - systemd 설정 예시 포함

### 3. 테스트 도구
- **파일**: `backend/scripts/test_analytics_api.py`
- **기능**:
  - YouTube Analytics API 연결 테스트
  - 게시된 영상 목록 확인
  - 샘플 데이터 수집 테스트

### 4. API 엔드포인트 (기존)
이미 구현되어 있는 API 엔드포인트들:

#### 클라이언트용
- `GET /api/v1/analytics/dashboard` - 내 회사 성과 대시보드
- `GET /api/v1/analytics/videos/{video_id}` - 특정 영상 성과
- `GET /api/v1/analytics/summary` - 간단 요약

#### 관리자용
- `GET /api/v1/admin/analytics/dashboard` - 전체 대시보드
- `GET /api/v1/admin/analytics/memes` - 밈별 성과
- `GET /api/v1/admin/analytics/categories` - 카테고리별 성과
- `GET /api/v1/admin/analytics/trends` - 시계열 트렌드

### 5. 프론트엔드 (기존)
이미 구현되어 있는 프론트엔드 페이지들:

- **클라이언트 대시보드** (`/main`):
  - 조회수 추이 그래프
  - 반응률 추이 그래프
  - 최근 영상 목록 및 성과
  - 프로젝트 상태 분포

- **관리자 분석 페이지** (`/admin/analytics`):
  - 전체 플랫폼 성과
  - 밈별 성과 비교
  - 카테고리별 성과 분석
  - 트렌드 분석

## 📁 생성된 파일

```
backend/
├── scripts/
│   ├── youtube_analytics_collector.py      # 데이터 수집 스크립트
│   ├── schedule_analytics_collection.py    # 자동 스케줄러
│   ├── test_analytics_api.py               # API 테스트 도구
│   ├── README_YOUTUBE_ANALYTICS.md         # 상세 가이드
│   └── QUICK_START_ANALYTICS.md            # 빠른 시작 가이드
├── pyproject.toml                           # schedule 패키지 추가
└── .gitignore                               # 토큰 파일 제외
```

## 🚀 사용 방법

### 1. 환경 설정

```bash
# 패키지 설치
cd backend
uv sync

# .env 파일에 추가
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 2. API 연결 테스트

```bash
cd backend
python scripts/test_analytics_api.py
```

### 3. 데이터 수집

```bash
# 특정 영상
python scripts/youtube_analytics_collector.py --video-id 1

# 모든 영상
python scripts/youtube_analytics_collector.py --all

# 최근 7일 데이터
python scripts/youtube_analytics_collector.py --all --days 7
```

### 4. 자동화 (선택)

```bash
# 스케줄러 시작 (매일 오전 9시 자동 실행)
python scripts/schedule_analytics_collection.py
```

### 5. 프론트엔드에서 확인

```bash
cd frontend
npm run dev
```

- 클라이언트: http://localhost:3000/main
- 관리자: http://localhost:3000/admin/analytics

## 🔍 데이터 흐름

```
YouTube 영상 업로드
    ↓
YouTube Analytics API
    ↓
youtube_analytics_collector.py (데이터 수집)
    ↓
performance_metrics 테이블 (DB 저장)
    ↓
Backend API (/api/v1/analytics/*)
    ↓
Frontend (대시보드 표시)
```

## 📊 수집되는 데이터

- **조회수** (views)
- **좋아요** (likes)
- **싫어요** (dislikes)
- **댓글** (comments)
- **공유** (shares)
- **시청 시간** (watch_time_seconds)
- **평균 시청 시간** (average_view_duration)
- **반응률** (engagement_rate) - 자동 계산
- **구독자 증가** (subscribers_gained)

## ⚠️ 주의사항

1. **YouTube Analytics API 지연**:
   - 데이터는 24-48시간 지연됨
   - 실시간 데이터가 아님

2. **API 할당량**:
   - 일일 10,000 쿼리 제한
   - 영상당 1개 쿼리 사용

3. **인증 토큰**:
   - `token_analytics.pickle` 파일은 Git에 커밋하지 않음
   - 프로덕션에서는 서비스 계정 사용 권장

4. **데이터베이스**:
   - `performance_metrics` 테이블에 저장
   - daily snapshot은 중복 방지 (unique index)

## 📚 문서

- **빠른 시작**: `backend/scripts/QUICK_START_ANALYTICS.md`
- **상세 가이드**: `backend/scripts/README_YOUTUBE_ANALYTICS.md`
- **API 문서**: `backend/docs/ContentPipelineAPI.md`

## 🎉 완료!

이제 YouTube에 업로드한 영상의 성과를 프론트엔드에서 실시간으로 확인할 수 있습니다!

### 다음 단계

1. **테스트**: 실제 YouTube 영상으로 데이터 수집 테스트
2. **자동화**: 스케줄러를 systemd 서비스로 등록
3. **모니터링**: 데이터 수집 로그 확인 및 알림 설정
4. **최적화**: 성과 데이터 기반 밈 추천 시스템 구축
