"""캐릭터 관련 엔드포인트"""
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import httpx

from app.core.constants import ApprovalStatus
from .common import (
    logger,
    video_crud,
    get_current_user,
    get_presigned_url,
    get_db,
    AIPipelineClient,
    CharacterListResponse,
    CharacterPreviewResponse,
    CharacterPromptSuggestRequest,
    CharacterPromptSuggestResponse,
    CharacterGenerateRequest,
    CharacterGenerateResponse,
    ApprovalRequest,
    ApprovalResponse,
    CharacterReviseRequest,
    CharacterRegenerateResponse,
)

router = APIRouter()


@router.get("/characters", response_model=List[CharacterListResponse])
async def get_company_characters(
    request: Request,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """회사 캐릭터 목록 조회 (이미지가 있는 캐릭터만 반환)"""
    user_info = await get_current_user(request)

    characters = video_crud.get_characters_by_company(
        db,
        user_info["company_id"],
        active_only=active_only
    )

    result = []
    for char in characters:
        if not char.image_url:
            continue
        presigned = get_presigned_url(char.image_url)
        image_url = presigned or char.image_url
        result.append(CharacterListResponse(
            character_id=char.character_id,
            image_url=image_url,
            is_active=char.is_active,
            created_at=char.created_at.isoformat() if char.created_at else "",
            image_prompt=char.image_prompt
        ))
    return result


@router.get("/character/{character_id}", response_model=CharacterPreviewResponse)
async def get_character_preview(
    character_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """캐릭터 미리보기 조회"""
    user_info = await get_current_user(request)

    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    # 권한 확인
    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    return CharacterPreviewResponse(
        character_id=character.character_id,
        image_url=character.image_url,
        voice_url=None,  # TODO: 음성 생성 후 URL 추가
        is_active=character.is_active,
        created_at=character.created_at.isoformat(),
        image_prompt=character.image_prompt,
        voice_design_prompt=character.voice_design_prompt
    )


@router.post("/character/{character_id}/approve", response_model=ApprovalResponse)
async def approve_character(
    character_id: int,
    approval: ApprovalRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """캐릭터 승인/거부"""
    user_info = await get_current_user(request)

    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    # 권한 확인
    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    if approval.approved:
        video_crud.activate_character(db, character_id)
        status = ApprovalStatus.APPROVED
        message = "캐릭터가 승인되었습니다"
    else:
        video_crud.deactivate_character(db, character_id)
        status = ApprovalStatus.REJECTED
        message = "캐릭터가 거부되었습니다"

    # 피드백이 있으면 저장 (TODO: feedback 테이블에 저장)
    if approval.feedback:
        # 향후 feedback 테이블 구현 시 저장
        pass

    return ApprovalResponse(
        character_id=character_id,
        status=status,
        message=message
    )


@router.post("/character/{character_id}/revise", response_model=CharacterRegenerateResponse)
async def revise_character_image(
    character_id: int,
    request: Request,
    revise_request: CharacterReviseRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 이미지 수정 요청 (재생성)"""
    user_info = await get_current_user(request)

    # 캐릭터 조회 및 권한 확인
    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    try:
        # 피드백 이력 누적 저장
        existing_review = character.review_result or {}
        history = existing_review.get('history', [])
        history.append({
            'feedback_type': 'image_revision',
            'revision_notes': revise_request.revision_notes,
            'requested_at': datetime.utcnow().isoformat()
        })
        character.review_result = {
            'history': history,
            'latest_feedback_type': 'image_revision',
            'latest_revision_notes': revise_request.revision_notes,
            'revision_count': len(history),
        }

        # AI 파이프라인에 이미지 재생성 요청
        ai_client = AIPipelineClient()

        # 원본 프롬프트 보존 (최초 1회만 저장)
        metadata = character.generation_metadata or {}
        if 'original_image_prompt' not in metadata:
            metadata['original_image_prompt'] = character.image_prompt
            character.generation_metadata = metadata

        # 새 프롬프트가 제공되면 사용, 아니면 원본 프롬프트 + 최신 피드백
        if revise_request.character_prompt:
            final_prompt = revise_request.character_prompt
        else:
            original_prompt = metadata.get('original_image_prompt') or character.image_prompt or "character image"
            final_prompt = f"{original_prompt}. Revision: {revise_request.revision_notes}"

        result = await ai_client.generate_character_image(
            character_prompt=final_prompt,
            character_name=f"Character_{character_id}",
            company_id=user_info["company_id"],
            aspect_ratio="1:1"
        )

        # AI 파이프라인 응답에서 이미지 URL 추출
        image_url = result.get('image_url')
        size_bytes = result.get('size_bytes', 0)
        created_at = result.get('created_at', datetime.utcnow().isoformat())

        # DB에 캐릭터 이미지 업데이트
        character.image_url = image_url
        character.image_prompt = final_prompt
        character.updated_at = datetime.utcnow()
        db.commit()

        return CharacterRegenerateResponse(
            character_id=character_id,
            image_url=image_url,
            size_bytes=size_bytes,
            created_at=created_at,
            message="캐릭터 이미지가 재생성되었습니다"
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI 파이프라인 통신 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 재생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/characters/prompts", response_model=CharacterPromptSuggestResponse)
async def suggest_character_prompts(
    request: Request,
    payload: CharacterPromptSuggestRequest,
):
    """제품 정보 기반 캐릭터 프롬프트 추천"""
    await get_current_user(request)

    ai_client = AIPipelineClient()
    result = await ai_client.suggest_character_prompts_from_product(
        item_name=payload.product_name,
        item_category=payload.product_category,
        item_description=payload.product_description,
    )

    image_prompt = (
        result.get("character_image_prompt")
        or result.get("character_prompt")
        or ""
    )
    voice_prompt = (
        result.get("character_voice_prompt")
        or result.get("voice_description")
        or ""
    )

    if not image_prompt or not voice_prompt:
        raise HTTPException(status_code=502, detail="프롬프트 추천 실패")

    return CharacterPromptSuggestResponse(
        character_image_prompt=image_prompt,
        character_voice_prompt=voice_prompt,
    )


@router.post("/characters/generate", response_model=CharacterGenerateResponse)
async def generate_character_image(
    request: Request,
    character_request: CharacterGenerateRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 이미지 생성 (AI 파이프라인 호출)"""
    user_info = await get_current_user(request)

    try:
        # AI 파이프라인에 이미지 생성 요청
        ai_client = AIPipelineClient()
        result = await ai_client.generate_character_image(
            character_prompt=character_request.character_prompt,
            character_name=f"Character_{user_info['company_id']}",  # 임시 이름
            company_id=user_info["company_id"],
            aspect_ratio=character_request.aspect_ratio
        )

        # AI 파이프라인 응답에서 이미지 URL 추출
        image_url = result.get('image_url')
        image_path = result.get('image_path', image_url)
        size_bytes = result.get('size_bytes', 0)
        created_at = result.get('created_at', datetime.utcnow().isoformat())

        # DB에 캐릭터 저장
        character = video_crud.create_company_character(
            db=db,
            company_id=user_info["company_id"],
            image_url=image_url,
            image_prompt=character_request.character_prompt,
            image_model=result.get('model', 'imagen-3.0')
        )

        return CharacterGenerateResponse(
            character_id=character.character_id,
            image_url=image_url,
            image_path=image_path,
            size_bytes=size_bytes,
            created_at=created_at,
            message="캐릭터 이미지가 생성되었습니다"
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI 파이프라인 통신 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 생성 중 오류가 발생했습니다: {str(e)}"
        )
