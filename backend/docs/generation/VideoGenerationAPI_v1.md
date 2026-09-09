# 영상 생성 API v1

## 개요

사용자가 캐릭터 이미지와 음성 파일을 직접 업로드하여 영상을 생성하는 API입니다.

**작업 기간**: 2026-01-21 이전  
**위치**: `scripts/generation/v1/`

---

## 시스템 구조

```
사용자 요청
  ↓
파일 업로드 (캐릭터 이미지, 음성, 제품 이미지)
  ↓
S3 업로드
  ↓
DB 저장 (workflow_execution)
  ↓
영상 생성 시작
  ↓
완료
```

---

## API 엔드포인트

### 1. POST /api/videos/generate

영상 생성 요청

**요청 (Multipart Form Data)**

필수 필드:
- `company_name` (string): 회사 이름
- `product_name` (string): 제품 이름
- `product_category` (string): 제품 카테고리
- `product_highlight` (string): 제품 강조문구
- `character_tone` (string): 캐릭터 말투
- `character_image` (file): 캐릭터 이미지 파일 (jpg/png, 최대 10MB)
- `character_voice` (file): 캐릭터 음성 파일 (mp3/wav, 최대 50MB)
- `product_images` (file[]): 제품 이미지 파일 (최대 3장, 각 10MB)

선택 필드:
- `meme_id` (int): 밈 ID
- `reference_notes` (string): 참고 사항

**응답**

```json
{
  "execution_id": "uuid",
  "status": "created",
  "message": "영상 생성 요청이 접수되었습니다."
}
```

### 2. GET /api/videos/status/{execution_id}

워크플로우 상태 조회

**응답**

```json
{
  "execution_id": "uuid",
  "status": "created|processing|completed|failed",
  "current_stage": "string",
  "progress_percentage": 0,
  "output_video_url": "string",
  "error_message": "string",
  "created_at": "datetime",
  "completed_at": "datetime"
}
```

### 3. GET /api/videos/my-videos

내 영상 목록 조회

**쿼리 파라미터**
- `limit` (int): 조회 개수 (기본 10)

**응답**

워크플로우 목록 배열

---

## 데이터베이스

### workflow_execution 테이블

```sql
CREATE TABLE workflow_execution (
    execution_id UUID PRIMARY KEY,
    company_id INT NOT NULL,
    user_id INT NOT NULL,
    meme_id INT,
    workflow_type VARCHAR(50) DEFAULT 'video',
    status VARCHAR(50) DEFAULT 'created',
    current_stage VARCHAR(100),
    progress_percentage INT DEFAULT 0,
    input_params JSONB NOT NULL,
    output_result JSONB,
    total_cost_usd NUMERIC(10, 4) DEFAULT 0,
    retry_count INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

### input_params 구조

```json
{
  "company_name": "테스트 회사",
  "product_name": "제품명",
  "product_category": "카테고리",
  "product_highlight": "강조문구",
  "character_tone": "친근한",
  "character_image_url": "s3://bucket/characters/1/image.jpg",
  "character_voice_url": "s3://bucket/voices/1/voice.mp3",
  "product_images": ["s3://bucket/products/1/prod1.jpg"],
  "meme_id": 1,
  "reference_notes": "참고사항"
}
```

### output_result 구조

```json
{
  "video_url": "s3://bucket/videos/1/final.mp4"
}
```

---

## 파일 처리

### S3 경로 규칙

- 캐릭터 이미지: `characters/{company_id}/{timestamp}_{filename}`
- 캐릭터 음성: `voices/{company_id}/{timestamp}_{filename}`
- 제품 이미지: `products/{company_id}/{timestamp}_{filename}`
- 출력 영상: `videos/{company_id}/{timestamp}_{filename}`

### 파일 검증

**캐릭터 이미지**
- 허용 포맷: jpg, jpeg, png, webp
- 최대 크기: 10MB

**캐릭터 음성**
- 허용 포맷: mp3, wav, m4a
- 최대 크기: 50MB

**제품 이미지**
- 허용 포맷: jpg, jpeg, png, webp
- 최대 크기: 10MB
- 최대 개수: 3장

---

## 주요 파일

### scripts/generation/v1/video_routes.py

API 엔드포인트 정의

주요 함수:
- `generate_video()`: 영상 생성 요청 처리
- `get_video_status()`: 상태 조회
- `get_my_videos()`: 목록 조회

### scripts/generation/v1/database.py

데이터베이스 모델 및 함수

주요 함수:
- `create_workflow()`: 워크플로우 생성
- `get_workflow_by_id()`: ID로 조회
- `get_workflows_by_user()`: 사용자별 조회
- `update_workflow_status()`: 상태 업데이트
- `check_duplicate_workflow()`: 중복 확인

### scripts/generation/v1/s3_handler.py

S3 파일 업로드 및 검증

주요 함수:
- `upload_file_to_s3()`: S3 업로드
- `generate_presigned_url()`: 임시 URL 생성
- `validate_character_image()`: 이미지 검증
- `validate_character_voice()`: 음성 검증
- `validate_product_image()`: 제품 이미지 검증

---

## 테스트 방법

### 1. 서버 실행

```bash
uv run uvicorn scripts.main:app --reload --port 8000
```

### 2. API 테스트

```python
import requests

# 로그인
response = requests.post('http://localhost:8000/auth/v2/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = response.json()['access_token']

# 영상 생성 요청
files = {
    'character_image': ('char.jpg', open('char.jpg', 'rb'), 'image/jpeg'),
    'character_voice': ('voice.mp3', open('voice.mp3', 'rb'), 'audio/mpeg'),
    'product_images': ('product.jpg', open('product.jpg', 'rb'), 'image/jpeg')
}
data = {
    'company_name': '테스트 회사',
    'product_name': '제품명',
    'product_category': '카테고리',
    'product_highlight': '강조문구',
    'character_tone': '친근한'
}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:8000/api/videos/generate',
    files=files,
    data=data,
    headers=headers
)
print(response.json())
```

---

## 상태 값

- `created`: 요청 접수됨
- `processing`: 영상 생성 중
- `completed`: 완료
- `failed`: 실패
- `cancelled`: 취소됨

---

## 제한사항

- 캐릭터 이미지/음성을 사용자가 직접 준비해야 함
- 파일 업로드 시간이 소요됨
- 부적절한 파일 업로드 가능성
- 사용자 검수 과정 없음
