# S3 사용 가이드

## 개요

백엔드 코드에 S3 연동이 완료되었습니다. 이제 실제 AWS S3를 사용하거나 Mock 모드로 개발할 수 있습니다.

## 환경 설정

### 1. Mock 모드 (개발/테스트용)

AWS 계정 없이 로컬에서 개발할 때 사용합니다.

`.env` 파일:
```bash
# Mock 모드 활성화
MOCK_MODE=true

# S3 설정 (Mock 모드에서는 무시됨)
AWS_ACCESS_KEY_ID=mock
AWS_SECRET_ACCESS_KEY=mock
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=mock-bucket
```

### 2. 실제 S3 모드 (프로덕션용)

실제 AWS S3를 사용할 때 설정합니다.

`.env` 파일:
```bash
# Mock 모드 비활성화
MOCK_MODE=false

# 실제 AWS 자격 증명
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=admeme-media-prod
```

## 구현된 기능

### 1. 파일 업로드

**지원 파일 타입:**
- `character_image`: 캐릭터 이미지 (.jpg, .jpeg, .png, .webp, 최대 10MB)
- `character_voice`: 캐릭터 음성 (.mp3, .wav, .m4a, 최대 50MB)
- `product_image`: 제품 이미지 (.jpg, .jpeg, .png, .webp, 최대 10MB)
- `output_video`: 최종 영상 (.mp4, .mov, .avi, 최대 500MB)

**사용 예시:**
```python
from app.services.s3_service import upload_file_to_s3

# 파일 업로드
s3_url = upload_file_to_s3(
    file_content=file_bytes,
    file_type="product_image",
    company_id=11,
    filename="product.jpg",
    content_type="image/jpeg"
)

# 결과: s3://admeme-media-prod/products/11/20260126_120000_product.jpg
```

### 2. Pre-signed URL 생성

다운로드 링크를 생성합니다 (기본 7일 유효).

**사용 예시:**
```python
from app.services.s3_service import generate_presigned_url

# Pre-signed URL 생성
download_url = generate_presigned_url(
    s3_url="s3://admeme-media-prod/videos/11/20260126_video.mp4",
    expiration=604800  # 7일 (초 단위)
)

# 결과: https://admeme-media-prod.s3.ap-northeast-2.amazonaws.com/...
```

### 3. 파일 삭제

**사용 예시:**
```python
from app.services.s3_service import delete_file_from_s3

# 파일 삭제
success = delete_file_from_s3(
    s3_url="s3://admeme-media-prod/products/11/20260126_product.jpg"
)
```

### 4. 파일 검증

**사용 예시:**
```python
from app.services.s3_service import validate_product_image

# 파일 검증
is_valid, error_msg = validate_product_image(
    filename="product.jpg",
    file_size=5242880  # 5MB
)

if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)
```

## API 엔드포인트

### 1. 영상 생성 (파일 업로드)

```http
POST /api/v1/videos/generate
Content-Type: multipart/form-data

{
  "product_name": "프리미엄 커피",
  "product_category": "식음료",
  "product_highlight": "최고의 맛",
  "product_images": [파일1, 파일2],
  ...
}
```

**동작:**
1. 제품 이미지 검증 (크기, 포맷)
2. S3에 업로드
3. S3 URL을 DB에 저장

### 2. 영상 다운로드

```http
GET /api/v1/videos/{video_id}/download
Authorization: Bearer {token}
```

**응답:**
```json
{
  "video_id": 1,
  "download_url": "https://admeme-media-prod.s3.amazonaws.com/...",
  "expires_at": "2026-02-02T12:00:00",
  "file_size": 10485760,
  "format": "mp4"
}
```

**동작:**
1. 권한 확인 (본인 회사 영상만)
2. Pre-signed URL 생성 (7일 유효)
3. 다운로드 링크 반환

### 3. 헬스 체크

#### 기본 헬스 체크
```http
GET /api/v1/health/health
```

**응답:**
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "mode": "production"
}
```

#### S3 연결 확인
```http
GET /api/v1/health/s3
```

**응답 (성공):**
```json
{
  "status": "healthy",
  "s3": "connected",
  "bucket": "admeme-media-prod",
  "region": "ap-northeast-2",
  "message": "S3 연결 성공: admeme-media-prod"
}
```

**응답 (실패):**
```json
{
  "status": "unhealthy",
  "s3": "connection_failed",
  "bucket": "admeme-media-prod",
  "region": "ap-northeast-2",
  "error": "버킷을 찾을 수 없습니다"
}
```

#### 전체 시스템 상태
```http
GET /api/v1/health/all
```

**응답:**
```json
{
  "app": {
    "status": "healthy",
    "version": "4.0.0",
    "mode": "production"
  },
  "database": {
    "status": "healthy",
    "connection": "connected"
  },
  "s3": {
    "status": "healthy",
    "connection": "connected",
    "bucket": "admeme-media-prod",
    "region": "ap-northeast-2"
  },
  "overall_status": "healthy"
}
```

## 테스트 방법

### 1. Mock 모드 테스트

```bash
# .env 설정
MOCK_MODE=true

