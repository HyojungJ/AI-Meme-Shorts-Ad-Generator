"""워크플로우 관리 엔드포인트"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session

from .common import (
    admin_crud,
    get_db,
    Company,
    Video,
    AdRequest,
    Meme,
    ScenarioScript,
    get_presigned_url,
    check_admin_permission,
    WorkflowListResponse,
    WorkflowActionResponse,
)

router = APIRouter()


@router.get("/workflows", response_model=WorkflowListResponse)
async def get_workflows(
    request: Request,
    status_filter: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """워크플로우 목록 조회"""
    await check_admin_permission(request)

    workflows, total_count = admin_crud.get_workflows_by_filter(
        db, status_filter=status_filter or 'all', offset=offset, limit=limit
    )

    ad_ids = {wf.ad_id for wf in workflows if wf.ad_id}
    company_ids = {wf.company_id for wf in workflows if wf.company_id}
    ad_requests = {ar.ad_id: ar for ar in db.query(AdRequest).filter(AdRequest.ad_id.in_(ad_ids)).all()} if ad_ids else {}
    companies = {c.company_id: c for c in db.query(Company).filter(Company.company_id.in_(company_ids)).all()} if company_ids else {}

    workflow_list = []
    for wf in workflows:
        ad_request = ad_requests.get(wf.ad_id)
        company = companies.get(wf.company_id)

        workflow_list.append({
            'execution_id': str(wf.execution_id),
            'ad_id': wf.ad_id,
            'company_id': wf.company_id,
            'title': ad_request.item_name if ad_request else None,
            'company_name': company.company_name if company else None,
            'status': wf.status,
            'current_stage': wf.current_stage,
            'progress_percentage': wf.progress_percentage,
            'retry_count': wf.retry_count,
            'created_at': wf.created_at.isoformat(),
            'completed_at': wf.completed_at.isoformat() if wf.completed_at else None,
            'error_message': wf.error_message
        })

    return WorkflowListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        workflows=workflow_list
    )


@router.get("/workflows/{execution_id}/logs")
async def get_workflow_logs(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 상세 로그"""
    await check_admin_permission(request)

    # execution_id를 UUID로 변환
    try:
        import uuid
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 execution_id 형식입니다")

    # 워크플로우 조회
    from app.models.workflow import WorkflowExecution, WorkflowStage

    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == exec_uuid
    ).first()

    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    # 워크플로우 단계 조회
    stages = db.query(WorkflowStage).filter(
        WorkflowStage.execution_id == exec_uuid
    ).order_by(WorkflowStage.stage_order).all()

    stage_list = []
    for stage in stages:
        stage_list.append({
            'stage_name': stage.stage_name,
            'stage_order': stage.stage_order,
            'status': stage.status,
            'started_at': stage.started_at.isoformat() if stage.started_at else None,
            'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
            'duration_seconds': stage.duration_seconds,
            'error_message': stage.error_message
        })

    # stages를 logs 형식으로 변환
    logs = []
    for stage in stages:
        # 시작 로그
        if stage.started_at:
            logs.append({
                'timestamp': stage.started_at.isoformat(),
                'level': 'info',
                'message': f"[{stage.stage_name}] 단계 시작"
            })
        # 완료 로그
        if stage.completed_at:
            logs.append({
                'timestamp': stage.completed_at.isoformat(),
                'level': 'info',
                'message': f"[{stage.stage_name}] 단계 완료"
            })
        # 에러 로그
        if stage.error_message:
            logs.append({
                'timestamp': (stage.completed_at or stage.started_at or workflow.created_at).isoformat(),
                'level': 'error',
                'message': f"[{stage.stage_name}] {stage.error_message}"
            })

    # logs를 timestamp 기준으로 정렬
    logs.sort(key=lambda x: x['timestamp'])

    return {
        'execution_id': str(workflow.execution_id),
        'ad_id': workflow.ad_id,
        'company_id': workflow.company_id,
        'status': workflow.status,
        'current_stage': workflow.current_stage,
        'progress_percentage': workflow.progress_percentage,
        'retry_count': workflow.retry_count,
        'total_cost_usd': float(workflow.total_cost_usd) if workflow.total_cost_usd else 0,
        'created_at': workflow.created_at.isoformat(),
        'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
        'error_message': workflow.error_message,
        'stages': stage_list,
        'logs': logs
    }


@router.get("/workflows/{execution_id}/detail")
async def get_workflow_detail(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 신청 내용 + 수정 이력"""
    await check_admin_permission(request)

    import uuid
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 execution_id 형식입니다")

    from app.models.workflow import WorkflowExecution

    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.execution_id == exec_uuid
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    # 신청 내용: AdRequest + Meme
    ad = db.query(AdRequest).filter(AdRequest.ad_id == workflow.ad_id).first()
    meme_name = None
    if ad and ad.meme_id:
        meme = db.query(Meme).filter(Meme.meme_id == ad.meme_id).first()
        if meme:
            meme_name = meme.meme_name

    ad_request_data = None
    if ad:
        ad_request_data = {
            "ad_id": ad.ad_id,
            "item_name": ad.item_name,
            "item_category": ad.item_category,
            "item_url": ad.item_url,
            "item_images": [get_presigned_url(img) for img in (ad.item_images or [])],
            "item_description": ad.item_description,  # item_keymessage -> item_description
            "character_image_prompt": ad.character_image_prompt,
            "character_voice_prompt": ad.character_voice_prompt,
            "meme_name": meme_name,
            "status": ad.status,
            "created_at": ad.created_at.isoformat() if ad.created_at else None,
        }

    # 수정 이력: ScenarioScript + Video
    scenarios = db.query(ScenarioScript).filter(
        ScenarioScript.ad_id == workflow.ad_id
    ).order_by(ScenarioScript.created_at).all()

    scenario_list = []
    for s in scenarios:
        scenario_list.append({
            "script_id": s.script_id,
            "title": s.title,
            "generation_type": s.generation_type,
            "approval_status": s.approval_status,
            "quality_check_passed": s.quality_check_passed,
            "quality_issues": s.quality_issues or [],
            "review_result": s.review_result,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    videos = db.query(Video).filter(
        Video.ad_id == workflow.ad_id
    ).order_by(Video.created_at).all()

    video_list = []
    for v in videos:
        video_list.append({
            "video_id": v.video_id,
            "title": v.title,
            "status": v.status,
            "rejection_reason": v.rejection_reason,
            "rejected_at": v.rejected_at.isoformat() if v.rejected_at else None,
            "review_result": v.review_result,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    return {
        "ad_request": ad_request_data,
        "revision_history": {
            "scenarios": scenario_list,
            "videos": video_list,
        },
    }


@router.post("/workflows/{execution_id}/retry", response_model=WorkflowActionResponse)
async def retry_workflow(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 재시도"""
    await check_admin_permission(request)

    workflow = admin_crud.retry_workflow(db, execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    return WorkflowActionResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message='워크플로우 재시도가 시작되었습니다'
    )


@router.post("/workflows/{execution_id}/cancel", response_model=WorkflowActionResponse)
async def cancel_workflow(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 취소"""
    await check_admin_permission(request)

    workflow = admin_crud.cancel_workflow(db, execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    return WorkflowActionResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message='워크플로우가 취소되었습니다'
    )
