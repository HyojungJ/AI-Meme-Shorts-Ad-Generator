"""
시나리오 검수 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.schemas.scenario import (
    ScenarioResponse,
    SceneInfo,
    ScenarioDetail,
    ApproveResponse,
    ReviseRequest,
    ReviseResponse
)
from app.crud import scenario as scenario_crud
from app.crud import video as video_crud
from app.core.security import get_current_user
from app.db.session import get_db

router = APIRouter()


@router.get("/{job_id}/scenarios", response_model=ScenarioResponse)
async def get_scenario(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """시나리오 조회 (단일)"""
    user_info = await get_current_user(request)
    
    scenario = scenario_crud.get_scenario_candidates(db, job_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오를 찾을 수 없습니다")
    
    # 권한 확인 - ad_request를 통해 company_id 확인
    ad_request = video_crud.get_ad_request_by_id(db, scenario.ad_id)
    if ad_request and ad_request.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # scenes JSONB 파싱
    scenes_data = scenario.scenes if scenario.scenes else {}
    scene_list = []
    
    # scenes가 dict 형태라고 가정 (예: {"intro": {...}, "main": {...}, "outro": {...}})
    if isinstance(scenes_data, dict):
        scene_number = 1
        for scene_key, scene_content in scenes_data.items():
            if scene_key == 'revision_requests':  # revision_requests는 제외
                continue
            
            scene_text = ""
            scene_duration = None
            
            if isinstance(scene_content, dict):
                scene_text = scene_content.get('text', '')
                scene_duration = scene_content.get('duration')
            elif isinstance(scene_content, str):
                scene_text = scene_content
            
            scene_list.append(SceneInfo(
                scene_number=scene_number,
                scene_key=scene_key,
                text=scene_text,
                duration=scene_duration
            ))
            scene_number += 1
    
    scenario_detail = ScenarioDetail(
        script_id=scenario.script_id,
        ad_id=scenario.ad_id,
        title=scenario.title,
        description=scenario.description,
        scenes=scene_list,
        total_duration=scenario.total_duration,
        approval_status=scenario.approval_status,
        generation_type=scenario.generation_type,
        review_result=scenario.review_result,
        used_templates=scenario.used_templates,
        created_at=scenario.created_at.isoformat()
    )
    
    return ScenarioResponse(
        job_id=job_id,
        scenario=scenario_detail
    )


@router.post("/{job_id}/scenarios/{script_id}/approve", response_model=ApproveResponse)
async def approve_scenario(
    job_id: str,
    script_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """시나리오 승인"""
    user_info = await get_current_user(request)
    
    scenario = scenario_crud.get_scenario_by_id(db, script_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오를 찾을 수 없습니다")
    
    # 권한 확인 - ad_request를 통해 company_id 확인
    ad_request = video_crud.get_ad_request_by_id(db, scenario.ad_id)
    if ad_request and ad_request.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 시나리오 승인
    updated_scenario = scenario_crud.approve_scenario(db, script_id)
    
    return ApproveResponse(
        script_id=script_id,
        ad_id=scenario.ad_id,
        status='approved',
        message='시나리오가 승인되었습니다'
    )


@router.post("/{job_id}/scenarios/{script_id}/revise", response_model=ReviseResponse)
async def revise_scenario(
    job_id: str,
    script_id: int,
    request: Request,
    revise_request: ReviseRequest,
    db: Session = Depends(get_db)
):
    """시나리오 수정 요청 (씬별)"""
    user_info = await get_current_user(request)
    
    scenario = scenario_crud.get_scenario_by_id(db, script_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="시나리오를 찾을 수 없습니다")
    
    # 권한 확인 - ad_request를 통해 company_id 확인
    ad_request = video_crud.get_ad_request_by_id(db, scenario.ad_id)
    if ad_request and ad_request.company_id != user_info.get("company_id"):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 씬별 수정 요청 처리
    scene_revisions = [
        {
            'scene_number': rev.scene_number,
            'revision_notes': rev.revision_notes
        }
        for rev in revise_request.scene_revisions
    ]
    
    new_scenario = scenario_crud.request_scenario_revision(
        db=db,
        script_id=script_id,
        scene_revisions=scene_revisions
    )
    
    return ReviseResponse(
        script_id=new_scenario.script_id if new_scenario else script_id,
        ad_id=scenario.ad_id,
        status='pending',  # revision_requested 대신 pending 사용
        message=f'{len(scene_revisions)}개 씬에 대한 수정이 요청되었습니다'
    )
