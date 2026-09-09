# YouTube Analytics 빠른 시작 가이드

## 🎯 목표

YouTube에 업로드한 영상의 성과(조회수, 좋아요, 댓글 등)를 프론트엔드에서 확인할 수 있도록 설정합니다.

## ⚡ 빠른 시작 (5분)

### 1단계: 패키지 설치

```bash
cd backend
uv sync
```

### 2단계: 환경 변수 설정

`.env` 파일에 Google OAuth 정보 추가:

```env
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

> 💡 **Google OAuth 정보가 없다면?**
> 1. [Google Cloud Console](https://console.cloud.google.com/) 접속
> 2. 프로젝트 생성 또는 선택
> 3. "API 및 서비스 > 라이브러리"에서 "YouTube Analytics API" 활성화
> 4. "API 및 서비스 > 사용자 인증 정보"에서 OAuth 2.0 클라이언트 ID 생성
> 5. 애플리케이션 유형: "데스크톱 앱" 선택

### 3단계: API 연결 테스트

```bash
cd backend
python scripts/test_analytics_api.py
```

처음 실행 시 브라우저가 열리고 Google 계정 로그인을 요청합니다.
- YouTube 채널 소유자 계정으로 로그인
- 권한 승인

### 4단계: 데이터 수집

#### 옵션 A: 특정 영상만 테스트

```bash
# video_id는 videos 테이블의 ID
python scripts/youtube_analytics_collector.py --video-id 1
```

#### 옵션 B: 모든 게시된 영상

```bash
python scripts/youtube_analytics_collector.py --all
```

### 5단계: 프론트엔드에서 확인

1. 프론트엔드 실행:
   ```bash
   cd frontend
   npm run dev
   ```

2. 브라우저에서 확인:
   - 클라이언트: `http://localhost:3000/main` (대시보드)
   - 관리자: `http://localhost:3000/admin/analytics` (분석 페이지)

## 🔄 자동화 (선택사항)

매일 자동으로 데이터를 수집하려면:

```bash
cd backend
python scripts/schedule_analytics_collection.py
```

- 매일 오전 9시에 자동 실행
- Ctrl+C로 종료
- 백그라운드 실행 권장 (screen, tmux, systemd 등)

## 📊 확인 사항

### ⚠️ 비공개 영상 주의사항

**비공개 영상도 데이터를 수집할 수 있지만 조회수가 0이거나 매우 적습니다.**

YouTube 공개 상태별 차이:
- **비공개 (Private)**: 본인과 지정한 사용자만 시청 가능 → 조회수 거의 없음
- **일부 공개 (Unlisted)**: 링크를 아는 사람만 시청 가능 → 조회수 집계됨 ✅ **테스트 추천**
- **공개 (Public)**: 모든 사람이 시청 가능 → 실제 성과 데이터 수집 가능

**영상 공개 상태 변경 방법:**
1. YouTube Studio (https://studio.youtube.com) 접속
2. 콘텐츠 → 해당 영상 선택
3. 공개 상태 → "일부 공개" 또는 "공개" 선택
4. 저장

### 데이터가 수집되었는지 확인

```sql
-- PostgreSQL에서 확인
SELECT 
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
```

### API 엔드포인트 테스트

```bash
# 클라이언트 대시보드 API
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 특정 영상 성과 API
curl -X GET "http://localhost:8000/api/v1/analytics/videos/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ❓ 문제 해결

### "조회수가 0입니다"

**원인**: 영상이 비공개 상태이거나 최근에 업로드됨

**해결**:
1. YouTube Studio에서 영상 공개 상태를 "일부 공개" 또는 "공개"로 변경
2. 영상 업로드 후 1-2일 기다리기 (YouTube Analytics 지연)
3. 직접 영상을 몇 번 재생해서 조회수 생성

### "데이터를 가져올 수 없습니다"

**원인**: YouTube Analytics는 24-48시간 지연됨

**해결**: 
- 영상 업로드 후 1-2일 기다리기
- 또는 YouTube Data API v3 사용 (실시간에 가까움)

### "인증 오류"

**원인**: OAuth 토큰이 만료되었거나 잘못됨

**해결**:
```bash
rm token_analytics.pickle
python scripts/test_analytics_api.py
```

### "API 할당량 초과"

**원인**: YouTube Analytics API 일일 할당량(10,000 쿼리) 초과

**해결**:
- 다음 날까지 대기
- 또는 Google Cloud Console에서 할당량 증가 요청

## 📚 더 알아보기

- 상세 가이드: `README_YOUTUBE_ANALYTICS.md`
- API 문서: `backend/docs/ContentPipelineAPI.md`
- 프론트엔드 가이드: `frontend/docs/FRONTEND_GUIDE.md`

## 🎉 완료!

이제 프론트엔드에서 실시간으로 영상 성과를 확인할 수 있습니다!
