# 작업 기록

## 2026-02-09 (영상 품질 개선)

### 작업 내용
- FFmpeg 병합: 반복 re-encode → single-pass xfade 체인 + H.264 CRF 18 인코딩
- FFmpeg 프레임 추출: `-q:v 2` → `-update 1` (FFmpeg 8.0 호환)
- 씬 간 캐릭터 일관성: prev_frame_path 우선순위 수정 (dead code 활성화)

### 변경 파일
- `content_pipeline/video/service.py`: `_local_merge_scene_videos`, `_remote_merge_scene_videos` single-pass 재작성, `extract_last_frame_local/remote` `-update 1` 적용
- `content_pipeline/video/nodes.py`: `generate_video_node()` line 218-225 — scene 2+에서 prev_frame이 character_image_url보다 우선하도록 조건 변경

### 알게 된 것 / 주의사항
- `pipeline_steps.py:287`에서 scene 2-4에 `character_image_url`을 fallback으로 넣기 때문에 `reference_image_url`이 항상 존재 → prev_frame fallback이 절대 실행되지 않았음 (dead code)
- xfade offset 공식: `accumulated += durations[i] - crossfade_seconds` (교차 구간만큼 빼야 함)

## 2026-02-08 (코드베이스 감사 Phase 1-4)

### 작업 내용
팀 분석(video/pipeline/backend 3개 에이전트)으로 28개 이슈 발견 → 4단계로 수정

#### Phase 1 (긴급 버그)
- H1: runner.py verify decision 값 불일치 ("show_to_user" → "present_to_user")
- H2: modification_request가 영상 생성 전 state에 미반영 → 이동 + prompt 주입

#### Phase 2 (핵심 설계)
- H5: 3개 동기 엔드포인트 → BackgroundTasks 변환 (voice/generate, scenario/revise, video/revise)
- H8: V4 시나리오 템플릿 대사 예시 제거 (LLM 복사 방지)

#### Phase 3 (코드 정리)
- M5: insert_image_generation 중복 제거 → upsert_image_generation 통일
- H7: 미사용 content_pipeline/state.py 삭제
- H6: should_regenerate() state 변경 → save_scenario_node()로 이동 (LangGraph 안티패턴 수정)
- M1: FFmpeg merge 오디오 스트림 존재 확인 추가 (로컬+원격)
- M2: run_video_step → generate_video_node + merge_video_node 위임 (~100줄 중복 제거)

#### Phase 4 (성능/품질)
- M3: merge_video_node duration_seconds=None → scene_outputs 합산
- M4: psycopg2 ThreadedConnectionPool 도입 + _PooledConnection 래퍼 (close()→putconn())
  - scenario_database.py도 db.py 풀 재사용
- M9: SSE N+1 쿼리 → 단일 LEFT JOIN LATERAL, 활성 ad만 조회, 세션 재활용, heartbeat 추가
- M6: workflow progress 하드코딩 → PROGRESS 상수 매핑 (17개소 통일)

### 변경 파일
- `AI/content_pipeline/video/runner.py`: H1 decision fix, H2 state 순서 변경
- `AI/content_pipeline/video/nodes.py`: H2 modification_request 지원, M2 retry+local_path, M3 duration 계산
- `AI/content_pipeline/video/service.py`: M1 _has_audio_stream + merge 오디오 분기
- `AI/content_pipeline/pipeline.py`: M2 run_video_step 위임 리팩토링
- `AI/content_pipeline/db.py`: M4 ThreadedConnectionPool, M5 insert_image_generation 제거
- `AI/content_pipeline/state.py`: H7 삭제
- `AI/content_pipeline/scenario/scenario_graph.py`: H6 should_regenerate state 변경 제거
- `AI/content_pipeline/scenario/scenario_nodes.py`: H6 save_scenario_node에 상태 결정 추가
- `AI/content_pipeline/scenario/scenario_database.py`: M4 db.py 풀 재사용
- `AI/content_pipeline/scenario/prompts/generate_scenario_templates.py`: H8 대사 예시 제거
- `AI/content_pipeline/image/nodes.py`: M5 upsert_image_generation 사용
- `backend/app/api/v1/endpoints/content_pipeline.py`: H5 BackgroundTasks 변환, M6 PROGRESS 상수
- `backend/app/api/v1/endpoints/sse.py`: M9 JOIN 쿼리 최적화

## 2026-02-08 (비디오 프롬프트 파이프라인 컨텍스트 주입)

### 작업 내용
- 영상 모델(LTX-2) 프롬프트가 제품/밈 맥락 없이 generic하게 생성되는 문제 수정
- `run_scenario_step`/`run_scenario_regenerate_step`에서 `company_data`/`meme_data` 반환 추가
- `_build_product_context` 헬퍼로 제품/밈 정보를 컨텍스트 문자열로 변환
- `run_video_step`에 `product_context` 파라미터 추가, JSON scene_data에 context 필드 주입
- `convert_video_prompt_node` 시스템 프롬프트 재작성 (Example Output 제거, context 활용 지시)
- `max_tokens` 220→400, 강제 prefix "A cinematic scene begins" 제거
- metadata 저장 시 `prompt[:200]` → `prompt[:500]`
- Graph 경로(`build_scene_inputs_from_db`)에도 `product_context` 전달
- `_build_scene_prompt`에서 `getattr` 사용으로 `AttributeError` 방지

### 변경 파일
- `content_pipeline/pipeline.py`: `_build_product_context` 추가, 리턴 dict 확장, `run_video_step` 시그니처 변경, 호출부 2곳 수정
- `content_pipeline/video/nodes.py`: 시스템 프롬프트 재작성, max_tokens 증가, prefix 제거, fallback 수정, getattr 안전성
- `content_pipeline/video/utils.py`: `product_context` 파라미터 추가, scene_payload에 context 주입
- `content_pipeline/video/state.py`: `product_context: str` 필드 추가

### 알게 된 것 / 주의사항
- 프롬프트에 Example Output을 넣으면 모델이 복사하는 문제가 비디오 프롬프트에서도 동일하게 발생
- 모든 변경이 optional 파라미터/리턴 필드 추가이므로 기존 코드 호환성 유지

## 2026-02-03 (전체 파이프라인 정합성 수정)

### 작업 내용
- 3개 레포 (Backend/AI/Frontend) 전수 분석 후 37개 이슈 발견, 31개 확인된 이슈 중 핵심 수정
- CRITICAL 3개 + HIGH 5개 + MEDIUM 3개 수정 완료

### 변경 파일
- `backend/content_pipeline.py:139`: C1 — `_lock_ad_request` SQL 컬럼명 `ad_request_id` → `ad_id`
- `backend/content_pipeline.py:121-122`: C2 — 영상 실패 시 `failed` 상태로 전환 (기존 `pending_approval`)
- `backend/content_pipeline.py:855-861`: C4 — `assets/approve`에 상태 검증 추가 (완료/생성중 상태 차단)
- `backend/content_pipeline.py:444`: M1 — `voice_design_prompt` None 덮어쓰기 방지
- `backend/content_pipeline.py:1055`: M6 — `video/revise` 시 ad_request 상태 업데이트 추가
- `AI/pipeline.py:541,577-581`: H3 — `run_asset_generation_step`에 `character_id` 파라미터 추가
- `AI/pipeline.py:627,673-678,693-699`: H2 — `run_content_generation_step`에 `character_id` 전달 (TTS/image)
- `AI/pipeline.py:718,934,978,1001,1020`: M7 — `run_video_step`에 `title` 전달 + 재생성 함수에도 동일 적용
- `frontend/video.ts:36`: H8 — `failed` → `failed` 매핑 (기존 `pending`)
- `frontend/page.tsx:1045-1068`: H10 — 완성 영상 `<video>` 태그 표시 (기존 플레이스홀더)

### 알게 된 것 / 주의사항
- `ad_requests` 테이블의 PK는 `ad_id` (NOT `ad_request_id`)
- `voice/approve`는 의도된 설계 — `elevenlabs_voice_id` 존재 = 승인 (명시적 플래그 없음)
- `scene_revisions=[]` (H1)은 Direct 모드에서는 DB에서 피드백을 읽으므로 무관
- `videoApi.generateCharacter/Voice`는 구 API URL 사용 — 현재 플로우에서 미사용 (dead code)
- `scenario/revise`는 동기 호출이라 타임아웃 위험 있음 (M3, 추후 BackgroundTasks로 전환 필요)

## 2026-02-03 (CLAUDE.md 설계문서 동기화)

### 작업 내용
- CLAUDE.md AI 함수 인터페이스를 실제 pipeline.py 코드와 동기화
- `run_character_step`: script_id 파라미터 제거 (캐릭터는 시나리오 전 생성)
- `run_scenario_step`: meme_id를 optional로 변경 (DB에서 자동 조회), 반환값에 meme_name 추가
- `run_scene_image_step`: character_image_path, product_image_path, character_id 파라미터 추가
- `run_video_step`: character_image_path 파라미터 추가
- `run_asset_generation_step`: 반환값에 character_image_path, character_prompt, voice_description 추가
- `run_content_generation_step`: path 파라미터 + company_id 추가, 반환값 확장
- `run_content_regenerate_step`: path 파라미터 + company_id 추가, 반환값 확장
- 새 함수 문서화: `run_image_regeneration_step`, `run_video_regeneration_step`
- Voice Provider 분기 설명 추가 (ElevenLabs/Qwen)
- Backend 상태명 매핑 표 추가
- video 파이프라인 노드 상태 ✅ 완료로 변경 (LTX-Video)

### 변경 파일
- `CLAUDE.md`: AI 함수 인터페이스 spec 동기화 (11건 수정)

### 알게 된 것 / 주의사항
- 코드가 설계문서보다 진화한 경우 문서를 코드에 맞춰 업데이트 (코드가 진실)

## 2026-02-03 (3-repo 전수 분석 추가 수정)

### 작업 내용
- [AI] voice/config.py: elevenlabs_max_custom_voices 타입 버그 수정 (str → int|None 변환 추가)
- [Backend] _bg_safe_rollback: 상태 복구 실패 시 'failed' 2차 fallback 추가 (generating 상태 영구 고착 방지)
- [Backend] content/approve: SELECT FOR UPDATE 행 잠금 추가 (동시 승인 race condition 방지)
- [Backend] voice/approve 거부 시 voice_sample_url도 같이 삭제 (거부된 음성 계속 재생되던 UX 버그)
- [Backend] video/revise: processing 상태 중복 요청 409 차단
- [Backend] content/generate, scenario/generate: completed 상태에서 재생성 차단
- [Frontend] failed 상태 UI 전면 추가: STATUS_CONFIG, GenerationContext TERMINAL_STATUSES, page.tsx 에러 카드+진행바
- [Frontend] SSE 재연결: 무한 3초 고정 재시도 → exponential backoff (1s~30s) + 최대 10회 + 실패 토스트 알림

### 변경 파일
- `content_pipeline/voice/config.py`: 타입 변환 수정
- `backend/app/api/v1/endpoints/content_pipeline.py`: rollback fallback, FOR UPDATE, voice rejection, completed 체크, video 409
- `frontend/src/lib/constants.ts`: failed 상태 추가
- `frontend/src/contexts/GenerationContext.tsx`: TERMINAL_STATUSES, STAGE_LABELS, SSE backoff
- `frontend/src/app/(dashboard)/user/video/[id]/page.tsx`: failed UI, getStepIndex, 진행바 에러 표시

