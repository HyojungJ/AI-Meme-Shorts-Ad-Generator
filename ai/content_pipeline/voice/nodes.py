import logging
import os
import re
import secrets
from functools import lru_cache
from openai import OpenAI

from content_pipeline.types import StepResult

logger = logging.getLogger(__name__)

from content_pipeline.voice.config import load_voice_config
from content_pipeline.db import (
    load_elevenlabs_voice_id,
    load_clone_prompt_url,
    update_elevenlabs_voice_id,
    update_generation_metadata,
    upsert_voice_generation,
    _maybe_presign_s3_url,
)
from content_pipeline.voice.service import VoiceService, VoiceSettings
from content_pipeline.voice.client_qwen import get_qwen_client
from content_pipeline.voice.state import VoiceState


def _strip_emotion_tags(text: str) -> str:
    """대사에서 감정 태그 (화남), (웃으며) 등을 제거하고 공백을 정리한다."""
    cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", text)
    return cleaned.strip()


@lru_cache(maxsize=1)
def _get_service() -> VoiceService:
    config = load_voice_config()
    return VoiceService(config)


def _build_settings(settings_data: dict | None) -> VoiceSettings:
    """
    튜닝 파라미터가 많고 재사용성이 높아 VoiceSettings 타입을 사용하며,
    외부 입력은 dict 형태로 전달되므로 dict → VoiceSettings 변환 로직이 필요
    """
    if not settings_data:
        return VoiceSettings()
    allowed = VoiceSettings.__dataclass_fields__.keys()
    filtered = {k: v for k, v in settings_data.items() if k in allowed}
    return VoiceSettings(**filtered)


def _resolve_provider(state: VoiceState) -> str:
    settings_data = state.get("settings") or {}
    provider = (
        settings_data.get("provider")
        or os.getenv("VOICE_PROVIDER", "qwen")
        or "qwen"
    )
    return provider



def design_voice_node(state: VoiceState) -> dict:
    provider = _resolve_provider(state)
    if provider == "elevenlabs":
        return design_voice_node_elevenlabs(state)
    if provider == "qwen":
        return design_voice_node_qwen(state)
    return {"status": "failed", "error": f"unsupported provider: {provider}"}


def generate_voice_node(state: VoiceState) -> dict:
    provider = _resolve_provider(state)
    if provider == "elevenlabs":
        return generate_voice_node_elevenlabs(state)
    if provider == "qwen":
        return generate_voice_node_qwen(state)
    return {"status": "failed", "error": f"unsupported provider: {provider}"}


