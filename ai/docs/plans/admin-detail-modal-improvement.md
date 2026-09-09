# 관리자 상세보기 모달 개선 계획

## 문제 정리

### 1. 로그가 비어있는 이유
백엔드 `GET /api/v1/admin/workflows/{execution_id}/logs` 엔드포인트가 `WorkflowStage` 레코드의 `started_at`, `completed_at`을 기반으로 로그를 생성하는데, **이 필드들이 실제로 업데이트되지 않아서** 항상 빈 배열을 반환함.

- `WorkflowStage`는 생성 시 `status='pending'`, `started_at=NULL`, `completed_at=NULL`
- `update_stage_status()` 함수가 `status.py`에 존재하지만 어디서도 호출되지 않음
- 결과: `logs` 배열은 항상 `[]`

**하지만** 같은 엔드포인트가 `stages` 데이터도 반환함 — 5개 단계의 `stage_name`, `status`, `stage_order` 정보는 있음. 이걸 활용하면 됨.

### 2. 관리자가 볼 수 있어야 하는 정보
사용자가 신청할 때 제출한 내용:
- **AdRequest**: `item_name`, `item_category`, `item_url`, `item_images`, `item_keymessage`, `character_style_raw`, `notes`, `meme_id`
- **WorkflowExecution**: `status`, `current_stage`, `progress_percentage`, `error_message`
- **WorkflowStage**: 5단계 (character_generation → scenario_generation → audio_generation → video_generation → final_processing) 각각의 상태
- **Company**: `company_name`
- **Meme**: 선택한 밈 이름

현재 모달은 `회사`, `제품명`, `상태`, `요청일`, `에러` + 빈 로그만 표시. 사용자가 제출한 상세 정보가 전혀 보이지 않음.

---

## 수정 계획

### Phase 1: 백엔드 — workflow logs 엔드포인트에 AdRequest 데이터 포함

**파일: `backend/app/api/v1/endpoints/admin.py` — `get_workflow_logs()`**

현재 반환: `execution_id`, `ad_id`, `company_id`, `status`, `stages`, `logs`

추가 반환:
```python
{
    ...기존 필드...
    'ad_request': {
        'item_name': ad_request.item_name,
        'item_category': ad_request.item_category,
        'item_url': ad_request.item_url,
        'item_images': ad_request.item_images or [],
        'item_keymessage': ad_request.item_keymessage,
        'character_style_raw': ad_request.character_style_raw,
        'notes': ad_request.notes,
        'meme_id': ad_request.meme_id,
    },
    'company_name': company.company_name,
    'meme_name': meme.meme_name if meme else None,
}
```

이를 위해 AdRequest, Company, Meme JOIN 추가.

### Phase 2: 프론트엔드 — WorkflowDetailModal 개선

**파일: `frontend/src/lib/api/admin.ts` — `getWorkflowLogs()` 반환 타입 업데이트**

**파일: `frontend/src/app/admin/page.tsx` — `WorkflowDetailModal` 재작성**

모달 구성:
1. **기본 정보 섹션** — 회사, 제품명, 상태, 요청일
2. **신청 상세 섹션** — 카테고리, 상품URL, 핵심 메시지, 캐릭터 스타일, 메모, 밈, 상품 이미지
3. **파이프라인 진행 상태 섹션** — 5단계 스테이지를 시각적 파이프라인으로 표시 (로그 대신)
   - 각 단계: 이름 + 상태 (pending/processing/completed/failed)
   - `started_at`/`completed_at`이 있으면 시간도 표시
   - 없으면 상태 배지만 표시
4. **에러 섹션** (에러 있을 때만)

---

## 변경 파일 요약

| 파일 | 변경 |
|------|------|
| `backend/app/api/v1/endpoints/admin.py` | `get_workflow_logs()`에 AdRequest, Company, Meme 데이터 추가 반환 |
| `frontend/src/lib/api/admin.ts` | `getWorkflowLogs()` 반환 타입에 `ad_request`, `company_name`, `meme_name`, `stages` 추가 |
| `frontend/src/app/admin/page.tsx` | `WorkflowDetailModal`을 신청 상세 + 파이프라인 진행 상태 표시로 재작성 |