### 알게 된 것 / 주의사항
- EventSource는 커스텀 헤더 미지원 → 토큰을 query string으로 전달할 수밖에 없음 (브라우저 제약)
- SELECT FOR UPDATE는 트랜잭션 내에서만 유효하므로 SQLAlchemy 세션이 자동커밋이 아닌지 확인 필요
- voice_sample_url을 null로 비우면 프론트가 "생성 중..." 으로 표시되므로 재생성 유도에 자연스러움

## 2026-02-03 (전체 코드 리뷰 기반 버그 수정)

### 작업 내용
- [A1 CRITICAL] 파인튜닝 시나리오 재생성 시 사용자 피드백이 프롬프트에 포함되지 않던 버그 수정
- [A2] pyproject.toml에서 qwen-tts 중복 의존성 (==0.0.5) 제거, >=0.0.5만 유지
- [A3/A4] "GPT-5" 잔여 docstring을 "GPT-4o"로 수정 (pipeline.py, image/nodes.py)
- [A5] voice/nodes.py 타이포 "생성된ㄴ" → "생성된" 수정
- [A6] scenario_nodes.py 미사용 import (Dict, Any) 및 주석처리된 import 블록 삭제
- [A7] db.py의 _maybe_presign_s3_url에서 매 호출마다 boto3 클라이언트를 재생성하던 문제를 @lru_cache로 캐싱
- [A8] pipeline.py의 scene 이미지 생성 조건에서 product_image_url 필수 조건 제거 (optional로 변경)
- [B1] backend: 영상 생성 실패 시 ad_request를 'failed' 대신 'pending_approval'로 전환하여 재시도 가능하게
- [B2] backend: 캐릭터 생성 실패 시 AI 응답의 error 필드를 로깅에 포함
- [F1] frontend: video_review 상태에서도 씬 데이터를 로드하도록 조건 추가

### 변경 파일
- `content_pipeline/scenario/scenario_nodes.py`: A1 피드백 포함 + A6 미사용 코드 삭제
- `pyproject.toml`: A2 중복 의존성 제거
- `content_pipeline/pipeline.py`: A3 docstring + A8 조건 완화 (2곳)
- `content_pipeline/image/nodes.py`: A4 docstring
- `content_pipeline/voice/nodes.py`: A5 타이포
- `content_pipeline/db.py`: A7 boto3 캐싱
- `backend/app/api/v1/endpoints/content_pipeline.py`: B1 복구 경로 + B2 에러 보존
- `frontend/src/app/(dashboard)/user/video/[id]/page.tsx`: F1 씬 로드 조건

### 알게 된 것 / 주의사항
- finetuned 분기와 일반 LLM 분기의 프롬프트 구성이 별도로 관리되어 동기화 주의 필요
- scene 이미지 생성 노드(generate_scene_image_node)는 product_image가 필수 validation인데, pipeline에서 optional로 넘기므로 불일치 가능 (별도 리팩토링 대상)

## 2026-02-03 (Backend ↔ AI Pipeline 통합 이슈 수정)

### 작업 내용
- Scene 데이터 키 통일: AI pipeline의 `dialogue`/`scenario_prompt` 키를 API 응답에 그대로 전달 + `content`/`visual_description` 하위호환 추가
- generate_scenario() 파라미터 검증 강화: ad_id/meme_id None일 때 기본값(0/1) 대신 Exception 발생
- revise_scenario() 피드백 경로 명확화: Direct 모드에서 scene_revisions 파라미터 무시 로깅 + docstring 보강
- generate_scene_image()에 scene_key 전달: DB image_generations 레코드가 scene과 연결되도록
- generate_video() company_id 생략 의도 주석 보강
- estimated_duration 동적 계산: 하드코딩 15/120 → 실제 scene_videos duration 합계 사용
- Frontend status 매핑 보강: content_generating, generating_scenario, generating_video 등 추가
- Scenario 조회 시 dialogue 키 fallback 추가 (content가 비어있으면 dialogue 사용)
- pipeline.py scene_videos DB insert 실패 로그 레벨 warning → error

### 변경 파일
- `backend/app/services/ai_pipeline_direct.py`: 키 통일, 파라미터 검증, scene_key 전달, 주석, estimated_duration
- `backend/app/api/v1/endpoints/content_pipeline.py`: scenario 조회/수정 시 dialogue fallback
- `frontend/src/lib/api/video.ts`: status 매핑 보강 (transformWorkflowToVideo, getProjectById)
- `AI/content_pipeline/pipeline.py`: 로그 레벨 변경

### 알게 된 것 / 주의사항
- Direct client에서 company_id를 생략하는 것은 의도된 설계 (Backend가 video row 생명주기 관리)
- revise_scenario()의 scene_revisions 파라미터는 Direct 모드에서 무시됨 — 피드백은 사전에 DB에 저장되어야 함
- Backend가 scenes를 DB에 저장할 때 AI가 반환한 키 구조 그대로 저장하므로, 조회 시 양쪽 키 모두 fallback 필요

## 2026-02-02 (파인튜닝 모델 성능 개선)

### 작업 내용
- Phase 1: 추론 코드 버그 수정
  - CoT + JSON 추론 방식 수정: structured output(json_schema) 제거 → extract_json_from_response()로 파싱, max_tokens 1200→2000, temperature 환경변수화(FINETUNED_TEMPERATURE, 기본값 0.5)
  - 추론 시 instruction/template 랜덤 선택 → 고정(index 0) 변경
- Phase 2: 학습 파이프라인 개선
  - Label masking 적용: system/user 토큰 -100 마스킹, assistant 응답만 loss 계산
  - 학습 데이터 품질 필터링 추가: Pydantic 스키마 + 대사 길이 + 한국어 비율 검증
  - 기업 템플릿 30→50개 확장 (헬스, 반려동물, 가전, 엔터, 교육 등)
  - LoRA rank 증가: r=16→32, alpha=32→64
- Phase 3: 평가 개선
  - Position bias 제거: A/B 순서 랜덤 swap + 결과 역매핑
  - Judge 모델 gpt-4o-mini → gpt-4o 업그레이드
  - 세분화된 평가 지표 추가: 대사 길이 준수율, 한국어 비율, CTA 포함 여부

### 변경 파일
- `content_pipeline/scenario/finetuned_client.py`: CoT 시도 → structured output fallback 전략, _call_runpod 헬퍼 분리, temperature 환경변수화
- `content_pipeline/scenario/scenario_nodes.py`: random.choice → 고정 index[0], random import 제거
- `AI-finetune/finetune/training/train.py`: label masking (system/user → -100)
- `AI-finetune/finetune/scripts/generate_data.py`: validate_scenario_quality() 추가 + 생성 루프에 품질 필터링 적용
- `AI-finetune/finetune/scripts/company_templates.py`: 20개 기업 템플릿 추가 (총 50개)
- `AI-finetune/finetune/training/configs/skt_ax.yaml`: lora_r 16→32, lora_alpha 32→64
- `AI-finetune/finetune/training/eval.py`: position bias 제거, gpt-4o judge, compute_detailed_metrics() 추가

### 추론 테스트 결과
- 짧은 프롬프트 (38 토큰): CoT 없이 JSON 정상 출력
- 간결한 instruction (946 토큰): Markdown 형태 출력 (JSON 파싱 실패)
- 상세 instruction (1391 토큰): 입력 에코 (모델 한계)
- **CoT → structured output fallback**: 1차 실패 → 2차 성공, 21.2초, 유효한 시나리오 생성 확인

### 알게 된 것 / 주의사항
- 3.1B 모델은 ~1000 토큰 이상의 프롬프트에서 입력 에코 또는 형식 무시 발생 → fallback 전략 필수
- CoT 시도 → structured output fallback이 현 모델에서 가장 실용적인 전략
- 재학습 (label masking + 데이터 증강 + LoRA rank 증가) 후 CoT 성공률 재측정 필요
- Label masking은 apply_chat_template(non_assistant, add_generation_prompt=True)로 prefix 길이를 계산하여 적용
- LLM-as-Judge에서 항상 A=finetuned 고정 시 position bias로 인해 ~5-10% 편향 발생 가능

## 2026-02-02 (3개 코드베이스 감사 기반 버그 수정)

### 작업 내용
- AI/Backend/Frontend 전체 감사 결과 CRITICAL+HIGH 이슈 수정
- AI: gpt-5→gpt-4o 모델명, voice design status 필드 누락, upsert_scene_assets 함수 추가, character_id 기본값, audio URL presign
- Backend: S3 URL presigning 누락(video preview + admin), asyncio.run→_run_async, GENERATING_STATUSES에 generating_voice 추가, admin N+1 쿼리
- Frontend: VideoStatus 타입에 누락 상태 추가, API endpoint plural 불일치, GenerationContext 상태 매핑 확장, content_generating 상태 반영

### 변경 파일
- `content_pipeline/image/nodes.py`: gpt-5→gpt-4o, character_id or 0 제거
- `content_pipeline/voice/nodes.py`: design 노드 status:"ok" 추가, audio_url presign 처리, _maybe_presign_s3_url import
- `content_pipeline/db.py`: upsert_scene_assets() 함수 추가
- `backend/app/api/v1/endpoints/content_pipeline.py`: _run_async 헬퍼, asyncio.run 전체 교체, video preview presign, generating_voice 추가
- `backend/app/api/v1/endpoints/admin.py`: s3_url presign, N+1 쿼리 batch 조회로 변경
- `frontend/src/types/index.ts`: VideoStatus에 asset_generating/pending/approved, content_pending, failed 추가
- `frontend/src/lib/api/video.ts`: /videos/ → /video/ 경로 통일
- `frontend/src/contexts/GenerationContext.tsx`: 상태 매핑/GENERATING_STATUSES/STAGE_LABELS 확장
- `frontend/src/app/(dashboard)/user/video/[id]/page.tsx`: scenario_generating → content_generating 상태 반영

### 알게 된 것 / 주의사항
- BackgroundTasks sync 함수는 Starlette run_in_threadpool에서 실행되므로 asyncio.run() 자체는 동작하지만, _run_async(new_event_loop)가 더 안전
- frontend build 실패는 admin 라우팅 충돌 (pre-existing) — 우리 변경과 무관
- backend import 검증은 bcrypt 의존성 누락으로 불가 (pre-existing)

## 2026-02-02 (scene_assets → DB ID 연결 누락 수정)

### 작업 내용
- `run_content_generation_step()` / `run_content_regenerate_step()`에서 TTS 결과의 `db_voice_gen_id`와 scene image 결과의 `db_image_id`를 `scene_assets`에 저장하지 않던 문제 수정
- `run_video_step()` 내 `upsert_scene_video()` 호출 시 `voice_gen_id=None`, `image_id=None` 하드코딩 → `asset`에서 실제 ID를 가져오도록 수정

### 변경 파일
- `content_pipeline/pipeline.py`: 5곳 수정
  - line ~680: TTS `db_voice_gen_id` → `asset`에 저장 (content generation)
  - line ~702: Scene image `db_image_id` → `scene_assets[i]`에 저장 (content generation)
  - line ~470-471: `upsert_scene_video()`에 `asset.get("db_voice_gen_id")`, `asset.get("db_image_id")` 전달
  - line ~979: TTS `db_voice_gen_id` → `asset`에 저장 (content regenerate)
  - line ~1001: Scene image `db_image_id` → `scene_assets[i]`에 저장 (content regenerate)

### 알게 된 것 / 주의사항
- `scene_videos` 테이블의 `voice_gen_id`, `image_id`가 항상 NULL이었던 원인
- presign 수정 (video/client.py)은 검증 결과 추가 수정 불필요

## 2026-02-02 (Voice Design 노드 DB 저장 로직 수정 + 캐릭터 이미지 안 보이는 문제 수정)

