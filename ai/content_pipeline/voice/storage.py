import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class VoiceStorageResult:
    """업로드 완료 후 반환되는 공통 결과 객체"""
    url: str            # 공개 접근 가능한 URL
    storage_path: str   # 실제 저장된 경로 (로컬 경로나 S3 경로 등)
    size_bytes: int     # 파일 크기 (바이트 단위)
    created_at: str     # 업로드된 시간 (ISO 포맷)
    metadata: dict      # 추가 메타데이터 (예: 원본 파일명, 사용자 ID 등)


class VoiceStorageBackend:
    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> VoiceStorageResult:
        raise NotImplementedError


class LocalStorageBackend(VoiceStorageBackend):
    """서버의 로컬 디스크에 파일을 저장하는 방식"""
    def __init__(self, base_dir: Path, public_base_url: str):
        self.base_dir = base_dir
        self.public_base_url = public_base_url.rstrip("/")

    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> VoiceStorageResult:
        # 저장할 전체 경로 생성 및 디렉토리 생성
        target_path = self.base_dir / key
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 임시 파일을 타겟 경로로 복사
        shutil.copyfile(local_path, target_path)

        # 접근 URL 결정
        url = (
            f"{self.public_base_url}/{key}"
            if self.public_base_url
            else str(target_path)
        )

        # 파일 크기 및 생성 시간 수집
        size_bytes = target_path.stat().st_size
        created_at = datetime.now(timezone.utc).isoformat()
        return VoiceStorageResult(
            url=url,
            storage_path=str(target_path),
            size_bytes=size_bytes,
            created_at=created_at,
            metadata=metadata,
        )


class S3StorageBackend(VoiceStorageBackend):
    """AWS S3 스토리지에 파일을 저장하는 방식"""
    def __init__(self, bucket: str, region: str, public_base_url: str):
        if not bucket:
            raise ValueError("VOICE_S3_BUCKET is not set")
        self.bucket = bucket
        self.region = region
        self.public_base_url = public_base_url.rstrip("/")

        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 uploads") from exc
        self.client = boto3.client("s3", region_name=region or None)

    def upload_file(self, local_path: Path, *, key: str, metadata: dict) -> VoiceStorageResult:
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
            
        # 파일 크기 및 생성 시간 수집
        created_at = datetime.now(timezone.utc).isoformat()
        size_bytes = local_path.stat().st_size
        return VoiceStorageResult(
            url=url,
            storage_path=f"s3://{self.bucket}/{key}",
            size_bytes=size_bytes,
            created_at=created_at,
            metadata=metadata,
        )
