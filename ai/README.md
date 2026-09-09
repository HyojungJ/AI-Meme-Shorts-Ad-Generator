# AI
콘텐츠 생성용 AI 파이프라인 레포지토리

## 개요
- 시나리오/이미지/음성/영상 생성 파이프라인을 통합 제공
- DB 연동 및 스토리지(S3/로컬) 업로드를 포함한 end-to-end 처리
- 로컬 실행/ComfyUI 연동/외부 모델(예: Qwen TTS, ElevenLabs) 지원

## 기술 스택
- Python 3.11+
- 패키지 매니저: `uv`
- 데이터 저장: PostgreSQL, S3 또는 로컬
- 영상 생성: ComfyUI
- 음성 생성: ElevenLabs, Qwen TTS

---

## 구조

```
AI/
├── content_pipeline/          # 시나리오/이미지/음성/영상 파이프라인
│   ├── scenario/              # 시나리오 생성/검수/수정
│   ├── image/                 # 캐릭터/씬 이미지 생성
│   ├── voice/                 # 음성 생성 (ElevenLabs/Qwen)
│   ├── video/                 # 영상 생성 (ComfyUI 연동)
│   ├── pipeline.py            # 통합 파이프라인 오케스트레이션
│   ├── schema.py              # 파이프라인 공용 스키마
│   └── db.py                  # 파이프라인 DB 접근
├── meme_collector/            # 밈 수집/정제 로직
├── finetune/                  # 시나리오 모델 파인튜닝/서빙
├── scripts/                   # 파이프라인 실행 단위 테스트 스크립트
├── tests/                     # 통합 테스트
├── docs/                      # 설계/변경 로그/운영 문서
├── migrations/                # DB 스키마 마이그레이션
├── data/                      # 로컬 결과물/캐시
├── .env.example               # 환경 변수 예시
├── pyproject.toml             # 프로젝트 설정
├── uv.lock                    # 의존성 락
└── README.md
```

---

## 주요 구성

### Content Pipeline
- `content_pipeline/pipeline.py`에서 전체 흐름 실행
- `content_pipeline/*/nodes.py`에 단계별 노드 구현
- `content_pipeline/*/service.py`에서 외부 API/스토리지 처리

### 시나리오 생성
- `content_pipeline/scenario/`에서 시나리오 생성/검수/수정

### 이미지 생성
- `content_pipeline/image/`에서 캐릭터/씬 이미지 생성

### 음성 생성
- `content_pipeline/voice/`에서 ElevenLabs / Qwen TTS 지원
- `VOICE_PROVIDER`로 분기

### ComfyUI 연동 (영상)
- `content_pipeline/video/`에서 ComfyUI 기반 영상 생성/병합

---

## 필수 환경 변수

```
### 공통
- `OPENAI_API_KEY`
- `OPENAI_MODEL_ID` (기본: `gpt-4o-mini`)

### DB
- `DATABASE_URL`

### 스토리지 (S3 사용 시)
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`

### 음성 (ElevenLabs / Qwen TTS)
- `VOICE_PROVIDER` (`qwen` 또는 `elevenlabs`)
- ElevenLabs 사용 시:
  - `ELEVENLABS_API_KEY`
  - `ELEVENLABS_MODEL_ID`
  - `ELEVENLABS_TTV_MODEL_ID`
- Qwen 사용 시:
  - `QWEN_TTS_VOICE_DESIGN_MODEL_ID`
  - `QWEN_TTS_BASE_MODEL_ID`
  - `QWEN_TTS_DEVICE`
  - `QWEN_TTS_DTYPE`
  - `QWEN_TTS_ATTN_IMPL`
  - `QWEN_TTS_SEED`

### 영상 (ComfyUI)
- `COMFY_MODE=comfyui`
- `COMFY_COMFYUI_BASE_URL`
- `COMFY_WORKFLOW_PATH`
- `COMFY_WORKFLOW_BASE`
- `COMFY_OUTPUT_DIR`
- `COMFY_TEMP_DIR`
- `COMFY_REQUEST_TIMEOUT_SEC`
- `COMFY_POLL_INTERVAL_SEC`
- `COMFY_MAX_WAIT_SEC`

### ComfyUI 원격 정리 (필요 시)
- `COMFY_SSH_HOST`
- `COMFY_SSH_PORT`
- `COMFY_SSH_USER`
- `COMFY_SSH_KEY`
- `COMFY_REMOTE_INPUT_DIR`
- `COMFY_REMOTE_OUTPUT_DIR`
- `COMFY_REMOTE_MERGE_DIR`
```

---

## 실행 방법

### 1) 패키지 설치

```bash
uv sync
```

### 2) 환경 변수 설정

`.env.example`를 `.env`로 복사한 뒤 값 입력:

```bash
cp .env.example .env
```

### 3) 파이프라인 실행 (예시)

```bash
uv run python -m scripts.run_pipeline --ad-id 1 --meme-id 1 --voice-id xxx
```

### 4) 개별 단계 실행(예시)

```bash
# 시나리오 생성
uv run python -m scripts.run_pipeline --scenario --ad-id 1 --meme-id 1

# 캐릭터 생성
uv run python -m scripts.run_pipeline --character --prompt "친근한 캐릭터"

# 음성 생성
uv run python -m scripts.run_pipeline --voice --name "테스터" --desc "밝은 목소리"
```
