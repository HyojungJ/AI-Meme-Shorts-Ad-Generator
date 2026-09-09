# ElevenLabs 기반 음성 생성 모듈 구축 (TTS)

- 작업 기간: 2026.01.20
- 작업자: 김진
- 관련 이슈 / PR: #17

---

## 개요

### 작업 내용
- 자동 제작 파이프라인의 음성 생성 단계(Voice Node) 구현
- 텍스트 대본의 음성 변환 및 멀티 클라우드 저장 자동화
- 모듈화, 확장성(S3/GCS), 유효성 검증, 메타데이터 추출

### 주요 기능
1. ElevenLabs 기반 음성 생성 모듈 추가 (Voice ID 기반 TTS 호출, 파라미터 검증)
2. 음성 파일 저장 파이프라인 구성 (로컬 + S3)
3. mutagen을 이용한 재생 시간(오디오 메타데이터) 자동 추출

---

## 데이터 입출력
### 입력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **text** | `str` | 음성으로 변환할 원문 대본 | "안녕하세요, 인공지능 테스트입니다." |
| **voice_id** | `str` | ElevenLabs의 목소리 고유 ID | "ZcZcEsYxXAIc3nNSev1H" |
| **user_id** | `str` | 저장 경로 식별을 위한 사용자 ID | "user_123" |
| **settings** | `VoiceSettings` | 음성 세부 설정 (Optional) | 하단 세부 항목 참조 |

**※ settings 내부 파라미터:**

- `stability`: 0.0 ~ 1.0 (목소리의 일관성)
- `similarity_boost`: 0.0 ~ 1.0 (원본 목소리와의 유사도)
- `style`: 0.0 ~ 1.0 (감정/스타일 강도)
- `use_speaker_boost`: `bool` (화자 선명도 강화)
- `speed`: 0.7 ~ 1.2 (말하기 속도)

### 출력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **audio_url** | `str` | 재생 가능한 파일의 공개 URL | `https://s3.../audio.mp3` |
| **storage_path** | `str` | 저장소 내 실제 저장 경로 (Key) | `user_123/voice/2026...mp3` |
| **duration_seconds** | `float` | **오디오의 전체 길이 (초 단위)** | `12.5` |
| **size_bytes** | `int` | 파일 용량 | `102400` |
| **text_hash** | `str` | 입력 텍스트의 고유 해시값 | `a1b2c3d4e5f6` |
| **created_at** | `str` | 생성 완료 일시 (ISO 8601) | `2026-01-20T21:26...` |


---

## 코드 구성
### 기능/모듈명: ElevenLabs Voice Service
- 추가/수정 파일:
  - `content_pipeline/voice/config.py`
  - `content_pipeline/voice/client.py`
  - `content_pipeline/voice/storage.py`
  - `content_pipeline/voice/service.py`
  - `content_pipeline/voice/__init__.py`
  - `content_pipeline/scripts/voice_generate_test.py`
  - `pyproject.toml`
- 주요 변경사항:
  - ElevenLabs TTS 호출 및 파라미터(안정성/유사도/스타일/속도) 검증
  - 음성 파일 로컬/S3 업로드 지원

---

## 프로젝트 구조
- 변경 여부: O
- 변경 사유: 음성 생성 전용 모듈 분리 및 재사용 가능한 저장 파이프라인 구축
```bash
content_pipeline/
├── voice/
|   ├── __init__.py           # 외부 노출 인터페이스
|   ├── config.py             # 환경 변수 및 설정 관리
|   ├── client.py            # ElevenLabs API 통신 클라이언트
|   ├── service.py            # 핵심 로직 (오디오 가공, 메타데이터, 저장소 제어)
|   └── storage.py            # 저장소 (Local, S3)
|
├── scripts/
|   └── voice_generate_test.py    # 독립 기능 테스트용
|
└── docs/kj/
    └── 2026-01-20_elevenlabs_tts.md
```

---

## 실행/테스트 방법
### 1. 환경 변수 설정

`.env`에 최소 항목을 설정
```powershell
copy .env.example .env 
```

필수:
- `ELEVENLABS_API_KEY` : ElevenLabs API 키
- `VOICE_STORAGE_BACKEND` : `local` 또는 `s3`

로컬 저장 시 권장:
- `VOICE_STORAGE_BASE_DIR` : 예) `data/voice`
- `VOICE_PUBLIC_BASE_URL` : 공개 URL이 있으면 설정 (없으면 비워도 됨)

S3 저장 시 추가:
- `VOICE_S3_BUCKET`
- `VOICE_S3_REGION`

### 2. 실행 스크립트(로컬 테스트)
```powershell
uv run python -m scripts.voice_generate_test --text "안녕하세요. 브랜드 음성을 테스트합니다." --voice-id "VOICE_ID" # ZcZcEsYxXAIc3nNSev1H
```

### 3. 결과 확인
- `VOICE_STORAGE_BACKEND=local`이면 `VOICE_STORAGE_BASE_DIR` 아래에 파일이 저장됩니다.
- `VOICE_PUBLIC_BASE_URL`을 설정했다면 `audio_url`이 공개 URL로 반환됩니다.

---

## 트러블슈팅

1. S3 업로드 사용 시 추가 패키지 필요
- 문제: S3 업로드 사용 시 추가 패키지 필요
- 원인: 선택적 의존성으로 기본 설치에 미포함
- 해결: `boto3` 설치 후 사용

  ```powershell
  python -m pip install boto3
  ```

2. REST API 호출 환경에서 외국어 생성 발생 문제
- 문제: FastAPI 서버 호출 시 한국어 문장이 외국어식 억양으로 생성
- 원인: HTTP 통신 레이어를 거치며 텍스트 인코딩(UTF-8)이 틀어져 모델이 언어를 잘못 인식 및 생성
- 해결: Python 모듈에서 직접 API로 유니코드 데이터를 전달
