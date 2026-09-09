# 서비스 전체 코드 리뷰 — 수정 계획서

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 3개 프로젝트(Backend, Frontend, AI Pipeline) 전체 서비스 흐름 리뷰 후 발견된 버그 수정

**Architecture:** Backend(FastAPI) ↔ AI Pipeline(Python) ↔ Frontend(Next.js) 간 상태 전이, 데이터 흐름, 에러 처리 일관성 확보

**Tech Stack:** Python/FastAPI, TypeScript/Next.js, PostgreSQL, S3, ComfyUI

---

## 이전 세션 수정 완료 항목 (참고용)

| ID | 내용 | 상태 |
|----|------|------|
| P1 | `_bg_generate_character` image_url 빈값 처리 | ✅ |
| P2 | `_bg_generate_character` stage명 `character_review`로 통일 | ✅ |
| P3 | `_bg_generate_character` db.rollback() 추가 | ✅ |
| P4 | `transformWorkflowToVideo` video stage 매핑 `video_review` | ✅ |
| P5 | `run_scene_image_step` character_id 전달 (direct client) | ✅ |
| P6 | S3 storage presigned URL → s3:// URI 반환 | ✅ |
| P7 | `approve_ad_scenario` status `completed`로 변경 | ✅ |

---

## 발견된 이슈 목록 (심각도순)

### HIGH — 서비스 흐름 차단/데이터 정합성

| # | 파일 | 라인 | 이슈 | 영향 |
|---|------|------|------|------|
| H1 | AI `pipeline.py` | 948 | `run_content_generation_step` → `run_scene_image_step` 호출 시 `character_id` 미전달 | image_generations FK 위반 |
| H2 | AI `pipeline.py` | 963-968 | `run_content_generation_step` → `run_video_step` 호출 시 `ad_id`, `script_id`, `company_id` 미전달 | 영상 DB insert 시 ad_id=None |
| H3 | Backend `content_pipeline.py` | 107 | `_bg_generate_character` 실패 시 `original_status`로 복원 → 실패 원인 손실 | 사용자에게 실패 상태 미표시 |
| H4 | Backend `content_pipeline.py` | 186 | `_bg_generate_scenario` 실패 시 `original_status`로 복원 → 동일 문제 | 시나리오+영상 생성 실패 상태 미표시 |
| H5 | Frontend `video.ts` | 393 | `approveScenario` URL이 `/api/v1/video/{id}/scenario/approve`인데 backend는 `ItemApprovalRequest` body 기대 | `{ approved: true }` 전송하므로 동작하나, 거부 시 사용 불가 (항상 true) |
| H6 | Backend `content_pipeline.py` | 505-511 | `get_ad_scenario`에서 scene의 `content` 키 사용하지만, AI가 생성하는 scene에는 `dialogue` 키 사용 | 시나리오 조회 시 빈 content 반환 |

### MEDIUM — 데이터 불일치/UX 문제

| # | 파일 | 라인 | 이슈 | 영향 |
|---|------|------|------|------|
| M1 | Backend `content_pipeline.py` | 652 | 음성 거부 시 `elevenlabs_voice_id = None` (삭제) | voice_id 복원 불가, 재생성 필요 |
| M2 | Backend `content_pipeline.py` | 737 | `assets/approve` → `processing` + `scenario_generation` 설정만, 자동 트리거 없음 | 프론트가 별도로 `/scenario/generate` 호출 필요 |
| M3 | Backend `content_pipeline.py` | 139 | `_bg_generate_scenario`에서 시나리오 생성 후 바로 영상 생성 연결 → 시나리오 검수 없이 진행 | 현재 플로우에서는 정상 (시나리오+영상 통합 생성) |
| M4 | AI `pipeline.py` | 189 | `scene_key` 형식 `scene_1` vs image/voice 모듈의 `scene_01` | DB ON CONFLICT 불일치 가능 |
| M5 | AI `pipeline.py` | 728-747 | scene_videos에 `voice_gen_id`, `image_id` 항상 NULL | DB 관계 추적 불가 |
| M6 | Frontend `page.tsx` | 321-332 | `handleApproveScenario`가 시나리오만 승인 → `completed`로 전이하지만 영상 승인 별도 미처리 | 현재 플로우에서 시나리오 승인 = 콘텐츠 승인 |
| M7 | Backend `content_pipeline.py` | 320 | 음성 생성 후 workflow progress를 `character_generation` stage로 업데이트 | 프론트 status 매핑 혼동 |

