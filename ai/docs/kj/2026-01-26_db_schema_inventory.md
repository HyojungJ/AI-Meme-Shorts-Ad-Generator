# 콘텐츠 파이프라인 DB 연동을 위한 기존 테이블 목록 확인

- 작업 기간: 2026.01.26
- 작업자: 김진
- 관련 이슈 / PR: #58

---

## 실행 로그

1) Python + psycopg2로 `information_schema.tables` 조회
2) 결과를 아래에 기록

---

## 결과
### 테이블 목록

```
public.accounts
public.ad_requests
public.admin_video_posts
public.admin_youtube_channels
public.admins
public.alembic_version
public.clients
public.companies
public.company_characters
public.company_members
public.image_generations
public.meme_examples
public.memes
public.performance_metrics
public.prompt_usage_logs
public.prompt_versions
public.retry_queue
public.scenario_scripts
public.scene_assets
public.scene_videos
public.videos
public.voice_generations
public.workflow_execution
public.workflow_stages
```

---

## 파이프라인 관리 대상 테이블

### company_characters
- character_id, company_id, character_name, character_mood, character_style, voice_tone, image_url, image_prompt, image_model, elevenlabs_voice_id, voice_design_prompt, generation_metadata, is_active, created_at
- constraint: UNIQUE(character_id)

### image_generations (캐릭터 이미지 생성 로그)
캐릭터별 대표 이미지 생성 이력을 남기는 용도.
- image_id, character_id, script_id, prompt, model, image_url, size_bytes, metadata_json, created_at
- constraint: UNIQUE(script_id)

### voice_generations (음성 합성 결과 저장)
텍스트, 해시, 길이, 크기, URL, 설정값 등 음성 생성 내역 로그.
- voice_gen_id, character_id, script_id, scene_key, text_content, text_hash, audio_url, duration_seconds, size_bytes, settings_json, created_at
- constraint: UNIQUE(character_id, text_hash)

### scene_videos (씬별 영상 생성 결과 로그)
음성/이미지 ID와 연결해 추적 가능.
- scene_video_id, script_id, scene_key, voice_gen_id, image_id, video_url, duration_seconds, size_bytes, generation_model, generation_metadata, created_at
- constraint: UNIQUE(script_id, scene_key)

### scene_assets (씬 단위 최종 자산 묶음)
씬에 쓰인 음성/이미지/비디오 경로를 한 곳에 모아둠.
- asset_id, script_id, scene_key, audio_url, audio_duration_seconds, audio_storage_path
- character_image_url, character_image_storage_path
- scene_video_url, scene_video_storage_path, scene_video_duration
- generation_model, generation_cost, created_at
- constraint: UNIQUE(script_id, scene_key)

### videos (최종 합쳐진 완성본 영상 메타)
업로드 상태/URL/파일 정보 등 서비스 배포 대상.

---

## 테이블 설계
### 정책 방향
목표:
- 테이블 구조 큰 변경 없이 운용 (컬럼만 변경)

권장 저장 정책:
- voice_generations: 보이스 디자인/설정 메타데이터만 저장 (사용 정책만 변경)
- scene_assets: 영상 제작에 필요한 오디오 URL만 기록
- TTS 결과 오디오: 오디오는 스토리지에만 보관, DB에는 `audio_url`만 기록, `audio_storage_path`는 미사용
  - 영상 만들 때만 쓰이고, 재사용 가치가 낮아서 URL만 남기고 경로는 안 남김(스토리지는 별도로 보관)
- 캐릭터 이미지 저장: image_generations에 `image_url` 기록 + `metadata_json`에 storage_path 저장
  - 재사용 가능성이 높고, 실제 파일이 어디 있는지 추적 필요

실행 기준:
- generate_voice_node에서 voice_generations upsert 제거
- scene_assets upsert 유지(오디오 URL/재생시간)

### 파이프라인 테이블 매핑 (정책 반영)

- Voice 노드 (design_voice_node) -> voice_generations
- Voice 노드 (generate_voice_node) -> scene_assets (audio_url만 기록)
- Image 노드 (generate_character_image_node) -> image_generations
- Image 노드 (generate_scene_image_node) -> scene_assets (character_image_url/character_image_storage_path 기록)
- Video 노드 (generate_video_node) -> scene_videos