### 작업 내용
- Voice Design 노드가 `upsert_voice_generation()` (씬별 TTS 테이블)에 잘못 저장하던 문제 수정
- `scene_key` 필수 요구 제거 (voice design은 캐릭터 단위 작업)
- S3 presigned URL 만료 문제 수정 (voice + image 모두): `s3://` URI로 저장하여 백엔드가 `get_presigned_url()`로 재생성 가능
- 캐릭터 이미지 안 보이는 문제 수정: image storage도 동일한 presigned URL 만료 문제 있었음
- 백엔드 preview 엔드포인트에서 `get_presigned_url()` 호출 추가
- `_parse_s3_url()` regex가 presigned URL의 쿼리 파라미터를 key에 포함시키던 버그 수정

### 변경 파일
- `content_pipeline/voice/nodes.py`: design 노드(elevenlabs/qwen) DB 블록 간소화
- `content_pipeline/pipeline.py`: `run_voice_design_step()` 시그니처에서 `scene_key` 파라미터 제거
- `content_pipeline/voice/storage.py`: S3 fallback URL을 presigned URL → `s3://` URI로 변경
- `content_pipeline/image/storage.py`: 동일하게 presigned URL → `s3://` URI로 변경
- `backend/.../content_pipeline.py`: preview 엔드포인트에서 `get_presigned_url()` 적용
- `backend/.../s3_service.py`: `_parse_s3_url()` regex에서 `(.+)` → `([^?]+)`로 변경 (쿼리 파라미터 제외)

### 알게 된 것 / 주의사항
- S3 storage에서 `url` 필드에 presigned URL을 저장하면 1시간 후 만료됨 → 항상 `s3://` URI로 저장하고 서빙 시점에 presign
- 기존 DB에 만료된 presigned URL이 남아있을 수 있음 → `_parse_s3_url()`이 쿼리 파라미터를 제거하여 정상 파싱
- 캐릭터 재생성하면 새 URL이 `s3://` 형식으로 저장되어 정상 동작함

## 2026-02-02 (파인튜닝 모델 학습-추론 프롬프트 정렬)

### 작업 내용
- **근본 원인 수정**: 파인튜닝 모델의 학습 데이터와 추론 시 프롬프트 불일치 해결
  - System Prompt: 빈 문자열 → 학습 시 사용한 `SYSTEM_PROMPT` (CoT + JSON 스키마 + 규칙)
  - User Prompt: V4 단일 블록 → 학습 시 사용한 `USER_PROMPT_TEMPLATES` + `INSTRUCTION_VARIANTS` 형식
  - `FINETUNED_JSON_SUFFIX` 제거 (학습 형식과 충돌)

### 변경 파일
- `content_pipeline/scenario/finetuned_client.py`:
  - `FINETUNED_JSON_SUFFIX` → `FINETUNED_SYSTEM_PROMPT`로 교체 (instruction_variants.py의 SYSTEM_PROMPT 복사)
  - `generate_with_finetuned()`: suffix 추가 제거, 빈 system_prompt 시 기본 FINETUNED_SYSTEM_PROMPT 사용
- `content_pipeline/scenario/scenario_nodes.py`:
  - `generate_scenario_node()`: finetuned 분기에서 학습 데이터 형식 프롬프트 생성
  - `regenerate_scenario_node()`: 동일하게 학습 데이터 형식 적용
  - `import random` 추가
- `content_pipeline/scenario/finetuned_prompts.py` (신규):
  - `INSTRUCTION_VARIANTS`: 5개 변형 (instruction_variants.py에서 복사)
  - `USER_PROMPT_TEMPLATES`: 3개 변형 (instruction_variants.py에서 복사)

### 알게 된 것 / 주의사항
- 학습 데이터는 `[system, user, assistant]` 3개 메시지 형식, assistant는 `<thinking>` + JSON
- 기존 추론은 system 비어있고, user에 V4 단일 프롬프트 + JSON suffix → 학습 형식과 완전 불일치
- **vLLM structured output** (`response_format: json_schema`) 필수 - 프롬프트만으로는 JSON 형식 보장 불가
  - 모델이 마크다운/자유 형식으로 출력하거나 필드명 오류(`type` vs `scene_type`) 발생
  - `Scenario.model_json_schema()`를 `response_format`에 전달하면 토큰 레벨에서 강제
- 기존 `extract_json_from_response()` + 필드명 보정은 불필요 → `json.loads()`로 직접 파싱
- 토큰 예산: System(~250) + User(~800) + Output(~1200) ≈ 2250 토큰 (4096 컨텍스트 내 여유)

## 2026-02-02 (콘텐츠 통합 검수 구현)

### 작업 내용
- Backend: `scenario/approve`에서 즉시 completed 처리 제거 (시나리오 승인만 수행)
- Backend: `content/generate` 통합 엔드포인트 추가 (시나리오+TTS+영상 백그라운드 생성)
- Backend: `content/revise` 통합 엔드포인트 추가 (씬별 피드백 기반 통합 재생성)
- Backend: `content/approve` 수정 → 시나리오+영상+광고 동시 완료 처리 (유일한 완료 경로)
- Backend: scene_key 매핑 변경 (hook/body_1/body_2/close → scene_1/scene_2/scene_3/scene_4)
- Backend: `ContentGenerateRequest`, `ContentReviseRequest`, `ContentGenerateResponse` 스키마 추가
- Frontend: `approveContent()`, `generateContent()`, `reviseContent()` API 메서드 추가
- Frontend: 최종 승인 → `content/approve` 호출로 변경
- Frontend: 수정 요청 → 단일 `content/revise` 호출로 변경 (기존 2번 호출 제거)
- Frontend: 에셋 승인 후 → `content/generate` 호출로 변경

### 변경 파일
- `backend/app/api/v1/endpoints/content_pipeline.py`: 통합 엔드포인트 3개 추가, scenario/approve 수정, scene_key 수정
- `backend/app/schemas/video.py`: 통합 스키마 3개 추가
- `frontend/src/lib/api/video.ts`: 통합 API 메서드 3개 추가
- `frontend/src/app/(dashboard)/user/video/[id]/page.tsx`: 핸들러 3개 수정

### 알게 된 것 / 주의사항
- 기존 개별 엔드포인트(scenario/generate, video/generate 등)는 디버깅용으로 유지
- `content_generating` 상태를 GENERATING_STATUSES에 추가하여 중복 요청 방지
- 프론트엔드의 통합 검수 UI(영상 미리보기 + 씬별 카드)는 기존 그대로 활용

## 2026-02-02 (콘텐츠 통합 검수 설계 + CLAUDE.md 업데이트)

### 작업 내용
- 서비스 플로우 전체 검증: Backend API ↔ AI Pipeline ↔ Frontend 대조 분석
- **CRITICAL 발견**: `scenario/approve`가 즉시 completed 처리 → 영상 검수 우회
- **CRITICAL 발견**: 프론트엔드 수정 요청 시 2번 API 호출 (scenario/revise + video/generate)
- **HIGH 발견**: scene_key 네이밍 불일치 (backend: hook/body_1 vs AI: scene_1/scene_2)
- 통합 검수 설계 문서 작성 (`docs/plans/2026-02-02-content-review-integration.md`)
- CLAUDE.md 업데이트: Celery → FastAPI BackgroundTasks, API 스펙 현실화, 통합 검수 원칙 명시

### 변경 파일
- `docs/plans/2026-02-02-content-review-integration.md` (신규): 통합 검수 설계
- `CLAUDE.md`: Backend 연동 섹션 전면 수정 (API 스펙 + 비동기 처리 방식)

### 알게 된 것 / 주의사항
- Backend는 Celery가 아닌 FastAPI BackgroundTasks 사용 중
- Frontend는 이미 시나리오+영상 통합 검수 UI 구현 완료
- Backend `content/generate`, `content/revise` 통합 엔드포인트 구현 필요
- `scenario/approve`의 즉시 completed 처리 제거 필요

## 2026-02-02 (pipeline.py 전체 검증 후 버그 수정)

### 작업 내용
- **CRITICAL 1**: `video/nodes/` 빈 디렉토리 삭제 — Python 패키지가 `video/nodes.py` 모듈을 가려 ImportError 발생
- **CRITICAL 2**: `run_scenario_regenerate_step` SQL에 `description`, `hashtags` 컬럼 추가 + `Scenario` 복원 시 `title`/`description`/`hashtags` 전달 (Pydantic ValidationError 수정)
- **CRITICAL 3**: backend `ai_pipeline_direct.py`에서 삭제된 `run_content_pipeline` import/등록 제거
- **CRITICAL 4**: 테스트 파일에서 존재하지 않는 `run_scenario_revise_step` → `run_scenario_regenerate_step`으로 변경
- **HIGH 1**: `run_content_generation_step` + `run_content_regenerate_step`에 `company_id` 파라미터 추가 → `run_video_step`에 전달

### 변경 파일
- `content_pipeline/video/nodes/` (삭제): 빈 디렉토리 제거
- `content_pipeline/pipeline.py`: SQL 쿼리 수정, Scenario 복원 수정, company_id 파라미터 추가
- `backend/app/services/ai_pipeline_direct.py`: run_content_pipeline import/등록 제거
- `tests/integration/test_pipeline_steps.py`: run_scenario_revise_step → run_scenario_regenerate_step

### 알게 된 것 / 주의사항
- `video/nodes.py` 파일과 `video/nodes/` 디렉토리가 동시에 존재하면 Python은 패키지(디렉토리)를 우선함
- `scenario_scripts` 테이블에 `description`, `hashtags` 컬럼 존재 확인 필요 (없으면 migration 필요)

## 2026-02-02 (파인튜닝 모델 실서비스 연결)

### 작업 내용
- **vLLM 서버 → 시나리오 파이프라인 연결**
  - `finetuned_client.py` 신규: vLLM HTTP 클라이언트 (JSON 파싱 + Scenario 검증)
  - `scenario_nodes.py` 수정: generate + regenerate 노드에 `USE_FINETUNED_SCENARIO` 환경변수 분기 추가
  - review 노드는 GPT-4o 유지 (범용 평가에 적합)
- **vLLM 서버 스키마 의존성 제거**
  - `vllm_server.py`에서 `content_pipeline.scenario.scenario_schemas` import 제거
  - Pydantic 검증을 서버에서 제거 → 클라이언트(pipeline)에서 검증
- **Backend config 업데이트**
  - `USE_FINETUNED_SCENARIO`, `FINETUNED_ENDPOINT` 환경변수 추가

### 변경 파일
- `AI/content_pipeline/scenario/finetuned_client.py` (신규): vLLM HTTP 클라이언트
- `AI/content_pipeline/scenario/scenario_nodes.py`: generate/regenerate 분기 추가
- `AI-finetune/finetune/serving/vllm_server.py`: 스키마 import/검증 제거
- `backend/app/core/config.py`: 파인튜닝 모델 환경변수 2개 추가

### 추가: RunPod Serverless 배포 (vLLM Worker 템플릿)
- `finetuned_client.py`를 RunPod vLLM Worker (OpenAI-compatible API) 방식으로 변경
- `FINETUNED_ENDPOINT` → `RUNPOD_ENDPOINT_ID` + `RUNPOD_API_KEY`로 환경변수 변경
- RunPod `/runsync` 호출 + 타임아웃 시 폴링 (`_poll_runpod`)
- LoRA 어댑터는 `model` 파라미터로 경로 지정 (`LORA_ADAPTER_PATH`)

