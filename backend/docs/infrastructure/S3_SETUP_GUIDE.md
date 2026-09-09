# AWS S3 설정 가이드

## 개요

Admeme 플랫폼에서 생성되는 모든 미디어 파일(이미지, 음성, 영상)은 AWS S3에 저장됩니다.

## 파일 저장 구조

### S3 버킷 구조
```
admeme-media-bucket/
├── characters/          # 캐릭터 이미지
│   └── {company_id}/
│       └── {timestamp}_{filename}
├── voices/              # 캐릭터 음성
│   └── {company_id}/
│       └── {timestamp}_{filename}
├── products/            # 제품 이미지
│   └── {company_id}/
│       └── {timestamp}_{filename}
└── videos/              # 최종 영상
    └── {company_id}/
        └── {timestamp}_{filename}
```

### 파일 타입별 제한사항

| 파일 타입 | 허용 포맷 | 최대 크기 |
|----------|----------|----------|
| 캐릭터 이미지 | .jpg, .jpeg, .png, .webp | 10MB |
| 캐릭터 음성 | .mp3, .wav, .m4a | 50MB |
| 제품 이미지 | .jpg, .jpeg, .png, .webp | 10MB |
| 최종 영상 | .mp4, .mov, .avi | 500MB |

## AWS S3 버킷 생성

### 1. AWS 콘솔에서 S3 버킷 생성

1. AWS Management Console 로그인
2. S3 서비스로 이동
3. "버킷 만들기" 클릭

### 2. 버킷 설정

**기본 설정:**
- 버킷 이름: `admeme-media-{환경}` (예: admeme-media-prod, admeme-media-dev)
- AWS 리전: `ap-northeast-2` (서울)
- 객체 소유권: ACL 비활성화됨 (권장)

**퍼블릭 액세스 차단 설정:**
```
✅ 모든 퍼블릭 액세스 차단
  ✅ 새 ACL을 통해 부여된 버킷 및 객체에 대한 퍼블릭 액세스 차단
  ✅ 임의의 ACL을 통해 부여된 버킷 및 객체에 대한 퍼블릭 액세스 차단
  ✅ 새 퍼블릭 버킷 또는 액세스 포인트 정책을 통해 부여된 버킷 및 객체에 대한 퍼블릭 액세스 차단
  ✅ 임의의 퍼블릭 버킷 또는 액세스 포인트 정책을 통해 부여된 버킷 및 객체에 대한 퍼블릭 액세스 차단
```

**버킷 버전 관리:**
- 비활성화 (선택사항: 활성화 시 파일 복구 가능)

**암호화:**
- 서버 측 암호화: SSE-S3 (Amazon S3 관리형 키)

### 3. CORS 설정

S3 버킷 → 권한 → CORS(Cross-Origin Resource Sharing) 편집:

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT",
            "POST",
            "DELETE",
            "HEAD"
        ],
        "AllowedOrigins": [
            "http://localhost:3000",
            "http://localhost:8000",
            "https://yourdomain.com"
        ],
        "ExposeHeaders": [
            "ETag",
            "x-amz-request-id"
        ],
        "MaxAgeSeconds": 3000
    }
]
```

### 4. 수명 주기 정책 (선택사항)

임시 파일 자동 삭제를 위한 수명 주기 규칙:

```json
{
    "Rules": [
        {
            "Id": "DeleteOldTempFiles",
            "Status": "Enabled",
            "Prefix": "temp/",
            "Expiration": {
                "Days": 7
            }
        }
    ]
}
```

## IAM 사용자 생성 및 권한 설정

### 1. IAM 사용자 생성

1. AWS IAM 콘솔로 이동
2. "사용자" → "사용자 추가"
3. 사용자 이름: `admeme-s3-user`
4. 액세스 유형: 프로그래밍 방식 액세스

### 2. 권한 정책 생성

**정책 이름:** `AdmemeS3Policy`

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3Operations",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::admeme-media-*",
                "arn:aws:s3:::admeme-media-*/*"
            ]
        },
        {
            "Sid": "AllowPresignedURL",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::admeme-media-*/*"
        }
    ]
}
```

### 3. Access Key 생성

1. IAM 사용자 선택
2. "보안 자격 증명" 탭
3. "액세스 키 만들기"
4. **Access Key ID**와 **Secret Access Key** 안전하게 저장

⚠️ **보안 주의사항:**
- Secret Access Key는 생성 시 한 번만 표시됩니다
- 절대 코드에 하드코딩하지 마세요
- 환경 변수로만 관리하세요

## 환경 변수 설정

### .env 파일 설정

```bash
# AWS S3 설정
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-2
S3_BUCKET_NAME=admeme-media-prod
```

### 환경별 버킷 이름

```bash
# 개발 환경
S3_BUCKET_NAME=admeme-media-dev

# 스테이징 환경
S3_BUCKET_NAME=admeme-media-staging

# 프로덕션 환경
S3_BUCKET_NAME=admeme-media-prod
```

