import hashlib
import logging
import tempfile
import random
from functools import lru_cache
from pathlib import Path
from content_pipeline.voice.config import load_voice_config
from content_pipeline.voice.state import VoiceState

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _get_qwen_model(model_id: str):
    config = load_voice_config()
    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError as exc:
        raise RuntimeError("qwen-tts is required to run Qwen3 TTS.") from exc

    device = (config.qwen_tts_device or "auto").strip()
    default_dtype = "bfloat16" if device.startswith("cuda") else "float32"
    dtype_name = (config.qwen_tts_dtype or default_dtype).strip()
    dtype = getattr(torch, dtype_name, torch.float32)

    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
        default_dtype = "float32"
        dtype_name = (config.qwen_tts_dtype or default_dtype).strip()
        dtype = getattr(torch, dtype_name, torch.float32)

    attn_impl = (config.qwen_tts_attn_impl or "").strip()
    kwargs = {"device_map": device, "dtype": dtype}
    # FlashAttention2가 설치되지 않은 환경에서는 attn_implementation 설정 제외
    if attn_impl and attn_impl.lower() != "flash_attention_2":
        kwargs["attn_implementation"] = attn_impl
    try:
        return Qwen3TTSModel.from_pretrained(model_id, **kwargs)
    except (RuntimeError, ValueError, OSError) as e:
        logger.warning(f"Failed to load model with custom settings: {e}. Trying fallback...")
        # Fallback for environments that don't support custom attention/dtype settings
        return Qwen3TTSModel.from_pretrained(model_id, device_map=device)


class QwenTTSClient:
    def __init__(self) -> None:
        self.config = load_voice_config()

    def build_voice_id(
        self,
        *,
        voice_name: str,
        voice_description: str,
        model_id: str,
    ) -> str:
        seed = f"clone|{voice_name}|{voice_description}|{model_id}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
        return f"qwen3:clone:{digest}"

    def resolve_params(self, state: VoiceState, voice_id: str) -> dict:
        settings_data = state.get("settings") or {}

        language = settings_data.get("qwen_language") or settings_data.get("language") or "Korean"
        design_model_id = (
            settings_data.get("qwen_voice_design_model_id")
            or settings_data.get("qwen_model_id")
            or self.config.qwen_tts_voice_design_model_id
        )
        base_model_id = (
            settings_data.get("qwen_base_model_id")
            or self.config.qwen_tts_base_model_id
        )

        return {
            "language": language,
            "design_model_id": design_model_id,
            "base_model_id": base_model_id,
        }

    def write_wav(self, wav, sample_rate: int, *, temp_dir: Path) -> Path:
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError("soundfile is required to write Qwen3 audio output.") from exc

        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, wav, sample_rate)
            return Path(tmp.name)

    def generate_audio(
        self,
        *,
        model_id: str,
        text: str,
        language: str,
        instruct: str,
    ):
        self._set_seed(self.config.qwen_tts_seed)
        model = _get_qwen_model(model_id)
        return model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct,
        )

    def create_clone_prompt(self, ref_wav, sample_rate: int, ref_text: str) -> list:
        """Base 모델로 참조 오디오에서 clone prompt 생성."""
        base_model_id = self.config.qwen_tts_base_model_id
        model = _get_qwen_model(base_model_id)
        return model.create_voice_clone_prompt((ref_wav, sample_rate), ref_text)

    def save_clone_prompt(self, prompt_items: list, *, temp_dir: Path) -> Path:
        """clone prompt를 safetensors로 직렬화하여 임시 파일에 저장."""
        try:
            import torch
            from safetensors.torch import save_file
        except ImportError as exc:
            raise RuntimeError("safetensors and torch are required for clone prompt serialization.") from exc

        tensors = {}
        metadata = {}

        for i, item in enumerate(prompt_items):
            prefix = f"item_{i}"
            if hasattr(item, "ref_spk_embedding") and item.ref_spk_embedding is not None:
                t = item.ref_spk_embedding
                if not isinstance(t, torch.Tensor):
                    t = torch.tensor(t)
                tensors[f"{prefix}.ref_spk_embedding"] = t.contiguous()
            if hasattr(item, "ref_code") and item.ref_code is not None:
                t = item.ref_code
                if not isinstance(t, torch.Tensor):
                    t = torch.tensor(t)
                tensors[f"{prefix}.ref_code"] = t.contiguous()

            metadata[f"{prefix}.x_vector_only_mode"] = str(
                getattr(item, "x_vector_only_mode", True)
            )
            metadata[f"{prefix}.icl_mode"] = str(
                getattr(item, "icl_mode", False)
            )
            metadata[f"{prefix}.ref_text"] = getattr(item, "ref_text", "") or ""

        metadata["num_items"] = str(len(prompt_items))

        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=".safetensors", delete=False) as tmp:
            save_file(tensors, tmp.name, metadata=metadata)
            return Path(tmp.name)

    def load_clone_prompt(self, file_path: Path) -> list:
        """safetensors 파일에서 clone prompt 복원."""
        try:
            from safetensors.torch import load_file
            from safetensors import safe_open
        except ImportError as exc:
            raise RuntimeError("safetensors is required for clone prompt deserialization.") from exc

        tensors = load_file(str(file_path))
        with safe_open(str(file_path), framework="pt") as f:
            metadata = f.metadata() or {}

        num_items = int(metadata.get("num_items", "1"))

        class _PromptItem:
            pass

        items = []
        for i in range(num_items):
            prefix = f"item_{i}"
            item = _PromptItem()
            item.ref_spk_embedding = tensors.get(f"{prefix}.ref_spk_embedding")
            item.ref_code = tensors.get(f"{prefix}.ref_code")
            item.x_vector_only_mode = metadata.get(f"{prefix}.x_vector_only_mode", "True") == "True"
            item.icl_mode = metadata.get(f"{prefix}.icl_mode", "False") == "True"
            item.ref_text = metadata.get(f"{prefix}.ref_text", "")
            items.append(item)

        return items

    def generate_clone_audio(
        self,
        *,
        base_model_id: str,
        text: str,
        language: str,
        clone_prompt_items: list,
    ):
        """Base 모델 + clone prompt로 음성 생성."""
        self._set_seed(self.config.qwen_tts_seed)
        model = _get_qwen_model(base_model_id)
        return model.generate_voice_clone(
            text=text,
            language=language,
            voice_clone_prompt=clone_prompt_items,
        )

    def _set_seed(self, seed: int) -> None:
        try:
            import numpy as np
        except ImportError:
            np = None

        random.seed(seed)
        if np is not None:
            np.random.seed(seed)

        try:
            import torch
        except ImportError:
            return

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        try:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        except (AttributeError, RuntimeError):
            logger.debug("Could not set cudnn deterministic mode")


@lru_cache(maxsize=1)
def get_qwen_client() -> QwenTTSClient:
    return QwenTTSClient()
