# 영상 생성 API v2

## 개요

사용자가 원하는 분위기를 입력하면 AI가 캐릭터를 생성하고, 사용자 승인 후 영상을 생성하는 API입니다.

**작업 기간**: 2026-01-21  
**위치**: `scripts/generation/v2/`

---

## v1에서 변경된 사항

### 제거된 것
- 캐릭터 이미지 파일 업로드
- 캐릭터 음성 파일 업로드
- 캐릭터 파일 검증 로직

### 추가된 것
- 캐릭터 분위기/스타일 텍스트 입력
- 캐릭터 미리보기 API
- 승인/거부 API
- 재생성 API
- 4개의 새로운 상태 값

---

## 시스템 구조

```
사용자 요청 (분위기 입력)
  ↓
DB 저장 (status="created")
  ↓
팀원의 AI 시스템이 캐릭터 생성
  ↓
DB 업데이트 (status="pending_approval")
  ↓
사용자 검수
  ↓
승인 (status="approved") / 거부 (status="rejected")
  ↓
영상 생성 시작
  ↓
완료 (status="completed")
```

---

## API 엔드포인트

### 1. POST /api/videos/generate

영상 생성 요청 (1단계: 캐릭터 생성 요청)

**요청 (Multipart Form Data)**

필수 필드:
- `company_name` (string): 회사 이름
- `product_name` (string): 제품 이름
- `product_category` (string): 제품 카테고리
- `product_highlight` (string): 제품 강조문구
- `character_mood` (string): 캐릭터 분위기 (예: "밝고 활기찬")
- `character_style` (string): 캐릭터 스타일 (예: "20대 여성")
- `voice_tone` (string): 음성 톤 (예: "친근한")
- `product_images` (file[]): 제품 이미지 파일 (최대 3장)

선택 필드:
- `meme_id` (int): 밈 ID
- `reference_notes` (string): 참고 사항

**응답**

```json
{
  "execution_id": "uuid",
  "status": "created",
  "message": "캐릭터 생성 요청이 접수되었습니다."
}
```

### 2. GET /api/videos/preview/{execution_id}

생성된 캐릭터 미리보기 조회

**응답**

```json
{
  "execution_id": "uuid",
  "status": "created|generating_character|pending_approval|approved|rejected",
  "character_image_url": "presigned_url",
  "character_voice_url": "presigned_url",
  "character_mood": "밝고 활기찬",
  "character_style": "20대 여성",
  "voice_tone": "친근한",
  "created_at": "datetime",
  "generated_at": "datetime"
}
```

### 3. POST /api/videos/approve/{execution_id}

캐릭터 승인/거부

**요청**

```json
{
  "approved": true,
  "rejection_reason": "음성 톤이 맞지 않음"
}
```

**응답 (승인 시)**

```json
{
  "execution_id": "uuid",
  "status": "approved",
  "message": "캐릭터가 승인되었습니다. 영상 생성이 시작됩니다."
}
```

**응답 (거부 시)**

```json
{
  "execution_id": "uuid",
  "status": "rejected",
  "message": "캐릭터가 거부되었습니다."
}
```

### 4. POST /api/videos/regenerate/{execution_id}

캐릭터 재생성 요청

**요청 (선택)**

```
character_mood (string): 수정할 분위기
character_style (string): 수정할 스타일
voice_tone (string): 수정할 음성 톤
```

**응답**

```json
{
  "execution_id": "uuid",
  "status": "created",
  "message": "캐릭터 재생성 요청이 접수되었습니다."
}
```

### 5. GET /api/videos/status/{execution_id}

워크플로우 상태 조회 (v1과 동일)

### 6. GET /api/videos/my-videos

내 영상 목록 조회 (v1과 동일)

---

## 데이터베이스

### workflow_execution 테이블 변경사항

**새로운 상태 값**
- `generating_character`: 캐릭터 생성 중
- `pending_approval`: 사용자 승인 대기
- `approved`: 사용자가 승인함
- `rejected`: 사용자가 거부함

**제약 조건 추가**

```sql
ALTER TABLE workflow_execution 
ADD CONSTRAINT chk_workflow_status 
CHECK (status IN (
    'created', 
    'generating_character', 
    'pending_approval', 
    'approved', 
    'rejected', 
    'processing', 
    'completed', 
    'failed', 
    'cancelled'
));
```

**인덱스 추가**

```sql
CREATE INDEX idx_workflow_status 
ON workflow_execution(status) 
WHERE status IN ('created', 'generating_character', 'approved');

CREATE INDEX idx_workflow_company_status 
ON workflow_execution(company_id, status);
```

### input_params 구조 (v2)

```json
{
  "company_name": "테스트 회사",
  "product_name": "제품명",
  "product_category": "카테고리",
  "product_highlight": "강조문구",
  "character_mood": "밝고 활기찬",
  "character_style": "20대 여성",
  "voice_tone": "친근한",
  "product_images": ["s3://bucket/products/1/prod1.jpg"],
  "meme_id": 1,
  "reference_notes": "참고사항"
}
```

