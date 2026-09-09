# 캐릭터 이미지 사전 생성 기반 씬 이미지 생성

- 작업 기간: 2026.01.22
- 작업자: 김진
- 관련 이슈 / PR: #34

---

## 개요

### 작업 내용
- 1. 캐릭터 분위기 프롬프트로 캐릭터 이미지를 먼저 생성
- 2. 제품 이미지 + 캐릭터 이미지 + 시나리오 프롬프트를 결합해 씬 이미지를 생성

### 주요 기능
1. 캐릭터 이미지 생성 노드와 씬 이미지 생성 노드 분리
2. 캐릭터 이미지 재사용 입력 지원
3. 캐릭터 이미지 전신/투명 배경 제약 적용
4. 캐릭터 이미지 선택 기반으로 씬 이미지 생성

---

## 입력/출력

### 입력
| 항목 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| character_prompt | `str` | 캐릭터 분위기 프롬프트 | "confident young CEO, clean studio" |
| scenario_prompt | `str` | 씬 구성 프롬프트 | "modern office, product spotlight" |
| character_image_path | `str` | 로컬 캐릭터 이미지 경로 | "data/images/character.png" |
| character_image_url | `str` | 캐릭터 이미지 URL | "https://.../character.png" |
| product_image_path | `str` | 로컬 제품 이미지 경로 | "data/images/product.jpg" |
| product_image_url | `str` | 제품 이미지 URL | "https://.../product.jpg" |

### 출력
| 항목 | 타입 | 설명 | 예시 |
| --- | --- | --- | --- |
| character_output_path | `str` | 캐릭터 이미지 저장 경로 | "data/images/character_....png" |
| scene_output_path | `str` | 씬 이미지 저장 경로 | "data/images/nanobanana_....png" |
| scene_image_url | `str` | 씬 이미지 공개 URL | "https://.../scene.png" |

---

## 코드 구성

### 기능/모듈
- `content_pipeline/image/client.py`
  - 캐릭터 단독 생성, 제품+캐릭터 결합 생성 지원
- `content_pipeline/image/service.py`
  - `generate_character_image`, `generate_scene_image` 분리
- `content_pipeline/image/nodes.py`
  - `generate_character_image_node`, `generate_scene_image_node` 분리
- `content_pipeline/image/graph.py`
  - 캐릭터 → 씬 순서 그래프 구성
- `scripts/image_generate_test.py`
  - 캐릭터/시나리오 입력 옵션 추가

---

## 사용 방법

### 1. 환경 변수
`.env`에 최소 항목 설정
- `NANO_BANANA_API_KEY`
- `NANO_BANANA_STORAGE_BACKEND` (`local` 또는 `s3`)

### 2. 실행 (테스트)
```powershell
uv run python -m scripts.image_generate_test `
  --prompt "modern office, product spotlight" `
  --character-prompt "confident young CEO, clean studio" `
  --product-image-path "data/images/product.jpg" `
  --mode both
```
출력에는 캐릭터 이미지와 씬 이미지 경로가 함께 표시

검수 분리 흐름 예시:
1) 캐릭터 생성만 실행
```powershell
uv run python -m scripts.image_generate_test `
  --character-prompt "confident young CEO, clean studio" `
  --mode character
```
출력에는 캐릭터 이미지 경로가 표시된다.

2) 검수 후 선택된 캐릭터 이미지를 씬 생성에 사용
```powershell
uv run python -m scripts.image_generate_test `
  --prompt "modern office, product spotlight" `
  --product-image-path "data/images/product.jpg" `
  --character-image-path "data/images/[character_selected].png" `
  --mode scene
```
출력에는 캐릭터 이미지와 씬 이미지 경로가 함께 표시