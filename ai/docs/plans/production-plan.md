# 프로젝트 완성 계획 (프로덕션 수준)

## 현재 상태 요약

| 레포 | 완성도 | 핵심 이슈 |
|------|--------|-----------|
| AI | ~80% | 시나리오 에이전트 미연결 (AI-finetune에 구현 있음) |
| Backend | ~75% | Celery 미구현, 수정/재생성 stub, 오늘 수정사항 미배포 |
| Frontend | ~85% | 오늘 수정사항 미배포, 영상 재생 placeholder |

---

## Phase 1: 오늘 수정사항 배포 (Backend + Frontend)

### 1-1. Backend 이슈 & 브랜치

**파일:**
- `app/api/v1/endpoints/video.py` — character_image_url/voice_sample_url 반환, presigned URL, voice_sample_url DB 저장
- `app/services/s3_service.py` — `_parse_s3_url()`, `get_presigned_url()` 추가

### 1-2. Frontend 이슈 & 브랜치

**파일:**
- `next.config.mjs` — S3 amazonaws.com 와일드카드 추가
- `src/lib/api/video.ts` — `getProjectById`에서 characterImageUrl/voiceSampleUrl 매핑
- `src/app/(dashboard)/user/video/[id]/page.tsx` — 이미지 object-contain, 음성 재생 로직 추가

---

## Phase 2: AI — 시나리오 에이전트 연결

### 2-1. AI-finetune에서 시나리오 코드 가져오기

**소스:** `/AI-finetune/content_pipeline/scenario/`
**타겟:** `/AI/content_pipeline/scenario/`

복사 대상:
- `scenario_agent.py` — `run_scenario_agent()`, `regenerate_from_feedback()`
- `scenario_schemas.py` — Pydantic 스키마
- `scenario_database.py` — DB 연동
- `scenario_graph.py` — LangGraph 워크플로우
- `scenario_nodes.py` — 노드 함수들
- `scenario_state.py` — State 정의

### 2-2. pipeline.py 연결 확인

`run_scenario_step()`, `run_scenario_regenerate_step()`이 `scenario_agent.py`의 함수를 호출하므로, import 경로와 인터페이스 일치 여부 확인.

현재 pipeline.py가 기대하는 인터페이스:
```python
run_scenario_agent(ad_id, meme_id, generate_template, review_template, regenerate_template, meme_example_template, used_templates)
regenerate_from_feedback(ad_id, regenerate_template, meme_example_template)
```

AI-finetune의 시그니처와 맞추거나 adapter 작성.

### 2-3. 검증

- `run_scenario_step(ad_id=1, meme_id=1)` 호출 → scenes 반환 확인
- `run_content_generation_step()` E2E 테스트

---

## Phase 3: Backend — 프로덕션 필수 기능

### 3-1. Celery 비동기 태스크 구현

AI 작업이 10~30초+ 소요 → HTTP 타임아웃 문제. 프로덕션 필수.

**신규 파일:**
- `app/tasks.py` — Celery 태스크 정의
- `app/core/celery_app.py` — Celery 앱 설정

**수정 파일:**
- `app/api/v1/endpoints/content_pipeline.py` — 동기 호출 → `.delay()` 비동기 호출로 전환
- `app/api/v1/endpoints/video.py` — 동일

**태스크:**
- `generate_character_task(ad_id, character_style)`
- `generate_voice_task(ad_id, character_id, voice_description)`
- `generate_scenario_task(ad_id, meme_id)`
- `generate_video_task(ad_id, script_id, voice_id, character_image_url)`

### 3-2. 수정/재생성 Direct Client 구현

**파일:** `app/services/ai_pipeline_direct.py`

현재 stub인 함수:
- `revise_scenario()` → `run_scenario_regenerate_step()` 연결
- `revise_video()` → `run_video_step()` 재호출
- `regenerate_video()` → 위와 동일

### 3-3. 피드백 저장 로직

**수정 파일:** `app/crud/video.py`, `app/crud/final.py`

현재 TODO로 남아있는 부분:
- 캐릭터/음성 수정 요청 시 피드백 저장
- 영상 승인/거부 시 피드백 저장
- `review_result` JSONB 컬럼 활용

---

## Phase 4: Frontend — 프로덕션 마무리

### 4-1. 실시간 진행 상태 폴링

현재 페이지 새로고침해야 상태 변경 반영됨.

**수정 파일:** `src/app/(dashboard)/user/video/[id]/page.tsx`

