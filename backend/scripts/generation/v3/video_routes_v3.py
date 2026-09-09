"""
영상 제작 요청 API 엔드포인트 V3
새로운 스키마: video_projects, company_characters, workflow_execution
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Mock S3 사용 (테스트용)
from generation.s3_handler_mock import (
    upload_file_to_s3,
    validate_product_image,
    generate_presigned_url
)

from .database_v3 import VideoProject
from .database_v3 import (
    get_db,
    create_video_project,
    get_project_by_id,
    get_projects_by_company,
    update_project_character,
    update_project_status,
    create_company_character,
    get_character_by_id,
    get_characters_by_company,
    activate_character,
    deactivate_character,
    create_workflow,
    get_workflow_by_id,
    get_workflow_by_project,
    get_workflows_by_company_filtered,
    update_workflow_status,
    check_duplicate_project,
    initialize_workflow_stages,
    increment_retry_count
)

# auth v3 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'auth', 'v3'))
from auth_v3 import auth_middleware_v3

router = APIRouter(prefix="/api/videos", tags=["영상 생성 V3"])


# ============================================
# 요청/응답 모델
# ============================================
class VideoGenerateResponse(BaseModel):
    """영상 생성 요청 응답"""
    execution_id: str
    project_id: int
    status: str
    message: str


class WorkflowStatusResponse(BaseModel):
    """워크플로우 상태 응답 (목록용 간단 버전)"""
    execution_id: str
    project_id: int
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class CharacterPreviewResponse(BaseModel):
    """캐릭터 미리보기 응답"""
    character_id: int
    character_name: str
    character_mood: str
    character_style: str
    voice_tone: str
    image_url: Optional[str]
    voice_url: Optional[str]
    is_active: bool
    created_at: str


class ApprovalRequest(BaseModel):
    """승인/거부 요청"""
    approved: bool
    rejection_reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """승인/거부 응답"""
    character_id: int
    status: str
    message: str


class RegenerateRequest(BaseModel):
    """캐릭터 재생성 요청"""
    character_mood: Optional[str] = None
    character_style: Optional[str] = None
    voice_tone: Optional[str] = None
    character_name: Optional[str] = None


class RegenerateResponse(BaseModel):
    """캐릭터 재생성 응답"""
    execution_id: str
    project_id: int
    character_id: int
    status: str
    message: str


class CharacterListResponse(BaseModel):
    """캐릭터 목록 응답"""
    character_id: int
    character_name: str
    character_mood: str
    character_style: str
    voice_tone: str
    image_url: str
    is_active: bool
    created_at: str


# ============================================
# 1. 영상 제작 요청 엔드포인트
# ============================================
@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: Request,
    # 필수 필드
    product_name: str = Form(...),
    product_category: str = Form(...),
    product_highlight: str = Form(...),  # DB의 item_description에 매핑
    
    # 캐릭터 선택 (기존 캐릭터 사용 OR 새로 생성)
    character_id: Optional[int] = Form(None),
    
    # 캐릭터 생성 정보 (새로 생성할 때)
    character_mood: Optional[str] = Form(None),
    character_style: Optional[str] = Form(None),
    voice_tone: Optional[str] = Form(None),
    character_name: Optional[str] = Form(None),
    
    # 제품 이미지
    product_images: List[UploadFile] = File(...),
    
    # 선택 필드
    item_url: Optional[str] = Form(None),  # 제품 URL 추가
    meme_id: Optional[int] = Form(None),
    reference_notes: Optional[str] = Form(None),
    
    # DB
    db: Session = Depends(get_db)
):
    """
    영상 제작 요청 API V3
    
    **케이스 1: 기존 캐릭터 사용**
    - character_id 제공
    
    **케이스 2: 새 캐릭터 생성**
    - character_mood, character_style, voice_tone 제공
    """
    
    # 1. 사용자 인증 확인
    await auth_middleware_v3(request)
    user_info = request.state.user
    account_id = user_info["account_id"]
    company_id = user_info["company_id"]
    
    # 2. 캐릭터 검증
    if character_id is None and (not character_mood or not character_style or not voice_tone):
        raise HTTPException(
            status_code=400,
            detail="기존 캐릭터 ID를 제공하거나, 새 캐릭터 정보(mood, style, tone)를 모두 입력해야 합니다"
        )
    
    # 3. 제품 이미지 개수 확인 (최대 3장)
    if len(product_images) > 3:
        raise HTTPException(
            status_code=400,
            detail="제품 이미지는 최대 3장까지 업로드 가능합니다"
        )
    
    # 4. 제품 이미지 검증 및 읽기
    product_img_contents = []
    for prod_img in product_images:
        content = await prod_img.read()
        is_valid, error_msg = validate_product_image(prod_img.filename, len(content))
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"제품 이미지: {error_msg}")
        product_img_contents.append((prod_img.filename, content))
    
    # 5. 중복 확인
    if meme_id:
        existing_project = check_duplicate_project(db, company_id, product_name, meme_id)
        if existing_project:
            raise HTTPException(
                status_code=409,
                detail=f"동일한 제품과 밈으로 진행 중인 프로젝트가 있습니다. Project ID: {existing_project.project_id}"
            )
    
    # 6. 제품 이미지 S3 업로드
    try:
        product_img_urls = []
        for filename, content in product_img_contents:
            url = upload_file_to_s3(
                content,
                "product_image",
                company_id,
                filename
            )
            product_img_urls.append(url)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 실패: {str(e)}"
        )
    
    # 7. VideoProject 생성
    project = create_video_project(
        db=db,
        company_id=company_id,
        user_id=account_id,
        item_name=product_name,
        item_category=product_category,
        item_description=product_highlight,  # item_highlight -> item_description
        item_url=item_url,  # 제품 URL 추가
        item_images=product_img_urls,
        character_id=character_id,
        character_mood=character_mood,
        character_style=character_style,
        voice_tone=voice_tone,
        meme_id=meme_id,
        reference_notes=reference_notes
    )
    
    # 8. WorkflowExecution 생성
    workflow = create_workflow(
        db=db,
        project_id=project.project_id,
        company_id=company_id,
        account_id=account_id,
        meme_id=meme_id
    )
    
    # 9. 워크플로우 단계 초기화
    initialize_workflow_stages(db, workflow.execution_id)
    
    # 10. 상태 결정
    if character_id:
        # 기존 캐릭터 사용 -> 바로 processing
        update_workflow_status(db, workflow.execution_id, "processing", "영상 생성 중", 10)
        message = "영상 생성이 시작되었습니다"
    else:
        # 새 캐릭터 생성 필요 -> generating_character
        update_workflow_status(db, workflow.execution_id, "generating_character", "캐릭터 생성 중", 5)
        message = "캐릭터 생성 요청이 접수되었습니다. 잠시 후 미리보기를 확인하세요"
    
    # 11. 응답 반환
    return VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        project_id=project.project_id,
        status=workflow.status,
        message=message
    )


# ============================================
# 2. 캐릭터 미리보기 조회
# ============================================
@router.get("/character/{character_id}", response_model=CharacterPreviewResponse)
async def get_character_preview(
    character_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    생성된 캐릭터 미리보기 조회
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 캐릭터 조회
    character = get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    
    # 3. 권한 확인 (같은 회사만)
    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. Pre-signed URL 생성
    image_url = None
    voice_url = None
    
    if character.image_url:
        try:
            image_url = generate_presigned_url(character.image_url, expiration=3600)
        except Exception as e:
            print(f"Pre-signed URL 생성 실패: {e}")
            image_url = character.image_url
    
    if character.voice_url:
        try:
            voice_url = generate_presigned_url(character.voice_url, expiration=3600)
        except Exception as e:
            print(f"Pre-signed URL 생성 실패: {e}")
            voice_url = character.voice_url
    
    # 5. 응답 반환
    return CharacterPreviewResponse(
        character_id=character.character_id,
        character_name=character.character_name,
        character_mood=character.character_mood,
        character_style=character.character_style,
        voice_tone=character.voice_tone,
        image_url=image_url,
        voice_url=voice_url,
        is_active=character.is_active,
        created_at=character.created_at.isoformat()
    )


# ============================================
# 3. 캐릭터 승인/거부
# ============================================
@router.post("/character/{character_id}/approve", response_model=ApprovalResponse)
async def approve_character_endpoint(
    character_id: int,
    approval: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    캐릭터 승인/거부
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 캐릭터 조회
    character = get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    
    # 3. 권한 확인
    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 활성화/비활성화 처리
    if approval.approved:
        # 활성화
        character = activate_character(db, character_id)
        
        return ApprovalResponse(
            character_id=character_id,
            status="active",
            message="캐릭터가 활성화되었습니다"
        )
    else:
        # 비활성화
        character = deactivate_character(db, character_id)
        
        return ApprovalResponse(
            character_id=character_id,
            status="inactive",
            message="캐릭터가 비활성화되었습니다"
        )


# ============================================
# 4. 회사 캐릭터 목록 조회
# ============================================
@router.get("/characters", response_model=List[CharacterListResponse])
async def get_company_characters(
    request: Request,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    회사의 캐릭터 목록 조회
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 캐릭터 목록 조회
    characters = get_characters_by_company(db, user_info["company_id"], active_only)
    
    # 3. 응답 변환
    result = []
    for char in characters:
        result.append(CharacterListResponse(
            character_id=char.character_id,
            character_name=char.character_name,
            character_mood=char.character_mood,
            character_style=char.character_style,
            voice_tone=char.voice_tone,
            image_url=char.image_url,
            is_active=char.is_active,
            created_at=char.created_at.isoformat()
        ))
    
    return result


# ============================================
# 5. 캐릭터 재생성 요청
# ============================================
@router.post("/character/{character_id}/regenerate", response_model=RegenerateResponse)
async def regenerate_character(
    character_id: int,
    regenerate_req: RegenerateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    거부된 캐릭터 재생성 요청
    
    **경로 파라미터:**
    - character_id: 재생성할 캐릭터 ID
    
    **요청 본문:**
    - character_mood: 수정할 캐릭터 분위기 (선택)
    - character_style: 수정할 캐릭터 스타일 (선택)
    - voice_tone: 수정할 음성 톤 (선택)
    - character_name: 수정할 캐릭터 이름 (선택)
    
    **응답:**
    - 재생성 요청 접수 확인
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 캐릭터 조회
    character = get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
    
    # 3. 권한 확인
    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 4. 캐릭터가 비활성화 상태인지 확인 (거부된 캐릭터만 재생성 가능)
    if character.is_active:
        raise HTTPException(
            status_code=400,
            detail="활성화된 캐릭터는 재생성할 수 없습니다. 비활성화된 캐릭터만 재생성 가능합니다."
        )
    
    # 5. 해당 캐릭터를 사용하는 프로젝트 찾기
    project = db.query(VideoProject).filter(
        VideoProject.character_id == character_id,
        VideoProject.company_id == user_info["company_id"]
    ).order_by(VideoProject.created_at.desc()).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="해당 캐릭터와 연결된 프로젝트를 찾을 수 없습니다")
    
    # 6. 워크플로우 찾기
    workflow = get_workflow_by_project(db, project.project_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="워크플로우를 찾을 수 없습니다")
    
    # 7. 프로젝트 정보 업데이트 (수정된 파라미터가 있으면 반영)
    if regenerate_req.character_mood:
        project.character_mood = regenerate_req.character_mood
    if regenerate_req.character_style:
        project.character_style = regenerate_req.character_style
    if regenerate_req.voice_tone:
        project.voice_tone = regenerate_req.voice_tone
    
    db.commit()
    db.refresh(project)
    
    # 8. 재시도 횟수 증가
    increment_retry_count(db, workflow.execution_id)
    
    # 9. 워크플로우 상태를 generating_character로 변경
    update_workflow_status(
        db, 
        workflow.execution_id, 
        "generating_character", 
        "캐릭터 재생성 중", 
        5
    )
    
    # 10. 캐릭터 이름 업데이트 (제공된 경우)
    if regenerate_req.character_name:
        character.character_name = regenerate_req.character_name
        db.commit()
        db.refresh(character)
    
    # 11. 응답 반환
    return RegenerateResponse(
        execution_id=str(workflow.execution_id),
        project_id=project.project_id,
        character_id=character_id,
        status="generating_character",
        message="캐릭터 재생성 요청이 접수되었습니다. 잠시 후 미리보기를 다시 확인하세요."
    )


# ============================================
# 6. 내 프로젝트 목록 조회 (보완)
# ============================================
class ProjectListResponse(BaseModel):
    """프로젝트 목록 응답"""
    total_count: int
    offset: int
    limit: int
    workflows: List[WorkflowStatusResponse]


@router.get("/my-projects", response_model=ProjectListResponse)
async def get_my_projects(
    request: Request,
    # 페이지네이션
    offset: int = 0,
    limit: int = 10,
    # 필터링
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    # 정렬
    sort_by: str = 'created_at',
    order: str = 'desc',
    db: Session = Depends(get_db)
):
    """
    내 영상 제작 프로젝트 목록 조회 (필터링, 페이지네이션)
    
    **쿼리 파라미터:**
    - offset: 시작 위치 (기본 0)
    - limit: 조회 개수 (기본 10, 최대 100)
    - status: 상태 필터 (created, processing, completed, failed 등)
    - date_from: 시작 날짜 (ISO 8601 형식)
    - date_to: 종료 날짜 (ISO 8601 형식)
    - sort_by: 정렬 기준 (created_at, completed_at)
    - order: 정렬 순서 (asc, desc)
    """
    # 1. 사용자 인증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # 2. 파라미터 검증
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 10
    if offset < 0:
        offset = 0
    
    if sort_by not in ['created_at', 'completed_at']:
        sort_by = 'created_at'
    if order not in ['asc', 'desc']:
        order = 'desc'
    
    # 3. 날짜 파싱
    date_from_dt = None
    date_to_dt = None
    
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_from 형식이 잘못되었습니다 (ISO 8601 형식 필요)")
    
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="date_to 형식이 잘못되었습니다 (ISO 8601 형식 필요)")
    
    # 4. 워크플로우 목록 조회
    workflows, total_count = get_workflows_by_company_filtered(
        db=db,
        company_id=user_info["company_id"],
        status=status,
        date_from=date_from_dt,
        date_to=date_to_dt,
        sort_by=sort_by,
        order=order,
        offset=offset,
        limit=limit
    )
    
    # 5. 응답 변환
    result = []
    for workflow in workflows:
        result.append(WorkflowStatusResponse(
            execution_id=str(workflow.execution_id),
            project_id=workflow.project_id,
            status=workflow.status,
            current_stage=workflow.current_stage,
            progress_percentage=workflow.progress_percentage,
            error_message=workflow.error_message,
            created_at=workflow.created_at.isoformat(),
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
        ))
    
    return ProjectListResponse(
        total_count=total_count,
        offset=offset,
        limit=limit,
        workflows=result
    )
