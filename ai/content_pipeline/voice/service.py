import hashlib
import logging
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from mutagen.mp3 import MP3

import requests

from content_pipeline.voice.config import VoiceConfig
from content_pipeline.voice.client import ElevenLabsClient, VoiceCreateResponse, VoiceDesignResponse
from content_pipeline.voice.storage import LocalStorageBackend, S3StorageBackend, VoiceStorageBackend
from content_pipeline.voice.client_qwen import get_qwen_client

logger = logging.getLogger(__name__)

# --- 1. 에러 타입 세분화 (재시도) ---
class VoiceNodeError(Exception):
    """기본 음성 노드 에러"""
    pass

class VoiceRetryableError(VoiceNodeError):
    """네트워크 장애 등 재시도 시 성공 가능성이 있는 에러"""
    pass

class VoiceFatalError(VoiceNodeError):
    """설정 오류, 권한 부족 등 재시도해도 실패할 에러"""
    pass

# --- 2. 데이터 모델 강화 ---
@dataclass(frozen=True)
class VoiceSettings:
    """튜닝 파라미터가 많고 재사용성이 높아 VoiceSettings 타입 사용"""
    stability: float = 0.5
    similarity_boost: float = 0.5
    style: float = 0.0
    use_speaker_boost: bool = True
    speed: float = 1.0

@dataclass(frozen=True)
class VoiceNodeOutput:
    """통합 파이프라인(State)에 전달될 최종 결과물"""
    voice_id: str
    audio_url: str
    storage_path: str
    duration_seconds: float  # 영상 합성을 위해 추가
    size_bytes: int
    created_at: str
    text_hash: str

