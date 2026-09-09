"""
영상 제작 요청 API 엔드포인트 (단계별 추적 기능 포함)
작업 내용 1번: 영상 제작 요청 엔드포인트 + 단계별 상태 추적
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from status.database import (
    get_db,
    create_workflow,
    get_workflow_by_id,
    get_workflows_by_user,
    check_duplicate_workflow,
    # 단계 관리 함수
    initialize_workflow_stages,
    get_stage_summary,
    calculate_estimated_completion
)
from generation.s3_handler import (
    upload_file_to_s3,
    validate_character_image,
    validate_character_voice,
    validate_product_image,
    generate_presigned_url
)
from auth.v2.auth_v2 import auth_middleware_v2

router = APIRouter(prefix="/api/videos", tags=["영상 생성"])


# ============================================
# 요청/응답 모델
# ============================================
class VideoGenerateResponse(BaseModel):
    """영상 생성 요청 응답"""
    execution_id: str
    status: str
    message: str


class WorkflowStatusResponse(BaseModel):
    """워크플로우 기본 상태 응답"""
    execution_id: str
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    output_video_url: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class StageInfo(BaseModel):
    """단계 정보"""
    name: str
    status: str
    order: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    error_message: Optional[str]


class WorkflowStatusDetailResponse(BaseModel):
    """워크플로우 상세 상태 응답"""
    execution_id: str
    status: str
    progress_percentage: int
    
    # 단계별 정보
    completed_stages: List[StageInfo]
    current_stage: Optional[StageInfo]
    pending_stages: List[str]
    
    # 시간 정보
    estimated_completion: Optional[str]
    estimated_remaining_seconds: Optional[int]
    
    # 기타
    output_video_url: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


# ============================================
# 1. 영상 제작 요청 엔드포인트
# ============================================
@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: Request,
    # 필수 필드
    company_name: str = Form(...),
    product_name: str = Form(...),
    product_category: str = Form(...),
    product_highlight: str = Form(...),
    character_tone: str = Form(...),
    
    # 파일 업로드
    character_image: UploadFile = File(...),
    character_voice: UploadFile = File(...),
    product_images: List[UploadFile] = File(...),
    
    # 선택 필드
    meme_id: Optional[int] = Form(None),
    reference_notes: Optional[str] = Form(None),
    
    # DB
    db: Session = Depends(get_db)
):
    """
    영상 제작 요청 API
    
    작업 내용 1번: POST /api/videos/generate 엔드포인트 구현
    
    **필수 입력:**
    - company_name: 회사 이름
    - product_name: 제품 이름
    - product_category: 제품 카테고리
    - product_highlight: 제품 강조문구
    - character_tone: 캐릭터 말투(톤)
    - meme_id: 밈 ID
    - character_image: 캐릭터 이미지 파일
    - character_voice: 캐릭터 음성 파일
    - product_images: 제품 이미지 파일 (최대 3장)
    
    **선택 입력:**
    - reference_notes: 참고 사항
    
    **응답:**
    - job_id: 작업 고유 ID (UUID)
    - status: 작업 상태
    - estimated_duration_seconds: 예상 소요 시간
    """
    
    # 1. 사용자 인증 확인
    await auth_middleware_v2(request)
    user_info = request.state.user
    user_id = user_info["user_id"]
    company_id = user_info["company_id"]
    
    # 2. 요청 데이터 검증 (작업 내용 1번)
    
    # 2-1. 제품 이미지 개수 확인 (최대 3장)
    if len(product_images) > 3:
        raise HTTPException(
            status_code=400,
            detail="제품 이미지는 최대 3장까지 업로드 가능합니다"
        )
    
    # 2-2. 캐릭터 이미지 검증
    char_img_content = await character_image.read()
    is_valid, error_msg = validate_character_image(
        character_image.filename,
        len(char_img_content)
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"캐릭터 이미지: {error_msg}")
    
    # 2-3. 캐릭터 음성 검증
    char_voice_content = await character_voice.read()
    is_valid, error_msg = validate_character_voice(
        character_voice.filename,
        len(char_voice_content)
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"캐릭터 음성: {error_msg}")
    
    # 2-4. 제품 이미지 검증
    product_img_contents = []
    for prod_img in product_images:
        content = await prod_img.read()
        is_valid, error_msg = validate_product_image(prod_img.filename, len(content))
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"제품 이미지: {error_msg}")
        product_img_contents.append((prod_img.filename, content))
    
    # 3. 중복 확인 (DMG-AUTO-07) - meme_id가 있을 때만
    if meme_id:
        existing_workflow = check_duplicate_workflow(db, company_id, product_name, meme_id)
        if existing_workflow:
            raise HTTPException(
                status_code=409,
                detail=f"동일한 제품과 밈으로 진행 중인 작업이 있습니다. Execution ID: {existing_workflow.execution_id}"
            )
    
    # 4. S3 파일 업로드 (작업 내용 2번)
    try:
        # 4-1. 캐릭터 이미지 업로드
        char_img_url = upload_file_to_s3(
            char_img_content,
            "character_image",
            company_id,
            character_image.filename,
            character_image.content_type
        )
        
        # 4-2. 캐릭터 음성 업로드
        char_voice_url = upload_file_to_s3(
            char_voice_content,
            "character_voice",
            company_id,
            character_voice.filename,
            character_voice.content_type
        )
        
        # 4-3. 제품 이미지 업로드
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
    
    # 5. 입력 파라미터 구성 (작업 내용 3번)
    input_params = {
        "company_name": company_name,
        "product_name": product_name,
        "product_category": product_category,
        "product_highlight": product_highlight,
        "character_tone": character_tone,
        "meme_id": meme_id,
        "reference_notes": reference_notes,
        # S3 파일 경로도 input_params에 저장
        "character_image_url": char_img_url,
        "character_voice_url": char_voice_url,
        "product_images": product_img_urls
    }
    
    # 6. 워크플로우 생성 (작업 내용 3번)
    workflow = create_workflow(
        db=db,
        user_id=user_id,
        company_id=company_id,
        input_params=input_params,
        meme_id=meme_id,
        workflow_type="video"
    )
    
    # 7. 단계 초기화 ✨ 새로 추가
    initialize_workflow_stages(db, workflow.execution_id)
    
    # 8. 비동기 작업 시작 (작업 내용 4번)
    # TODO: Celery 태스크 시작
    # from generation.tasks import generate_video_task
    # generate_video_task.delay(str(workflow.execution_id))
    
    # 9. 응답 반환
    return VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message="영상 생성 요청이 접수되었습니다. Execution ID로 진행 상황을 확인하세요."
    )


# ============================================
# 2. 워크플로우 기본 상태 조회
# ============================================
@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_video_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 생성 기본 상태 조회
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **응답:**
    - 작업 상태, 진행률, 출력 영상 URL 등
    """
    
    # 1. 사용자 인증
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 2. Execution ID 검증
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 Execution ID 형식입니다")
    
    # 3. 워크플로우 조회
    workflow = get_workflow_by_id(db, exec_uuid)
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 Execution ID를 찾을 수 없습니다")
    
    # 4. 권한 확인 (자신의 작업만 조회 가능)
    if workflow.user_id != user_info["user_id"] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. Pre-signed URL 생성 (출력 영상이 있는 경우)
    output_url = None
    if workflow.output_result and workflow.output_result.get("video_url"):
        try:
            output_url = generate_presigned_url(workflow.output_result["video_url"], expiration=7*24*3600)  # 7일
        except:
            output_url = workflow.output_result.get("video_url")
    
    # 6. 응답 반환
    return WorkflowStatusResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        current_stage=workflow.current_stage,
        progress_percentage=workflow.progress_percentage,
        output_video_url=output_url,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
    )


