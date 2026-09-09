import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass(frozen=True)
class VideoStorageConfig:
    """비디오 저장소 설정"""
    backend: str                    # 저장소 종류 (예: local, s3)   
    base_dir: Path                  # 로컬 저장소의 기본 디렉토리
    public_base_url: str            # 공개 접근을 위한 기본 URL
    s3_bucket: str                  # S3 버킷 이름
    s3_region: str                  # S3 리전
    prefix: str                     # 저장소 내 경로 접두사 (설정 이유: 파일 구분 용이)


@dataclass(frozen=True)
class VideoConfig:
    """비디오 파이프라인 설정"""
    google_api_key: str             # Google/Gemini API 키
    openai_api_key: str             # OpenAI API 키
    openai_model_id: str            # OpenAI model ID
    mode: str                       # ComfyUI 모드 설정
    comfyui_base_url: str           # ComfyUI 서버 주소
    comfyui_workflow_path: Path     # 워크플로우(JSON) 파일의 경로
    comfy_ssh_host: str             # ComfyUI SSH 호스트
    comfy_ssh_user: str             # ComfyUI SSH 유저
    comfy_ssh_key: str              # ComfyUI SSH 키 경로
    comfy_ssh_port: str             # ComfyUI SSH 포트
    comfy_remote_input_dir: str     # ComfyUI 원격 input 디렉터리
    comfy_remote_output_dir: str    # ComfyUI 원격 output 디렉터리
    comfy_remote_merge_dir: str     # ComfyUI 원격 merge 디렉터리
    runpod_comfy_api_key: str       # RunPod API 키 (Serverless ComfyUI용)
    runpod_comfy_endpoint_id: str   # RunPod 엔드포인트 ID (Serverless ComfyUI용)
    comfyui_poll_interval: float    # 폴링 간격: 서버에 작업 완료 여부를 확인하는 주기 (초 단위)
    comfyui_max_wait: float         # 최대 대기 시간: 영상 생성 완료까지 기다릴 최대 시간 (초 단위, 초과 시 Timeout)
    output_dir: Path                # 비디오 파일이 저장될 디렉토리 경로
    temp_dir: Path                  # 임시 파일(다운로드 이미지 등) 저장 경로
    request_timeout: float          # API 요청 타임아웃
    storage: VideoStorageConfig     # 비디오 저장소 설정


def load_video_config() -> VideoConfig:
    """환경 변수에서 비디오 파이프라인 설정 로드"""
    base_dir = Path(os.getenv("COMFY_OUTPUT_DIR", "data/video"))
    return VideoConfig(
        google_api_key=(
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("NANO_BANANA_API_KEY")
            or ""
        ),
        mode=os.getenv("COMFY_MODE", "mock"),
        comfyui_base_url=os.getenv("COMFY_COMFYUI_BASE_URL", ""),
        comfyui_workflow_path=Path(os.getenv("COMFY_WORKFLOW_PATH", "")),
        comfy_ssh_host=os.getenv("COMFY_SSH_HOST", ""),
        comfy_ssh_user=os.getenv("COMFY_SSH_USER", ""),
        comfy_ssh_key=os.path.expanduser(os.getenv("COMFY_SSH_KEY", "")),
        comfy_ssh_port=os.getenv("COMFY_SSH_PORT", "22"),
        comfy_remote_input_dir=os.getenv("COMFY_REMOTE_INPUT_DIR", ""),
        comfy_remote_output_dir=os.getenv("COMFY_REMOTE_OUTPUT_DIR", ""),
        comfy_remote_merge_dir=os.getenv("COMFY_REMOTE_MERGE_DIR", ""),
        runpod_comfy_api_key=(os.getenv("COMFY_RUNPOD_API_KEY") or os.getenv("RUNPOD_API_KEY") or ""),
        runpod_comfy_endpoint_id=os.getenv("COMFY_RUNPOD_ENDPOINT_ID", ""),
        comfyui_poll_interval=float(os.getenv("COMFY_POLL_INTERVAL_SEC", "2.0")),
        comfyui_max_wait=float(os.getenv("COMFY_MAX_WAIT_SEC", "300")),
        output_dir=base_dir,
        temp_dir=Path(os.getenv("COMFY_TEMP_DIR", "data/video/tmp")),
        request_timeout=float(os.getenv("COMFY_REQUEST_TIMEOUT_SEC", "60")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
        # 이미지 파일 저장소 설정
        storage=VideoStorageConfig(
            backend=os.getenv("COMFY_STORAGE_BACKEND", "local"),
            base_dir=base_dir,
            public_base_url=os.getenv("COMFY_PUBLIC_BASE_URL", ""),
            s3_bucket=os.getenv("COMFY_S3_BUCKET", ""),
            s3_region=os.getenv("COMFY_S3_REGION", ""),
            prefix=os.getenv("COMFY_STORAGE_PREFIX", ""),
        ),
    )