- 생성 중 상태(`*_generating`)일 때 5초 간격 폴링
- `statusApi.getWorkflowStatus()` 주기적 호출
- 상태 변경 시 자동 UI 업데이트

### 4-2. 영상 재생 연결

현재 placeholder 이미지 사용. 실제 영상 URL 연결 필요.

**수정 파일:** `src/app/(dashboard)/user/video/[id]/page.tsx`

- `video.videoUrl`을 `<video>` 태그 src로 연결
- S3 presigned URL 사용 (백엔드에서 변환)

### 4-3. 에러 상태 처리

생성 실패 시 사용자에게 명확한 안내 + 재시도 버튼.

**수정 파일:** `src/app/(dashboard)/user/video/[id]/page.tsx`

- `failed` 상태 시 에러 메시지 표시
- "다시 시도" 버튼 추가

---

## Phase 5: AI — 자동 품질 검증 (Quality Gate)

사용자 검수 전에 파이프라인 내부에서 1차 품질 검증 수행. 밈 수집기의 Verifier 패턴 (100점 채점 + 재생성) 참고.

### 5-1. 시나리오 품질 검증

**신규 파일:** `content_pipeline/quality/scenario_verifier.py`

검증 항목:
- 씬 수 (4개 = hook + body×2 + close)
- 각 씬에 dialogue, visual_description 존재
- total_duration 범위 (15~60초)
- 대사 길이 적정 (빈 문자열, 500자 초과 방지)
- LLM 기반 품질 점수 (선택적: 재미, 밈 활용도, 자연스러움)

동작:
- 점수 70점 미만 → 자동 재생성 (최대 2회)
- 70점 이상 → 사용자 검수로 전달

### 5-2. 이미지 품질 검증

**신규 파일:** `content_pipeline/quality/image_verifier.py`

검증 항목:
- 이미지 해상도 (최소 512×512)
- 파일 크기 (0 byte 아님)
- 이미지 로드 가능 여부 (corrupted file 감지)
- (선택적) Gemini Vision으로 캐릭터 프롬프트 일치도 확인

### 5-3. 음성 품질 검증

**신규 파일:** `content_pipeline/quality/voice_verifier.py`

검증 항목:
- 오디오 파일 크기 (0 byte 아님)
- duration 존재 (ElevenLabs 응답에서 확인)
- voice_id 유효성

### 5-4. 영상 품질 검증

**신규 파일:** `content_pipeline/quality/video_verifier.py`

검증 항목:
- 영상 파일 크기 (0 byte 아님)
- duration > 0
- (선택적) FFprobe로 코덱/해상도 확인

### 5-5. pipeline.py 통합

각 step 함수 내부에서 생성 후 verifier 호출:
```python
# 예시: run_scenario_step 내부
result = run_scenario_agent(...)
score = verify_scenario(result)
if score < 70 and attempt < max_retries:
    result = run_scenario_agent(...)  # 재생성
```

**공통 인터페이스:**
```python
def verify_*(result) -> {"score": int, "passed": bool, "issues": list[str]}
```

---

## Phase 6: 통합 테스트 & 배포

### 6-1. E2E 플로우 검증

1. 영상 생성 요청 (제품 정보 + 캐릭터 스타일)
2. 캐릭터 이미지 + 음성 샘플 생성
3. 검수 화면에서 이미지 확인 + 음성 재생
4. 에셋 승인
5. 시나리오 생성
6. 시나리오 검수 + 승인
7. 영상 생성
8. 최종 영상 확인 + 승인
9. 영상 다운로드

### 6-2. 배포

- AI: develop → main merge
- Backend: develop → main merge
- Frontend: develop → main merge

---

## 우선순위

| 순서 | 작업 | 이유 |
|------|------|------|
| 1 | Phase 1: 오늘 수정사항 배포 | 이미 완료된 코드, 바로 배포 가능 |
| 2 | Phase 2: 시나리오 연결 | E2E 플로우의 핵심 누락 부분 |
| 3 | Phase 3-2: 수정/재생성 연결 | 검수 워크플로우 완성 |
| 4 | Phase 4-1: 폴링 | UX 필수 |
| 5 | Phase 5: 자동 품질 검증 | 사용자 검수 전 불량 필터링, 재생성 비용 절감 |
| 6 | Phase 3-1: Celery | 프로덕션 안정성 |
| 7 | Phase 4-2,3: 영상 재생, 에러 처리 | 마무리 |
| 8 | Phase 3-3: 피드백 저장 | 데이터 보존 |
| 9 | Phase 6: 통합 테스트 & 배포 | 최종 검증 |
