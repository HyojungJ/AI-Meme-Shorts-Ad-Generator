import logging
import os
from functools import lru_cache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def _get_s3_client(region: str | None = None):
    import boto3
    return boto3.client("s3", region_name=region)


def _maybe_presign_s3_url(url: str) -> str:
    bucket, key, region = _parse_s3_location(url)
    if not bucket or not key:
        return url
    try:
        client = _get_s3_client(region or None)
    except Exception as exc:
        logger.warning("Failed to create S3 client for presigning (url=%s): %s", url, exc)
        return url
    expires = int(os.getenv("NANO_BANANA_S3_PRESIGN_EXPIRES", "3600") or "3600")
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def _parse_s3_location(url: str) -> tuple[str | None, str | None, str | None]:
    if url.startswith("s3://"):
        parsed = urlparse(url)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket or None, key or None, os.getenv("NANO_BANANA_S3_REGION") or None

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None, None, None
    host = parsed.netloc
    path = parsed.path.lstrip("/")
    if not host:
        return None, None, None

    if host.endswith(".amazonaws.com"):
        parts = host.split(".")
        if len(parts) >= 4 and parts[1] == "s3":
            bucket = parts[0]
            region = parts[2] if parts[2] != "amazonaws" else None
            return bucket or None, path or None, region or os.getenv("NANO_BANANA_S3_REGION") or None
        if parts[0] == "s3":
            # path-style: s3.amazonaws.com/bucket/key or s3.<region>.amazonaws.com/bucket/key
            if len(parts) >= 4:
                region = parts[1]
            else:
                region = None
            if "/" in path:
                bucket, key = path.split("/", 1)
                return bucket or None, key or None, region or os.getenv("NANO_BANANA_S3_REGION") or None
    return None, None, None
