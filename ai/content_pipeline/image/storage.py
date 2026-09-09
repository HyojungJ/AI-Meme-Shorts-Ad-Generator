from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ImageStorageResult:
    """업로드 완료 후 반환되는 이미지 스토리지 결과"""
    url: str                # 공개 접근 가능한 URL
    storage_path: str       # 스토리지 내 경로 (로컬 경로나 S3 경로 등)
    size_bytes: int         # 파일 크기 (바이트 단위)
    created_at: str         # 업로드 시각 (ISO 포맷)
    metadata: dict          # 추가 메타데이터 (예: 원본 파일명, 사용자 ID 등)


class ImageStorageBackend:
    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> ImageStorageResult:
        raise NotImplementedError


class LocalStorageBackend(ImageStorageBackend):
    """서버의 로컬 파일 시스템에 이미지를 저장하는 방식"""
    def __init__(self, base_dir: Path, public_base_url: str):
        self.base_dir = base_dir
        self.public_base_url = public_base_url.rstrip("/")

    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> ImageStorageResult:
        # 대상 경로 생성
        if self.public_base_url:
            # 접근 URL 결정
            try:
                # 키가 base_dir 하위 경로인 경우 상대 경로 계산
                relative_key = local_path.relative_to(self.base_dir).as_posix()
                url = f"{self.public_base_url}/{relative_key}"
            except ValueError:
                # 그렇지 않은 경우 전체 키 사용
                url = f"{self.public_base_url}/{Path(key).as_posix()}"
        else:
            url = str(local_path)

        # 파일 크기 및 생성 시간 수집
        size_bytes = local_path.stat().st_size
        created_at = datetime.now(timezone.utc).isoformat()
        return ImageStorageResult(
            url=url,
            storage_path=str(local_path),
            size_bytes=size_bytes,
            created_at=created_at,
            metadata=metadata,
        )


class S3StorageBackend(ImageStorageBackend):
    """AWS S3 스토리지에 이미지를 저장하는 방식"""
    def __init__(self, bucket: str, region: str, public_base_url: str):
        if not bucket:
            raise ValueError("NANO_BANANA_S3_BUCKET is not set")
        self.bucket = bucket
        self.region = region
        self.public_base_url = public_base_url.rstrip("/")

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 uploads") from exc
        self.client = boto3.client("s3", region_name=region or None)

    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> ImageStorageResult:
        # S3에 파일 업로드
        self.client.upload_file(
            Filename=str(local_path),
            Bucket=self.bucket,
            Key=key,
        )

        # 접근 URL 결정 (s3:// URI로 저장하여 백엔드가 get_presigned_url()로 재생성 가능)
        if self.public_base_url:
            url = f"{self.public_base_url}/{key}"
        else:
            url = f"s3://{self.bucket}/{key}"

        # 메타데이터 포함하여 결과 반환
        created_at = datetime.now(timezone.utc).isoformat()
        size_bytes = local_path.stat().st_size
        return ImageStorageResult(
            url=url,
            storage_path=f"s3://{self.bucket}/{key}",
            size_bytes=size_bytes,
            created_at=created_at,
            metadata=metadata,
        )
