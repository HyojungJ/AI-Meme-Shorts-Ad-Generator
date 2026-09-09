import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class VoiceStorageConfig:
    """음성 파일 저장소 설정"""
    backend: str            # 저장소 종류 (예: local, s3)   
    base_dir: Path          # 로컬 저장소의 기본 디렉토리
    public_base_url: str    # 공개 접근을 위한 기본 URL
    s3_bucket: str          # S3 버킷 이름
    s3_region: str          # S3 리전


@dataclass(frozen=True)
class VoiceConfig:
    """음성 생성 서비스 전체 설정"""
    # ====== 1. ellevenlabs ======
    openai_api_key: str             # OpenAI API 키
    openai_model_id: str            # OpenAI model ID
    elevenlabs_api_key: str         # ElevenLabs API 키
    elevenlabs_model_id: str        # 사용할 음성 TTS 모델 ID (기본값: eleven_v3)
    elevenlabs_ttv_model_id: str    # 사용할 보이스 TTV 모델 ID (기본값: multilingual_ttv_v2)
    elevenlabs_output_format: str   # 출력 오디오 포맷
    elevenlabs_music_api_key: str   # ElevenLabs Music API 키
    elevenlabs_max_custom_voices: int | None  # 음성 커스텀 최대 개수
    # ====== 2. qwen ======
    qwen_tts_voice_design_model_id: str     # Qwen3 VoiceDesign model ID
    qwen_tts_base_model_id: str             # Qwen3 Base model ID (voice clone용)
    qwen_tts_device: str                    # Qwen3 TTS device (cpu, cuda:0, auto)
    qwen_tts_dtype: str                     # Qwen3 TTS dtype (float32, float16, bfloat16)
    qwen_tts_attn_impl: str                 # Qwen3 attention implementation
    qwen_tts_seed: int                      # Qwen3 TTS seed (fixed for determinism)
    temp_dir: Path                          # 임시 파일 저장 디렉토리
    storage: VoiceStorageConfig             # 음성 파일 저장소 설정


def load_voice_config() -> VoiceConfig:
    """환경 변수에서 음성 생성 설정 로드"""
    base_dir = Path(os.getenv("VOICE_STORAGE_BASE_DIR", "data/voice"))
    return VoiceConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        elevenlabs_model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        elevenlabs_ttv_model_id=os.getenv("ELEVENLABS_TTV_MODEL_ID","eleven_multilingual_ttv_v2",),
        elevenlabs_output_format=os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
        elevenlabs_music_api_key=os.getenv("ELEVENLABS_MUSIC_API_KEY", ""),
        elevenlabs_max_custom_voices=int(v) if (v := os.getenv("ELEVENLABS_MAX_CUSTOM_VOICES", "").strip()) else None,
        qwen_tts_voice_design_model_id=os.getenv(
            "QWEN_TTS_VOICE_DESIGN_MODEL_ID",
            "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        ),
        qwen_tts_base_model_id=os.getenv(
            "QWEN_TTS_BASE_MODEL_ID",
            "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        ),
        qwen_tts_device=os.getenv("QWEN_TTS_DEVICE", "auto"),
        qwen_tts_dtype=os.getenv("QWEN_TTS_DTYPE", "bfloat16"),
        qwen_tts_attn_impl=os.getenv("QWEN_TTS_ATTN_IMPL", "flash_attention_2"),
        qwen_tts_seed=int(os.getenv("QWEN_TTS_SEED", "42")),
        temp_dir=Path(os.getenv("VOICE_TEMP_DIR", "data/voice/tmp")),
        # 음성 파일 저장소 설정
        storage=VoiceStorageConfig(
            backend=os.getenv("VOICE_STORAGE_BACKEND", "local"),
            base_dir=base_dir,
            public_base_url=os.getenv("VOICE_PUBLIC_BASE_URL", ""),
            s3_bucket=os.getenv("VOICE_S3_BUCKET", ""),
            s3_region=os.getenv("VOICE_S3_REGION", ""),
        ),
    )