# 서버 실행
uvicorn app.main:app --reload

# 헬스 체크
curl http://localhost:8000/api/v1/health/s3
```

**예상 응답:**
```json
{
  "status": "mock",
  "s3": "mock mode enabled",
  "message": "S3 연결 테스트를 건너뜁니다 (Mock 모드)"
}
```

### 2. 실제 S3 테스트

```bash
# .env 설정
MOCK_MODE=false
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_NAME=admeme-media-dev

# 서버 실행
uvicorn app.main:app --reload

# S3 연결 확인
curl http://localhost:8000/api/v1/health/s3
```

**예상 응답 (성공):**
```json
{
  "status": "healthy",
  "s3": "connected",
  "bucket": "admeme-media-dev",
  "region": "ap-northeast-2",
  "message": "S3 연결 성공: admeme-media-dev"
}
```

### 3. 파일 업로드 테스트

```bash
# 영상 생성 요청 (제품 이미지 업로드)
curl -X POST http://localhost:8000/api/v1/videos/generate \
  -H "Authorization: Bearer {token}" \
  -F "product_name=테스트 제품" \
  -F "product_category=전자제품" \
  -F "product_highlight=최고의 품질" \
  -F "product_images=@/path/to/image.jpg"
```

**로그 확인:**
```
✅ S3 업로드 성공: s3://admeme-media-dev/products/11/20260126_120000_image.jpg (크기: 524288 bytes)
```

### 4. 다운로드 링크 테스트

```bash
# 영상 다운로드 링크 생성
curl http://localhost:8000/api/v1/videos/1/download \
  -H "Authorization: Bearer {token}"
```

**응답:**
```json
{
  "video_id": 1,
  "download_url": "https://admeme-media-dev.s3.ap-northeast-2.amazonaws.com/videos/11/20260126_video.mp4?X-Amz-Algorithm=...",
  "expires_at": "2026-02-02T12:00:00",
  "file_size": 10485760,
  "format": "mp4"
}
```

## 에러 처리

### 1. AWS 자격 증명 오류

**에러:**
```
S3 클라이언트가 초기화되지 않았습니다. AWS 자격 증명을 확인하세요.
```

**해결:**
- `.env` 파일에 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` 확인
- IAM 사용자 권한 확인

### 2. 버킷 접근 오류

**에러:**
```
S3 업로드 실패: Access Denied
```

**해결:**
- IAM 정책에 `s3:PutObject` 권한 추가
- 버킷 정책 확인

### 3. 파일 크기 초과

**에러:**
```
이미지 크기가 너무 큽니다. 최대: 10MB
```

**해결:**
- 파일 크기 확인
- 필요시 이미지 압축

### 4. 지원하지 않는 포맷

**에러:**
```
지원하지 않는 이미지 형식입니다. 허용: .jpg, .jpeg, .png, .webp
```

**해결:**
- 파일 확장자 확인
- 지원 포맷으로 변환

## 모니터링

### 로그 확인

S3 작업은 모두 로그로 기록됩니다:

```python
# 성공 로그
✅ S3 업로드 성공: s3://bucket/key (크기: 1024 bytes)
✅ Pre-signed URL 생성 성공 (유효기간: 604800초)
✅ S3 파일 삭제 성공: s3://bucket/key

# 실패 로그
❌ S3 업로드 실패 (AccessDenied): Access Denied
❌ Pre-signed URL 생성 실패: 버킷을 찾을 수 없습니다
❌ S3 파일 삭제 실패: NoSuchKey
```

### CloudWatch 메트릭

AWS 콘솔에서 확인:
- S3 → 메트릭 → 버킷 메트릭
- `BucketSizeBytes`: 버킷 크기
- `NumberOfObjects`: 객체 수
- `AllRequests`: 총 요청 수

## 다음 단계

1. **AWS 계정 준비** → [S3_SETUP_GUIDE.md](./S3_SETUP_GUIDE.md) 참고
2. **S3 버킷 생성** → 개발/프로덕션 환경별로 생성
3. **IAM 권한 설정** → Access Key 생성
4. **환경 변수 설정** → `.env` 파일 업데이트
5. **연결 테스트** → `/api/v1/health/s3` 호출
6. **파일 업로드 테스트** → 영상 생성 API 호출
7. **프로덕션 배포** → Mock 모드 비활성화

## 참고 자료

- [S3 설정 가이드](./S3_SETUP_GUIDE.md)
- [S3 구현 작업 체크리스트](./S3_IMPLEMENTATION_TASK.md)
- [AWS S3 공식 문서](https://docs.aws.amazon.com/s3/)
- [Boto3 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