## 입력/출력 컬럼 매핑 (코드 함수 기준)

### 1) 텍스트/프롬프트 로딩 (DB → 파이프라인)

| 함수 | 입력 컬럼(DB) | 파이프라인 값(출력) |
|---|---|---|
| `load_scenario_prompts(script_id)` (`content_pipeline/db.py`) | `scenario_scripts.scenes`의 `visual_description` → `scene_motion_prompt` → `purpose` → `beats[].text` | `scene_inputs[*].prompt` (영상/이미지 프롬프트) |
| `load_scene_prompt(script_id, scene_index)` (`content_pipeline/db.py`) | 위 `load_scenario_prompts` 결과 | `scenario_prompt` (이미지 노드) |
| `load_voice_text(script_id, scene_index)` (`content_pipeline/db.py`) | `scenario_scripts.scenes.sceneX.dialogue` → `beats[].text` → `ad_requests.item_keymessage` | `text` (음성 합성 입력) |
| `load_character_prompt(character_id)` (`content_pipeline/db.py`) | `company_characters.character_name/mood/style` | `character_prompt` (캐릭터 이미지 프롬프트) |

### 2) scene_inputs 생성 (DB → 파이프라인 입력 조립)

| 함수 | 입력 컬럼(DB) | 파이프라인 값(출력) |
|---|---|---|
| `build_scene_inputs_from_db(script_id)` (`content_pipeline/pipeline_utils.py`) | `scenario_scripts.scenes` (`scene_type`) | `scene_inputs[*].scene_key` |
| 〃 | `load_scenario_prompts()` 결과 | `scene_inputs[*].prompt` |
| 〃 (옵션) | `scene_assets.audio_url/audio_storage_path/character_image_url/audio_duration_seconds` | `scene_inputs[*].audio_path`, `reference_image_path`, `duration_seconds` |

### 3) 이미지 생성 결과 저장 (파이프라인 → DB)

| 함수 | 입력(파이프라인) | 출력 컬럼(DB) |
|---|---|---|
| `generate_character_image_node()` → `upsert_image_generation()` (`content_pipeline/image/nodes.py`) | `character_id`, `script_id`, `character_prompt`, `result.image_url`, `result.size_bytes`, `metadata` | `image_generations.character_id/script_id/prompt/image_url/size_bytes/metadata_json` |
| `generate_scene_image_node()` → `upsert_scene_assets()` (`content_pipeline/image/nodes.py`) | `script_id`, `scene_key`, `result.image_url`, `result.storage_path`, `result.model` | `scene_assets.character_image_url/character_image_storage_path/generation_model` |

### 4) 음성 생성 결과 저장 (파이프라인 → DB)

| 함수 | 입력(파이프라인) | 출력 컬럼(DB) |
|---|---|---|
| `generate_voice_node()` → `upsert_voice_generation()` (`content_pipeline/voice/nodes.py`) | `character_id`, `script_id`, `scene_key`, `text`, `audio_url`, `duration_seconds`, `size_bytes`, `settings` | `voice_generations.character_id/script_id/scene_key/text_content/audio_url/duration_seconds/size_bytes/settings_json` |
| `generate_voice_node()` → `upsert_scene_assets()` (`content_pipeline/voice/nodes.py`) | `script_id`, `scene_key`, `audio_url`, `storage_path`, `duration_seconds`, `model` | `scene_assets.audio_url/audio_storage_path/audio_duration_seconds/generation_model` |

### 5) 씬 비디오 생성 결과 저장 (파이프라인 → DB)

| 함수 | 입력(파이프라인) | 출력 컬럼(DB) |
|---|---|---|
| `generate_video_node()` → `upsert_scene_video()` (`content_pipeline/video/nodes.py`) | `script_id`, `scene_key`, `voice_gen_id`, `image_id`, `video_url`, `duration_seconds`, `size_bytes`, `model` | `scene_videos.script_id/scene_key/voice_gen_id/image_id/video_url/duration_seconds/size_bytes/generation_model` |
| `generate_video_node()` → `upsert_scene_assets()` (`content_pipeline/video/nodes.py`) | `script_id`, `scene_key`, `video_url`, `storage_path`, `duration_seconds`, `model` | `scene_assets.scene_video_url/scene_video_storage_path/scene_video_duration/generation_model` |