### LOW — 개선 사항

| # | 파일 | 라인 | 이슈 |
|---|------|------|------|
| L1 | Frontend `page.tsx` | — | 비디오 플레이어 컴포넌트 없음 (다운로드만 가능) |
| L2 | Frontend `page.tsx` | — | 음성 미리듣기 오디오 플레이어 없음 |
| L3 | AI `pipeline.py` | 171-198 | 시나리오 변환 함수가 4씬 하드코딩 |
| L4 | Backend 전체 | — | 상태 전이 감사 로그 없음 |

---

## 수정 계획

### Task 1: AI Pipeline — `run_content_generation_step` 파라미터 전달 수정 (H1, H2)

**Files:**
- Modify: `AI/content_pipeline/pipeline.py:948-968`

**Step 1: `run_scene_image_step` 호출에 `character_id` 추가**

```python
# pipeline.py L948 부근
img_result = run_scene_image_step(
    scenario_prompt=scenario_prompt,
    character_image_url=character_image_url,
    product_image_url=product_image_url,
    script_id=scenario_result.get("script_id"),
    scene_key=scene["scene_key"],
    character_id=character_id,  # 추가
)
```

함수 시그니처에 `character_id` 파라미터 추가 필요:
```python
def run_content_generation_step(
    ad_id: int,
    meme_id: int,
    voice_id: str,
    character_image_url: str = None,
    character_image_path: str = None,
    product_image_url: str = None,
    character_id: int = None,  # 추가
) -> dict:
```

**Step 2: `run_video_step` 호출에 `ad_id`, `script_id`, `company_id` 추가**

```python
# pipeline.py L963 부근
video_result = run_video_step(
    scenes=scenes,
    scene_assets=scene_assets,
    character_image_url=character_image_url,
    character_image_path=character_image_path,
    script_id=scenario_result.get("script_id"),  # 추가
    ad_id=ad_id,                                   # 추가
)
```

**Step 3: 구문 검사**

Run: `cd /Users/kimjm/Desktop/meme-fluencer/AI && python -c "import ast; ast.parse(open('content_pipeline/pipeline.py').read()); print('OK')"`

---

### Task 2: AI Pipeline — `run_content_regenerate_step` 동일 수정

**Files:**
- Modify: `AI/content_pipeline/pipeline.py` (run_content_regenerate_step 함수)

`run_content_regenerate_step`도 동일하게 `character_id`를 `run_scene_image_step`에, `ad_id`/`script_id`를 `run_video_step`에 전달하도록 수정.

**Step 1: 함수 코드 확인 후 동일 패턴 적용**

**Step 2: 구문 검사**

Run: `cd /Users/kimjm/Desktop/meme-fluencer/AI && python -c "import ast; ast.parse(open('content_pipeline/pipeline.py').read()); print('OK')"`

---

### Task 3: Backend — 백그라운드 태스크 실패 시 `failed` 상태로 설정 (H3, H4)

**Files:**
- Modify: `backend/app/api/v1/endpoints/content_pipeline.py:103-112, 182-191`

**현재 문제:** 실패 시 `original_status`(예: `draft`)로 복원 → 사용자는 아무 일도 안 일어난 것으로 인식

**수정:**

```python
# _bg_generate_character except 블록 (L103-112)
except Exception as e:
    logger.error(f"백그라운드 캐릭터 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
    db.rollback()
    try:
        video_crud.update_ad_status(db, ad_id, 'failed')
    except Exception as inner:
        logger.error(f"상태 업데이트도 실패 (ad_id={ad_id}): {inner}", exc_info=True)
        db.rollback()
```

