"""영상 프로젝트 관련 엔드포인트 (생성, 상세, 삭제)"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, BackgroundTasks
from sqlalchemy.orm import Session

from .common import (
    logger,
    video_crud,
    get_current_user,
    get_presigned_url,
    get_db,
    settings,
    WorkflowExecution,
    AIPipelineClient,
    upload_file_to_s3,
    validate_product_image,
    VideoGenerateResponse,
)

router = APIRouter()


@router.get("/{ad_id}")
async def get_video_detail(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 상세 정보 조회"""
    user_info = await get_current_user(request)

    # AdRequest 조회
    ad_request = video_crud.get_ad_request_by_id(db, ad_id)
    if not ad_request:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    # 권한 확인 (Admin이 아닌 경우)
    if user_info.get("account_type") != 'admin':
        if ad_request.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    logger.info(f"[VIDEO DETAIL] ad_id={ad_id}, ad_request.status={ad_request.status}")

    # Workflow 조회
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.ad_id == ad_id
    ).first()

    # 시나리오 조회
    from app.models.scenario import ScenarioScript

    # 테이블에 실제로 존재하는 컬럼만 조회
    try:
        scenario = db.query(ScenarioScript).filter(
            ScenarioScript.ad_id == ad_id
        ).first()
    except Exception as e:
        logger.warning(f"시나리오 조회 실패 (ad_id={ad_id}): {str(e)}")
        scenario = None

    # 영상 조회
    from app.models.video import Video
    video = db.query(Video).filter(
        Video.ad_id == ad_id
    ).first()

    # 캐릭터 조회
    character = None
    if ad_request.character_id:
        character = video_crud.get_character_by_id(db, ad_request.character_id)

    return {
        "ad_id": ad_request.ad_id,
        "character_id": ad_request.character_id,
        "character_image_url": get_presigned_url(character.image_url) if character and character.image_url else None,
        "voice_sample_url": get_presigned_url(character.voice_sample_url) if character and character.voice_sample_url else None,
        "company_name": ad_request.company.company_name if ad_request.company else None,
        "item_name": ad_request.item_name,
        "item_category": ad_request.item_category,
        "item_description": ad_request.item_description,  # item_keymessage -> item_description
        "item_url": ad_request.item_url,
        "item_images": [get_presigned_url(img) for img in (ad_request.item_images or [])],
        "character_image_prompt": ad_request.character_image_prompt or (character.image_prompt if character else None),
        "character_voice_prompt": ad_request.character_voice_prompt or (character.voice_design_prompt if character else None),
        "character_revision_history": (character.review_result or {}).get('history', []) if character else [],
        "status": ad_request.status,
        "created_at": ad_request.created_at.isoformat(),
        "workflow": {
            "execution_id": str(workflow.execution_id) if workflow else None,
            "status": workflow.status if workflow else None,
            "current_stage": workflow.current_stage if workflow else None,
            "progress_percentage": workflow.progress_percentage if workflow else 0,
            "error_message": workflow.error_message if workflow else None
        } if workflow else None,
        "scenario": {
            "script_id": scenario.script_id if scenario else None,
            "title": scenario.title if scenario else None,
            "description": scenario.description if scenario else None,
            "approval_status": scenario.approval_status if scenario else None
        } if scenario else None,
        "video": {
            "video_id": video.video_id if video else None,
            "s3_url": get_presigned_url(video.s3_url) if video and video.s3_url else None,
            "thumbnail_url": video.thumbnail_url if video else None,
            "duration_seconds": video.duration_seconds if video else None,
            "status": video.status if video else None
        } if video else None
    }


