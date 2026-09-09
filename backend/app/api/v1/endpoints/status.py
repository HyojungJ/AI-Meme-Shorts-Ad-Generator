"""
영상 상태 추적 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.video import WorkflowStatusResponse, ProjectListResponse
from app.crud import status as status_crud
from app.crud import video as video_crud
from app.core.security import get_current_user
from app.db.session import get_db
from app.services.s3_service import get_presigned_url

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/my-projects", response_model=ProjectListResponse)
async def get_my_projects(
    request: Request,
    offset: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """내 프로젝트 목록 조회"""
    user_info = await get_current_user(request)

    from app.crud.video import get_workflows_by_company_filtered

    workflows, total_count = get_workflows_by_company_filtered(
        db=db,
        company_id=user_info["company_id"],
        status=status,
        offset=offset,
        limit=limit
    )

    workflow_list = []
    for workflow in workflows:
        from app.models.ad_request import AdRequest
        from app.models.scenario import ScenarioScript
        from app.models.asset import ImageGeneration
        from app.models.video import Video
        ad = db.query(AdRequest).filter(AdRequest.ad_id == workflow.ad_id).first()

        # ad_request.status를 우선 사용 (영상 상세 정보와 동일)
        display_status = ad.status if ad else workflow.status

        scene_image_url = None
        scenario = db.query(ScenarioScript).filter(
            ScenarioScript.ad_id == workflow.ad_id
        ).order_by(ScenarioScript.created_at.desc()).first()
        if scenario:
            image_gen = db.query(ImageGeneration).filter(
                ImageGeneration.script_id == scenario.script_id
            ).order_by(ImageGeneration.created_at.desc()).first()
            if image_gen and image_gen.image_url:
                presigned = get_presigned_url(image_gen.image_url)
                if presigned:
                    scene_image_url = presigned
                elif image_gen.image_url.startswith('http'):
                    scene_image_url = image_gen.image_url
        if not scene_image_url:
            video = db.query(Video).filter(Video.ad_id == workflow.ad_id).first()
            if video and video.thumbnail_url:
                presigned = get_presigned_url(video.thumbnail_url)
                if presigned:
                    scene_image_url = presigned
                elif video.thumbnail_url.startswith('http'):
                    scene_image_url = video.thumbnail_url

        logger.debug(f"ad_id={workflow.ad_id}, ad.status={ad.status if ad else None}, workflow.status={workflow.status}, display_status={display_status}")

        workflow_list.append({
            'execution_id': str(workflow.execution_id),
            'ad_id': workflow.ad_id,
            'character_id': ad.character_id if ad else None,
            'item_name': ad.item_name if ad else '제목 없음',
            'scene_image_url': scene_image_url,
            'status': display_status,  # ad_request.status 사용
            'current_stage': workflow.current_stage,
            'progress_percentage': workflow.progress_percentage,
            'error_message': workflow.error_message,
            'created_at': workflow.created_at.isoformat(),
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
        })

    return ProjectListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        workflows=workflow_list
    )


@router.get("/{execution_id}", response_model=WorkflowStatusResponse)
async def get_video_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 기본 상태 조회"""
    user_info = await get_current_user(request)

    workflow = status_crud.get_workflow_status(db, execution_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    # 권한 확인 (Admin이 아닌 경우)
    if user_info.get("account_type") != 'admin':
        if workflow.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    return WorkflowStatusResponse(
        execution_id=str(workflow.execution_id),
        ad_id=workflow.ad_id,
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress_percentage=workflow.progress_percentage,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        error_message=workflow.error_message
    )


@router.get("/{execution_id}/detail")
async def get_video_status_detail(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """워크플로우 상세 상태 조회"""
    user_info = await get_current_user(request)

    workflow_detail = status_crud.get_workflow_detail(db, execution_id)
    if not workflow_detail:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")

    workflow = workflow_detail['workflow']

    # 권한 확인 (Admin이 아닌 경우)
    if user_info.get("account_type") != 'admin':
        if workflow.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    stages = []
    for stage in workflow_detail['stages']:
        stages.append({
            'stage_name': stage.stage_name,
            'stage_order': stage.stage_order,
            'status': stage.status,
            'started_at': stage.started_at.isoformat() if stage.started_at else None,
            'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
            'error_message': stage.error_message
        })

    return {
        'execution_id': str(workflow.execution_id),
        'ad_id': workflow.ad_id,
        'status': workflow.status,
        'current_stage': workflow.current_stage,
        'progress_percentage': workflow.progress_percentage,
        'retry_count': workflow.retry_count,
        'created_at': workflow.created_at.isoformat(),
        'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
        'error_message': workflow.error_message,
        'stages': stages
    }