# ============================================
# 3. 워크플로우 상세 상태 조회 ✨ 새로 추가
# ============================================
@router.get("/status/{execution_id}/detail", response_model=WorkflowStatusDetailResponse)
async def get_video_status_detail(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 생성 상세 상태 조회 (단계별 정보 포함)
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **응답:**
    - 완료된 단계 목록 (소요 시간 포함)
    - 현재 진행 중인 단계
    - 대기 중인 단계 목록
    - 예상 완료 시간
    """
    
    # 1. 사용자 인증
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 2. Execution ID 검증
    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 Execution ID 형식입니다")
    
    # 3. 워크플로우 조회
    workflow = get_workflow_by_id(db, exec_uuid)
    if not workflow:
        raise HTTPException(status_code=404, detail="해당 Execution ID를 찾을 수 없습니다")
    
    # 4. 권한 확인
    if workflow.user_id != user_info["user_id"] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 단계 정보 조회
    completed, current, pending = get_stage_summary(workflow)
    estimated_time, remaining_seconds = calculate_estimated_completion(workflow)
    
    # 6. Pre-signed URL 생성
    output_url = None
    if workflow.output_result and workflow.output_result.get("video_url"):
        try:
            output_url = generate_presigned_url(workflow.output_result["video_url"], expiration=7*24*3600)
        except:
            output_url = workflow.output_result.get("video_url")
    
    # 7. 응답 반환
    return WorkflowStatusDetailResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        progress_percentage=workflow.progress_percentage,
        completed_stages=[StageInfo(**stage) for stage in completed],
        current_stage=StageInfo(**current) if current else None,
        pending_stages=pending,
        estimated_completion=estimated_time,
        estimated_remaining_seconds=remaining_seconds,
        output_video_url=output_url,
        error_message=workflow.error_message,
        created_at=workflow.created_at.isoformat(),
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
    )


# ============================================
# 4. 사용자의 워크플로우 목록 조회
# ============================================
@router.get("/my-videos", response_model=List[WorkflowStatusResponse])
async def get_my_videos(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    내 영상 제작 이력 조회
    
    **쿼리 파라미터:**
    - limit: 조회 개수 (기본 10개)
    
    **응답:**
    - 워크플로우 목록
    """
    
    # 1. 사용자 인증
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 2. 워크플로우 목록 조회
    workflows = get_workflows_by_user(db, user_info["user_id"], limit)
    
    # 3. 응답 변환
    result = []
    for workflow in workflows:
        output_url = None
        if workflow.output_result and workflow.output_result.get("video_url"):
            try:
                output_url = generate_presigned_url(workflow.output_result["video_url"], expiration=7*24*3600)
            except:
                output_url = workflow.output_result.get("video_url")
        
        result.append(WorkflowStatusResponse(
            execution_id=str(workflow.execution_id),
            status=workflow.status,
            current_stage=workflow.current_stage,
            progress_percentage=workflow.progress_percentage,
            output_video_url=output_url,
            error_message=workflow.error_message,
            created_at=workflow.created_at.isoformat(),
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
        ))
    
    return result
