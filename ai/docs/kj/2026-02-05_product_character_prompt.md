# 제품 정보 기반 광고 캐릭터 자동 생성 프롬프트 제공

- 작업 기간: 2026.02.05
- 작업자: 김진
- 관련 이슈 / PR: #125

---

## 개요

### 작업 내용
1. AI 파이프라인 변경
- 제품 정보 기반 프롬프트 추천 함수 추가: `suggest_character_prompts_from_product`
- `ad_requests` 컬럼 분리: `character_image_prompt`, `character_voice_prompt`
- 레거시 입력(`character_style`, `character_style_raw`, `notes`, `reference_notes`)은 호환 유지
- 확정 프롬프트는 생성 단계에서 `company_characters`에 저장

2. 백엔드 변경
- 신규 API: `POST /api/v1/videos/characters/prompts`
  - 제품 정보 기반 프롬프트 추천 (이미지/보이스 동시 반환)
- 이미지 프롬프트: 반드시 입력된 값이 있어야 함 (필수)
- 음성 프롬프트: 입력된 값이 없으면 제품 정보 기반으로 자동 생성 구조 (선택)

3. 프론트 변경
- 프론트 요청/응답 스키마에 새 컬럼 반영
- `VideoRequestForm`에 Generate_Prompt 버튼 추가
- 이미지/보이스 프롬프트를 UI에서 확인/수정 가능
- 제작 요청 시 `character_image_prompt`, `character_voice_prompt`로 전송

### 주요 기능
1. 사용자 제품 정보(`item_name`, `item_category`, `item_description`)를 기반으로 LLM이 캐릭터 이미지/음성 프롬프트를 추천 
2. Generate_Prompt 버튼으로 이미지/보이스 프롬프트를 생성 → `ad_requests`에 저장하여 프론트에서 미리보기/재사용 가능
3. 추천 프롬프트를 화면에 노출하고 사용자가 직접 수정 가능
4. 최종 확정 프롬프트는 `company_characters.image_prompt` / `company_characters.voice_design_prompt`에 저장
5. `제작 요청` 시 확정된 프롬프트로 이미지/보이스 생성

---

## 데이터 입출력

### 입력 데이터 (주요 필드)

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **product_name** | `str` | 제품명 | "스파클링 워터" |
| **product_category** | `str` | 제품 카테고리 | "음료" |
| **product_description** | `str` | 제품 설명/강조점 | "무설탕, 상쾌한 탄산" |
| **character_image_prompt** | `str` | 이미지 프롬프트 직접 입력(우선) | "Bright friendly mascot..." |
| **character_voice_prompt** | `str` | 음성 프롬프트 직접 입력(우선) | "Warm, upbeat voice..." |
| **character_style_hint** | `str` | LLM 추천용 힌트(선택) | "귀여운 20대 느낌" |

**레거시 입력 호환**
- `character_style`, `character_style_raw`, `notes`, `reference_notes`는 입력으로만 허용하며,
  실제 저장은 `character_image_prompt`, `character_voice_prompt`로 통일

### 출력 데이터 (저장/응답)

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **character_image_prompt** | `str` | 생성/추천된 이미지 프롬프트 | "A friendly mascot..." |
| **character_voice_prompt** | `str` | 생성/추천된 음성 프롬프트 | "Warm, calm voice..." |

---

## 코드 구성

### 기능/모듈명: Product Character Prompt Suggestion
- 변경/추가 파일:
- `AI/`
  - `content_pipeline/__init__.py`
  - `content_pipeline/pipeline.py`
  - `content_pipeline/schema.py`
- `backend/`
  - `app/models/ad_request.py`
  - `app/crud/video.py`
  - `app/schemas/video.py`
  - `app/api/v1/endpoints/video.py`
  - `app/api/v1/endpoints/admin.py`
  - `app/services/ai_pipeline_client.py`
  - `app/services/ai_pipeline_direct.py`
  - `app/services/ai_pipeline_mock.py`
  - `alembic/versions/20260205_0900_rename_ad_request_prompts.py`
- `frontend/`
  - `src/lib/api/video.ts`
  - `src/types/index.ts`
  - `src/components/forms/VideoRequestForm.tsx`
  - `src/app/(dashboard)/user/request/page.tsx`
  - `src/app/admin/page.tsx`
  - `src/lib/api/admin.ts`

---

## 프로젝트 구조

```bash
AI/
├─ content_pipeline/
│  ├─ pipeline.py                             # 제품 정보 기반 프롬프트 추천
│  └─ schema.py                               # AdRequestDB 컬럼명 정리
├─ docs/kj/
│  └─ 2026-02-05_product_character_prompt.md

backend/
├─ app/models/ad_request.py                   # 컬럼명 변경
├─ app/crud/video.py                          # 생성 시 저장 컬럼 변경
├─ app/api/v1/endpoints/video.py              # 요청/응답/저장 흐름 변경
├─ app/services/ai_pipeline_client.py         # character_style_hint 전달
└─ alembic/versions/20260205_0900_rename_ad_request_prompts.py

frontend/
├─ src/app/(dashboard)/user/request/page.tsx  # 폼 전송 필드 변경
├─ src/lib/api/video.ts                       # 응답 매핑 변경
├─ src/types/index.ts                         # 타입 변경
└─ src/app/admin/page.tsx                     # 상세 표시 변경
```

---

## 실행/테스트 방법

### 1. DB 마이그레이션
```powershell
uv run alembic upgrade head
```

### 2. 요청 예시 (폼 데이터)
- `character_image_prompt` 또는 `character_voice_prompt`를 입력하면 해당 값 우선
- 미입력 시 제품 정보로 LLM 추천 프롬프트 생성