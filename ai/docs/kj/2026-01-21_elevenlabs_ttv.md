# ElevenLabs Text-to-Voice (TTV) 기능 추가

- 작업 기간: 2026.01.21
- 작업자: 김진
- 관련 이슈 / PR: #24
- 선행 파일: 2026-01-20_elevenlabs_tts.md

---

## 개요

ElevenLabs의 Text-to-Voice(보이스 디자인) 기능을 통해 설명과 샘플 텍스트로 새로운 목소리를 생성하고,
생성된 `voice_id`를 기존 TTS 파이프라인에서 바로 사용할 수 있도록 확장했다.

---

## 주요 변경 사항

- TTV 디자인/생성 API 연동 추가
- 신규 환경 변수 `ELEVENLABS_TTV_MODEL_ID` 지원
- `scripts/voice_generate_test.py`에서 voice design → create → TTS까지 원스톱 실행 지원

---

## 음성 생성 파이프라인 (Voice Generation Pipeline)

```
[ 입 력 ] ──▶  묘사 프롬프트 (Description) + 샘플 텍스트 (Text)
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1. Voice Design Node (음성 기획)                       │
│  - AI가 목소리 시안 4종 생성                                  │
│  - 출 력: Preview IDs (임시 식별자)                          │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2. Voice Create Node (성우 등록)                       │
│  - 선택한 시안을 라이브러리에 영구 저장                        │
│  - 출 력: Permanent Voice ID (고유 성우 ID)                 │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3. Voice Synthesis Node (최종 합성)                    │
│  - Voice ID + 실제 광고 대본 결합                             │
│  - 오디오 추출 및 메타데이터(재생 시간) 계산                   │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4. Storage & Integration (저장 및 연동)                │
│  - 로컬 또는 S3 클라우드 업로드                               │
│  - 출 력: Audio URL + Duration (초 단위 길이)                │
└─────────────────────────────────────────────────────────────┘
               │
               ▼
[ 출 력 ] ──▶  Wan 2.6 비디오 노드로 전달 (립싱크 및 프레임 매칭)
```

---

## 데이터 입출력
### 입력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **voice_description** | `str` | 목소리의 특징을 묘사하는 보이스 디자인 프롬프트 | "A deep, warm narrator voice." |
| **text** | `str` | 미리보기 음성 생성을 위한 샘플 텍스트 | "Hello, this is a brand voice test." |
| **voice_name** | `str` | 생성된 목소리를 저장할 이름 | "Warm Narrator" |
| **preview_index** | `int` | 선택할 미리보기 번호 (0부터 시작) | 0 |
| **model_id** | `str` | 사용할 TTV 모델 (선택 사항) | "eleven_multilingual_ttv_v2" |

### 출력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| **voice_id** | `str` | 최종 생성된 ElevenLabs Voice ID | "ZcZcEsYxXAIc3nNSev1H" |
| **previews** | `array` | 디자인 단계에서 생성된 미리보기 후보 목록 | [{"generated_voice_id":"...","audio_base_64":"..."}] |
| **generated_voice_id** | `str` | 미리보기 목소리의 고유 식별자 | "b9f3f6f1..." |
| **audio_base_64** | `str` | Base64로 인코딩된 미리보기 오디오 데이터 | "SUQzBAAAAA..." |

---

## 환경 변수

```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
ELEVENLABS_TTV_MODEL_ID=eleven_multilingual_ttv_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_22050_32
```

---

## 코드 구성
### 기능/모듈명: ElevenLabs Voice Service
- 추가/수정 파일:
- `content_pipeline/voice/client.py`
  - `text_to_voice_design`, `text_to_voice_create` 함수 추가
- `content_pipeline/voice/service.py`
  - `design_voice`, `create_voice`, `design_and_create_voice` 함수 추가
- `scripts/voice_generate_test.py`
  - `--voice-description`, `--voice-name`, `--preview-index` 옵션 추가

---

## 프로젝트 구조
- 변경 여부: X
```bash
content_pipeline/
├── voice/
|   ├── __init__.py           
|   ├── config.py                 # 수정
|   ├── client.py                 # 수정
|   ├── service.py                # 수정
|   └── storage.py            
|
├── scripts/
|   └── voice_generate_test.py    # 수정
|
└── docs/kj/
    └── 2026-01-21_elevenlabs_ttv.md    # 추가
```

---

## 실행/테스트 방법

### 1. 기존 voice_id로 TTS

```bash
uv run python -m scripts.voice_generate_test --text "[whispers] 오늘 밤 와주셔서 감사합니다. 저게 뭐지?[gunshot]" --voice-id "WzMnDIgiICcj1oXbUBO0"
```

### 2. 보이스 디자인 → 생성 → TTS
- text는 최소 100자 이상

```bash
uv run python -m scripts.voice_generate_test --text "안녕하세요. 현재 음성 생성 파이프라인의 테스트를 진행하고 있습니다. 이 문장은 일레븐랩스의 보이스 디자인 기능을 활성화하기 위해 필요한 백 자 이상의 테스트 텍스트입니다. 목소리가 자연스럽게 생성되는지 확인하기 위해 조금 더 길게 작성해 보겠습니다. 이제 백 자가 넘었을 것 같네요." --voice-description "A deep, warm narrator voice." --voice-name "Warm Narrator"
```

필요 시 디자인용 텍스트를 별도로 지정:

```bash
uv run python -m scripts.voice_generate_test --text "안녕하세요" --design-text "Your weapons are but toothpicks to me." --voice-description "A massive evil ogre speaking at a quick pace." --voice-name "Ogre"
```

---


## 비고

- `preview_index`로 여러 프리뷰 중 선택 가능 (기본값: 0)
- `ELEVENLABS_TTV_MODEL_ID`는 필요 시 환경 변수로 변경 가능

---

## 트러블슈팅

1. ElevenLabs API 호출 시 404 Not Found 에러 발생
문제: design_and_create_voice 실행 중 목소리 생성(Create) 단계에서 404 에러가 발생
원인: ElevenLabsClient 클래스 내부에 정의된 API 엔드포인트(.../text-to-voice/create)가 ElevenLabs의 최신 API 스펙과 일치하지 않아 서버에서 해당 경로를 찾지 못함
해결: 엔드포인트 주소를 최신 규격인 https://api.elevenlabs.io/v1/voice-generation/create-voice로 수정하여 해결