# --- 3. 핵심 서비스 (Node) ---
class VoiceService:
    """
    음성 생성 및 관리 서비스
    1. 음성 디자인 생성
    2. 음성 생성 및 등록
    3. 통합 관리
    4. 최종 오디오 합성 및 저장s
    """
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.client = ElevenLabsClient(
            api_key=config.elevenlabs_api_key,
            model_id=config.elevenlabs_model_id,
        )
        self.storage = self._build_storage_backend(config)

    def design_voice(
        self,
        *,
        voice_description: str,
        text: str,
        model_id: Optional[str] = None,
    ) -> VoiceDesignResponse:
        """
        1. 음성 디자인 생성
        - 사용자가 입력한 설명과 텍스트를 바탕으로 음성 디자인을 생성하고 미리보기 오디오 반환
        - voice_description: 음성에 대한 설명
        - text: 음성 디자인에 사용할 샘플 텍스트
        - model_id: 사용할 음성 모델 ID (기본값은 config의 elevenlabs_ttv_model_id)
        - 반환: 디자인된 음성의 미리보기 오디오 및 메타데이터
        - 예외 처리: 네트워크 오류 등 재시도 가능한 에러는 VoiceRetryableError로 래핑
        """
        model_id = model_id or self.config.elevenlabs_ttv_model_id
        try:
            return self.client.text_to_voice_design(
                model_id=model_id,
                voice_description=voice_description,
                text=text,
            )
        except (requests.RequestException, RuntimeError) as exc:
            raise VoiceRetryableError(f"Voice design failed: {exc}") from exc

    def create_voice(
        self,
        *,
        voice_name: str,
        voice_description: str,
        generated_voice_id: str,
    ) -> VoiceCreateResponse:
        """
        2. 디자인된 음성으로 실제 음성 생성 및 등록
        - 생성된 음성의 고유 ID를 ElevenLabs 보이스 라이브러리에 영구적으로 등록
        - voice_name: 사용자가 지정한 음성 이름
        - voice_description: 음성에 대한 설명
        - generated_voice_id: design_voice에서 반환된 임시 음성 ID
        - 반환: 등록된 음성의 고유 ID 및 메타데이터
        - 예외 처리1: 네트워크 오류 등 재시도 가능한 에러는 VoiceRetryableError 발생
        - 예외 처리2: 텍스트가 비어있는 등 치명적인 에러는 VoiceFatalError 발생
        """
        try:
            self._ensure_voice_quota(required_slots=1)
            result = self.client.text_to_voice_create(
                voice_name=voice_name,
                voice_description=voice_description,
                generated_voice_id=generated_voice_id,
            )
            logger.info("created voice_id=%s", result.voice_id)
            return result
        except (requests.RequestException, RuntimeError) as exc:
            raise VoiceRetryableError(f"Voice create failed: {exc}") from exc

    def design_and_create_voice(
        self,
        *,
        voice_name: str,
        voice_description: str,
        text: str,
        preview_index: int = 0,
        model_id: Optional[str] = None,
    ) -> str:
        design = self.design_voice(
            voice_description=voice_description,
            text=text,
            model_id=model_id,
        )
        """
        3. 통합 관리
        - design_voice+create_voice 과정을 하나로 묶어, 설명 입력부터 최종 ID 발급까지 한 번에 처리
        - preview_index: design_voice에서 반환된 미리보기 오디오 중 선택할 인덱스
        - 반환: 최종 생성된 음성의 고유 ID
        - 예외 처리: 미리보기 오디오가 없거나 인덱스가 범위를 벗어날 경우 VoiceFatalError 발생
        """
        if not design.previews:
            raise VoiceFatalError("No previews returned from voice design.")
        if preview_index < 0 or preview_index >= len(design.previews):
            raise VoiceFatalError("preview_index is out of range.")
        selected = design.previews[preview_index]
        created = self.create_voice(
            voice_name=voice_name,
            voice_description=voice_description,
            generated_voice_id=selected.generated_voice_id,
        )
        return created.voice_id

    def _ensure_voice_quota(self, *, required_slots: int = 1) -> None:
        max_custom = self.config.elevenlabs_max_custom_voices
        if not max_custom or max_custom <= 0 or required_slots <= 0:
            return

        deletable_categories = {"generated", "cloned", "custom"}
        deletable: list[dict] = []
        delete_batch_size = 5

        data = self.client.list_voices(
            voice_type="non-default",
            sort="created_at_unix",
            sort_direction="asc",
            page_size=100,
            include_total_count=False,
        )
        next_token = data.get("next_page_token")

        def _collect(items: list[dict]) -> None:
            for voice in items:
                if not voice.get("is_owner"):
                    continue
                if voice.get("category") not in deletable_categories:
                    continue
                deletable.append(voice)

        _collect(data.get("voices", []) or [])
        while next_token:
            data = self.client.list_voices(
                voice_type="non-default",
                sort="created_at_unix",
                sort_direction="asc",
                page_size=100,
                next_page_token=next_token,
                include_total_count=False,
            )
            _collect(data.get("voices", []) or [])
            next_token = data.get("next_page_token")

        total_deletable = len(deletable)
        delete_count = max(0, total_deletable + required_slots - max_custom)
        if delete_count <= 0:
            return
        if delete_count < delete_batch_size:
            delete_count = delete_batch_size
        if delete_count > total_deletable:
            delete_count = total_deletable

        for voice in deletable[:delete_count]:
            voice_id = voice.get("voice_id")
            if voice_id:
                logger.info("deleting voice_id=%s", voice_id)
                self.client.delete_voice(voice_id=voice_id)

    def generate_voice(
        self,
        text: str,
        voice_id: str,
        user_id: Optional[str] = None,
        settings: Optional[VoiceSettings] = None,
    ) -> VoiceNodeOutput:
        """
        4. 최종 오디오 합성 및 저장
        - 실제 광고 대본(text)과 확정된 voice_id를 결합하여 최종 MP3 파일을 생성 및 저장
        - user_id: 오디오를 생성한 사용자 ID (메타데이터에 포함)
        - settings: 음성 합성에 사용할 세부 설정 (VoiceSettings 객체)
        - 반환: 최종 생성된 오디오의 URL, 저장 경로, 길이, 크기 등 메타데이터를 포함한 VoiceNodeOutput 객체
        - 예외 처리1: 네트워크 오류 등 재시도 가능한 에러는 VoiceRetryableError 발생
        - 예외 처리2: 텍스트가 비어있는 등 치명적인 에러는 VoiceFatalError 발생
        """
        if not text.strip():
            raise VoiceFatalError("No text provided for voice generation.")
        
        current_settings = settings or VoiceSettings()
        
        # 1. ElevenLabs API 호출
        try:
            response = self.client.text_to_speech(
                voice_id=voice_id,
                text=text,
                **current_settings.__dict__,
                output_format=self.config.elevenlabs_output_format,
            )
        except (requests.RequestException, RuntimeError) as e:
            raise VoiceRetryableError(f"failed API : {str(e)}")

        # 2. 임시 파일 생성 및 오디오 정보 추출
        temp_path = self._write_temp_audio(response.audio_bytes)
        try:
            return self._upload_result(
                temp_path=temp_path,
                voice_id=voice_id,
                text=text,
                user_id=user_id,
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def upload_audio_file(
        self,
        *,
        temp_path: Path,
        voice_id: str,
        text: str,
        user_id: Optional[str],
    ) -> VoiceNodeOutput:
        """이미 생성된 오디오 파일을 업로드 파이프라인에 태우기 위한 헬퍼(Qwen WAV 등)."""
        return self._upload_result(
            temp_path=temp_path,
            voice_id=voice_id,
            text=text,
            user_id=user_id,
        )

    def qwen_generate_and_upload(
        self,
        *,
        model_id: str,
        mode: str,
        text: str,
        language: str,
        speaker: str,
        instruct: str,
        voice_id: str,
        user_id: Optional[str],
    ) -> VoiceNodeOutput:
        """Qwen3 TTS 음성 생성 후 업로드."""
        qwen_client = get_qwen_client()
        wavs, sample_rate = qwen_client.generate_audio(
            model_id=model_id,
            mode=mode,
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruct,
        )
        temp_path = qwen_client.write_wav(
            wavs[0],
            sample_rate,
            temp_dir=self.config.temp_dir,
        )
        try:
            return self.upload_audio_file(
                temp_path=temp_path,
                voice_id=voice_id,
                text=text,
                user_id=user_id,
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def qwen_clone_generate_and_upload(
        self,
        *,
        base_model_id: str,
        text: str,
        language: str,
        clone_prompt_items: list,
        voice_id: str,
        user_id: Optional[str],
    ) -> VoiceNodeOutput:
        """Qwen3 TTS clone 모드 음성 생성 후 업로드."""
        qwen_client = get_qwen_client()
        wavs, sample_rate = qwen_client.generate_clone_audio(
            base_model_id=base_model_id,
            text=text,
            language=language,
            clone_prompt_items=clone_prompt_items,
        )
        temp_path = qwen_client.write_wav(
            wavs[0],
            sample_rate,
            temp_dir=self.config.temp_dir,
        )
        try:
            return self.upload_audio_file(
                temp_path=temp_path,
                voice_id=voice_id,
                text=text,
                user_id=user_id,
            )
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _upload_result(
        self,
        *,
        temp_path: Path,
        voice_id: str,
        text: str,
        user_id: Optional[str],
    ) -> VoiceNodeOutput:
        """
        5. 통합 관리
        생성 결과를 스토리지에 업로드하고, 업로드된 영상/메타데이터 정보를 반환
        - 로컬에 생성된 영상 및 메타데이터 파일 로드
        - 스토리지 업로드용 key 생성
        - 영상 파일 업로드
        - 메타데이터에 스토리지 정보 및 접근 URL 반영
        - 업데이트된 메타데이터 파일 업로드
        - 최종 결과 반환        
        """
        duration = _get_audio_duration(temp_path)

        # 4. 메타데이터 및 저장 키 생성
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        created_at = datetime.now(timezone.utc).isoformat()
        metadata = {
            "voice_id": voice_id,
            "user_id": user_id or "anonymous",
            "text_hash": text_hash,
            "duration": str(duration),
        }

        safe_user_id = _sanitize_key_part(metadata["user_id"])
        safe_voice_id = _sanitize_key_part(voice_id)
        suffix = temp_path.suffix or ".mp3"
        key = f"{safe_user_id}/{safe_voice_id}/{created_at.replace(':', '')}_{text_hash}{suffix}"

        # 5. 저장소 업로드
        storage_result = self.storage.upload_file(temp_path, key=key, metadata=metadata)

        return VoiceNodeOutput(
            voice_id=voice_id,
            audio_url=storage_result.url,
            storage_path=storage_result.storage_path,
            duration_seconds=duration,
            size_bytes=storage_result.size_bytes,
            created_at=created_at,
            text_hash=text_hash,
        )

    def _write_temp_audio(self, audio_bytes: bytes, *, suffix: str = ".mp3") -> Path:
        """오디오 바이트를 임시 파일로 저장"""
        self.config.temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=self.config.temp_dir, suffix=suffix, delete=False
        ) as tmp:
            tmp.write(audio_bytes)
            return Path(tmp.name)

    def _build_storage_backend(self, config: VoiceConfig) -> VoiceStorageBackend:
        """저장소 백엔드 생성"""
        backend = config.storage.backend.lower()
        if backend == "s3":
            return S3StorageBackend(
                bucket=config.storage.s3_bucket,
                region=config.storage.s3_region,
                public_base_url=config.storage.public_base_url,
            )
        return LocalStorageBackend(
            base_dir=config.storage.base_dir,
            public_base_url=config.storage.public_base_url,
        )


def _sanitize_key_part(value: str) -> str:
    """스토리지 key에 쓰일 값 정규화(슬래시/콜론 등 위험 문자 제거)"""
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", value.strip())
    return safe or "unknown"


def _get_audio_duration(temp_path: Path) -> float:
    """오디오 길이 계산(MP3는 mutagen, 그 외는 soundfile/librosa fallback)."""
    suffix = temp_path.suffix.lower()
    if suffix == ".mp3":
        audio = MP3(temp_path)
        return float(audio.info.length)
    try:
        import soundfile as sf

        with sf.SoundFile(str(temp_path)) as handle:
            return float(handle.frames) / float(handle.samplerate)
    except (ImportError, RuntimeError, OSError) as exc:
        logger.debug("soundfile failed for %s, falling back to librosa: %s", temp_path, exc)
        import librosa

        return float(librosa.get_duration(path=str(temp_path)))
