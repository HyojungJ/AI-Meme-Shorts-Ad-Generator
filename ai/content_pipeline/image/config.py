import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ImageStorageConfig:
    """이미지 저장소 설정"""
    backend: str            # 저장소 종류 (예: local, s3)   
    base_dir: Path          # 로컬 저장소의 기본 디렉토리
    public_base_url: str    # 공개 접근을 위한 기본 URL
    s3_bucket: str          # S3 버킷 이름
    s3_region: str          # S3 리전
    prefix: str             # 저장소 내 경로 접두사 (설정 이유: 파일 구분 용이)


@dataclass(frozen=True)
class ImageConfig:
    """이미지 파이프라인 설정"""
    openai_api_key: str            # OpenAI API 키 (검증/LLM 용도)
    api_key: str                    # 이미지 생성 API 키
    model_name: str                 # 사용할 이미지 생성 모델 이름
    output_dir: Path                # 생성된 이미지의 출력 디렉토리
    temp_dir: Path                  # 임시 파일 저장 디렉토리
    max_retries: int                # 최대 재시도 횟수
    base_sleep: float               # 기본 대기 시간
    max_sleep: float                # 최대 대기 시간
    storage: ImageStorageConfig     # 이미지 저장소 설정


def load_image_config() -> ImageConfig:
    """환경 변수에서 이미지 파이프라인 설정 로드"""
    base_dir = Path(os.getenv("NANO_BANANA_OUTPUT_DIR", "data/images"))
    return ImageConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        api_key=os.getenv("NANO_BANANA_API_KEY", ""),
        model_name=os.getenv("NANO_BANANA_MODEL", "gemini-2.0-flash-image-preview"),
        output_dir=base_dir,
        temp_dir=Path(os.getenv("NANO_BANANA_TEMP_DIR", "data/images/tmp")),
        max_retries=int(os.getenv("NANO_BANANA_MAX_RETRIES", "5")),
        base_sleep=float(os.getenv("NANO_BANANA_BASE_SLEEP_SEC", "1.0")),
        max_sleep=float(os.getenv("NANO_BANANA_MAX_SLEEP_SEC", "8.0")),
        # 이미지 파일 저장소 설정
        storage=ImageStorageConfig(
            backend=os.getenv("NANO_BANANA_STORAGE_BACKEND", "local"),
            base_dir=base_dir,
            public_base_url=os.getenv("NANO_BANANA_PUBLIC_BASE_URL", ""),
            s3_bucket=os.getenv("NANO_BANANA_S3_BUCKET", ""),
            s3_region=os.getenv("NANO_BANANA_S3_REGION", ""),
            prefix=os.getenv("NANO_BANANA_STORAGE_PREFIX", ""),
        ),
    )
