# Nano Banana Pro 기반 캐릭터 이미지 생성 모듈 구축

- 작업 기간: 2026.01.21
- 업데이트 기간: 2026.01.22
- 작업자: 김진
- 관련 이슈 / PR: #21

---

## 개요

### 작업 내용
- nano banana pro 모델 기반 캐릭터 이미지 생성(Image Node) 구현
- Python SDK(`google-genai`) 기반 호출 방식 적용
- 광고 영상 입력에 적합한 캐릭터 스타일 고정 및 9:16 비율 유지
- 로컬/URL 입력 지원, 생성 이미지 저장 및 메타데이터 기록
- S3 업로드 옵션 추가

### 주요 기능
1. nano banana pro 기반 이미지 생성 호출
2. 9:16 비율(세로형) 유지 및 품질 검증
3. 생성 결과 저장 및 메타데이터 기록
4. URL 입력 지원 및 S3 업로드 옵션 제공

### 개선 사항
- 재시도 관련 설정은 config로 관리
(`NANO_BANANA_MAX_RETRIES`, `NANO_BANANA_BASE_SLEEP_SEC`, `NANO_BANANA_MAX_SLEEP_SEC`)
- generate_image()가 config를 직접 읽지 않고,
호출할 때 필요한 값을 매개변수로 받아서 실행되도록 변경
  - 함수는 이미지 생성만 하고 설정은 서비스가 관리

---

## 모델
| 항목 | 모델 |
| --- | --- |
Nano Banana | Gemini 2.5 Flash Image 모델 (gemini-2.5-flash-image)
Nano Banana Pro | Gemini 3 Pro Image Preview 모델 (gemini-3-pro-image-preview)

---

## 데이터 입출력
### 입력 데이터

| 항목 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| prompt | `str` | 이미지 프롬프트 | "young female office worker, friendly smile" |
| product_image_path | `str` | 로컬 제품 이미지 경로(옵션) | "data/images/product.jpg" |
| product_image_url | `str` | 제품 이미지 URL(옵션) | "https://.../product.jpg" |
| aspect_ratio | `str` | 비율(옵션) | "9:16" |
| output_dir | `str` | 출력 디렉토리(옵션) | "data/images" |
| output_path | `str` | 출력 경로(옵션) | "data/images/character.png" |

### 출력 데이터

| 항목 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| output_path | `str` | 저장된 이미지 경로 | "data/images/character_20260121.png" |
| metadata_path | `str` | 메타데이터 JSON 경로 | "data/images/character_20260121.json" |
| image_url | `str` | 공개 이미지 URL | "https://.../character_20260121.png" |
| metadata_url | `str` | 공개 메타데이터 URL | "https://.../character_20260121.json" |
| storage_path | `str` | 저장 위치 | "s3://bucket/path/..." |
| size_bytes | `int` | 파일 용량 | 245678 |
| created_at | `str` | 생성 시각(ISO 8601) | "2026-01-21T02:34:56Z" |
| model | `str` | 사용 모델 | "gemini-3-pro-image-preview" |
| aspect_ratio | `str` | 비율 | "9:16" |

---

## 코드 구성
### 기능/모듈명: Nano Banana Image Service
- 추가/수정 파일:
  - `content_pipeline/image/config.py`
  - `content_pipeline/image/client.py`
  - `content_pipeline/image/nodes.py`
  - `content_pipeline/image/state.py`
  - `content_pipeline/image/graph.py`
  - `content_pipeline/image/storage.py`
  - `content_pipeline/image/service.py`
  - `content_pipeline/image/__init__.py`
- 주요 변경사항:
  - 이미지 생성 호출 + 9:16 비율 유지
  - 로컬/URL 입력 처리 및 메타데이터 저장
  - 스토리지(S3/로컬) 업로드 옵션 제공

---

## 프로젝트 구조
```bash
content_pipeline/
├── image/
|   ├── __init__.py             # 이미지 모듈 인터페이스
|   ├── config.py               # 환경 변수/설정 로드
|   ├── client.py               # nano banana API 클라이언트
|   ├── nodes.py                # LangGraph 노드
|   ├── state.py                # 입력/출력 스키마
|   ├── graph.py                # LangGraph 그래프
|   ├── service.py              # 이미지 서비스 로직
|   └── storage.py              # 로컬/S3 스토리지 구현
└── docs/kj/
    └── 2026-01-21_nanobanana_image.md
```

---

## 실행/테스트 방법
### 1. 환경 변수 설정
`.env`에 최소 항목을 설정합니다.

필수:
- `NANO_BANANA_API_KEY`

선택:
- `NANO_BANANA_MODEL` (기본 `gemini-2.0-flash-image-preview`)
- `NANO_BANANA_OUTPUT_DIR` (기본 `data/images`)
- `NANO_BANANA_PUBLIC_BASE_URL`
- `NANO_BANANA_TEMP_DIR`
- `NANO_BANANA_STORAGE_BACKEND` (`local` 또는 `s3`)
- `NANO_BANANA_STORAGE_PREFIX`
- `NANO_BANANA_S3_BUCKET`
- `NANO_BANANA_S3_REGION`
- `NANO_BANANA_MAX_RETRIES`
- `NANO_BANANA_BASE_SLEEP_SEC`
- `NANO_BANANA_MAX_SLEEP_SEC`
### 2. 간단 실행
로컬 파일:
```bash
uv run python -m scripts.image_generate_test --prompt "..." --product-image-path "data/images/product.jpg"
```

URL:
```bash
uv run python -m scripts.image_generate_test --prompt "..." --product-image-url "https://.../product.jpg"
```

예시:
```bash
uv run python -m scripts.image_generate_test --prompt "Stylish young male with a confident smile, casual urban outfit." --product-image-path "data/images/product.jpg"
```

### 3. 결과 확인
- `NANO_BANANA_OUTPUT_DIR` 아래 이미지 및 `.json` 메타데이터가 저장됩니다.
- `NANO_BANANA_STORAGE_BACKEND=s3` 설정 시 S3에도 업로드됩니다.

---

## 트러블슈팅