### 알게 된 것 / 주의사항
- 학습 데이터는 `[system, user, assistant]` 메시지로 분리, assistant 출력에 `<thinking>` 태그 + JSON
- 현재 파이프라인은 단일 프롬프트를 `user_prompt`로 전달 (system은 빈 문자열)
- RunPod vLLM Worker 사용 시 OpenAI-compatible API 형식 (messages 배열)
- RunPod Serverless `/runsync`는 ~90초 타임아웃, 초과 시 폴링 필요
- Network Volume에 베이스 모델 + LoRA 어댑터를 미리 업로드해야 함

---

## 2026-01-30 (프로덕션급 서비스 완성도 개선)

### 작업 내용

**Phase 1: 상태 정합성 & 중복 방지**
- 생성 엔드포인트(character/scenario/video)에 `_check_not_generating()` 가드 추가 (409 반환)
- `update_ad_status()` 2개 커밋 → 단일 트랜잭션으로 통합 (AdRequest + WorkflowExecution)
- `get_scenario_by_ad()` 정렬을 `created_at DESC` → `script_id DESC`로 변경 (PK 기반 정렬)

**Phase 2: 에러 처리 & 타임아웃**
- 프론트엔드 폴링에 5분 타임아웃 추가 + 타임아웃 시 에러 UI + 재시도 버튼
- 백엔드 모든 에러 메시지에서 raw exception 제거, 사용자 친화적 메시지로 통일
- `handleApproveAssets` 체인에 단계별 에러 추적 (`currentStep` 변수)

**Phase 3: 비동기 전환**
- `generate_ad_character`, `generate_ad_scenario`, `generate_ad_video`를 FastAPI `BackgroundTasks`로 전환
- 즉시 `{"status": "generating_*"}` 반환, 완료 시 DB 상태 업데이트
- `GET /{ad_id}/status` 경량 폴링 엔드포인트 추가 (status, current_stage, progress만 반환)

**Phase 4: API 계약**
- `backend/app/schemas/ai_response.py` 신규: AI 클라이언트 응답 Pydantic 모델 7개
- `AdRequestStatus`, `VideoStatus`, `ScenarioApprovalStatus` Enum 추가

**Phase 5: UX 보완**
- 빈 상태/404/서버 에러 UI 분리 (각각 다른 메시지 + 액션 버튼)
- 생성 중 4단계 step indicator 추가 (캐릭터 → 음성 → 시나리오 → 영상)

### 변경 파일
- `backend/app/api/v1/endpoints/content_pipeline.py`: 상태 가드, 백그라운드 태스크, 상태 엔드포인트
- `backend/app/crud/video.py`: 단일 트랜잭션 업데이트, script_id 정렬
- `backend/app/schemas/video.py`: 상태 Enum 3개 추가
- `backend/app/schemas/ai_response.py` (신규): AI 응답 스키마
- `frontend/.../page.tsx`: 폴링 타임아웃, 에러 상태 분리, step indicator
- `frontend/src/lib/api/video.ts`: (변경 없음, 참고만)

### 알게 된 것 / 주의사항
- FastAPI `BackgroundTasks`는 요청 반환 후 같은 프로세스에서 실행됨 (Celery 불필요)
- 백그라운드에서 DB 세션은 `SessionLocal()`로 새로 생성해야 함 (request scope 밖)
- `asyncio.run()`을 백그라운드 sync 함수에서 사용하여 async AI 클라이언트 호출
- 상태 가드로 race condition의 시간 창을 크게 줄일 수 있음 (완벽하지는 않음 - 분산 락 필요)

---

## 2026-01-29 (Backend ↔ AI 미연결 항목 통합)

### 작업 내용
- `final.py`에 Direct 모드 분기 추가 (기존 Mock/HTTP만 있던 곳에 `elif AI_PIPELINE_DIRECT_MODE` 추가)
- `ai_pipeline_direct.py`의 `revise_video()` 플레이스홀더를 실제 구현으로 교체 (`run_video_regeneration_step` 호출)
- 3개 클라이언트(Direct/HTTP/Mock)에 `regenerate_character_image()` 메서드 추가
- `content_pipeline.py`의 `revise_ad_character()` 엔드포인트에서 `regenerate_character_image()` 호출하도록 변경 (AI 검수 포함)

### 변경 파일
- `backend/app/api/v1/endpoints/final.py`: Direct 모드 분기 추가 (2줄)
- `backend/app/services/ai_pipeline_direct.py`: `revise_video()` 구현 + `regenerate_character_image()` 추가
- `backend/app/services/ai_pipeline_client.py`: `regenerate_character_image()` 추가
- `backend/app/services/ai_pipeline_mock.py`: `regenerate_character_image()` mock 추가
- `backend/app/api/v1/endpoints/content_pipeline.py`: 캐릭터 수정 시 AI 검수 포함 재생성 호출

### 알게 된 것 / 주의사항
- `CharacterRevisionRequest.revision_notes`는 필수 필드(min_length=1)이므로 항상 AI 검수 경로를 타게 됨
- `revise_video()`는 `scene_revisions`를 텍스트로 합쳐서 `modification_request`로 전달
- Mock/Direct/HTTP 3개 클라이언트의 메서드 시그니처 일관성 유지 필수

---

## 2026-01-29 (검수 노드 버그 수정 + 파이프라인 연결)

### 작업 내용

**버그 수정 (이미지/영상 검수 노드):**
- **이미지 검수 노드**: Claude → GPT-5 Vision으로 교체, S3 private URL presign 처리
- **영상 검수 노드**: URL → 로컬 다운로드 후 `genai.upload_file(path=로컬경로)` 전달
- **공통**: JSON 파싱을 `split("```")` → regex 기반 `parse_json_from_llm()`으로 교체
- **음성 검수 노드 제거**: 이미 사용자 피드백 루프 존재 → AI 자동 검수 불필요

**점수 기준 단순화:**
- 3단계(auto_approve/needs_confirmation/auto_retry) → 2단계(show_to_user/auto_retry)
- 이미지: ≥50점, 영상: ≥60점

**검수 결과 DB 저장:**
- 신규 테이블 대신 기존 `review_result` JSONB 컬럼 활용
- image → `company_characters.review_result` (`ai_verification_image` 키)
- video → `scenario_scripts.review_result` (`ai_verification_video` 키)

**파이프라인 연결:**
- `pipeline.py`에 `run_image_regeneration_step()`, `run_video_regeneration_step()` 추가
- `ai_pipeline_direct.py`에 두 함수 등록 + `regenerate_video()` 실제 구현
- `db.py`에 `load_video_by_id()` 추가 (video_id → s3_url, script_id 조회)
- `video/runner.py`의 `scenes_path` optional로 변경 (DB 기반 흐름에서 파일 불필요)

### 변경 파일

**AI:**
- `content_pipeline/utils.py` (신규): `download_to_temp()`, `parse_json_from_llm()`
- `content_pipeline/db.py`: `save_verification_result()`, `load_video_by_id()` 추가
- `content_pipeline/image/nodes.py`: Claude→GPT-5, presigned URL, JSON 파싱, DB 저장
- `content_pipeline/video/nodes.py`: 로컬 다운로드, JSON 파싱, DB 저장
- `content_pipeline/image/runner.py`: decision 값 동기화 (show_to_user/auto_retry)
- `content_pipeline/video/runner.py`: decision 값 동기화, `scenes_path` optional
- `content_pipeline/voice/runner.py`: `run_voice_regeneration_with_verification()` 제거
- `content_pipeline/voice/nodes.py`: `verify_audio_modification_node()` 제거
- `content_pipeline/pipeline.py`: `run_image_regeneration_step()`, `run_video_regeneration_step()` 추가

**Backend:**
- `backend/app/services/ai_pipeline_direct.py`: `regenerate_video()` DB 조회 + 파이프라인 호출 구현

### 프론트엔드 연결 상태

```
[Frontend] POST /{videoId}/revise
  → [Backend] final.py revise_video()
    → ai_client.regenerate_video(video_id, ad_id, revision_notes, feedback, company_id)
      → [Direct Client] load_video_by_id() → run_video_regeneration_step()
        → generate → merge → Gemini 검수 → 자동 재시도(최대 3회)
```

| 체인 | 상태 | 비고 |
|------|------|------|
| 영상 재생성 (Direct) | ✅ 연결됨 | `final.py` → `regenerate_video()` → 검수 포함 |
| 영상 씬별 수정 (Direct) | ⚠️ 미구현 | `content_pipeline.py` → `revise_video()` placeholder |
| 이미지 재생성 (Direct) | ⚠️ 미연결 | `run_image_regeneration_step` 등록됨, 호출 엔드포인트 없음 |
| `final.py` Direct 모드 | ⚠️ 미지원 | Mock/HTTP만 지원, `AI_PIPELINE_DIRECT_MODE` 분기 없음 |

### 알게 된 것 / 주의사항
- Gemini `genai.upload_file(path=)`는 로컬 파일 경로만 지원 (URL 불가)
- 기존 `review_result` JSONB 컬럼에 `jsonb_set()`으로 검수 결과 저장 (신규 테이블 불필요)
- `final.py`는 `AI_PIPELINE_DIRECT_MODE` 분기가 없음 — Direct 모드 사용 시 `final.py`에도 동일 분기 추가 필요
- 캐릭터 이미지 수정은 Backend에서 `generate_character_image()`로 단순 재생성 → AI 검수 없이 사용자가 직접 검수

## 2026-01-29 (시나리오 에이전트 연결 - Phase 2)

### 작업 내용
- **시나리오 에이전트 코드를 `origin/feature/59-regenerate-scenario-improve` 브랜치에서 가져옴**
  - scene1/scene2/scene3/scene4 형식 (hook/body/close 구버전 아님)
  - 생성 → 저장 → 검수 → 조건부 재생성 LangGraph 워크플로우 포함
- **pipeline.py 어댑터 수정**
  - `run_scenario_agent()` 호출에서 `meme_id` 제거 (DB에서 자동 로드)
  - `run_scenario_regenerate_step()` 전면 재작성: DB에서 이전 시나리오 + 휴먼 피드백 로드 → `regenerate_scenario_node` 직접 호출
  - `_merge_scene_videos` import 수정 (팀원 리팩토링으로 `VideoService._merge_scene_videos()`로 이동됨)
- **휴먼 피드백 연동 검증**
  - Backend `request_scenario_revision()`이 저장하는 형식과 AI `regenerate_scenario_node`가 기대하는 형식 일치 확인

### 변경 파일
- `content_pipeline/scenario/scenario_agent.py`: branch 59에서 복사 (진입점)
- `content_pipeline/scenario/scenario_schemas.py`: branch 59에서 복사 (scene1-4 + ReviewResult)
- `content_pipeline/scenario/scenario_state.py`: branch 59에서 복사
- `content_pipeline/scenario/scenario_graph.py`: branch 59에서 복사
- `content_pipeline/scenario/scenario_nodes.py`: branch 59에서 복사
- `content_pipeline/scenario/scenario_database.py`: branch 59에서 복사
- `content_pipeline/pipeline.py`:
  - `generate_scenario_task`: `meme_id` 파라미터 제거
  - `run_scenario_step`: `meme_id` optional로 변경
  - `run_scenario_regenerate_step`: DB 기반 재생성으로 전면 재작성
  - `_merge_scene_videos` → `service._merge_scene_videos()` 호출로 변경 (2곳)