### 6) 최종 병합 결과 저장 (파이프라인 → DB)

| 함수 | 입력(파이프라인) | 출력 컬럼(DB) |
|---|---|---|
| `merge_video_node()` → `insert_final_video()` (`content_pipeline/video/nodes.py`) | `company_id`, `ad_id`, `account_id`, `title`, `description`, `merged_video_url`, `script_id` | `videos.company_id/ad_id/account_id/title/description/s3_url/status/script_id` |


---

## 코드 구성
### 기능/모듈명
- 추가/수정 파일:
 - `content_pipeline/db.py`
 - `content_pipeline/voice/state.py`    # design_text, ttv_model_id 추가
 - `content_pipeline/voice/nodes.py`    # generate_voice_node에서 voice insert 수행
 - `content_pipeline/image/state.py`
 - `content_pipeline/image/nodes.py`
 - `content_pipeline/video/state.py`    # ad_id, company_id, account_id, title, description 필드 추가
 - `content_pipeline/video/nodes.py`    # merge_video_node에서 videos insert 수행
 - `scripts/image_generate_test.py`     # DB 연동을 위해 --script-id / --character-id / --scene-number / --scene-key 추가
 - `scripts/voice_generate_test.py`     # 그래프 실행 방식으로 전환, --script-id/--character-id/--scene-number/--scene-key 추가
 - `scripts/video_graph_from_scenes.py` # --script-id 필수로 추가, 시나리오에 주입
 - `scripts/db_healthcheck.py`

---

## 프로젝트 구조
- 변경 사항: O
```bash
content_pipeline/
├─ db.py
├─ voice/
|   ├─ nodes.py
|   └─ state.py
├─ image/
|   ├─ nodes.py
|   └─ state.py
├─ video/
|   ├─ nodes.py                  
|   └─ state.py
├─ scripts/
|   ├─ video_graph_from_scenes.py
|   ├─ voice_generate_test.py
|   ├─ image_generate_test.py
|   └─ db_healthcheck.py
└─ docs/kj/2026-01-26_db_schema_inventory.md
```

## 실행/테스트 방법
- 이미지(캐릭터)
```bash
python scripts\image_generate_test.py `
  --mode character --character-prompt "..." `
  --script-id 21 --character-id 10
```

- 이미지(씬)
```bash
python scripts\image_generate_test.py `
  --mode scene --use-db-prompts `
  --script-id 21 --scene-number 1 --character-id 10 `
  --product-image-path data/images/product.jpg
```

- 음성
```bash
python scripts\voice_generate_test.py `
  --use-db-text `
  --script-id 21 --scene-number 1 --character-id 10 `
  --voice-description "A calm Korean narrator voice." `
  --voice-name "TestVoice"
```

- 비디오 그래프
```bash
python scripts\video_graph_from_scenes.py `
  --scenes data/scenes/scenes.jsonl `
  --script-id 21 `
  --company-id 11 `
  --ad-id 13 `
  --title "Scene merge test" `
  --description "..."
```

### S3/공개 URL 변경시
- `audio_storage_path`: 저장 위치(파일 경로 또는 스토리지 key)
  - 예) file.mp3 또는 s3://bucket/key.mp3
- `audio_url`: 외부에서 접근 가능한 URL
  - 예) https://cdn.example.com/audio/file.mp3

---

## 트러블 슈팅

### 1) TTS 합성 음성은 DB에 저장하지 않는 것으로 결정
- 원인: 영상 만들때 제외하고는 사용할 일이 없기 때문.
- 해결: 오디오 파일은 스토리지에만 보관하고 DB에는 URL만 기록. scene_assets에만 최소 정보(audio_url, duration) 기록. 

### 2) 오디오가 DB에 저장되지 않는데 영상 생성이 안 됨
- 원인: video 노드에서 audio_url/audio_path를 DB에서 찾도록 구현.
- 해결: video 노드 입력(state/scene_inputs)에 audio_url 또는 audio_path를 직접 전달하도록 변경

### 3) voice_generations 재생성/추적 이슈
- 원인: text_hash나 settings_json을 DB에 남기지 않으면 재현이 어려움
- 해결: 재현 필요 시 scene_assets에 최소 메타(모델, 옵션)를 남기거나, voice_generations에 설계/설정만 기록
