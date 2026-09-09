# YouTube 자동 게시 통합

## 개요

Admin이 승인한 영상을 YouTube에 자동으로 업로드하는 기능입니다.

## 구현 내용

### 1. YouTube 서비스 (`app/services/youtube_service.py`)

YouTube Data API v3를 사용하여 영상을 업로드하는 서비스 클래스입니다.

**주요 기능:**
- OAuth2 인증을 통한 YouTube API 접근
- 영상 업로드 (재시도 로직 포함)
- 액세스 토큰 자동 갱신

**사용 예시:**
```python
from app.services.youtube_service import YouTubeService

youtube_service = YouTubeService(
    access_token=channel.access_token,  # 자동으로 복호화됨
    refresh_token=channel.refresh_token,  # 자동으로 복호화됨
    token_expiry=channel.token_expires_at
)

result = youtube_service.upload_video(
    file_path="/path/to/video.mp4",
    title="영상 제목",
    description="영상 설명",
    privacy_status="public"  # public, private, unlisted
)
```

### 2. Admin API 수정 (`app/api/v1/endpoints/admin.py`)

`POST /api/v1/admin/videos/{video_id}/publish` 엔드포인트가 YouTube 업로드를 수행합니다.

**처리 흐름:**
1. 영상 상태 확인 (`client_approved` 상태만 게시 가능)
2. YouTube 채널 정보 조회
3. `AdminVideoPost` 레코드 생성
4. 즉시 업로드 또는 예약 게시
   - **즉시 업로드**: S3에서 영상 다운로드 → YouTube 업로드 → 상태 업데이트
   - **예약 게시**: 상태만 업데이트 (별도 스케줄러 필요)

### 3. 스키마 수정 (`app/schemas/admin.py`)

`PublishVideoRequest`에 `privacy_status` 필드 추가:
- `public`: 전체 공개
- `private`: 비공개
- `unlisted`: 링크가 있는 사용자만

### 4. 토큰 암호화 (`app/core/security.py`, `app/models/youtube.py`)

**보안 기능:**
- OAuth 토큰(access_token, refresh_token)을 Fernet 대칭 암호화로 DB에 저장
- 모델의 hybrid_property를 사용해 자동으로 암호화/복호화
- JWT_SECRET_KEY를 기반으로 암호화 키 생성

**동작 방식:**
```python
# 저장할 때 자동 암호화
channel.access_token = "raw_token"  # 내부적으로 암호화되어 저장됨

# 조회할 때 자동 복호화
token = channel.access_token  # 자동으로 복호화됨
```

### 5. 환경 변수 설정 (`.env`)

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## 데이터베이스 구조

### `admin_youtube_channels` 테이블
- `channel_id`: 채널 ID (PK)
- `admin_id`: Admin ID (FK)
- `yt_channel_id`: YouTube 채널 ID
- `channel_name`: 채널 이름
- `channel_handle`: 채널 핸들 (@username)
- `access_token`: OAuth 액세스 토큰 (암호화됨)
- `refresh_token`: OAuth 리프레시 토큰 (암호화됨)
- `token_expires_at`: 토큰 만료 시간
- `is_active`: 활성화 여부

### `admin_video_posts` 테이블
- `post_id`: 게시 ID (PK)
- `video_id`: 영상 ID (FK)
- `channel_id`: 채널 ID (FK)
- `yt_video_id`: YouTube 영상 ID
- `yt_title`: YouTube 제목
- `yt_description`: YouTube 설명
- `post_status`: 게시 상태 (pending, published, failed)
- `scheduled_at`: 예약 시간
- `published_at`: 게시 시간
- `error_message`: 에러 메시지
- `retry_count`: 재시도 횟수

## API 사용 예시

### 영상 게시 (즉시 업로드)

```http
POST /api/v1/admin/videos/3/publish
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "channel_id": 1,
  "yt_title": "매끈매끈하다 매끈매끈한",
  "yt_description": "from admeme",
  "privacy_status": "public"
}
```