### 알게 된 것 / 주의사항
- 시나리오 최신 코드는 AI-finetune이 아니라 AI 레포의 `feature/59-regenerate-scenario-improve` 브랜치에 있음
- `run_scenario_agent`에 `meme_id`를 넘기지 않음 — `load_company_data(ad_id)`에서 `ad_requests.meme_id` 자동 조회
- 휴먼 피드백 형식: `{feedback_type: "human_feedback", scene_feedback: {"scene1": "...", "scene3": "..."}}`
- `scenario_prompts.py`는 삭제됨 — 템플릿은 pipeline.py에서 주입
- 팀원이 video 모듈 리팩토링하여 `_merge_scene_videos`가 `VideoService` 메서드로 이동됨

---

## 2026-01-29 (Character Style 프롬프트 변환 개선)

### 작업 내용
- **`split_character_style()` 함수의 프롬프트 전면 개선**
  - ElevenLabs/Gemini API 가이드라인에 맞는 출력 형식으로 변경
  - 키워드 나열 → 서술형 문장 (영어)
  - 필수 포함 요소 명시 (스타일, 조명, 분위기, 나이, 음색, 속도 등)

### 변경 파일
- `content_pipeline/pipeline.py`:
  - `CharacterStyleSplit` Field 설명 업데이트 (lines 47-52)
  - `SPLIT_CHARACTER_STYLE_PROMPT` 전면 개선 (lines 55-96)
    - Gemini용: 서술형 문장, style/lighting/mood 포함
    - ElevenLabs용: 서술형 문장, age/timbre/pacing/emotion 포함
  - 기본값 영어로 변경 (lines 113-116)
  - docstring 예시 업데이트 (lines 108-109)

### 변경 전후 비교

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| character_prompt | "젊은 20대 남성, 밝은 표정" | "A cheerful young man in his early 20s with bright eyes and a warm smile. Photorealistic style with soft, even studio lighting..." |
| voice_description | "활기찬 목소리, 20대 남성" | "A young man in his early 20s with an energetic, warm voice. He speaks at a natural conversational pace with a bright, friendly tone..." |
| 언어 | 한국어 | 영어 (API 최적화) |
| 형식 | 키워드 나열 | 서술형 문장 |

### 알게 된 것 / 주의사항
- ElevenLabs Voice Design: age, timbre, pacing, emotion/character 필수
- Gemini Image Gen: subject, style, lighting, composition, mood 권장
- API 영어 프롬프트가 더 정확한 결과 생성

---

## 2026-01-29 (검수 상태 표시 불일치 수정)

### 작업 내용
- **마이 비디오 목록/상세 페이지 상태 표시 불일치 문제 수정**
  - 목록: "시나리오/영상 검수" → 상세: "캐릭터/음성 검수" 불일치 해결
  - `pending_approval` 기본값을 `character_review`로 변경

### 변경 파일 (Frontend)
- `frontend/src/lib/api/video.ts`:
  - Line 34: `'pending_approval': 'scenario_review'` → `'pending_approval': 'character_review'`

### 원인 분석
- `transformWorkflowToVideo()` 함수에서 `pending_approval` 상태 매핑 시:
  - 기본값이 `scenario_review`로 설정되어 있었음
  - `current_stage`가 NULL일 경우 기본값 사용 → 잘못된 단계 표시
  - 실제 워크플로우에서는 캐릭터/음성 검수가 먼저 진행됨

### 알게 된 것 / 주의사항
- 목록 API (`/api/v1/status/my-projects`)에서 `current_stage`가 NULL일 수 있음
- 기본값은 워크플로우 순서에 맞게 설정해야 함 (캐릭터 → 시나리오 순)
- `current_stage`가 있으면 여전히 정확한 단계로 오버라이드됨 (lines 47-52)

---

## 2026-01-29 (Video Generation Pipeline 연결)

### 작업 내용
- **Backend Direct Client에서 실제 영상 생성 호출 구현**
  - 기존 PLACEHOLDER 응답 → `run_video_step()` 실제 호출
  - TTS 생성 (씬별) → Video 생성 (씬별) → 병합 파이프라인 완성

### 변경 파일 (Backend)
- `backend/app/services/ai_pipeline_direct.py`:
  - `run_tts_step` 함수 lazy import 추가
  - `generate_video()` 메서드 전면 재구현:
    - 각 씬별 TTS 생성 (`run_tts_step`)
    - scenes 형식 변환 (API → pipeline)
    - `run_video_step()` 호출하여 영상 생성
    - 신규 파라미터 추가: `scenes`, `character_image_url`, `voice_id`, `title`
- `backend/app/api/v1/endpoints/content_pipeline.py`:
  - `generate_ad_video()` 엔드포인트 업데이트:
    - 캐릭터 데이터 조회 (image_url, voice_id)
    - `generate_video()` 호출 시 추가 파라미터 전달
    - 영상 생성 결과로 video 레코드 업데이트 (s3_url, status)
- `backend/app/services/ai_pipeline_mock.py`:
  - `generate_video()` 시그니처 업데이트 (API 호환성)
- `backend/app/services/ai_pipeline_client.py`:
  - `generate_video()` 시그니처 업데이트 (API 호환성)

### 파이프라인 흐름
```
POST /{ad_id}/video/generate
  ├─ 캐릭터 조회 (image_url, voice_id)
  ├─ AIPipelineDirectClient.generate_video()
  │   ├─ TTS 생성 (씬별, ElevenLabs)
  │   ├─ run_video_step() 호출
  │   │   ├─ 씬별 영상 생성 (ComfyUI)
  │   │   └─ ffmpeg 병합
  │   └─ 결과 반환 (video_url, video_path)
  └─ Video 레코드 업데이트 (s3_url, status='completed')
```

### 알게 된 것 / 주의사항
- COMFY_MODE 기본값이 "mock" → 실제 영상 생성 시 환경변수로 "comfyui" 설정 필요
- scenes 형식이 API (content, visual_description)와 pipeline (dialogue, scenario_prompt)에서 다름 → 변환 필요
- Mock 클라이언트 status도 "completed"로 변경하여 테스트 일관성 확보

### 검증 체크리스트
| 단계 | 확인 항목 | 예상 결과 |
|------|----------|----------|
| TTS | `scene_assets[*].audio_url` | ElevenLabs 음성 URL |
| 영상 | `videos.s3_url` | ✅ S3/로컬 영상 URL |
| 영상 | `videos.status` | ✅ "completed" |

---

## 2026-01-28 (Backend AI Direct Client 구현)

### 작업 내용
- **AI 함수 직접 호출 클라이언트 구현**: HTTP 대신 AI 함수를 직접 호출하여 프로토타입 테스트 가능
- **Config 옵션 추가**: `AI_PIPELINE_DIRECT_MODE` 환경변수로 direct/HTTP/mock 모드 전환
- **voice_design_prompt 자동 저장**: 캐릭터 생성 시 character_style 분리하여 DB에 저장

### 변경 파일 (Backend)
- `backend/app/services/ai_pipeline_direct.py` (신규):
  - `AIPipelineDirectClient` 클래스: HTTP client와 동일 인터페이스, AI 함수 직접 호출
  - Lazy import: 서버 시작 시 의존성 에러 지연 (mock 모드와 공존 가능)
  - `generate_character_image()`: `split_character_style()` → `run_character_step()` 호출
  - `generate_voice()`: `run_voice_design_step()` 호출
  - `generate_scenario()`: `run_scenario_step()` 호출
  - `generate_scene_image()`: `run_scene_image_step()` 호출
- `backend/app/core/config.py`:
  - `AI_PIPELINE_DIRECT_MODE` 설정 추가
- `backend/app/api/v1/endpoints/content_pipeline.py`:
  - Direct client 자동 선택 로직 추가
  - voice_design_prompt DB 저장 로직 추가 (캐릭터 생성 응답에서)
  - voice_description 우선순위: 요청값 > 캐릭터 저장값 > 기본값
- `backend/app/services/ai_pipeline_client.py`:
  - `generate_scenario()`: ad_id 파라미터 추가
- `backend/app/services/ai_pipeline_mock.py`:
  - `generate_scenario()`: ad_id 파라미터 추가 (호환성)

### 사용 방법
```bash
# AI 폴더의 환경에서 backend 실행 (의존성 공유)
cd AI && uv run -- uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 또는 환경변수로 direct 모드 활성화
AI_PIPELINE_DIRECT_MODE=true uvicorn backend.app.main:app
```

### 알게 된 것 / 주의사항
- AI 패키지 의존성(mutagen, langchain 등)이 backend 환경에 없으면 import 실패
- Lazy import로 서버 시작은 가능, 실제 호출 시점에 에러 발생
- 두 폴더가 같은 부모 디렉토리에 있어야 함: `meme-fluencer/AI`, `meme-fluencer/backend`

---

## 2026-01-28 (Backend/Frontend 연동 계획 구현)

### 작업 내용
- **status 값 통일**: `run_scenario_step`의 status를 `"completed"` → `"ok"`로 변경
- **DB 저장 로직 추가**:
  - `run_voice_design_step`: character_id가 있으면 `update_elevenlabs_voice_id()` 호출
  - `run_video_step`: company_id가 있으면 `insert_final_video()` 호출
- **CLAUDE.md 문서 업데이트**:
  - 2단계 검수 워크플로우로 간소화 (Asset → Content)
  - AI 함수 인터페이스 전면 갱신 (DB 파라미터, 응답 형식 명시)
  - Backend API 스펙 및 코드 예시 업데이트

### 변경 파일
- `content_pipeline/pipeline.py`:
  - Line 466: `"status": "completed"` → `"status": "ok"`
  - Line 556-559: `run_voice_design_step`에 DB 저장 로직 추가
  - Line 642-643, 690-703: `run_video_step`에 ad_id, title 파라미터 및 DB 저장 로직 추가
- `CLAUDE.md`:
  - 검수 워크플로우 섹션: 4단계 → 2단계로 간소화
  - 상태 흐름: asset_generating/pending/approved → content_generating/pending → completed
  - AI 함수 인터페이스: 모든 step 함수 시그니처 + 통합 함수 추가
  - Backend API 스펙: 2단계 워크플로우에 맞게 갱신
  - Backend 코드 예시: run_asset_generation_step, run_content_generation_step 사용

### 알게 된 것 / 주의사항
- 응답 형식 통일: 성공 시 `"ok"`, 실패 시 `"failed"`
- DB 저장 파라미터는 모두 optional (기존 호출 코드 영향 없음)
- 2단계 워크플로우가 UX 측면에서 더 간단함 (검수 횟수 감소)

---

## 2026-01-28 (시나리오 파인튜닝 데이터 생성 완료)

### 작업 내용
- **파인튜닝 학습 데이터 2,379개 생성** (GPT-4o Teacher)
- **Config 하이퍼파라미터 수정** (논문 기반)
- **train.py Chat Template 동적 적용**
- **RunPod 학습 가이드 문서 작성**

### 생성된 데이터

| 항목 | 값 |
|------|-----|
| 총 샘플 | 2,379개 |
| 밈 수 | 119개 (전체) |
| 밈당 샘플 | 20개 |
| 성공률 | 99.96% |
| 비용 | $49.96 |

### Split 결과

| Split | 샘플 수 | 비율 |
|-------|--------|------|
| Train | 1,962 | 77.8% |
| Val | 238 | 9.4% |
| Test | 322 | 12.8% |

### 변경 파일 (AI-finetune repo)
- `finetune/training/configs/*.yaml`: lora_dropout 0.1, use_dora true
- `finetune/training/train.py`: tokenizer.apply_chat_template() 사용
- `finetune/data/splits/`: train.jsonl, val.jsonl, test.jsonl
- `docs/RUNPOD_TRAINING_GUIDE.md`: RunPod 학습 가이드 신규

