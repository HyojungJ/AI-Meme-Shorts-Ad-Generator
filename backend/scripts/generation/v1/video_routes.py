"""
?곸긽 ?쒖옉 ?붿껌 API ?붾뱶?ъ씤???묒뾽 ?댁슜 1踰? ?곸긽 ?쒖옉 ?붿껌 ?붾뱶?ъ씤??"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import sys
import os

# 寃쎈줈 異붽?
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from generation.database import (
    get_db,
    create_workflow,
    get_workflow_by_id,
    get_workflows_by_user,
    check_duplicate_workflow
)
from generation.s3_handler import (
    upload_file_to_s3,
    validate_character_image,
    validate_character_voice,
    validate_product_image,
    generate_presigned_url
)
from auth.v2.auth_v2 import auth_middleware_v2

router = APIRouter(prefix="/api/videos", tags=["?곸긽 ?앹꽦"])


# ============================================
# ?붿껌/?묐떟 紐⑤뜽
# ============================================
class VideoGenerateResponse(BaseModel):
    """?곸긽 ?앹꽦 ?붿껌 ?묐떟"""
    execution_id: str
    status: str
    message: str


class WorkflowStatusResponse(BaseModel):
    """?뚰겕?뚮줈???곹깭 ?묐떟"""
    execution_id: str
    status: str
    current_stage: Optional[str]
    progress_percentage: int
    output_video_url: Optional[str]
    error_message: Optional[str]
    created_at: str
    completed_at: Optional[str]


# ============================================
# 1. ?곸긽 ?쒖옉 ?붿껌 ?붾뱶?ъ씤??# ============================================
@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: Request,
    # ?꾩닔 ?꾨뱶
    company_name: str = Form(...),
    product_name: str = Form(...),
    product_category: str = Form(...),
    product_highlight: str = Form(...),
    character_tone: str = Form(...),
    
    # ?뚯씪 ?낅줈??    character_image: UploadFile = File(...),
    character_voice: UploadFile = File(...),
    product_images: List[UploadFile] = File(...),
    
    # ?좏깮 ?꾨뱶
    meme_id: Optional[int] = Form(None),
    reference_notes: Optional[str] = Form(None),
    
    # DB
    db: Session = Depends(get_db)
):
    """
    ?곸긽 ?쒖옉 ?붿껌 API
    
    ?묒뾽 ?댁슜 1踰? POST /api/videos/generate ?붾뱶?ъ씤??援ы쁽
    
    **?꾩닔 ?낅젰:**
    - company_name: ?뚯궗 ?대쫫
    - product_name: ?쒗뭹 ?대쫫
    - product_category: ?쒗뭹 移댄뀒怨좊━
    - product_highlight: ?쒗뭹 媛뺤“臾멸뎄
    - character_tone: 罹먮┃??留먰닾(??
    - meme_id: 諛?ID
    - character_image: 罹먮┃???대?吏 ?뚯씪
    - character_voice: 罹먮┃???뚯꽦 ?뚯씪
    - product_images: ?쒗뭹 ?대?吏 ?뚯씪 (理쒕? 3??
    
    **?좏깮 ?낅젰:**
    - reference_notes: 李멸퀬 ?ы빆
    
    **?묐떟:**
    - job_id: ?묒뾽 怨좎쑀 ID (UUID)
    - status: ?묒뾽 ?곹깭
    - estimated_duration_seconds: ?덉긽 ?뚯슂 ?쒓컙
    """
    
    # 1. ?ъ슜???몄쬆 ?뺤씤
    await auth_middleware_v2(request)
    user_info = request.state.user
    user_id = user_info["user_id"]
    company_id = user_info["company_id"]
    
    # 2. ?붿껌 ?곗씠??寃利?(?묒뾽 ?댁슜 1踰?
    
    # 2-1. ?쒗뭹 ?대?吏 媛쒖닔 ?뺤씤 (理쒕? 3??
    if len(product_images) > 3:
        raise HTTPException(
            status_code=400,
            detail="?쒗뭹 ?대?吏??理쒕? 3?κ퉴吏 ?낅줈??媛?ν빀?덈떎"
        )
    
    # 2-2. 罹먮┃???대?吏 寃利?    char_img_content = await character_image.read()
    is_valid, error_msg = validate_character_image(
        character_image.filename,
        len(char_img_content)
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"罹먮┃???대?吏: {error_msg}")
    
    # 2-3. 罹먮┃???뚯꽦 寃利?    char_voice_content = await character_voice.read()
    is_valid, error_msg = validate_character_voice(
        character_voice.filename,
        len(char_voice_content)
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"罹먮┃???뚯꽦: {error_msg}")
    
    # 2-4. ?쒗뭹 ?대?吏 寃利?    product_img_contents = []
    for prod_img in product_images:
        content = await prod_img.read()
        is_valid, error_msg = validate_product_image(prod_img.filename, len(content))
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"?쒗뭹 ?대?吏: {error_msg}")
        product_img_contents.append((prod_img.filename, content))
    
    # 3. 以묐났 ?뺤씤 (DMG-AUTO-07) - meme_id媛 ?덉쓣 ?뚮쭔
    if meme_id:
        existing_workflow = check_duplicate_workflow(db, company_id, product_name, meme_id)
        if existing_workflow:
            raise HTTPException(
                status_code=409,
                detail=f"?숈씪???쒗뭹怨?諛덉쑝濡?吏꾪뻾 以묒씤 ?묒뾽???덉뒿?덈떎. Execution ID: {existing_workflow.execution_id}"
            )
    
    # 4. S3 ?뚯씪 ?낅줈??(?묒뾽 ?댁슜 2踰?
    try:
        # 4-1. 罹먮┃???대?吏 ?낅줈??        char_img_url = upload_file_to_s3(
            char_img_content,
            "character_image",
            company_id,
            character_image.filename,
            character_image.content_type
        )
        
        # 4-2. 罹먮┃???뚯꽦 ?낅줈??        char_voice_url = upload_file_to_s3(
            char_voice_content,
            "character_voice",
            company_id,
            character_voice.filename,
            character_voice.content_type
        )
        
        # 4-3. ?쒗뭹 ?대?吏 ?낅줈??        product_img_urls = []
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
            detail=f"?뚯씪 ?낅줈???ㅽ뙣: {str(e)}"
        )
    
    # 5. ?낅젰 ?뚮씪誘명꽣 援ъ꽦 (?묒뾽 ?댁슜 3踰?
    input_params = {
        "company_name": company_name,
        "product_name": product_name,
        "product_category": product_category,
        "product_highlight": product_highlight,
        "character_tone": character_tone,
        "meme_id": meme_id,
        "reference_notes": reference_notes,
        # S3 ?뚯씪 寃쎈줈??input_params?????        "character_image_url": char_img_url,
        "character_voice_url": char_voice_url,
        "product_images": product_img_urls
    }
    
    # 6. ?뚰겕?뚮줈???앹꽦 (?묒뾽 ?댁슜 3踰?
    workflow = create_workflow(
        db=db,
        user_id=user_id,
        company_id=company_id,
        input_params=input_params,
        meme_id=meme_id,
        workflow_type="video"
    )
    
    # 7. 鍮꾨룞湲??묒뾽 ?쒖옉 (?묒뾽 ?댁슜 4踰?
    # TODO: Celery ?쒖뒪???쒖옉
    # from generation.tasks import generate_video_task
    # generate_video_task.delay(str(workflow.execution_id))
    
    # 8. ?묐떟 諛섑솚
    return VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        status=workflow.status,
        message="?곸긽 ?앹꽦 ?붿껌???묒닔?섏뿀?듬땲?? Execution ID濡?吏꾪뻾 ?곹솴???뺤씤?섏꽭??"
    )


# ============================================
# 2. ?뚰겕?뚮줈???곹깭 議고쉶
# ============================================
@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def get_video_status(
    execution_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ?곸긽 ?앹꽦 ?곹깭 議고쉶
    
    **寃쎈줈 ?뚮씪誘명꽣:**
    - execution_id: ?묒뾽 怨좎쑀 ID (UUID)
    
    **?묐떟:**
    - ?묒뾽 ?곹깭, 吏꾪뻾瑜? 異쒕젰 ?곸긽 URL ??    """
    
    # 1. ?ъ슜???몄쬆
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 2. Execution ID 寃利?    try:
        exec_uuid = uuid.UUID(execution_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="?좏슚?섏? ?딆? Execution ID ?뺤떇?낅땲??)
    
    # 3. ?뚰겕?뚮줈??議고쉶
    workflow = get_workflow_by_id(db, exec_uuid)
    if not workflow:
        raise HTTPException(status_code=404, detail="?대떦 Execution ID瑜?李얠쓣 ???놁뒿?덈떎")
    
    # 4. 沅뚰븳 ?뺤씤 (?먯떊???묒뾽留?議고쉶 媛??
    if workflow.user_id != user_info["user_id"] and user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="?묎렐 沅뚰븳???놁뒿?덈떎")
    
    # 5. Pre-signed URL ?앹꽦 (異쒕젰 ?곸긽???덈뒗 寃쎌슦)
    output_url = None
    if workflow.output_result and workflow.output_result.get("video_url"):
        try:
            output_url = generate_presigned_url(workflow.output_result["video_url"], expiration=7*24*3600)  # 7??        except:
            output_url = workflow.output_result.get("video_url")
    
    # 6. ?묐떟 諛섑솚
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
# 3. ?ъ슜?먯쓽 ?뚰겕?뚮줈??紐⑸줉 議고쉶
# ============================================
@router.get("/my-videos", response_model=List[WorkflowStatusResponse])
async def get_my_videos(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    ???곸긽 ?쒖옉 ?대젰 議고쉶
    
    **荑쇰━ ?뚮씪誘명꽣:**
    - limit: 議고쉶 媛쒖닔 (湲곕낯 10媛?
    
    **?묐떟:**
    - ?뚰겕?뚮줈??紐⑸줉
    """
    
    # 1. ?ъ슜???몄쬆
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 2. ?뚰겕?뚮줈??紐⑸줉 議고쉶
    workflows = get_workflows_by_user(db, user_info["user_id"], limit)
    
    # 3. ?묐떟 蹂??    result = []
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
