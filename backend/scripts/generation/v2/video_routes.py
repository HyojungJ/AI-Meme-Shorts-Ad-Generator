"""
영상 제작 요청 API 엔드포인트
승인 기반 워크플로우: 캐릭터 생성 → 사용자 검수 → 영상 생성
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
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

# 실제 S3 사용 시 아래 주석 해제
# from generation.v2.s3_handler import (
#     upload_file_to_s3,
#     validate_product_image,
#     generate_presigned_url
# )

from generation.v2.database import (
    get_db,
    create_workflow,
    get_workflow_by_id,
    get_workflows_by_user,
    check_duplicate_workflow
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
    """워크플로우 상태 응답"""
    execution_id: str
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    output_video_url: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


class CharacterPreviewResponse(BaseModel):
    """캐릭터 미리보기 응답"""
    execution_id: str
    status: str
    character_image_url: Optional[str]
    character_voice_url: Optional[str]
    character_mood: str
    character_style: str
    voice_tone: str
    created_at: str
    generated_at: Optional[str]


class ApprovalRequest(BaseModel):
    """승인/거부 요청"""
    approved: bool
    rejection_reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """승인/거부 응답"""
    execution_id: str
    status: str
    message: str


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
    
    # 캐릭터 생성 정보 (파일 업로드 대신 텍스트 입력)
    character_mood: str = Form(...),      # 예: "밝고 활기찬"
    character_style: str = Form(...),     # 예: "20대 여성"
    voice_tone: str = Form(...),          # 예: "친근한"
    
    # 제품 이미지만 업로드
    product_images: List[UploadFile] = File(...),
    
    # 선택 필드
    meme_id: Optional[int] = Form(None),
    reference_notes: Optional[str] = Form(None),
    
    # DB
    db: Session = Depends(get_db)
):
    """
    영상 제작 요청 API - 1단계: 캐릭터 생성 요청
    
    **필수 입력:**
    - company_name: 회사 이름
    - product_name: 제품 이름
    - product_category: 제품 카테고리
    - product_highlight: 제품 강조문구
    - character_mood: 원하는 캐릭터 분위기 (예: "밝고 활기찬")
    - character_style: 캐릭터 스타일 (예: "20대 여성")
    - voice_tone: 음성 톤 (예: "친근한")
    - product_images: 제품 이미지 파일 (최대 3장)
    
    **선택 입력:**
    - meme_id: 밈 ID
    - reference_notes: 참고 사항
    
    **응답:**
    - execution_id: 작업 고유 ID (UUID)
    - status: "created" 또는 "generating_character"
    - message: "캐릭터 생성 중입니다. 잠시 후 미리보기를 확인하세요."
    
    **다음 단계:**
    1. 팀원의 AI 시스템이 캐릭터 이미지/음성 생성
    2. GET /api/videos/preview/{execution_id}로 미리보기 확인
    3. POST /api/videos/approve/{execution_id}로 승인/거부
    """
    
    # 1. 사용자 인증 확인
    await auth_middleware_v2(request)
    user_info = request.state.user
    user_id = user_info["user_id"]
    company_id = user_info["company_id"]
    
    # 2. 요청 데이터 검증
    
    # 2-1. 제품 이미지 개수 확인 (최대 3장)
    if len(product_images) > 3:
        raise HTTPException(
            status_code=400,
            detail="제품 이미지는 최대 3장까지 업로드 가능합니다"
        )
    
    # 2-2. 제품 이미지 검증 및 읽기
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
    
    # 4. 제품 이미지 S3 업로드
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
    
    # 5. 입력 파라미터 구성
    input_params = {
        "company_name": company_name,
        "product_name": product_name,
        "product_category": product_category,
        "product_highlight": product_highlight,
        # 캐릭터 생성 정보
        "character_mood": character_mood,
        "character_style": character_style,
        "voice_tone": voice_tone,
        # 제품 이미지
        "product_images": product_img_urls,
        # 선택 필드
        "meme_id": meme_id,
        "reference_notes": reference_notes
    }
    
    # 6. 워크플로우 생성
    workflow = create_workflow(
        db=db,
        user_id=user_id,
        company_id=company_id,
        input_params=input_params,
        meme_id=meme_id,
        workflow_type="video"
    )
    
    # 7. 캐릭터 생성 요청 (팀원의 AI 시스템이 DB 폴링으로 처리)
    # 팀원이 status="created" 인 워크플로우를 찾아서 캐릭터 생성
    # 생성 완료 후 status="pending_approval"로 변경
    
    # 8. 응답 반환
    return VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message="캐릭터 생성 요청이 접수되었습니다. 잠시 후 미리보기를 확인하세요."
    )


# ============================================
# 2. 캐릭터 미리보기 조회 (새로 추가)
# ============================================
@router.get("/preview/{execution_id}", response_model=CharacterPreviewResponse)
async def get_character_preview(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    생성된 캐릭터 미리보기 조회
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **응답:**
    - 생성된 캐릭터 이미지/음성 URL (Pre-signed URL)
    - 상태: generating_character, pending_approval, approved, rejected
    
    **사용 시나리오:**
    1. 사용자가 영상 생성 요청 후 이 API로 캐릭터 생성 완료 확인
    2. status="pending_approval"이면 미리보기 가능
    3. 이미지/음성 확인 후 /approve API로 승인/거부
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
    if workflow.user_id != user_info["user_id"] and user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. Pre-signed URL 생성 (생성된 캐릭터가 있는 경우)
    char_img_url = None
    char_voice_url = None
    generated_at = None
    
    if workflow.output_result:
        if workflow.output_result.get("generated_character_image_url"):
            try:
                char_img_url = generate_presigned_url(
                    workflow.output_result["generated_character_image_url"],
                    expiration=3600  # 1시간
                )
            except Exception as e:
                print(f"Pre-signed URL 생성 실패: {e}")
                char_img_url = workflow.output_result.get("generated_character_image_url")
        
        if workflow.output_result.get("generated_voice_url"):
            try:
                char_voice_url = generate_presigned_url(
                    workflow.output_result["generated_voice_url"],
                    expiration=3600
                )
            except Exception as e:
                print(f"Pre-signed URL 생성 실패: {e}")
                char_voice_url = workflow.output_result.get("generated_voice_url")
        
        generated_at = workflow.output_result.get("generated_at")
    
    # 6. 응답 반환
    return CharacterPreviewResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        character_image_url=char_img_url,
        character_voice_url=char_voice_url,
        character_mood=workflow.input_params.get("character_mood", ""),
        character_style=workflow.input_params.get("character_style", ""),
        voice_tone=workflow.input_params.get("voice_tone", ""),
        created_at=workflow.created_at.isoformat(),
        generated_at=generated_at
    )


# ============================================
# 3. 캐릭터 승인/거부 (새로 추가)
# ============================================
@router.post("/approve/{execution_id}", response_model=ApprovalResponse)
async def approve_character(
    execution_id: str,
    approval: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    캐릭터 승인/거부
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **요청 본문:**
    - approved: true (승인) / false (거부)
    - rejection_reason: 거부 시 이유 (선택)
    
    **승인 시:**
    - status → "approved"
    - 팀원의 영상 생성 시스템이 DB 폴링으로 감지하여 영상 생성 시작
    
    **거부 시:**
    - status → "rejected"
    - /regenerate API로 재생성 요청 가능
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
    if workflow.user_id != user_info["user_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 상태 확인 (pending_approval 상태여야 함)
    if workflow.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"승인 가능한 상태가 아닙니다. 현재 상태: {workflow.status}"
        )
    
    # 6. 승인/거부 처리
    from datetime import datetime
    
    if approval.approved:
        # 승인
        workflow.status = "approved"
        if not workflow.output_result:
            workflow.output_result = {}
        workflow.output_result["approval_status"] = "approved"
        workflow.output_result["approval_at"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(workflow)
        
        # 팀원의 영상 생성 시스템이 status="approved" 감지하여 영상 생성 시작
        
        return ApprovalResponse(
            execution_id=str(workflow.execution_id),
            status="approved",
            message="캐릭터가 승인되었습니다. 영상 생성이 시작됩니다."
        )
    else:
        # 거부
        workflow.status = "rejected"
        if not workflow.output_result:
            workflow.output_result = {}
        workflow.output_result["approval_status"] = "rejected"
        workflow.output_result["rejection_reason"] = approval.rejection_reason or "사용자가 거부함"
        workflow.output_result["rejection_at"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(workflow)
        
        return ApprovalResponse(
            execution_id=str(workflow.execution_id),
            status="rejected",
            message="캐릭터가 거부되었습니다. /regenerate API로 재생성을 요청하세요."
        )


# ============================================
# 4. 캐릭터 재생성 요청 (새로 추가 - 선택)
# ============================================
@router.post("/regenerate/{execution_id}", response_model=VideoGenerateResponse)
async def regenerate_character(
    execution_id: str,
    request: Request,
    # 수정할 내용 (선택)
    character_mood: Optional[str] = Form(None),
    character_style: Optional[str] = Form(None),
    voice_tone: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    캐릭터 재생성 요청
    
    **경로 파라미터:**
    - execution_id: 작업 고유 ID (UUID)
    
    **요청 본문 (선택):**
    - character_mood: 수정할 분위기
    - character_style: 수정할 스타일
    - voice_tone: 수정할 음성 톤
    
    **사용 시나리오:**
    - 사용자가 캐릭터를 거부한 후 재생성 요청
    - 원하는 경우 분위기/스타일 수정 가능
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
    if workflow.user_id != user_info["user_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    
    # 5. 상태 확인 (rejected 상태여야 함)
    if workflow.status != "rejected":
        raise HTTPException(
            status_code=400,
            detail=f"재생성 가능한 상태가 아닙니다. 현재 상태: {workflow.status}"
        )
    
    # 6. 재시도 횟수 확인 (최대 10회)
    if workflow.retry_count >= 10:
        raise HTTPException(
            status_code=400,
            detail="재생성 횟수가 최대 제한(10회)을 초과했습니다."
        )
    
    # 7. input_params 업데이트 (수정 사항이 있으면)
    if character_mood:
        workflow.input_params["character_mood"] = character_mood
    if character_style:
        workflow.input_params["character_style"] = character_style
    if voice_tone:
        workflow.input_params["voice_tone"] = voice_tone
    
    # 8. 상태 변경
    workflow.status = "created"  # 다시 생성 대기 상태로
    workflow.retry_count += 1
    
    db.commit()
    db.refresh(workflow)
    
    # 팀원의 AI 시스템이 status="created" 감지하여 재생성
    
    return VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message=f"캐릭터 재생성 요청이 접수되었습니다. (재시도 {workflow.retry_count}회)"
    )


# ============================================
# 5. 워크플로우 상태 조회
# ============================================
@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_video_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    영상 생성 상태 조회
    
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
# 3. 사용자의 워크플로우 목록 조회
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
