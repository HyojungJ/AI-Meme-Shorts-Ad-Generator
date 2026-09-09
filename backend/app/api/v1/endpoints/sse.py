"""
SSE(Server-Sent Events) 엔드포인트 — 실시간 생성 상태 스트리밍
"""
import asyncio
import json

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from app.core.constants import WorkflowStatus
from app.core.security import verify_token
from app.db.session import SessionLocal

router = APIRouter()

POLL_INTERVAL = 2  # seconds
HEARTBEAT_INTERVAL = 30  # seconds

# 완료/취소된 상태는 폴링 불필요
_TERMINAL_STATUSES = (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED)


def _snapshot_active(db, company_id: int) -> dict[int, dict]:
    """활성 ad_request + workflow를 단일 JOIN 쿼리로 조회."""
    rows = db.execute(
        text("""
            SELECT
                a.ad_id,
                COALESCE(w.status, a.status) AS status,
                w.current_stage,
                COALESCE(w.progress_percentage, 0) AS progress
            FROM ad_requests a
            LEFT JOIN LATERAL (
                SELECT status, current_stage, progress_percentage
                FROM workflow_execution
                WHERE ad_id = a.ad_id
                ORDER BY created_at DESC
                LIMIT 1
            ) w ON true
            WHERE a.company_id = :company_id
              AND COALESCE(w.status, a.status)
                  NOT IN ('completed', 'failed', 'cancelled')
        """),
        {"company_id": company_id},
    ).fetchall()

    return {
        row.ad_id: {
            "ad_id": row.ad_id,
            "status": row.status,
            "current_stage": row.current_stage,
            "progress": row.progress,
        }
        for row in rows
    }


async def _event_generator(company_id: int):
    prev: dict[int, dict] = {}
    heartbeat_counter = 0

    db = SessionLocal()
    try:
        while True:
            try:
                current = _snapshot_active(db, company_id)

                for ad_id, data in current.items():
                    if prev.get(ad_id) != data:
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                # 이전에 있었는데 현재 없으면 완료/취소된 것 → 마지막 상태 전송
                for ad_id in set(prev) - set(current):
                    yield f"data: {json.dumps({'ad_id': ad_id, 'status': 'completed', 'current_stage': None, 'progress': 100}, ensure_ascii=False)}\n\n"

                prev = current

            except Exception as e:
                error_data = {"error": True, "message": f"상태 조회 실패: {str(e)}"}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                # 세션 오류 시 재생성
                try:
                    db.close()
                except Exception:
                    pass
                db = SessionLocal()

            heartbeat_counter += POLL_INTERVAL
            if heartbeat_counter >= HEARTBEAT_INTERVAL:
                yield ": heartbeat\n\n"
                heartbeat_counter = 0

            await asyncio.sleep(POLL_INTERVAL)
    finally:
        db.close()


@router.get("/generation-status")
async def generation_status_stream(token: str = Query(...)):
    """SSE 스트림 — 생성 상태 실시간 푸시.

    EventSource API는 커스텀 헤더를 지원하지 않으므로 query param으로 JWT를 전달합니다.
    """
    try:
        payload = verify_token(token, "access")
    except HTTPException:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    company_id = payload.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="회사 정보가 없습니다")

    return StreamingResponse(
        _event_generator(company_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/generation-poll")
async def generation_poll(token: str = Query(...)):
    """폴링 방식 — 생성 상태 조회 (SSE 대신 사용 가능)"""
    try:
        payload = verify_token(token, "access")
    except HTTPException:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    company_id = payload.get("company_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="회사 정보가 없습니다")

    db = SessionLocal()
    try:
        current = _snapshot_active(db, company_id)
        # 배열로 직접 반환 (프론트엔드 호환성)
        return list(current.values())
    finally:
        db.close()