### output_result 구조 (v2)

```json
{
  "generated_character_image_url": "s3://bucket/generated/1/char.jpg",
  "generated_voice_url": "s3://bucket/generated/1/voice.mp3",
  "generated_at": "2026-01-21T10:30:00Z",
  "approval_status": "pending|approved|rejected",
  "approval_at": "2026-01-21T11:00:00Z",
  "rejection_reason": "음성 톤이 맞지 않음",
  "video_url": "s3://bucket/videos/1/final.mp4"
}
```

---

## 팀원과의 협업 (DB 기반 통신)

### 팀원이 구현할 부분 1: 캐릭터 생성

```python
# 1. DB에서 status="created" 작업 찾기
workflows = db.query(WorkflowExecution).filter(
    WorkflowExecution.status == "created"
).all()

# 2. 각 작업에 대해 캐릭터 생성
for workflow in workflows:
    # 입력 파라미터 가져오기
    character_mood = workflow.input_params["character_mood"]
    character_style = workflow.input_params["character_style"]
    voice_tone = workflow.input_params["voice_tone"]
    
    # AI로 이미지/음성 생성
    image_url = generate_character_image(character_mood, character_style)
    voice_url = generate_character_voice(voice_tone)
    
    # S3 업로드
    # ...
    
    # DB 업데이트
    workflow.status = "pending_approval"
    workflow.output_result = {
        "generated_character_image_url": image_url,
        "generated_voice_url": voice_url,
        "generated_at": datetime.utcnow().isoformat()
    }
    db.commit()
```

### 팀원이 구현할 부분 2: 영상 생성

```python
# 1. DB에서 status="approved" 작업 찾기
workflows = db.query(WorkflowExecution).filter(
    WorkflowExecution.status == "approved"
).all()

# 2. 각 작업에 대해 영상 생성
for workflow in workflows:
    # 캐릭터 정보 가져오기
    char_img_url = workflow.output_result["generated_character_image_url"]
    char_voice_url = workflow.output_result["generated_voice_url"]
    
    # 영상 생성
    video_url = generate_video(char_img_url, char_voice_url, ...)
    
    # DB 업데이트
    workflow.status = "completed"
    workflow.output_result["video_url"] = video_url
    workflow.completed_at = datetime.utcnow()
    db.commit()
```

---

## 주요 파일

### scripts/generation/v2/video_routes.py

API 엔드포인트 정의

주요 변경사항:
- `generate_video()`: 파일 업로드 제거, 텍스트 입력으로 변경
- `get_character_preview()`: 미리보기 API 추가
- `approve_character()`: 승인/거부 API 추가
- `regenerate_character()`: 재생성 API 추가

### scripts/generation/v2/database.py

데이터베이스 모델 및 함수

주요 변경사항:
- 상태 값 주석 업데이트 (9개 상태)

### scripts/generation/v2/s3_handler.py

S3 파일 업로드 및 검증

주요 변경사항:
- `validate_character_image()`: 제거
- `validate_character_voice()`: 제거
- `validate_product_image()`: 유지

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

# 영상 생성 요청 (v2)
files = {
    'product_images': ('product.jpg', open('product.jpg', 'rb'), 'image/jpeg')
}
data = {
    'company_name': '테스트 회사',
    'product_name': '제품명',
    'product_category': '카테고리',
    'product_highlight': '강조문구',
    'character_mood': '밝고 활기찬',
    'character_style': '20대 여성',
    'voice_tone': '친근한'
}
headers = {'Authorization': f'Bearer {token}'}

response = requests.post(
    'http://localhost:8000/api/videos/generate',
    files=files,
    data=data,
    headers=headers
)
execution_id = response.json()['execution_id']

# 미리보기 조회
response = requests.get(
    f'http://localhost:8000/api/videos/preview/{execution_id}',
    headers=headers
)
print(response.json())

# 승인
response = requests.post(
    f'http://localhost:8000/api/videos/approve/{execution_id}',
    json={'approved': True},
    headers=headers
)
print(response.json())
```

---

## 상태 전환 흐름

```
created (요청 접수)
  ↓
generating_character (팀원이 캐릭터 생성 중)
  ↓
pending_approval (사용자 검수 대기)
  ↓
  ├─ approved (승인) → processing (영상 생성) → completed
  │
  └─ rejected (거부) → created (재생성)
```

---

## v1 대비 장점

1. 사용자 편의성 향상
   - 파일 준비 불필요
   - 텍스트 입력만으로 요청 가능

2. 품질 관리
   - 사용자 검수 단계 추가
   - 부적절한 캐릭터 사전 차단

3. 리소스 절약
   - 승인 후에만 영상 생성
   - 불필요한 영상 생성 방지

4. 재생성 가능
   - 거부 시 재생성 요청
   - 분위기/스타일 수정 가능

---

## 제한사항

- 캐릭터 생성 시간 소요 (AI 처리)
- 팀원의 AI 시스템 필요
- DB 폴링 방식 (실시간성 낮음)
- 재생성 횟수 제한 (최대 10회)