@router.delete("/{ad_id}")
async def delete_video_project(
    ad_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """영상 프로젝트 삭제"""
    user_info = await get_current_user(request)

    ad_request = video_crud.get_ad_request_by_id(db, ad_id)
    if not ad_request:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    if user_info.get("account_type") != 'admin':
        if ad_request.company_id != user_info.get("company_id"):
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    video_crud.delete_ad_request(db, ad_id)
    return {"message": "영상이 삭제되었습니다"}


@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    request: Request,
    background_tasks: BackgroundTasks,
    product_name: str = Form(...),
    product_category: str = Form(...),
    product_description: str = Form(...),  # product_highlight -> product_description
    character_id: Optional[int] = Form(None),
    character_image_prompt: Optional[str] = Form(None),
    character_voice_prompt: Optional[str] = Form(None),
    character_style: Optional[str] = Form(None),  # 프론트엔드: character_style
    character_style_raw: Optional[str] = Form(None),  # 레거시 호환
    product_image: Optional[UploadFile] = File(None),  # 프론트엔드: product_image (단수)
    product_images: Optional[List[UploadFile]] = File(None),  # 레거시 호환 (복수)
    product_url: Optional[str] = Form(None),  # 프론트엔드: product_url
    item_url: Optional[str] = Form(None),  # 레거시 호환
    meme_id: Optional[int] = Form(None),
    character_choice: str = Form(...),  # existing | new
    force_new_character: Optional[bool] = Form(False),
    notes: Optional[str] = Form(None),  # 프론트엔드: notes
    reference_notes: Optional[str] = Form(None),  # 레거시 호환
    product_highlight: Optional[str] = Form(None),  # 레거시 호환 (구 필드명)
    db: Session = Depends(get_db)
):
    """영상 제작 요청"""
    user_info = await get_current_user(request)

    # 필드 통합 (프론트엔드 vs 레거시)
    final_image_prompt = character_image_prompt or character_style or character_style_raw
    final_item_url = product_url or item_url
    final_voice_prompt = character_voice_prompt or notes or reference_notes
    final_description = product_description or product_highlight  # 새 필드 우선, 레거시 호환

    # 이미지 파일 수집 (단수/복수 모두 처리)
    all_images = []
    if product_image:
        all_images.append(product_image)
    if product_images:
        all_images.extend(product_images)

    # 제품 이미지 S3 업로드
    image_urls = []
    for img in all_images:
        # 파일 읽기
        file_content = await img.read()
        file_size = len(file_content)

        # 파일 검증
        is_valid, error_msg = validate_product_image(img.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # S3 업로드
        try:
            s3_url = upload_file_to_s3(
                file_content=file_content,
                file_type="product_image",
                company_id=user_info["company_id"],
                filename=img.filename,
                content_type=img.content_type
            )
            image_urls.append(s3_url)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"이미지 업로드 실패: {str(e)}"
            )

    # 캐릭터 선택 강제
    normalized_choice = (character_choice or "").strip().lower()
    if normalized_choice not in ("existing", "new"):
        raise HTTPException(
            status_code=400,
            detail="character_choice must be one of: existing, new",
        )
    if normalized_choice == "existing":
        if not character_id or character_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="character_id is required when character_choice=existing",
            )
        force_new_character = False
        character_id_value = character_id
        # 기존 캐릭터의 음성/이미지 설정을 우선 사용
        character = video_crud.get_character_by_id(db, character_id_value)
        if not character:
            raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")
        if not character.elevenlabs_voice_id:
            raise HTTPException(status_code=400, detail="선택한 캐릭터에 음성이 없습니다")
        if not final_image_prompt:
            final_image_prompt = character.image_prompt
        final_voice_prompt = character.voice_design_prompt
    else:
        # new
        force_new_character = True
        character_id_value = None

    # 0을 None으로 변환 (외래키 제약 조건 위반 방지)
    meme_id_value = meme_id if meme_id and meme_id > 0 else None

    # AdRequest 생성
    ad_request = video_crud.create_ad_request(
        db=db,
        company_id=user_info["company_id"],
        account_id=user_info["account_id"],
        item_name=product_name,
        item_category=product_category,
        item_description=final_description,  # product_highlight -> final_description
        item_url=final_item_url,
        item_images=image_urls,
        character_id=character_id_value,
        character_image_prompt=final_image_prompt,
        meme_id=meme_id_value,
        character_voice_prompt=final_voice_prompt
    )

    # WorkflowExecution 생성
    workflow = video_crud.create_workflow(
        db=db,
        ad_id=ad_request.ad_id,
        company_id=user_info["company_id"],
        account_id=user_info["account_id"],
        meme_id=meme_id_value
    )

    # 워크플로우 단계 초기화
    video_crud.initialize_workflow_stages(db, workflow.execution_id)

    # === 즉시 응답 반환 (백그라운드에서 캐릭터/음성 생성) ===
    response = VideoGenerateResponse(
        execution_id=str(workflow.execution_id),
        ad_id=ad_request.ad_id,
        status=workflow.status,
        message="영상 생성 요청이 접수되었습니다"
    )

    # === 백그라운드에서 자동 캐릭터/음성 생성 시작 ===
    # 기존 캐릭터 선택 시에는 생성 트리거하지 않음
    if normalized_choice == "new" and (final_image_prompt or final_voice_prompt):
        background_tasks.add_task(
            _generate_character_and_voice_background,
            ad_id=ad_request.ad_id,
            final_image_prompt=final_image_prompt,
            final_voice_prompt=final_voice_prompt,
            user_info=user_info,
            force_new_character=bool(force_new_character),
        )

    return response