## 백엔드 코드 설정

### 1. 필요한 패키지 설치

```bash
pip install boto3
```

또는 `pyproject.toml`에 추가:
```toml
[tool.poetry.dependencies]
boto3 = "^1.34.0"
```

### 2. S3 클라이언트 초기화

`app/services/s3_service.py` 생성:

```python
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

s3_client = boto3.client(
    's3',
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)
```

### 3. Mock 모드에서 실제 S3로 전환

현재 코드는 Mock S3를 사용 중입니다. 실제 S3로 전환하려면:

**scripts/generation/v2/video_routes.py:**
```python
# Mock S3 사용 (현재)
from generation.s3_handler_mock import (
    upload_file_to_s3,
    validate_product_image,
    generate_presigned_url
)

# 실제 S3 사용 (변경)
from generation.v2.s3_handler import (
    upload_file_to_s3,
    validate_product_image,
    generate_presigned_url
)
```

## Pre-signed URL 생성

### 개요

Pre-signed URL은 임시로 S3 객체에 접근할 수 있는 URL입니다.
- 유효 기간: 기본 7일 (604800초)
- 인증 없이 다운로드 가능
- 보안: URL 만료 후 자동 무효화

### 사용 예시

```python
from app.services.s3_service import generate_presigned_url

# 영상 다운로드 URL 생성
video_url = generate_presigned_url(
    s3_url="s3://admeme-media-prod/videos/11/20260126_video.mp4",
    expiration=604800  # 7일
)
```

## 비용 최적화

### 1. S3 스토리지 클래스

| 클래스 | 용도 | 비용 |
|--------|------|------|
| S3 Standard | 자주 액세스하는 파일 (최근 영상) | 높음 |
| S3 Standard-IA | 가끔 액세스하는 파일 (30일 이상) | 중간 |
| S3 Glacier | 아카이브 (1년 이상) | 낮음 |

### 2. 수명 주기 정책 권장사항

```json
{
    "Rules": [
        {
            "Id": "MoveToIA",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 365,
                    "StorageClass": "GLACIER"
                }
            ]
        }
    ]
}
```

### 3. 예상 비용 (서울 리전 기준)

**스토리지 비용:**
- S3 Standard: $0.025/GB/월
- S3 Standard-IA: $0.0138/GB/월

**데이터 전송 비용:**
- 업로드: 무료
- 다운로드 (인터넷): $0.126/GB (첫 10TB)

**예상 월 비용 (100GB 저장, 500GB 다운로드):**
- 스토리지: $2.50
- 전송: $63.00
- **총합: 약 $65.50/월**

## 모니터링 및 알림

### CloudWatch 메트릭

모니터링할 주요 메트릭:
- `BucketSizeBytes`: 버킷 크기
- `NumberOfObjects`: 객체 수
- `AllRequests`: 총 요청 수
- `4xxErrors`: 클라이언트 오류
- `5xxErrors`: 서버 오류

### CloudWatch 알림 설정

1. CloudWatch 콘솔 → 경보 → 경보 생성
2. 메트릭 선택: S3 → Storage Metrics
3. 조건 설정:
   - BucketSizeBytes > 100GB
   - 4xxErrors > 100 (5분간)

## 보안 체크리스트

- [ ] 퍼블릭 액세스 차단 활성화
- [ ] IAM 사용자 최소 권한 원칙 적용
- [ ] Access Key를 환경 변수로 관리
- [ ] CORS 설정에서 허용 도메인 제한
- [ ] 서버 측 암호화 활성화
- [ ] CloudTrail로 S3 API 호출 로깅
- [ ] MFA Delete 활성화 (프로덕션)
- [ ] 버킷 정책으로 IP 제한 (선택사항)

## 트러블슈팅

### 1. Access Denied 오류

**원인:**
- IAM 권한 부족
- 버킷 정책 제한
- 퍼블릭 액세스 차단

**해결:**
```bash
# IAM 정책 확인
aws iam get-user-policy --user-name admeme-s3-user --policy-name AdmemeS3Policy

# 버킷 정책 확인
aws s3api get-bucket-policy --bucket admeme-media-prod
```

### 2. CORS 오류

**원인:**
- CORS 설정 누락
- AllowedOrigins에 도메인 미포함

**해결:**
S3 콘솔 → 권한 → CORS 설정 확인

### 3. Pre-signed URL 만료

**원인:**
- 유효 기간 초과
- 시스템 시간 불일치

**해결:**
```python
# 유효 기간 연장
generate_presigned_url(s3_url, expiration=604800)  # 7일
```

## 참고 자료

- [AWS S3 공식 문서](https://docs.aws.amazon.com/s3/)
- [Boto3 S3 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [S3 요금 계산기](https://calculator.aws/)