# ====== 1. ellevenlabs ======
def design_voice_node_elevenlabs(state: VoiceState) -> dict:
    """
    ElevenLabs Voice Design 노드
    - 사용자가 입력한 설명과 텍스트를 바탕으로 음성 디자인을 생성하고 음성을 생성
    - 필수 입력값: text, voice_name, voice_description
    - 반환값: 생성된 voice_id
    """
    text = (state.get("text") or "").strip()
    design_text = (state.get("design_text") or "").strip() or text
    voice_name = (state.get("voice_name") or "").strip()
    voice_description = (state.get("voice_description") or "").strip()
    preview_index = state.get("preview_index", 0)
    ttv_model_id = (state.get("ttv_model_id") or "").strip() or None

    # 필수 입력값 확인
    if not text:
        return {"status": "failed", "error": "text is required"}
    if not voice_name:
        return {"status": "failed", "error": "voice_name is required"}
    if not voice_description:
        return {"status": "failed", "error": "voice_description is required"}

    # 보이스 디자인 및 생성 시도
    try:
        service = _get_service()
        voice_id = service.design_and_create_voice(
            voice_name=voice_name,
            voice_description=voice_description,
            text=design_text,
            preview_index=preview_index,
            model_id=ttv_model_id,
        )
        response = {"status": "ok", "voice_id": voice_id}
        try:
            character_id = state.get("character_id")
            if character_id:
                update_elevenlabs_voice_id(character_id, voice_id)
        except Exception as exc:
            logger.warning("DB write failed in design_voice_node_elevenlabs: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def generate_voice_node_elevenlabs(state: VoiceState) -> dict:
    """
    ElevenLabs TTS 노드
    - 사용자가 입력한 텍스트와 기존 voice_id를 바탕으로 최종 음성 파일을 생성 및 저장
    - 필수 입력값: text, voice_id
    - 반환값: 생성된 오디오 URL 및 메타데이터
    """
    text = _strip_emotion_tags(state.get("text") or "")
    voice_id = (state.get("voice_id") or "").strip()
    if not voice_id:
        character_id = state.get("character_id")
        if character_id:
            voice_id = load_elevenlabs_voice_id(character_id)
    user_id = (state.get("user_id") or "").strip() or None
    settings = _build_settings(state.get("settings"))

    # 필수 입력값 확인
    if not text:
        return {"status": "failed", "error": "text is required"}
    if not voice_id:
        return {"status": "failed", "error": "voice_id is required"}

    # 음성 생성 시도
    try:
        service = _get_service()
        result = service.generate_voice(
            text=text,
            voice_id=voice_id,
            user_id=user_id,
            settings=settings,
        )
        # 로컬 스토리지 모드에서 실행 시 로컬 경로를 대체 URL로 사용
        audio_url = result.audio_url or _maybe_presign_s3_url(result.storage_path)
        response = {
            "status": "ok",
            "audio_url": audio_url,
            "storage_path": result.storage_path,
            "duration_seconds": result.duration_seconds,
            "size_bytes": result.size_bytes,
            "created_at": result.created_at,
            "text_hash": result.text_hash,
        }
        try:
            character_id = state.get("character_id")
            scene_key = state.get("scene_key")
            scene_number = state.get("scene_number")
            if not scene_key and scene_number is not None:
                scene_key = f"scene_{scene_number:02d}"
            script_id = state.get("script_id")
            if not character_id or not scene_key:
                missing = []
                if not character_id:
                    missing.append("character_id")
                if not scene_key:
                    missing.append("scene_key")
                response["db_error"] = f"missing required fields: {', '.join(missing)}"
                return response
            # 추적 가능성을 위해 음성 생성 상세 정보 저장
            voice_gen_id = upsert_voice_generation(
                character_id=character_id,
                script_id=script_id,
                scene_key=scene_key,
                text_content=text,
                text_hash=result.text_hash,
                audio_url=audio_url,
                duration_seconds=result.duration_seconds,
                size_bytes=result.size_bytes,
                settings={
                    "provider": "elevenlabs",
                    **settings.__dict__,
                },
            )
            response["db_voice_gen_id"] = voice_gen_id
            if not script_id:
                return response
        except Exception as exc:
            logger.warning("DB write failed in generate_voice_node_elevenlabs: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


# ====== 2. qwen ======
def design_voice_node_qwen(state: VoiceState) -> dict:
    """
    Qwen3 Design-Then-Clone 노드
    1. VoiceDesign 모델로 참조 오디오 생성
    2. Base 모델로 clone prompt 추출
    3. clone prompt를 safetensors로 S3 업로드
    4. DB 업데이트 (voice_id + clone_prompt_url)
    """
    import time

    text = (state.get("text") or "").strip()
    design_text = (state.get("design_text") or "").strip() or text
    voice_name = (state.get("voice_name") or "").strip()
    voice_description = (state.get("voice_description") or "").strip()

    if not text:
        return {"status": "failed", "error": "text is required"}
    if not voice_name:
        return {"status": "failed", "error": "voice_name is required"}
    if not voice_description:
        return {"status": "failed", "error": "voice_description is required"}

    try:
        service = _get_service()
        qwen_client = get_qwen_client()
        config = load_voice_config()
        qwen_params = qwen_client.resolve_params(state, "qwen3:clone")

        # 1. VoiceDesign 모델로 참조 오디오 생성
        design_model_id = qwen_params["design_model_id"]
        wavs, sample_rate = qwen_client.generate_audio(
            model_id=design_model_id,
            text=design_text,
            language=qwen_params["language"],
            instruct=voice_description,
        )
        ref_wav = wavs[0]

        # 2. 참조 오디오를 S3에 업로드 (voice_sample_url)
        voice_id = qwen_client.build_voice_id(
            voice_name=voice_name,
            voice_description=voice_description,
            model_id=config.qwen_tts_base_model_id,
        )

        ref_temp_path = qwen_client.write_wav(ref_wav, sample_rate, temp_dir=config.temp_dir)
        try:
            preview_result = service.upload_audio_file(
                temp_path=ref_temp_path,
                voice_id=voice_id,
                text=design_text,
                user_id=state.get("user_id"),
            )
        finally:
            if ref_temp_path.exists():
                ref_temp_path.unlink()

        # 3. Base 모델로 clone prompt 생성
        clone_prompt_items = qwen_client.create_clone_prompt(
            ref_wav, sample_rate, ref_text=design_text,
        )

        # 4. clone prompt를 safetensors로 저장 → S3 업로드
        prompt_temp_path = qwen_client.save_clone_prompt(
            clone_prompt_items, temp_dir=config.temp_dir,
        )
        try:
            timestamp = int(time.time())
            prompt_key = f"clone_prompts/{voice_id.replace(':', '_')}_{timestamp}.safetensors"
            prompt_upload = service.storage.upload_file(
                prompt_temp_path,
                key=prompt_key,
                metadata={"voice_id": voice_id, "type": "clone_prompt"},
            )
            clone_prompt_url = prompt_upload.url
        finally:
            if prompt_temp_path.exists():
                prompt_temp_path.unlink()

        # 5. DB 업데이트
        response = {
            "status": "ok",
            "voice_id": voice_id,
            "voice_sample_url": preview_result.audio_url,
            "voice_sample_storage_path": preview_result.storage_path,
            "voice_sample_duration_seconds": preview_result.duration_seconds,
            "clone_prompt_url": clone_prompt_url,
        }

        try:
            character_id = state.get("character_id")
            if character_id:
                update_elevenlabs_voice_id(character_id, voice_id)
                update_generation_metadata(character_id, {
                    "clone_prompt_url": clone_prompt_url,
                    "clone_ref_text": design_text,
                    "clone_mode": "design_then_clone",
                })
        except Exception as exc:
            logger.warning("DB write failed in design_voice_node_qwen: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


_ALLOWED_S3_HOSTS = {
    "s3.amazonaws.com",
    "s3.ap-northeast-2.amazonaws.com",
}


def _download_clone_prompt(clone_prompt_url: str, temp_dir) -> "Path":
    """S3/presigned URL에서 safetensors 다운로드."""
    import shutil
    import tempfile as _tf
    import urllib.error
    import urllib.parse
    import urllib.request
    from pathlib import Path as _Path

    url = _maybe_presign_s3_url(clone_prompt_url)

    if url.startswith("http"):
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname and not any(parsed.hostname.endswith(h) for h in _ALLOWED_S3_HOSTS):
            raise ValueError(f"Disallowed host for clone prompt: {parsed.hostname}")

        _Path(temp_dir).mkdir(parents=True, exist_ok=True)
        try:
            with _tf.NamedTemporaryFile(dir=temp_dir, suffix=".safetensors", delete=False) as tmp:
                resp = urllib.request.urlopen(url, timeout=60)
                shutil.copyfileobj(resp, tmp)
                dest = _Path(tmp.name)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Failed to download clone prompt: HTTP {e.code}") from e

        if dest.stat().st_size == 0:
            raise RuntimeError("Downloaded clone prompt file is empty")
        return dest

    # 로컬 파일 경로 (파이프라인 자체가 생성한 경로만 허용)
    return _Path(url)


def generate_voice_node_qwen(state: VoiceState) -> dict:
    """
    Qwen3 TTS 노드
    - clone 경로만 사용 (Base 모델 + clone prompt로 음성 생성)
    """
    text = _strip_emotion_tags(state.get("text") or "")
    voice_id = (state.get("voice_id") or "").strip()
    if not voice_id:
        character_id = state.get("character_id")
        if character_id:
            voice_id = load_elevenlabs_voice_id(character_id)
    user_id = (state.get("user_id") or "").strip() or None
    settings_data = state.get("settings") or {}
    if not text:
        return {"status": "failed", "error": "text is required"}
    if not voice_id:
        return {"status": "failed", "error": "voice_id is required"}

    try:
        service = _get_service()
        qwen_client = get_qwen_client()
        config = load_voice_config()
        qwen_params = qwen_client.resolve_params(state, voice_id)

        clone_prompt_url = (state.get("clone_prompt_url") or "").strip()
        if not clone_prompt_url:
            character_id = state.get("character_id")
            if character_id:
                clone_prompt_url = load_clone_prompt_url(character_id)
        if not clone_prompt_url:
            return {"status": "failed", "error": "clone_prompt_url is required for clone mode"}

        # S3에서 safetensors 다운로드 → clone prompt 복원
        prompt_temp_path = _download_clone_prompt(clone_prompt_url, config.temp_dir)
        try:
            clone_prompt_items = qwen_client.load_clone_prompt(prompt_temp_path)
        finally:
            # 다운로드한 임시 파일 정리
            if str(prompt_temp_path).startswith(str(config.temp_dir)) and prompt_temp_path.exists():
                prompt_temp_path.unlink()

        result = service.qwen_clone_generate_and_upload(
            base_model_id=qwen_params["base_model_id"],
            text=text,
            language=qwen_params["language"],
            clone_prompt_items=clone_prompt_items,
            voice_id=voice_id,
            user_id=user_id,
        )
        model_id = qwen_params["base_model_id"]

        audio_url = result.audio_url or _maybe_presign_s3_url(result.storage_path)
        response = {
            "status": "ok",
            "audio_url": audio_url,
            "storage_path": result.storage_path,
            "duration_seconds": result.duration_seconds,
            "size_bytes": result.size_bytes,
            "created_at": result.created_at,
            "text_hash": result.text_hash,
        }
        try:
            character_id = state.get("character_id")
            scene_key = state.get("scene_key")
            scene_number = state.get("scene_number")
            if not scene_key and scene_number is not None:
                scene_key = f"scene_{scene_number:02d}"
            script_id = state.get("script_id")
            if not character_id or not scene_key:
                missing = []
                if not character_id:
                    missing.append("character_id")
                if not scene_key:
                    missing.append("scene_key")
                response["db_error"] = f"missing required fields: {', '.join(missing)}"
                return response
            voice_gen_id = upsert_voice_generation(
                character_id=character_id,
                script_id=script_id,
                scene_key=scene_key,
                text_content=text,
                text_hash=result.text_hash,
                audio_url=audio_url,
                duration_seconds=result.duration_seconds,
                size_bytes=result.size_bytes,
                settings={
                    "provider": "qwen3",
                    "voice_id": voice_id,
                    "model_id": model_id,
                    "language": qwen_params["language"],
                    "raw_settings": settings_data,
                },
            )
            response["db_voice_gen_id"] = voice_gen_id
            if not script_id:
                return response
        except Exception as exc:
            logger.warning("DB write failed in generate_voice_node_qwen: %s", exc)
            response["status"] = "partial"
            response["db_error"] = str(exc)
        return response
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

def convert_to_tts_node(dialogue: str) -> str:
    """
    (감정) 대사 → [tag] 대사 변환
    
    Example:
        >>> convert_to_tts_prompt("(기쁨) 오늘 날씨가 정말 좋네!")
        "[excited] 오늘 날씨가 정말 좋네!"
    """
    text = (dialogue or "").strip()
    if not text:
        return ""

    service = _get_service()
    config = service.config
    client = OpenAI(api_key=config.openai_api_key)

    prompt = f"""다음 대사를 ElevenLabs v3 형식으로 변환하세요.

규칙:
- (감정) 제거하고 영어 태그로 변환
- 대사 내용은 절대 변경 금지
- 한 줄로만 출력

예시:
입력: (기쁨) 오늘 날씨가 정말 좋네!
출력: [excited] 오늘 날씨가 정말 좋네!

입력: (슬픔) 이제 정말 끝인가봐...
출력: [sad] 이제 정말 끝인가봐...

입력: {dialogue}
출력:"""
    
    response = client.chat.completions.create(
        model=config.openai_model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200
    )
    
    return response.choices[0].message.content.strip().split('\n')[0]


# scenario: dict  # 또는 ScenarioOutput - 시나리오 데이터
# total_duration: float  # 시나리오의 총 길이 (초)
# bgm_asset_id: int  # DB 저장 후 반환되는 asset_id
# state에 추가해야 되는 것들.
def generate_bgm_node(state: VoiceState) -> dict:
    """elevenlabs의 뮤직 생성 모델에 들어갈 프롬프트를 생성하는 노드"""
    import json
    import tempfile
    from pathlib import Path
    from datetime import datetime, timezone
    from langchain_openai import ChatOpenAI
    from elevenlabs.client import ElevenLabs
    from content_pipeline.voice.prompts.generate_music_prompt import GENERATE_MUSIC_PROMPT_TEMPLATE_V2
    from content_pipeline.db import upsert_scene_assets

    service = _get_service()
    config = service.config

    # 1. 시나리오 확인
    scenario = state.get("scenario")
    if not scenario:
        return {"status": "failed", "error": "scenario is required"}
    
    # 2. Pydantic 모델을 dict로 변환 후 JSON 문자열로
    if hasattr(scenario, 'model_dump'):
        scenario_json = json.dumps(scenario.model_dump(), ensure_ascii=False, indent=2)
    else:
        scenario_json = json.dumps(scenario, ensure_ascii=False, indent=2)

    # 3. 프롬프트 생성
    prompt = GENERATE_MUSIC_PROMPT_TEMPLATE_V2.format(scenario_json=scenario_json)

    # 4. LLM 호출해서 음악 프롬프트 생성
    llm = ChatOpenAI(temperature=0.7, model=config.openai_model_id, openai_api_key=config.openai_api_key)
    music_prompt_response = llm.invoke(prompt)
    music_prompt = music_prompt_response.content.strip()

    # 5. 음악 길이 계산 (총 duration을 ms단위로.)
    music_length_ms = int(state["total_duration"] * 1000)

    try:
        # 6. ElevenLabs Music API 호출
        elevenlabs = ElevenLabs(
            api_key=config.elevenlabs_music_api_key
        )
        track = elevenlabs.music.compose(
            prompt=music_prompt, 
            music_length_ms=music_length_ms
        )

        # 7. 임시 파일로 저장
        config.temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=config.temp_dir, 
            suffix=".mp3", 
            delete=False
        ) as tmp:
            for chunk in track:
                tmp.write(chunk)
            temp_path = Path(tmp.name)

        # 8. 메타데이터 생성
        script_id = state.get("script_id")
        created_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "type": "bgm",
            "script_id": script_id or "unknown",
            "music_prompt": music_prompt,
            "duration_ms": music_length_ms,
        }

        # 9. S3 또는 로컬 스토리지에 업로드 (config에 따라 자동 선택)
        key = f"bgm/{script_id}/{created_at.replace(':', '')}.mp3"
        storage_result = service.storage.upload_file(
            temp_path, 
            key=key, 
            metadata=metadata
        )

        # 10. 임시 파일 삭제
        if temp_path.exists():
            temp_path.unlink()

        # 11. DB에 저장 (scene_assets 테이블)
        try:
            asset_id = upsert_scene_assets(
                script_id=script_id,
                scene_key="bgm",  # BGM 전용 특수 키
                audio_url=storage_result.url,
                audio_duration_seconds=music_length_ms / 1000,
                audio_storage_path=storage_result.storage_path,
                character_image_url=None,
                character_image_storage_path=None,
                scene_video_url=None,
                scene_video_storage_path=None,
                scene_video_duration=None,
                generation_model="elevenlabs_music",
                generation_cost=None,
            )
            return {
                "status": "ok",
                "bgm_asset_id": asset_id,
            }
        except Exception as db_exc:
            return {
                "status": "failed", 
                "error": f"DB save failed: {str(db_exc)}"
            }

    except Exception as exc:
        return {"status": "failed", "error": f"BGM generation failed: {str(exc)}"}

