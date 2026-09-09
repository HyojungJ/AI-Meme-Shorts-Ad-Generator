import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

from content_pipeline.image.config import load_image_config
from content_pipeline.image.service import ImageService
from content_pipeline.image.state import ImageState
from content_pipeline.db import (
    upsert_image_generation,
    save_verification_result,
    update_company_character_image_url,
    _maybe_presign_s3_url,
)
from content_pipeline.utils import parse_json_from_llm as _parse_json_from_llm

@lru_cache(maxsize=1)
def _get_service() -> ImageService:
    config = load_image_config()
    return ImageService(config)


def generate_character_image_node(state: ImageState) -> dict:
    """
    캐릭터 이미지 생성 노드
    - 사용자가 입력한 캐릭터 설명을 바탕으로 캐릭터 이미지를 생성
    - 필수 입력값: character_prompt
    - 반환값: 생성된 캐릭터 이미지 경로 및 메타데이터
    """
    character_prompt = (state.get("character_prompt") or "").strip()
    character_image_path = (state.get("character_image_path") or "").strip()
    character_image_url = (state.get("character_image_url") or "").strip()
    aspect_ratio = state.get("aspect_ratio") or "9:16"

    # 이미 이미지가 제공된 경우 생성 생략
    if character_image_path or character_image_url:
        return {
            "status": "ok",
            "character_output_path": character_image_path or None,
            "character_image_path": character_image_path or None,
            "character_image_url": character_image_url or None,
        }
    
    # 필수 입력값 확인
    if not character_prompt:
        return {"status": "failed", "error": "character_prompt is required"}
    
    # 보이스 디자인 및 생성 시도
    try:
        service = _get_service()
        output_path = state.get("character_output_path")

        # 출력 경로가 지정되지 않은 경우 기본 경로 생성
        if not output_path and state.get("output_dir"):
            filename = f"character_{int(time.time())}.png"
            output_path = str(Path(state["output_dir"]) / "character_images" / filename)

        # 캐릭터 이미지 생성
        result = service.generate_character_image(
            prompt=character_prompt,
            aspect_ratio=aspect_ratio,
            output_path=output_path,
        )
        response = {
            "status": "ok",
            "character_output_path": result.output_path,
            "character_metadata_path": result.metadata_path,
            "character_image_path": result.output_path,
            "character_image_url": result.image_url,
            "character_metadata_json": result.metadata_json,
            "character_storage_path": result.storage_path,
            "character_storage_backend": service.config.storage.backend,
        }
        try:
            script_id = state.get("script_id")
            character_id = state.get("character_id")
            if not character_id:
                response["db_error"] = "missing required field: character_id"
                return response
            # 재사용 또는 사용자에게 제공을 위해 캐릭터 이미지 생성 결과 저장
            if result.image_url:
                update_company_character_image_url(character_id, result.image_url)
            metadata_payload = dict(result.metadata_json)
            metadata_payload["kind"] = "character"
            image_id = upsert_image_generation(
                character_id=character_id,
                script_id=script_id,
                prompt=character_prompt,
                model=result.model,
                image_url=result.image_url,
                size_bytes=result.size_bytes,
                metadata=metadata_payload,
            )
            response["db_image_id"] = image_id
        except Exception as exc:
            logger.warning("DB write failed in generate_character_image_node: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def generate_scene_image_node(state: ImageState) -> dict:
    """
    장면 이미지 생성 노드
    - 사용자가 입력한 시나리오 프롬프트와 이미지들을 바탕으로 장면 이미지 생성
    - 필수 입력값: scenario_prompt, product_image_path or product_image_url, character
    - 반환값: 생성된 장면 이미지 경로 및 메타데이터
    """
    scenario_prompt = (state.get("scenario_prompt") or state.get("prompt") or "").strip()
    product_image_path = (state.get("product_image_path") or "").strip()
    product_image_url = (state.get("product_image_url") or "").strip()
    character_image_path = (state.get("character_image_path") or "").strip()
    character_image_url = (state.get("character_image_url") or "").strip()
    aspect_ratio = state.get("aspect_ratio") or "9:16"

    # 필수 입력값 확인
    if not scenario_prompt:
        return {"status": "failed", "error": "scenario_prompt is required"}
    if not product_image_path and not product_image_url:
        return {"status": "failed", "error": "product_image_path or product_image_url is required"}
    if not character_image_path and not character_image_url:
        return {"status": "failed", "error": "character_image_path or character_image_url is required"}

    # 씬 이미지 생성 시도
    try:
        service = _get_service()
        output_path = state.get("output_path")

        # 출력 경로가 지정되지 않은 경우 기본 경로 생성
        if not output_path and state.get("output_dir"):
            filename = f"nanobanana_{int(time.time())}.png"
            output_path = str(Path(state["output_dir"]) / filename)

        # 씬 이미지 생성
        result = service.generate_scene_image(
            scenario_prompt=scenario_prompt,
            product_image_path=product_image_path or None,
            product_image_url=product_image_url or None,
            character_image_path=character_image_path or None,
            character_image_url=character_image_url or None,
            aspect_ratio=aspect_ratio,
            output_path=output_path,
        )
        response = {
            "status": "ok",
            "output_path": result.output_path,
            "scene_output_path": result.output_path,
            "metadata_path": result.metadata_path,
            "size_bytes": result.size_bytes,
            "created_at": result.created_at,
            "model": result.model,
            "image_url": result.image_url,
            "metadata_json": result.metadata_json,
            "storage_path": result.storage_path,
            "storage_backend": service.config.storage.backend,
        }
        try:
            script_id = state.get("script_id")
            scene_key = state.get("scene_key")
            scene_number = state.get("scene_number")
            if not scene_key and scene_number is not None:
                scene_key = f"scene_{scene_number:02d}"
            if not script_id or not scene_key:
                missing = []
                if not script_id:
                    missing.append("script_id")
                if not scene_key:
                    missing.append("scene_key")
                response["db_error"] = f"missing required fields: {', '.join(missing)}"
                return response
            # 추후 영상 합성을 위해 씬 단위 이미지 필드 저장
            metadata_payload = dict(result.metadata_json)
            metadata_payload["kind"] = "scene"
            metadata_payload["scene_key"] = scene_key
            image_id = upsert_image_generation(
                character_id=state.get("character_id"),
                script_id=script_id,
                prompt=scenario_prompt,
                model=result.model,
                image_url=result.image_url,
                size_bytes=result.size_bytes,
                metadata=metadata_payload,
            )
            response["db_image_id"] = image_id
        except Exception as exc:
            logger.warning("DB write failed in generate_scene_image_node: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}



def verify_image_modification_node(state: ImageState) -> dict:
    """
    이미지 수정 검증 노드 - GPT-4o Vision 사용
    - 수정 요청이 제대로 반영되었는지 VLM으로 자동 검증
    - 검증 대상: 캐릭터 생김새, 그림체/화풍, 분위기/느낌, 색감/톤
    - 점수 기준: ≥50점 → 사용자에게 제시, <50점 → 자동 재생성 (최대 2회)
    """
    original_image_url = (state.get("original_image_url") or "").strip()
    modified_image_url = (state.get("image_url") or "").strip()
    modification_request = (state.get("modification_request") or "").strip()
    retry_count = state.get("retry_count", 0)

    if not original_image_url:
        return {"status": "failed", "error": "original_image_url is required"}
    if not modified_image_url:
        return {"status": "failed", "error": "modified_image_url (image_url) is required"}
    if not modification_request:
        return {"status": "failed", "error": "modification_request is required"}

    try:
        config = load_image_config()
        client = OpenAI(api_key=config.openai_api_key)

        presigned_original = _maybe_presign_s3_url(original_image_url)
        presigned_modified = _maybe_presign_s3_url(modified_image_url)

        prompt = f"""다음 이미지 수정 요청이 제대로 반영되었는지 평가해주세요.

수정 요청: {modification_request}

평가 기준:
1. 캐릭터 생김새 (얼굴형, 헤어스타일, 눈 모양 등)
2. 그림체/화풍 (애니메이션, 수채화, 사실적 등)
3. 분위기/느낌 (귀여움, 어두움, 몽환적 등)
4. 색감/톤 (따뜻함, 차가움, 채도 등)

응답 형식 (JSON):
{{
    "score": 0-100 사이의 점수,
    "confidence": 0.0-1.0 사이의 신뢰도,
    "analysis": "상세 분석 내용",
    "missing_elements": ["미반영된 요소1", "미반영된 요소2"]
}}"""

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": presigned_original}},
                        {"type": "image_url", "image_url": {"url": presigned_modified}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        result_text = response.choices[0].message.content
        verification_result = _parse_json_from_llm(result_text)
        score = verification_result.get("score", 0)
        confidence = verification_result.get("confidence", 0.0)

        if score >= 50:
            decision = "show_to_user"
            message = f"AI 분석 점수: {score}점. 이대로 괜찮으신가요?"
        else:
            if retry_count >= 2:
                decision = "show_to_user"
                message = f"재생성 한도 초과. AI 분석 점수: {score}점. 이대로 진행하시겠습니까?"
            else:
                decision = "auto_retry"
                message = "수정사항이 충분히 반영되지 않아 자동으로 재생성합니다."

        try:
            character_id = state.get("character_id")
            if character_id:
                save_verification_result(
                    media_type="image",
                    score=score,
                    confidence=confidence,
                    decision=decision,
                    analysis=verification_result.get("analysis", ""),
                    missing_elements=verification_result.get("missing_elements", []),
                    retry_count=retry_count,
                    modification_request=modification_request,
                    character_id=character_id,
                )
        except Exception:
            pass

        return {
            "status": "ok",
            "verification_result": verification_result,
            "decision": decision,
            "message": message,
            "score": score,
            "confidence": confidence,
            "retry_count": retry_count,
        }

    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