### 품질 검사 결과
- 감정 다양성: 15개+ 사용 (신나서 12.8%, 진지하게 11.2%, 기타 76%)
- Hook 다양성: 밈별로 다르게 활용 ✅
- 회사별 차이: 상품 특성 반영 ✅

### 다음 단계
1. 데이터 파일 Git push (AI-finetune repo)
2. RunPod에서 학습 실행
3. 모델 평가 및 배포

---

## 2026-01-28 (Pipeline DB 연동 수정)

### 작업 내용
- **템플릿 V1 → V4 변경**: `{character_mood}` 키 에러 해결
- **Step 함수에 DB 필드 파라미터 추가**: optional로 character_id, script_id, scene_key, company_id 등

### 변경 파일
- `content_pipeline/pipeline.py`:
  - Line 29: import `GENERATE_SCENARIO_TEMPLATE_V1` → `GENERATE_SCENARIO_TEMPLATE_V4`
  - Line 177, 450: 템플릿 사용처 V1 → V4 변경, used_templates 업데이트
  - `run_character_step()`: `character_id`, `script_id` 파라미터 추가
  - `run_voice_design_step()`: `character_id`, `scene_key` 파라미터 추가
  - `run_tts_step()`: `character_id`, `script_id`, `scene_key` 파라미터 추가
  - `run_scene_image_step()`: `script_id`, `scene_key` 파라미터 추가
  - `run_video_step()`: `script_id`, `company_id` 파라미터 추가

### 검증
```bash
uv run python -c "from content_pipeline.pipeline import run_scenario_step; print('OK')"
# OK
```

### 알게 된 것 / 주의사항
- 템플릿 V4가 `{character_mood}` 대신 다른 변수 사용
- DB 필드 파라미터는 모두 optional (기존 호출 코드 영향 없음)

---

## 2026-01-28 (train.py Chat Template 동적 적용)

### 작업 내용
- **모델별 Chat Template 자동 적용 기능 추가**
  - 기존: ChatML 형식 하드코딩 (`<|im_start|>`, `<|im_end|>`)
  - 수정: `tokenizer.apply_chat_template()` 사용

### 변경 파일
- `finetune/training/train.py`:
  - `format_chat_messages(messages, tokenizer)`: tokenizer.apply_chat_template() 사용
  - `load_dataset_from_jsonl(jsonl_path, tokenizer)`: tokenizer 파라미터 추가
  - `load_datasets()`: tokenizer 전달하도록 수정
  - 미사용 import 제거 (`peft.LoraConfig`)

### 문제 해결
| 모델 | 이전 (ChatML) | 수정 후 |
|------|--------------|--------|
| SKT A.X 3.1 | ❌ 템플릿 불일치 | ✅ 자동 적용 |
| Kakao Kanana 8B | ❌ Llama3 스타일 | ✅ 자동 적용 |
| Mi:dm 2.0 Mini | ❌ 자체 템플릿 | ✅ 자동 적용 |

### 알게 된 것 / 주의사항
- 한국어 모델들은 각자 다른 Chat Template 사용
- `tokenizer.apply_chat_template(tokenize=False)` → 문자열 반환
- Unsloth는 "any transformers model" 지원하므로 한국어 모델도 동작

---

## 2026-01-28 (시나리오 파인튜닝 Config 하이퍼파라미터 수정)

### 작업 내용
- **검증된 논문/문서 기반으로 Config 하이퍼파라미터 수정**
  - lora_dropout: 0.05 → 0.1 (QLoRA 논문 권장)
  - use_dora: true 추가 (ICML 2024 DoRA 논문)

### 변경 파일
- `finetune/training/configs/skt_ax.yaml`:
  - `lora_dropout: 0.1` (QLoRA 논문: 7-13B 모델 권장)
  - `use_dora: true` (ICML 2024: +3.7pp 성능 향상)
- `finetune/training/configs/kanana_8b.yaml`:
  - `lora_dropout: 0.1`
  - `use_dora: true`
- `finetune/training/configs/midm_mini.yaml`:
  - `lora_dropout: 0.1` (보수적 적용)
  - `use_dora: true`

### 검증 근거 (논문/공식문서)

| 항목 | 이전 값 | 수정 값 | 근거 |
|------|--------|---------|------|
| lora_dropout | 0.05 | 0.1 | QLoRA Paper: 7-13B는 0.1, 33-65B는 0.05 |
| use_dora | (없음) | true | ICML 2024 DoRA: LLaMA 7B +3.7pp, 13B +1.0pp |