```python
# _bg_generate_scenario except 블록 (L182-191)
except Exception as e:
    logger.error(f"백그라운드 시나리오+영상 생성 실패 (ad_id={ad_id}): {e}", exc_info=True)
    db.rollback()
    try:
        video_crud.update_ad_status(db, ad_id, 'failed')
    except Exception as inner:
        logger.error(f"상태 업데이트도 실패 (ad_id={ad_id}): {inner}", exc_info=True)
        db.rollback()
```

**연관 수정: 프론트엔드 `failed` 상태 처리**

Frontend `video.ts:36`: `'failed': 'pending'` 매핑이 이미 있으므로 사용자에게 `pending`으로 표시됨. 이건 의도적인지 확인 필요하나, 최소한 에러 상태가 DB에 기록되어 디버깅 가능.

**Step 1: 두 except 블록 수정**

**Step 2: 구문 검사**

Run: `cd /Users/kimjm/Desktop/meme-fluencer/backend && python -c "import ast; ast.parse(open('app/api/v1/endpoints/content_pipeline.py').read()); print('OK')"`

---

### Task 4: Backend — 시나리오 scene `content` vs `dialogue` 키 불일치 수정 (H6)

**Files:**
- Modify: `backend/app/api/v1/endpoints/content_pipeline.py:505-511`
- Modify: `backend/app/api/v1/endpoints/content_pipeline.py:831-837`

**현재:** AI가 `dialogue` 키로 scene 생성 → `create_scenario`가 DB에 `dialogue`로 저장 → `get_ad_scenario`에서 `content` 키로 읽으려고 함 → 빈 문자열 반환

**수정:**

```python
# L505-511
scenes = [
    SceneResponse(
        scene_number=i + 1,
        content=scene.get('content', '') or scene.get('dialogue', ''),
        timestamp=scene.get('timestamp'),
        visual_description=scene.get('visual_description', '') or scene.get('scenario_prompt', ''),
    )
    for i, scene in enumerate(scenes_data)
]
```

동일하게 L831-837의 `revise_ad_scenario` 응답에도 적용:
```python
# L831-837
scenes = [
    SceneResponse(
        scene_number=i + 1,
        content=scene.get('content', '') or scene.get('dialogue', ''),
        timestamp=scene.get('timestamp'),
    )
    for i, scene in enumerate(new_scenes)
]
```

**연관:** `SceneResponse` 스키마에 `visual_description` 필드 추가 여부 확인

**Step 1: SceneResponse 스키마 확인**

**Step 2: scene 매핑 수정**

**Step 3: 구문 검사**

---

### Task 5: Backend — 음성 생성 후 workflow stage 불일치 수정 (M7)

**Files:**
- Modify: `backend/app/api/v1/endpoints/content_pipeline.py:320`

**현재:**
```python
video_crud.update_workflow_progress(db, ad_id, 30, 'character_generation')
```

**수정:**
```python
video_crud.update_workflow_progress(db, ad_id, 30, 'voice_generation')
```

음성 생성 완료 후이므로 `voice_generation` stage가 정확.

---

### Task 6: AI Pipeline — `scene_key` 형식 통일 (M4)

**Files:**
- Modify: `AI/content_pipeline/pipeline.py:189`

**현재:**
```python
"scene_key": f"scene_{i}",   # scene_0, scene_1, ...
```

**수정:**
```python
"scene_key": f"scene_{i+1}",  # scene_1, scene_2, ...
```

> 참고: image/voice 모듈은 `scene_01` (zero-padded) 형식을 사용하나, DB ON CONFLICT에서 `scene_key` 비교 시 불일치. 하지만 `_bg_generate_scenario`가 scene_key를 직접 설정하지 않고 AI에서 받은 데이터를 그대로 전달하므로, 이 함수에서만 `scene_key`가 생성되는 경로를 확인 후 결정.