def _generate_character_and_voice_background(
    ad_id: int,
    final_image_prompt: Optional[str],
    final_voice_prompt: Optional[str],
    user_info: dict,
    force_new_character: bool = False,
):
    """백그라운드에서 캐릭터와 음성 생성 (동기 함수, 새 DB 세션 사용)"""
    import asyncio

    # 새로운 이벤트 루프 생성
    asyncio.run(_generate_character_and_voice_background_impl(
        ad_id=ad_id,
        final_image_prompt=final_image_prompt,
        final_voice_prompt=final_voice_prompt,
        user_info=user_info
    ))


async def _generate_character_and_voice_background_impl(
    ad_id: int,
    final_image_prompt: Optional[str],
    final_voice_prompt: Optional[str],
    user_info: dict,
    force_new_character: bool = False,
):
    """백그라운드에서 캐릭터와 음성 생성 (새 DB 세션 사용)"""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        logger.info(f"[백그라운드] DB 세션 생성 완료 (ad_id={ad_id})")

        ad_request = video_crud.get_ad_request_by_id(db, ad_id)
        if not ad_request:
            logger.error(f"AdRequest를 찾을 수 없음 (ad_id={ad_id})")
            return
        video_crud.update_ad_status(db, ad_id, 'generating_character', 'character_generation')
        video_crud.update_workflow_progress(db, ad_id, 10, 'character_generation')

        ai_client = AIPipelineClient()

        # 1. 캐릭터 이미지 생성
        use_product_context = not (final_image_prompt and final_image_prompt.strip())
        char_result = await ai_client.generate_character_image(
            character_prompt=final_image_prompt or "",
            character_name=f"Ad_{ad_request.ad_id}_Character",
            company_id=user_info["company_id"],
            aspect_ratio="9:16",
            product_name=ad_request.item_name if use_product_context else None,
            product_category=ad_request.item_category if use_product_context else None,
            product_description=ad_request.item_description if use_product_context else None,
        )

        image_url = char_result.get('image_url')
        if not image_url:
            video_crud.update_ad_status(db, ad_id, 'failed')
            logger.error(f"캐릭터 이미지 생성 결과에 image_url 없음 (ad_id={ad_id})")
            return


        image_prompt = final_image_prompt or char_result.get('image_prompt')
        voice_design_prompt = final_voice_prompt or char_result.get('voice_design_prompt') or final_image_prompt
        if not voice_design_prompt:
            voice_design_prompt = 'A clear, neutral voice.'

        ad_request.character_image_prompt = image_prompt
        ad_request.character_voice_prompt = voice_design_prompt

        # 캐릭터 DB 저장
        video_crud.enforce_character_slot_limit(db, user_info["company_id"], max_active=5)
        character = video_crud.create_company_character(
            db=db,
            company_id=user_info["company_id"],
            image_url=image_url,
            image_prompt=image_prompt,
            image_model=char_result.get('model', 'gemini'),
            voice_design_prompt=voice_design_prompt,
        )

        ad_request.character_id = character.character_id
        db.commit()

        video_crud.update_workflow_progress(db, ad_id, 20, 'voice_generation')

        # 2. 음성 디자인 생성
        sample_text = (
            "안녕하세요, 저는 이 광고의 캐릭터입니다. "
            "오늘 여러분께 정말 좋은 제품을 소개해 드리려고 해요. "
            "이 제품은 여러분의 일상을 더욱 편리하고 즐겁게 만들어 줄 거예요. 지금 바로 확인해 보세요!"
        )
        if len(voice_design_prompt) < 20:
            voice_design_prompt = voice_design_prompt + ", 자연스럽고 친근한 목소리"
        voice_result = await ai_client.generate_voice(
            text=sample_text,
            voice_description=voice_design_prompt,
            character_id=character.character_id,
            company_id=user_info["company_id"]
        )

        voice_id = voice_result.get('voice_id')
        voice_sample_url = voice_result.get('voice_url')
        if not voice_id:
            video_crud.update_ad_status(db, ad_id, 'failed')
            logger.error(f"음성 디자인 생성 결과에 voice_id 없음 (ad_id={ad_id})")
            return

        character.elevenlabs_voice_id = voice_id
        if voice_sample_url:
            character.voice_sample_url = voice_sample_url
        db.commit()

        # 상태를 검수 대기로 변경
        video_crud.update_ad_status(db, ad_id, 'pending_approval', 'character_review')
        video_crud.update_workflow_progress(db, ad_id, 30, 'character_review')

        logger.info(f"자동 캐릭터/음성 생성 완료 (ad_id={ad_id})")

    except Exception as e:
        logger.error(f"자동 캐릭터/음성 생성 실패 (ad_id={ad_id}): {str(e)}")
        try:
            video_crud.update_ad_status(db, ad_id, 'failed')
        except Exception:
            logger.error(f"상태 업데이트 실패 (ad_id={ad_id})")
    finally:
        db.close()