### 참고 자료
- [QLoRA Paper - HuggingFace LLM Course](https://huggingface.co/learn/llm-course/en/chapter11/4)
- [DoRA: ICML 2024](https://arxiv.org/html/2402.09353v4)
- [NEFTune: ICLR 2024](https://arxiv.org/abs/2310.05914) - alpha=5 유지 (검증됨)

---

## 2026-01-28 (시나리오 파인튜닝 Config 업데이트)

### 작업 내용
- **Config 파일 모델명 수정 및 최신 기법 적용**
  - 잘못된 모델명 수정 (HuggingFace ID 정확히 반영)
  - NEFTune, DoRA 옵션 추가
  - lora_alpha = 2x lora_r 권장값으로 업데이트

### 변경 파일
- `finetune/training/configs/skt_ax.yaml` (신규, skt_ax_7b.yaml 대체):
  - 모델명: `SKT/A.X-3.1-7B-Instruct-Light` → `skt/A.X-3.1-Light`
  - lora_alpha: 16 → 32
  - lora_dropout: 0 → 0.05
  - NEFTune 추가: `use_neftune: true`, `neftune_noise_alpha: 5`
- `finetune/training/configs/kanana_8b.yaml` (신규):
  - 모델: `kakaocorp/kanana-1.5-8b-instruct-2505` (Apache 2.0)
  - 32K 토큰 컨텍스트, Function Calling 강화
- `finetune/training/configs/midm_mini.yaml`:
  - 모델명: `KT-AI/midm-bitext-S-1.8B-inst-v1` → `K-intelligence/Midm-2.0-Mini-Instruct`
  - lora_r: 16 → 8 (경량 모델용)
  - lora_alpha: 16 (2x lora_r)
- `finetune/training/configs/hyperclova_x.yaml` (삭제):
  - API 기반 파인튜닝 불필요, 데이터 형식 불일치
- `finetune/training/train.py`:
  - NEFTune 지원: `neftune_noise_alpha` 파라미터 추가
  - DoRA 지원: `use_dora=True` 옵션 추가

### 모델 선정 근거

| 순위 | 모델 | HuggingFace ID | 선택 이유 |
|------|------|----------------|----------|
| 1순위 | SKT A.X 3.1 Light | `skt/A.X-3.1-Light` | CLIcK 1위, 한국어 from-scratch |
| 2순위 | 카카오 Kanana 1.5 8B | `kakaocorp/kanana-1.5-8b-instruct-2505` | Apache 2.0, 32K 토큰 |
| 3순위 | Mi:dm 2.0 Mini | `K-intelligence/Midm-2.0-Mini-Instruct` | 경량 (2.3B), Ko-IFEval 우수 |

### 최신 파인튜닝 기법 적용

| 기법 | 설명 | 적용 |
|------|------|------|
| NEFTune | 학습 시 노이즈 추가, 성능 향상 | 기본 적용 (alpha=5) |
| DoRA | Weight-Decomposed LoRA, QLoRA보다 성능 우수 | 선택 적용 |

### 알게 된 것 / 주의사항
- HuggingFace 모델 ID는 대소문자 구분 (`skt/A.X-3.1-Light` vs `SKT/A.X-3.1-7B-Instruct-Light`)
- lora_alpha = 2x lora_r가 권장값 (기존 1:1 비율 수정)
- EXAONE 3.5는 NC 라이선스로 상업 사용 불가 → Kanana 8B로 대체
- KT Mi:dm 2.0은 `K-intelligence` organization에서 제공

---

## 2026-01-27 (Content Pipeline 흐름 수정)

### 작업 내용
- **프론트엔드 흐름에 맞게 AI 파이프라인 step 함수 수정**
  - 1단계: 캐릭터 이미지 + 음성 디자인 동시 생성
  - 2단계: 시나리오 → TTS → 영상 통합 생성
  - character_style 분리 (LLM 기반) 추가

### 변경 파일
- `content_pipeline/pipeline.py`:
  - `split_character_style()`: LLM으로 character_style을 이미지용/음성용 프롬프트로 분리
  - `_save_voice_sample()`: Base64 샘플 음성을 storage에 저장하는 헬퍼
  - `run_voice_design_step()` 수정: voice_sample_url 반환 추가
  - `run_asset_generation_step()`: 캐릭터 + 음성 병렬 생성 (ThreadPoolExecutor)
  - `run_content_generation_step()`: 시나리오 → TTS → 영상 통합 생성
  - `run_scenario_revise_step()`: 시나리오 재생성 틀 (NotImplementedError)
- `tests/integration/test_pipeline_steps.py`:
  - `TestSplitCharacterStyle`: split_character_style 테스트 3개
  - `TestAssetGeneration`: run_asset_generation_step 통합 테스트
  - `TestScenarioRevise`: run_scenario_revise_step NotImplementedError 테스트
  - `TestVoiceDesignStep` 업데이트: voice_sample_url 검증 추가

### 신규 함수 요약
| 함수 | 용도 | 입력 | 출력 |
|------|------|------|------|
| `split_character_style()` | character_style 분리 | character_style | character_prompt, voice_description |
| `run_asset_generation_step()` | 1단계 병렬 생성 | character_style, voice_name | image_url, voice_id, voice_sample_url |
| `run_content_generation_step()` | 2단계 통합 생성 | ad_id, meme_id, voice_id, ... | scenes, video_url, ... |
| `run_scenario_revise_step()` | 시나리오 재생성 | scene_revisions | NotImplementedError (팀원 구현 예정) |

### 테스트 결과 (신규 테스트 포함)
| 테스트 | 상태 | 비고 |
|--------|------|------|
| split_character_style_basic | ✅ PASSED | LLM 분리 정상 |
| split_character_style_empty | ✅ PASSED | 빈 입력 시 기본값 |
| split_character_style_visual_only | ✅ PASSED | 시각 요소만 입력해도 voice 추론 |
| scenario_revise_not_implemented | ✅ PASSED | NotImplementedError 발생 |
| voice_design_step | ✅ PASSED | voice_sample_url 반환 확인 |

### 알게 된 것 / 주의사항
- `VoiceDesignResponse.previews[0].audio_base_64`에 샘플 음성 있음
- `design_voice()` → 샘플 저장 → `create_voice()` 순서로 호출해야 URL 확보 가능
- ThreadPoolExecutor로 캐릭터/음성 병렬 생성 시 오류 수집 방식 주의

---

## 2026-01-27 (Content Pipeline 통합 테스트)

### 작업 내용
- **Content Pipeline step 함수들 통합 테스트 구현**
  - `run_scenario_step()`, `run_character_step()`, `run_voice_design_step()`, `run_tts_step()`, `run_scene_image_step()` 테스트
  - `run_video_step()` 제외 (RunPod 의존성)
  - pytest markers 활용 (`@pytest.mark.integration`, `@pytest.mark.slow`)
  - API 키 없으면 자동 스킵

### 변경 파일
- `tests/integration/test_pipeline_steps.py`: 신규
  - `TestScenarioStep`: 시나리오 생성 테스트 (OpenAI + DB)
  - `TestCharacterStep`: 캐릭터 이미지 생성 테스트 (NanoBanana/Gemini)
  - `TestVoiceDesignStep`: Voice Design 테스트 (ElevenLabs)
  - `TestTTSStep`: TTS 생성 테스트 (프리셋 voice_id, 생성된 voice_id, 에러 케이스)
  - `TestSceneImageStep`: 씬 이미지 생성 테스트 (path 방식, 에러 케이스)
  - `TestPipelineStepsSequence`: 전체 시퀀스 테스트 (0→1→2→3→4 순차 실행)
- `tests/conftest.py`:
  - dotenv 로딩 추가 (테스트에서 .env 환경변수 사용)
- `tests/unit/test_verifier.py`:
  - `is_valid_korean_definition` import 경로 수정 (verifier → common)

### 테스트 결과 (10개)
| 테스트 | 상태 | 비고 |
|--------|------|------|
| Scenario | ✅ PASSED | 시나리오 4씬 생성 |
| Character | ✅ PASSED | 캐릭터 이미지 생성 |
| Voice Design | ✅ PASSED | voice_id 생성 |
| TTS (프리셋) | ✅ PASSED | duration: 2.27s |
| TTS (생성된 voice) | ✅ PASSED | |
| TTS (에러 케이스) | ✅ PASSED | |
| Scene Image | ⚠️ FLAKY | API rate limit으로 가끔 실패 |
| Scene Image (paths) | ⏭️ SKIPPED | 로컬 제품 이미지 없음 |
| Scene Image (에러) | ✅ PASSED | |
| Full Sequence | ✅ PASSED | 전체 파이프라인 성공 |

### 실행 방법
```bash
# 전체 통합 테스트
uv run pytest tests/integration/test_pipeline_steps.py -v

# ElevenLabs 테스트만
uv run pytest tests/integration/test_pipeline_steps.py -v -k "Voice or TTS"

# 전체 시퀀스 (모든 API 키 필요)
uv run pytest tests/integration/test_pipeline_steps.py -v -k "full_sequence"
```

### 알게 된 것 / 주의사항
- `run_scene_image_step()`은 character_image_path 지원함 (pipeline.py:455-479)
- ElevenLabs 프리셋 voice_id "21m00Tcm4TlvDq8ikWAM" (Rachel)로 테스트 가능
- 테스트 간 결과 공유를 위해 모듈 레벨 `_test_results` dict 사용
- pytest `-s` 플래그로 print 출력 확인 가능

---

## 2026-01-26 (Video 모듈 연결)

### 작업 내용
- **Content Pipeline에 Video 모듈 연결 완료**
  - `generate_video_task` 추가 (씬별 영상 생성 + ffmpeg 병합)
  - `run_video_step` 추가 (검수 워크플로우용)
  - `run_content_pipeline()`에서 video 단계 활성화

### 변경 파일
- `content_pipeline/pipeline.py`:
  - video 모듈 import 추가 (`load_video_config`, `VideoService`, `_merge_scene_videos`)
  - `generate_video_task`: 씬별 VideoService.generate_video() 호출 + _merge_scene_videos로 병합
  - `run_video_step`: 검수용 step 함수 (동일 로직, @task 없이)
  - `run_content_pipeline`: video_result 추가, 반환값에 video_url/video_path/scene_videos 포함

### 구현 상세
- VideoService 직접 호출 (nodes.py 우회) - 더 유연한 인터페이스
- 첫 씬에만 character_image를 reference로 전달
- crossfade 0.3초로 씬 병합
- storage 업로드 후 video_url 반환

### 테스트 결과
- RunPod + ComfyUI + LTX-2 모델로 실제 영상 생성 성공
- 생성 파일: `data/video/scene_1769416079.mp4` (603KB)

### 알게 된 것 / 주의사항
- video/nodes.py의 generate_video_node는 ScenarioOutput 객체 필수 → VideoService 직접 사용이 더 유연
- ffmpeg, ffprobe가 PATH에 있어야 병합 가능
- COMFY_MODE=mock이면 mock 영상 생성 (테스트용)
- RunPod ComfyUI 실행 시 필요: ffmpeg, opencv-python, imageio-ffmpeg

---

## 2026-01-26 (리팩토링)

### 작업 내용
- **meme_collector 디렉토리 리팩토링**
  - 사용하지 않는 코드/함수 제거
  - 중복 로직 통합
  - import 정리

### 변경 파일
- `meme_collector/workers/context_builder.py`:
  - `get_collected_summary()` 함수 제거 (사용처 없음)
- `meme_collector/deep_research/__init__.py`:
  - `ContextBuilder`, `get_collected_summary` export 제거
- `meme_collector/deep_research/researchers/text.py`:
  - `_is_korean_text()` 함수 제거 (중복)
  - `_clean_definition()` 함수 간소화 - `common.is_valid_korean_definition` 사용
- `meme_collector/deep_research/researchers/usage.py`:
  - 사용하지 않는 import 제거 (json, Literal, HumanMessage, SystemMessage, ChatOpenAI, create_react_agent, BaseModel, Field, config)
  - 사용하지 않는 클래스 제거 (UsageExample, UsageNotes)
  - 사용하지 않는 상수 제거 (USAGE_TOOLS, USAGE_SYSTEM_PROMPT)
  - 사용하지 않는 도구 함수 제거 (extract_usage_from_video_list)
  - 중복 import 제거 (extract_usage_from_videos - 함수 내부에서 중복 import)
- `meme_collector/nodes/finalize.py`:
  - logging import를 모듈 레벨로 이동 (함수 내부 import 제거)
- `meme_collector/_legacy/__init__.py`:
  - export 제거 및 DEPRECATED 표시 (compile_legacy_graph, run_collector)

### 제거된 코드 요약
| 항목 | 파일 | 이유 |
|------|------|------|
| `get_collected_summary()` | context_builder.py | 미사용 함수 |
| `_is_korean_text()` | text.py | common/utils.py와 중복 |
| `UsageExample`, `UsageNotes` | usage.py | ReAct Agent 제거로 미사용 |
| `USAGE_TOOLS`, `USAGE_SYSTEM_PROMPT` | usage.py | ReAct Agent 제거로 미사용 |
| `extract_usage_from_video_list` | usage.py | ReAct Agent 도구, 미사용 |
| `_legacy/` exports | __init__.py | 레거시 코드, 외부 참조 없음 |

### 알게 된 것 / 주의사항
- `_legacy/` 디렉토리: 외부 import 없음, 삭제 가능 상태 (권한 문제로 파일 삭제 대신 export 비활성화)
- usage.py: ReAct Agent에서 직접 도구 호출 방식으로 이미 변경됨 (source_url 보존 목적)
- 중복 한국어 검증 로직: text.py의 `_is_korean_text()` vs common/utils.py의 `is_valid_korean_definition()` - 후자로 통합

---

## 2026-01-26

### 추가 작업: 밈 일괄 처리

#### source_video 채우기 (fill_source_videos.py)
- **대상**: PROCESSED 상태이면서 source_video가 비어있는 밈 67개
- **성공**: 66개
- **실패**: 1개 (폰팔이차팔이용팔이의치킨회동 - 영상 없음)

#### READY 밈 처리 (process_unprocessed_memes.py)
- **대상**: READY 상태 밈 17개
- **PASS**: 5개 (score ≥ 70, PROCESSED로 이동)
- **FAIL**: 12개 (품질 검증 실패, READY 유지)
- **ERROR**: 0개

#### DB 현재 상태
| 상태 | 밈 수 |
|------|-------|
| PROCESSED | 120개 |
| READY | 12개 |

| source_video 유무 | 수 |
|------------------|-----|
| 있음 | 119개 |
| 없음 | 1개 |

---

### 작업 내용
- **Deep Research 에이전트 종합 개선 (LangGraph 2025 패턴 적용)**
  - 실행 순서 변경: text → media/usage (의존성 해결)
  - Send API로 병렬 작업 디스패치 (Map 패턴)
  - YouTube 검색 성공률 향상 (key_phrase 파라미터 추가)
  - 프롬프트 품질 개선 (TextResearcher, Verifier)

### 변경 파일
- `meme_collector/deep_research/supervisor.py`:
  - 실행 순서: text 먼저 → media/usage 병렬 (Send API)
  - Type alias 추가: ResearcherNode, AnalysisNode, AllNodes
  - 명시적 로깅 추가 (Phase 1/2/3/4)
- `meme_collector/deep_research/graph.py`:
  - docstring 강화 (아키텍처, 기술 포인트 문서화)
- `meme_collector/tools/youtube.py`:
  - `search_youtube_shorts()`: key_phrase 파라미터 추가
  - `_build_meme_queries()`: key_phrase로 직접 검색, 챌린지 검색어 추가
  - `_filter_relevant_videos()`: fallback 로직 (LLM이 "없음" 반환 시 상위 2개 반환)
- `meme_collector/deep_research/researchers/media.py`:
  - 프롬프트: creator, key_phrase 전달 강조
  - 컨텍스트: key_phrase 변수 명시적 추출
- `meme_collector/deep_research/researchers/usage.py`:
  - text_researcher 결과 활용 (definition, key_phrase, origin)
- `meme_collector/deep_research/researchers/text.py`:
  - definition: 200자 이상, 마크다운 금지
  - key_phrase: 이모지/ㅋㅋ/!! 보존 강조
  - origin: source/date/platform 형식 명시
- `meme_collector/workers/verifier.py`:
  - 추가 검증 항목 (definition, key_phrase, usage_examples, origin 품질)

### 알게 된 것 / 주의사항
- LangGraph Send API: `return [Send("node", state), ...]` 형태로 병렬 디스패치
- 의존성 있는 researcher는 순차 실행 후 Send API로 나머지 병렬 처리
- YouTube 검색: creator + key_phrase 조합이 meme_name 단독보다 정확도 높음
- LLM 필터 실패 시 fallback으로 검색 결과 유지 (완전 실패 방지)

### 예상 효과
| 영역 | 현재 | 목표 |
|------|------|------|
| 영상 검색 성공률 | 3% | 30%+ |
| definition 품질 | 영어 혼재, 짧음 | 200자+, 한국어, 유래 포함 |
| key_phrase 정확도 | 설명문 포함 | 실제 대사만 |

### 추가 작업: yt-dlp fallback 추가

YouTube Data API 할당량 초과 시에도 영상 검색 가능하도록 yt-dlp fallback 추가

#### 변경 파일
- `meme_collector/tools/youtube.py`:
  - `_search_ytdlp()`: yt-dlp로 YouTube 검색 (subprocess)
  - `search_youtube_shorts()`: API 실패 시 yt-dlp fallback 사용
  - 쇼츠 필터링: `duration <= 60`으로 60초 이하 영상만

- `meme_collector/deep_research/researchers/usage.py`:
  - `origin` 파라미터 제거 (string vs dict 타입 불일치 버그 수정)

#### 테스트 결과 (매끈매끈하다 매끈매끈한)
- **reference_videos: 5개** (yt-dlp로 검색 성공)
- **Score: 75점 PASS**
- YouTube API 할당량 초과 상태에서도 정상 작동

---

## 2026-01-25

### 작업 내용
- **나무위키 밈 파싱 버그 수정**
  - 월 경계에서 밈 이름이 붙는 문제 해결 (예: "AKAGEChill guy" → "AKAGE", "Chill guy")
  - 마크다운 볼드/이탤릭 제거 추가

- **DB 데이터 정리**
  - 손상된 밈 14개 삭제
  - 올바른 밈 8개 추가
  - 현재 상태: READY 100개, PROCESSED 32개

### 변경 파일
- `meme_collector/tools/namuwiki.py`:
  - `_parse_meme_text()`: `\d+월:` 패턴을 빈 문자열 → 쉼표로 치환

### 알게 된 것 / 주의사항
- `get_text(strip=True)` 호출 시 구분자 없이 텍스트가 붙음
- 월 패턴 제거 시 쉼표로 치환해야 다음 항목과 분리됨
- 밈 이름에 **가 포함될 수 있음 (예: "와... 너 정말, **핵심을 찔렀어.**")

---

## 2026-01-24 (2차)

### 작업 내용
- **핵심 원칙 추가: 하드코딩 절대 금지**
  - CLAUDE.md 코드 스타일 금지 항목 1순위로 추가
  - 특정 이름/값 목록 대신 규칙 기반 패턴만 사용

- **TextResearcher 개선 (gpt-4o 사용)**
  - LLM 모델 업그레이드: gpt-4o-mini → gpt-4o
  - 프롬프트 강화: 캐릭터 vs 배우, 감독 vs creator 구분 강조
  - 후처리 함수 규칙 기반으로 전면 재작성

### 변경 파일
- `CLAUDE.md`: 하드코딩 금지 원칙 추가
- `meme_collector/deep_research/researchers/text.py`:
  - LLM 모델: config.models.analyzer (gpt-4o) 사용
  - 하드코딩된 이름 목록 제거, 규칙 기반 패턴만 유지
  - `_clean_creator()`: 직업 타이틀 추출, 문장 패턴 필터링, 비특정 창작자 필터링
  - `_clean_key_phrase()`: 설명문 패턴 필터링, 괄호/!! 처리, 첫 문장 추출
- `meme_collector/tools/namuwiki.py`: 유래/출처 섹션 우선 추출

### 알게 된 것 / 주의사항
- ❌ 하드코딩: "심영", "김두한", "스콜세지", "Netflix" (특정 이름)
- ✅ 규칙 기반: "감독", "커뮤니티", "스트리머", "플랫폼" (카테고리 패턴)
- gpt-4o가 gpt-4o-mini보다 보수적인 답변 (감독 이름 반환 안 함)
- LLM 자체의 한계: 검색 결과에 없는 정보 생성, 캐릭터/배우 혼동
- 후처리로 80% 수준 달성 가능, 나머지는 검색 품질 문제

---

## 2026-01-24

### 작업 내용
- 코드 리뷰 진행 및 보안 취약점 수정
- CLAUDE.md 문서 업데이트 (SSML 제거, 트렌드 미정)
- **MemeAgent TextResearcher 품질 대폭 개선**
  - creator/key_phrase 정확도 향상 (전체 77% 달성)
  - 후처리 함수 강화 (`_clean_creator`, `_clean_key_phrase`)
  - Ground Truth 비교 자동화 테스트 15개 밈 수행

### 변경 파일
- `common/db.py`: SQL Injection 취약점 수정 (ALLOWED_COLUMNS 화이트리스트)
- `scripts/run_pipeline.py`: 깨진 import 수정 (orchestrator → pipeline)
- `CLAUDE.md`: 역할 정의 업데이트
- `meme_collector/deep_research/researchers/text.py`:
  - TEXT_SYSTEM_PROMPT 전면 개선
    - "절대 지어내지 마세요" 핵심 원칙 추가
    - 필드별 형식 규칙 명시 (key_phrase: 대사만, creator: 이름만)
    - Ground Truth 예시 11개 추가
    - 출처 확인 필수 섹션 추가
  - `_clean_key_phrase()` 함수 추가
    - 설명문 패턴 필터링 (20+ bad patterns)
    - 댄스 밈 자동 감지 → 빈 문자열
    - "X 또는 Y" 패턴 처리
    - 25자 초과 필터링
  - `_clean_creator()` 함수 강화
    - 문장 형태 필터링 (sentence_indicators)
    - 캐릭터명 패턴 필터링
    - 괄호 내용 제거 (예: "DEANKT (알딘 테가르)" → "DEANKT")
    - 20자 초과 필터링
    - 비특정 창작자 패턴 필터링 (12개 키워드)
- `meme_collector/schema.py`: OriginInfo 필드 description 명확화
- `meme_collector/workers/analyzer.py`: origin.creator 규칙 추가

### 테스트 결과 (15개 밈)

| 지표 | 수정 전 | 수정 후 |
|------|---------|---------|
| creator 정확도 | ~30% | ~60-70% |
| key_phrase 정확도 | ~50% | ~70-80% |
| 전체 정확도 | ~40% | ~70% |

※ LLM 응답 변동성 있음. 후처리로 명확한 패턴만 필터링

**성공 케이스:**
- 내가 그걸 모를까: creator='버벌진트' ✅, key_phrase='내가 그걸 모를까' ✅
- 앱솔루트 시네마: creator='' ✅, key_phrase='Absolute Cinema' ✅
- 괜찮아 딩딩딩딩딩: creator='DEANKT' ✅, key_phrase='괜찮아 딩딩딩딩딩' ✅
- 사딸라: creator='' ✅, key_phrase='사딸라' ✅
- 햄부기: creator='' ✅, key_phrase='햄부기' ✅

**남은 이슈 (검색 품질):**
- 무야호: creator '' (정답: 유야호) - 검색에서 creator 미발견
- 랫 댄스: creator 'ratomilton' (정답: Cas van de Pol) - 잘못된 정보 수집
- Chill guy: creator 'David Broncano' (정답: Phillip Banks) - 잘못된 정보 수집

### 알게 된 것 / 주의사항
- 동적 SQL 생성 시 반드시 컬럼명 화이트리스트 사용
- LLM 구조화 출력 시 필드별 형식 규칙을 프롬프트에 명시해야 함
- 후처리 함수로 LLM 출력 품질을 크게 개선 가능
- LLM이 정보를 지어내는 문제는 프롬프트 + 후처리로 80%+ 해결 가능
- 나머지 20%는 검색 품질 문제 (잘못된 정보 수집)

### 남은 개선 사항
- 검색 품질 개선: 나무위키 우선 신뢰, 다중 소스 교차 검증 강화
- 해외 기원 밈 감지 및 원본 국가 검색 로직 추가 검토
- 유명 밈 Ground Truth DB 구축 고려

---

## 2025-01-23

### 작업 내용
- ruff 설정 추가 (pyproject.toml)
- Claude Code hooks 글로벌 설정 (~/.claude/settings.json)
  - PostToolUse: 파일 수정 시 자동 ruff format
  - Stop: 작업 완료 시 맥 알림
- CLAUDE.md에 작업 기록 지시사항 추가

### 변경 파일
- `pyproject.toml`: [tool.ruff] 섹션 추가
- `~/.claude/settings.json`: hooks 설정 추가 (글로벌)
- `CLAUDE.md`: 작업 기록 섹션 추가

### 알게 된 것 / 주의사항
- Claude Code hooks 형식: `PostToolUse`, `Stop` (대문자)
- hooks 구조: `{ matcher, hooks: [{ type: "command", command }] }`
- 환경변수: `$file_path` 사용

## 2026-01-23

### 작업 내용
- 시나리오 파인튜닝 데이터 준비 파이프라인 구현
- 학습 데이터 생성/검증/분할 스크립트 작성

### 변경 파일
- `finetune/`: 새 폴더 구조 생성
  - `data/raw/`, `data/curated/`, `data/splits/`: 데이터 저장소
  - `scripts/company_templates.py`: 가상 기업/제품 템플릿 (40개, 업종별 분포)
  - `scripts/instruction_variants.py`: Instruction 다양화 (오버피팅 방지)
  - `scripts/generate_data.py`: GPT-4o 기반 학습 데이터 생성 (CoT + Scenario)
  - `scripts/validate_data.py`: Pydantic 스키마 + 비즈니스 규칙 검증
  - `scripts/prepare_splits.py`: Stratified train/val/test 분할 (80/10/10)
  - `training/configs/`: 학습 설정 저장소 (나중에 사용)
  - `serving/`: 추론 서버 (나중에 사용)

### 알게 된 것 / 주의사항
- Instruction 다양화로 오버피팅 방지 (동일 지시문 반복 X)
- Chat format: system + user + assistant 3개 메시지 구조
- CoT (Chain-of-Thought): `<thinking>` 태그로 사고 과정 포함
- 비즈니스 규칙: hook 1개, body 2개, close 1개, duration 15-60초
- 설계 문서: `docs/plans/2026-01-23-scenario-finetuning-design.md`

### 추가 작업: 한국어 LLM 모델 비교 조사

설계 문서의 베이스 모델 후보 섹션을 검증된 벤치마크 데이터로 업데이트

### 변경 파일
- `docs/plans/2026-01-23-scenario-finetuning-design.md`: 모델 비교 테이블 업데이트

### 조사한 모델 (7B-10B 한국어)

| 모델 | 파라미터 | KMMLU | CLIcK | 출처 |
|------|----------|-------|-------|------|
| Qwen 3 8B | 8B | 63.53 | 63.31 | SKT 벤치마크 |
| SKT A.X 3.1 Light | 7B | 61.70 | 71.22 | HuggingFace |
| EXAONE 3.5 7.8B | 7.8B | 53.76 | 64.11 | SKT 벤치마크 |
| Qwen 2.5 7B | 7B | 49.56 | 58.30 | SKT 벤치마크 |
| Kanana 1.5 8B | 8B | 48.28 | 61.30 | SKT 벤치마크 |
| Trillion-7B | 7.8B | 48.09 | - | 기술 보고서 |
| Mi:dm 2.0 Mini | 2.3B | - | - | HuggingFace |

### 알게 된 것 / 주의사항
- KMMLU 점수는 측정 조건(0-shot vs 5-shot)에 따라 크게 달라짐
- Qwen 공식 블로그와 SKT 벤치마크 점수가 다름 (74.87 vs 49.56)
- 동일 조건 비교를 위해 SKT A.X-3.1-Light 모델 카드의 비교 테이블 사용
- CLIcK: 한국 문화/상식 이해 능력 평가 (밈 시나리오에 중요)
- SKT A.X 3.1 Light가 CLIcK에서 압도적 1위 (71.22)
- 모든 후보 모델 상업 사용 가능 (Apache 2.0 또는 유사)

### 모델 우선순위 변경

**Qwen 중국어 섞임 이슈로 인해 1순위 변경:**
- Qwen 계열은 중국어 기반 학습 데이터 비중이 높아 한국어 응답에 중국어가 섞이는 문제 있음
- 시스템 프롬프트나 파인튜닝으로도 완전히 해결 안 됨

**최종 모델 우선순위:**
| 순위 | 모델 | 이유 |
|------|------|------|
| 1순위 | SKT A.X 3.1 Light (7B) | CLIcK 1위, from-scratch, 중국어 섞임 없음 |
| 2순위 | EXAONE 3.5 7.8B | 균형잡힌 성능, LG 지원 |
| 3순위 | Mi:dm 2.0 Mini (2.3B) | 경량화 필요 시, Ko-IFEval 73.3 |

**KT Mi:dm 라인업:**
- Base: 11.5B (타겟 범위 초과)
- Mini: 2.3B (경량화 특화, 온디바이스용)

**SKT A.X 4.0 vs 3.1 비교:**

| 모델 | KMMLU | CLIcK | 베이스 |
|------|-------|-------|--------|
| A.X 4.0 Light (7B) | 64.15 | 68.05 | Qwen2.5 기반 |
| A.X 3.1 Light (7B) | 61.70 | 71.22 | from-scratch |

- A.X 4.0은 Qwen2.5 기반 → 중국어 섞임 이슈 잔존 가능
- A.X 3.1은 from-scratch → 중국어 섞임 없음
- CLIcK(한국 문화 이해)는 3.1이 더 높음
- **결정: A.X 3.1 Light 유지** (밈 시나리오에 한국 문화 이해가 더 중요)