**Step 1: `convert_to_scenes` 함수의 scene_key 형식 확인**

**Step 2: 실제 사용처와 DB의 scene_key 값 비교 후 통일**

---

### Task 7: 프론트엔드 — `failed` 상태 UI 처리

**Files:**
- Modify: `frontend/src/lib/api/video.ts:36`
- Modify: `frontend/src/lib/constants.ts` (STATUS_CONFIG에 failed 추가)

**현재:** `'failed': 'pending'` → 사용자가 실패를 인지할 수 없음

**수정 옵션 A (최소):** `failed` 상태를 별도 타입으로 추가
```typescript
// types/index.ts
type VideoStatus = ... | 'failed'

// video.ts L36
'failed': 'failed',

// constants.ts
failed: { text: '생성 실패', color: 'text-red-600', bgColor: 'bg-red-50' }
```

**수정 옵션 B (간단):** `failed` → `pending`으로 매핑 유지하되, 에러 메시지 표시

Task 3에서 backend가 `failed`로 설정하게 되므로, 최소한 프론트에서 이를 인지하는 UI가 필요.

---

### Task 8: Backend — SceneResponse 스키마에 visual_description 추가

**Files:**
- Modify: `backend/app/schemas/video.py` (SceneResponse 클래스)

**현재:**
```python
class SceneResponse(BaseModel):
    scene_number: int
    content: str
    timestamp: Optional[str] = None
```

**수정:**
```python
class SceneResponse(BaseModel):
    scene_number: int
    content: str
    timestamp: Optional[str] = None
    visual_description: Optional[str] = None
    action: Optional[str] = None
```

프론트엔드에서 씬별 피드백 시 visual_description (씬 이미지 설명)을 볼 수 있어야 정확한 피드백 가능.

---

### Task 9: 검증

**Step 1: Backend 구문 검사**
```bash
cd /Users/kimjm/Desktop/meme-fluencer/backend
python -c "import ast; ast.parse(open('app/api/v1/endpoints/content_pipeline.py').read()); print('OK')"
```

**Step 2: AI Pipeline 구문 검사**
```bash
cd /Users/kimjm/Desktop/meme-fluencer/AI
python -c "import ast; ast.parse(open('content_pipeline/pipeline.py').read()); print('OK')"
```

**Step 3: Frontend 빌드**
```bash
cd /Users/kimjm/Desktop/meme-fluencer/frontend
npm run build
```

**Step 4: 코드 리뷰 에이전트 실행**

---

## 수정 대상 파일 요약

| 파일 | Task | 수정 내용 |
|------|------|----------|
| `AI/content_pipeline/pipeline.py` | 1, 2, 6 | `character_id`/`ad_id`/`script_id` 전달, scene_key 형식 |
| `backend/app/api/v1/endpoints/content_pipeline.py` | 3, 4, 5 | 실패 상태 처리, scene content/dialogue 호환, voice stage명 |
| `backend/app/schemas/video.py` | 8 | SceneResponse에 visual_description 추가 |
| `frontend/src/lib/api/video.ts` | 7 | failed 상태 매핑 |
| `frontend/src/types/index.ts` | 7 | VideoStatus에 failed 추가 |
| `frontend/src/lib/constants.ts` | 7 | STATUS_CONFIG에 failed 추가 |

---

## 수정하지 않는 항목 (의도적 보류)

| 이슈 | 보류 이유 |
|------|----------|
| M1: 음성 거부 시 voice_id 삭제 | 현재 플로우에서 거부=재생성 필요이므로 의도적 동작 |
| M2: assets/approve 후 자동 시나리오 생성 | 프론트가 별도 호출하는 현재 플로우가 더 안전 |
| M5: scene_videos voice_gen_id/image_id NULL | 현재 플로우에서 미사용, 향후 개선 |
| L1-L4: UI/로깅 개선 | 기능 수정 아닌 개선 사항 |
