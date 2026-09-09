# DB 스키마 변경 반영 (company_characters 컬럼 변경/scene_assets 테이블 제거)

- 작업 기간: 2026.01.28
- 작업자: 김진
- 관련 이슈 / PR: #58

---

## 개요

- DB 스키마 변경으로 기존 프롬프트/보이스 입력 경로가 맞지 않는 구간 발생

- **제거된 컬럼**
    - ad_requests 테이블의 voice_description 컬럼 삭제
    - company_characters 테이블의 character_name, character_mood, character_style, voice_tone 컬럼 삭제
    - scene_assets 테이블 미사용
    
- **scene_assets 저장 로직 제거**
  - `content_pipeline/db.py`의 `upsert_scene_assets` 함수 및 SQL 삭제
  - `voice_generations`에서 최신 오디오 URL/길이 로딩
  - `image_generations`에서 최신 장면 이미지 URL 로딩
  - `scenario_scripts.scenes.action` → `scene_inputs[*].prompt`

- **씬 입력 자동 주입 소스 변경**
  - `voice_generations`와 `image_generations`에서 최신 결과를 조회해
    영상 생성용 입력(audio/reference_image)을 구성

- **보이스 생성 흐름 정리**
    - voice-id 기본값 → company_characters.elevenlabs_voice_id
       - 없을 경우, design → DB 업데이트 → TTS
       - 있을 경우, 기존/신규 선택

- **최신 script_id 로딩**
  - 사용자가 스크립트를 수정함에 따라 동일한 `ad_id`로 여러 스크립트 생성될 수 있음. 
  - 따라서 `scenario_scripts.created_at`이 최신인 `scenario_scripts.script_id`를 조회해서 사용하도록 변경
  - db.py에 `load_latest_script_id_by_ad_id(ad_id)` 추가

---

## 코드 구성
### 기능/모듈명
- 추가/수정 파일
- `content_pipeline/db.py`
- `content_pipeline/pipeline_utils.py::build_scene_inputs_from_db()`
- `content_pipeline/video/nodes.py`
- `content_pipeline/voice/nodes.py`
- `content_pipeline/image/nodes.py`
- `scripts/voice_generate_test.py`
- `scripts/image_generate_test.py`
- `scripts/video_graph_from_scenes.py`
- `docs/kj/2026-01-28_db_schema_update.md`

---

## 프로젝트 구조
- 변경 사항: O
```bash
content_pipeline/
├─ db.py
├─ pipeline_utils.py
├─ voice/
│  └─ nodes.py
├─ image/
│  └─ nodes.py
├─ video/
│  └─ nodes.py
scripts/
├─ voice_generate_test.py
├─ image_generate_test.py
└─ video_graph_from_scenes.py
```

---

## 주요 데이터 흐름
### LLM Prompt Generator 단계
    - 사용자 입력(`character_style_raw`)을 받아서
    - 음성용 프롬프트(`voice_design_prompt`)와
    - 이미지용 프롬프트(`image_prompt`)를 각각 생성

### 데이터 저장 위치
    - `company_characters`: 캐릭터 관련 모든 정보 (프롬프트, voice_id, image_url)
    - `voice_generations`: 생성된 음성 파일들
    - `image_generations`: 생성된 장면 이미지들
    - `scene_videos`: 생성된 장면 영상들
    - `videos`: 최종 병합 영상

### 입력 데이터 → 노드
- **design_voice_node**
  - 입력: `company_characters.voice_design_prompt`
  - 출력: `company_characters.elevenlabs_voice_id`

- **generate_character_image_node**
  - 입력: `company_characters.image_prompt`
  - 출력: `company_characters.image_url`

- **generate_voice_node**
  - 입력: `company_characters.elevenlabs_voice_id` + `scenario_scripts.scenes.dialogue`
  - 출력: `voice_generations`

- **generate_scene_image_node**
  - 입력: `company_characters.image_url` + `ad_requests.item_images` + `scenario_scripts.scenes.visual_description`
  - 출력: `image_generations`

- **generate_video_node**
  - 입력: `scenario_scripts.scenes.action` + `image_generations.image_url` + `voice_generations.audio_url`
  - 출력: `scene_videos`

- **merge_video_node**
  - 입력: `scene_videos.video_url` (모든 씬)
  - 출력: `videos`

---

## 사용 테이블

| 구분 | 테이블 | 주요 사용 컬럼 |
|---|---|---|
| 사용자 입력 | `ad_requests` | `item_images`, `character_style_raw` |
| 캐릭터 정보 | `company_characters` | `image_prompt`, `voice_design_prompt`, `elevenlabs_voice_id`, `image_url` |
| 시나리오 | `scenario_scripts` | `scenes` (`dialogue`, `visual_description`, `action`, `scene_type`) |
| 음성 결과 | `voice_generations` | `audio_url`, `duration_seconds`, `size_bytes`, `settings_json` |
| 이미지 결과 | `image_generations` | `image_url`, `size_bytes`, `metadata_json` |
| 씬 비디오 | `scene_videos` | `video_url`, `duration_seconds`, `size_bytes`, `generation_metadata` |
| 최종 비디오 | `videos` | `s3_url`, `status`, `script_id` |

> 참고: `scene_assets` 테이블은 더 이상 사용하지 않음.

---

## 실행/테스트 방법