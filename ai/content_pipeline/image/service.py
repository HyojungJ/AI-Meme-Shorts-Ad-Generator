import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from content_pipeline.image.client import ImageClient, ImageGenerationResult
from content_pipeline.image.config import ImageConfig
from content_pipeline.image.storage import (
    ImageStorageBackend,
    LocalStorageBackend,
    S3StorageBackend,
)

# --- 1. 데이터 모델 정의 ---
@dataclass(frozen=True)
class ImageNodeOutput:
    """통합 파이프라인(State)에 전달될 최종 결과물"""
    output_path: str
    metadata_path: str
    image_url: str
    metadata_json: dict[str, Any]
    storage_path: str
    size_bytes: int
    created_at: str
    model: str
    aspect_ratio: str


# --- 2. 핵심 서비스 ---
class ImageService:
    """이미지 생성 및 관리 서비스
    1. 캐릭터 이미지 생성
    2. 장면 이미지 생성
    3. 통합 관리
    """
    def __init__(self, config: ImageConfig):
        self.config = config
        self.client = ImageClient(
            api_key=config.api_key,
            model_name=config.model_name,
        )
        self.storage = self._build_storage_backend(config)

    def generate_character_image(
        self,
        *,
        prompt: str,
        aspect_ratio: str = "9:16",
        output_path: str | None = None,
    ) -> ImageNodeOutput:
        """
        1. 캐릭터 이미지 생성
        - 프롬프트를 기반으로 캐릭터 이미지를 생성하고 저장
        - 반환값: 생성된 이미지와 메타데이터 경로
        """
        if not prompt.strip():
            raise ValueError("character_prompt is required")

        if not output_path:
            filename = f"character_{int(time.time())}.png"
            output_path = str(self.config.output_dir / filename)

        # 프롬프트에 강제 요소 추가 (예: 전신 캐릭터, 투명 배경)
        enforced_prompt = "full body character, transparent background"
        full_prompt = f"{enforced_prompt} {prompt}".strip()

        # 이미지 생성 API 호출
        result = self.client.generate_character_image(
            character_prompt=full_prompt,
            aspect_ratio=aspect_ratio,
            output_path=output_path,
            max_retries=self.config.max_retries,
            base_sleep=self.config.base_sleep,
            max_sleep=self.config.max_sleep,
        )

        return self._upload_result(result)

    def generate_scene_image(
        self,
        *,
        scenario_prompt: str,
        product_image_path: str | None = None,
        product_image_url: str | None = None,
        character_image_path: str | None = None,
        character_image_url: str | None = None,
        aspect_ratio: str = "9:16",
        output_path: str | None = None,
    ) -> ImageNodeOutput:
        """
        2. 씬 이미지 생성
        - 제품 이미지+캐릭터 이미지+프롬프트를 기반으로 캐릭터 이미지를 생성하고 저장
        - 반환값: 생성된 이미지와 메타데이터 경로
        """
        if not scenario_prompt.strip():
            raise ValueError("scenario_prompt is required")
        if not product_image_path and not product_image_url:
            raise ValueError("product_image_path or product_image_url is required")
        if not character_image_path and not character_image_url:
            raise ValueError("character_image_path or character_image_url is required")

        if not output_path:
            filename = f"nanobanana_{int(time.time())}.png"
            output_path = str(self.config.output_dir / filename)

        # 이미지 생성 API 호출
        result = self.client.generate_scene_image(
            scenario_prompt=scenario_prompt,
            product_image_path=product_image_path,
            product_image_url=product_image_url,
            character_image_path=character_image_path,
            character_image_url=character_image_url,
            aspect_ratio=aspect_ratio,
            output_path=output_path,
            temp_dir=self.config.temp_dir,
            max_retries=self.config.max_retries,
            base_sleep=self.config.base_sleep,
            max_sleep=self.config.max_sleep,
        )

        return self._upload_result(result)

    def _upload_result(self, result: ImageGenerationResult) -> ImageNodeOutput:
        """
        3. 통합 관리
        이미지 생성 결과를 스토리지에 업로드하고, 업로드된 이미지/메타데이터 정보를 반환
        - 로컬에 생성된 이미지 및 메타데이터 파일 로드
        - 스토리지 업로드용 key 생성
        - 이미지 파일 업로드
        - 메타데이터에 스토리지 정보 및 접근 URL 반영
        - 업데이트된 메타데이터 파일 업로드
        - 최종 결과 반환        
        """
        # 메타데이터 및 이미지 파일 경로
        metadata_path = Path(result.metadata_path)
        image_path = Path(result.output_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        # output_dir 기준 상대 경로를 스토리지 key로 사용
        # (output_dir 외부에 있을 경우 파일명만 사용)
        try:
            relative_key = image_path.relative_to(self.config.output_dir).as_posix()
        except ValueError:
            relative_key = image_path.name

        # 스토리지 prefix 정리 (앞/뒤 슬래시 제거)
        prefix = self.config.storage.prefix.strip("/")
        # 최종 스토리지 key 구성
        if "character_" in image_path.name:
            relative_key = f"character_images/{image_path.name}"
        else:
            relative_key = f"scene_images/{image_path.name}"
        key = f"{prefix}/{relative_key}" if prefix else relative_key
        # 이미지 파일 업로드
        upload_metadata = metadata
        if self.config.storage.backend.lower() == "s3":
            upload_metadata = {}
        image_upload = self.storage.upload_file(image_path, key=key, metadata=upload_metadata)

        # 업로드 결과를 메타데이터에 반영
        metadata.update(
            {
                "storage_backend": self.config.storage.backend,
                "image_url": image_upload.url,
                "storage_path": image_upload.storage_path,
            }
        )

        # 로컬 메타데이터 파일 갱신
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")
        # 메타데이터 파일용 스토리지 key (.json 확장자)
        # 메타데이터 파일 업로드

        # 노드 출력용 결과 객체 반환
        return ImageNodeOutput(
            output_path=result.output_path,
            metadata_path=result.metadata_path,
            image_url=image_upload.url,
            metadata_json=metadata,
            storage_path=image_upload.storage_path,
            size_bytes=result.size_bytes,
            created_at=result.created_at,
            model=result.model,
            aspect_ratio=result.aspect_ratio,
        )

    def _build_storage_backend(self, config: ImageConfig) -> ImageStorageBackend:
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
