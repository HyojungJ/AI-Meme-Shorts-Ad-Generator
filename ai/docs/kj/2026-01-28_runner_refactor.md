# Runner 리팩터링 정리

- 작업 기간: 2026.01.28
- 작업자: 김진
- 관련 이슈 / PR: #58

---

## 개요
scripts의 실행 로직을 content_pipeline 내부 runner 모듈로 이동해 자동화 경로에서 재사용 가능하게 함

- 수동 실행 스크립트는 유지하되 자동화는 runner 모듈을 호출하도록 설계
- 자동 경로는 pipeline_utils 사용

---

## 변경 요약

- runner 모듈 추가
  - `content_pipeline/voice/runner.py`
  - `content_pipeline/image/runner.py`
  - `content_pipeline/video/runner.py`
- 기존 스크립트는 얇은 CLI 래퍼로 변경
  - `scripts/voice_generate_test.py`
  - `scripts/image_generate_test.py`
  - `scripts/video_graph_from_scenes.py`

---

## 역할 구분

- `content_pipeline/pipeline_utils.py`
  - DB → 파이프라인 입력 조립 유틸
  - `build_scene_inputs_from_db()`로 scene_inputs 생성
- `content_pipeline/*/runner.py`
  - 실제 실행 로직 (음성/이미지/영상)
  - 자동화 경로에서 직접 호출 가능

---

## runner 함수 요약

### 음성
- 함수: `run_voice_generation()`
- 위치: `content_pipeline/voice/runner.py`
- 입력: text/voice_id/voice_description/voice_name 등
- DB 연동:
  - text: `scenario_scripts.scenes.dialogue` → `ad_requests.item_keymessage` fallback
  - voice_description: `company_characters.voice_design_prompt`
- 출력: voice 생성 결과 dict
- 서비스 플로우:
  - company_characters.elevenlabs_voice_id
    - 있으면, 기본은 그 값을 사용해서 generate_voice_node로 TTS
    - 없으면, design_voice_node로 새 보이스 생성 → DB 저장 → generate_voice_node로 TTS
    - 있어도 새로 만들고 싶으면 --force-new-voice 옵션으로 강제 생성

### 이미지
- 함수: `run_image_generation()`
- 위치: `content_pipeline/image/runner.py`
- 입력: mode(character/scene/both), prompt/scenario_prompt/character_prompt 등
- DB 연동:
  - character_prompt: `company_characters.image_prompt`
  - scenario_prompt: `scenario_scripts.scenes` 기반
- 출력: 이미지 생성 결과 dict

### 영상
- 함수: `run_video_from_scenes()`
- 위치: `content_pipeline/video/runner.py`
- 입력: scenes.jsonl 경로, script_id, title/description 등
- DB 연동:
  - prompt: `scenario_scripts.scenes.action` 기반 로딩 (`prompt_kind="action"`)
- 출력: 씬 생성 + 병합 결과 dict

---

## 파일 목록

```text
content_pipeline/
  voice/runner.py
  image/runner.py
  video/runner.py
  pipeline_utils.py
scripts/
  voice_generate_test.py
  image_generate_test.py
  video_graph_from_scenes.py
```

