"""캐릭터 음성 관련 엔드포인트"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
import httpx

from app.core.constants import ApprovalStatus
from .common import (
    logger,
    video_crud,
    get_current_user,
    get_db,
    settings,
    AIPipelineClient,
    VoiceGenerateRequest,
    VoiceGenerateResponse,
    VoicePreviewResponse,
    VoiceApprovalRequest,
    ApprovalResponse,
    VoiceReviseRequest,
)

router = APIRouter()


async def _rewrite_voice_description(original_prompt: str, revision_notes: str) -> str:
    """원본 영문 voice description + 한국어 피드백 -> 새 영문 voice description 생성."""
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You rewrite an ElevenLabs voice description based on user feedback. "
                "Output ONLY the new English voice description (1-2 sentences). "
                "Fully replace conflicting attributes (e.g. if feedback says 'male voice', "
                "change gender/tone entirely instead of appending)."
            )},
            {"role": "user", "content": (
                f"Original description:\n{original_prompt}\n\n"
                f"User feedback (may be Korean):\n{revision_notes}\n\n"
                "Rewritten description:"
            )},
        ],
        temperature=0.3,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


@router.post("/characters/{character_id}/voice/generate", response_model=VoiceGenerateResponse)
async def generate_character_voice(
    character_id: int,
    request: Request,
    voice_request: VoiceGenerateRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 음성 생성 (AI 파이프라인 호출)"""
    user_info = await get_current_user(request)

    # 캐릭터 조회 및 권한 확인
    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    try:
        # AI 파이프라인에 음성 생성 요청
        ai_client = AIPipelineClient()
        result = await ai_client.generate_voice(
            text=voice_request.sample_text,
            voice_description=voice_request.voice_description or "neutral voice",
            character_id=character_id,
            company_id=user_info["company_id"]
        )

        # AI 파이프라인 응답에서 음성 URL 추출
        voice_url = result.get('voice_url')
        voice_id = result.get('voice_id')  # ElevenLabs voice_id
        duration_seconds = result.get('duration_seconds', 0)
        size_bytes = result.get('size_bytes', 0)
        created_at = result.get('created_at', datetime.utcnow().isoformat())

        # DB에 음성 정보 업데이트
        character.elevenlabs_voice_id = voice_id
        character.voice_design_prompt = voice_request.voice_description
        character.updated_at = datetime.utcnow()
        db.commit()

        return VoiceGenerateResponse(
            character_id=character_id,
            voice_url=voice_url,
            voice_id=voice_id,
            duration_seconds=duration_seconds,
            size_bytes=size_bytes,
            created_at=created_at,
            message="음성이 생성되었습니다"
        )

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI 파이프라인 통신 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"음성 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/characters/{character_id}/voice", response_model=VoicePreviewResponse)
async def get_character_voice(
    character_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """캐릭터 음성 미리듣기"""
    user_info = await get_current_user(request)

    # 캐릭터 조회 및 권한 확인
    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    # 음성 생성 이력 조회 (voice_generations 테이블)
    from app.models.asset import VoiceGeneration

    voice_gen = db.query(VoiceGeneration).filter(
        VoiceGeneration.character_id == character_id
    ).order_by(VoiceGeneration.created_at.desc()).first()

    if not voice_gen or not voice_gen.audio_url:
        raise HTTPException(status_code=404, detail="생성된 음성이 없습니다")

    return VoicePreviewResponse(
        character_id=character_id,
        voice_url=voice_gen.audio_url,
        voice_design_prompt=character.voice_design_prompt,
        duration_seconds=voice_gen.duration_seconds,
        created_at=voice_gen.created_at.isoformat()
    )


@router.post("/characters/{character_id}/voice/approve", response_model=ApprovalResponse)
async def approve_character_voice(
    character_id: int,
    request: Request,
    approval: VoiceApprovalRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 음성 승인"""
    user_info = await get_current_user(request)

    # 캐릭터 조회 및 권한 확인
    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    if approval.approved:
        # 캐릭터 활성화 (이미지 + 음성 모두 승인됨)
        character.is_active = True
        character.updated_at = datetime.utcnow()
        db.commit()

        return ApprovalResponse(
            character_id=character_id,
            status=ApprovalStatus.APPROVED,
            message="캐릭터 음성이 승인되었습니다. 캐릭터가 활성화되었습니다."
        )
    else:
        return ApprovalResponse(
            character_id=character_id,
            status=ApprovalStatus.REJECTED,
            message="캐릭터 음성이 거부되었습니다."
        )


@router.post("/characters/{character_id}/voice/revise", response_model=VoiceGenerateResponse)
async def revise_character_voice(
    character_id: int,
    request: Request,
    revise_request: VoiceReviseRequest,
    db: Session = Depends(get_db)
):
    """캐릭터 음성 수정 요청"""
    user_info = await get_current_user(request)

    # 캐릭터 조회 및 권한 확인
    character = video_crud.get_character_by_id(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다")

    if character.company_id != user_info["company_id"]:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    try:
        # 피드백 이력 누적 저장
        revision_notes = revise_request.get_revision_notes()
        existing_review = character.review_result or {}
        history = existing_review.get('history', [])
        history.append({
            'feedback_type': 'voice_revision',
            'revision_notes': revision_notes,
            'requested_at': datetime.utcnow().isoformat()
        })
        character.review_result = {
            'history': history,
            'latest_feedback_type': 'voice_revision',
            'latest_revision_notes': revision_notes,
            'revision_count': len(history),
        }

        # AI 파이프라인에 음성 재생성 요청
        ai_client = AIPipelineClient()

        # 원본 프롬프트 보존 (최초 1회만 저장, API 호출 전에 commit)
        metadata = character.generation_metadata or {}
        if 'original_voice_prompt' not in metadata:
            metadata['original_voice_prompt'] = character.voice_design_prompt
            character.generation_metadata = metadata
            db.commit()

        # 원본 영문 프롬프트 + 한국어 피드백 -> LLM으로 새 영문 voice description 생성
        original_prompt = metadata.get('original_voice_prompt') or character.voice_design_prompt or ""
        voice_description = await _rewrite_voice_description(original_prompt, revision_notes)

        # 샘플 텍스트가 제공되지 않으면 기본 텍스트 사용 (ElevenLabs 최소 100자 요구)
        sample_text = revise_request.sample_text or "안녕하세요, 저는 활기차고 밝은 캐릭터입니다. 오늘도 좋은 하루 보내세요! 여러분과 함께하는 이 시간이 정말 즐겁습니다. 매일매일 새로운 이야기를 들려드릴게요. 앞으로도 많은 응원 부탁드립니다. 감사합니다!"

        result = await ai_client.generate_voice(
            text=sample_text,
            voice_description=voice_description,
            character_id=character_id,
            company_id=user_info["company_id"]
        )

        # AI 파이프라인 응답에서 음성 URL 추출
        voice_url = result.get('voice_url')
        voice_id = result.get('voice_id')
        duration_seconds = result.get('duration_seconds', 0)
        size_bytes = result.get('size_bytes', 0)
        created_at = result.get('created_at', datetime.utcnow().isoformat())

        # DB에 음성 정보 업데이트
        character.elevenlabs_voice_id = voice_id
        character.voice_design_prompt = voice_description
        if voice_url:
            character.voice_sample_url = voice_url
        character.updated_at = datetime.utcnow()
        db.commit()

        return VoiceGenerateResponse(
            character_id=character_id,
            voice_url=voice_url,
            voice_id=voice_id,
            duration_seconds=duration_seconds,
            size_bytes=size_bytes,
            created_at=created_at,
            message="음성이 재생성되었습니다"
        )

    except Exception as e:
        logger.error(f"음성 재생성 중 오류 (character_id={character_id}): {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"음성 재생성 중 오류가 발생했습니다: {str(e)}"
        )