**응답:**
```json
{
  "video_id": 3,
  "post_id": 1,
  "status": "published",
  "message": "YouTube에 업로드 완료! 영상 ID: abc123xyz"
}
```

### 영상 게시 (예약)

```http
POST /api/v1/admin/videos/3/publish
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "channel_id": 1,
  "yt_title": "매끈매끈하다 매끈매끈한",
  "yt_description": "from admeme",
  "privacy_status": "public",
  "scheduled_at": "2026-02-01T10:00:00"
}
```

**응답:**
```json
{
  "video_id": 3,
  "post_id": 1,
  "status": "scheduled",
  "message": "YouTube 게시가 예약되었습니다"
}
```

## YouTube 채널 설정

### 1. Google Cloud Console 설정
1. Google Cloud Console에서 프로젝트 생성
2. YouTube Data API v3 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. 승인된 리디렉션 URI 추가: `http://localhost:8080/`
5. 테스트 사용자 추가 (앱이 테스트 모드인 경우)

### 2. 채널 인증 (최초 1회)
루트 디렉토리의 `main.py` 스크립트를 사용하여 OAuth 인증을 수행합니다:

```bash
uv run python main.py --file="test.mp4" --title="Test" --description="Test" --privacyStatus="private" --keywords="test"
```

브라우저가 열리면 Google 계정으로 로그인하고 권한을 승인합니다.
인증이 완료되면 `main.py-oauth2.json` 파일이 생성됩니다.

### 3. 채널 정보 DB 저장
인증 후 생성된 토큰 정보를 `admin_youtube_channels` 테이블에 저장합니다:

```sql
UPDATE admin_youtube_channels
SET 
    yt_channel_id = 'UCFVXdh2ss60nRj6xLViP1NA',
    channel_name = 'AdMeme',
    channel_handle = '@AdMeme-skn',
    access_token = '{main.py-oauth2.json의 access_token}',
    refresh_token = '{main.py-oauth2.json의 refresh_token}',
    token_expires_at = '{main.py-oauth2.json의 token_expiry}',
    is_active = true
WHERE admin_id = 2;
```

**주의:** 토큰은 자동으로 암호화되어 저장됩니다.

## 에러 처리

### 업로드 실패 시
- `post_status`가 `failed`로 변경
- `error_message`에 에러 내용 저장
- 영상 상태는 `client_approved` 유지 (재시도 가능)

### 토큰 만료 시
- `YouTubeService.refresh_access_token()` 메서드가 자동으로 토큰 갱신
- 갱신 실패 시 재인증 필요

## 보안 고려사항

### 토큰 암호화
- 모든 OAuth 토큰은 Fernet 대칭 암호화로 DB에 저장
- JWT_SECRET_KEY를 기반으로 암호화 키 생성
- 모델 조회 시 자동으로 복호화되어 반환

### 권장 사항
1. JWT_SECRET_KEY를 강력한 값으로 설정
2. 정기적으로 토큰 갱신
3. 토큰 만료 시간 모니터링
4. 에러 로그에서 토큰 정보 노출 방지

## 향후 개선 사항

1. **예약 게시 스케줄러**: 백그라운드 작업으로 예약된 영상 자동 업로드
2. **토큰 자동 갱신**: 만료 전 자동으로 토큰 갱신
3. **업로드 진행률**: 대용량 영상 업로드 시 진행률 표시
4. **다중 채널 지원**: Admin이 여러 YouTube 채널 관리
5. **영상 분석**: YouTube Analytics API 연동

## 참고 자료

- [YouTube Data API v3 문서](https://developers.google.com/youtube/v3)
- [OAuth 2.0 인증](https://developers.google.com/identity/protocols/oauth2)
- [영상 업로드 가이드](https://developers.google.com/youtube/v3/guides/uploading_a_video)
- [Fernet 암호화](https://cryptography.io/en/latest/fernet/)
