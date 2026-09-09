import json
import re
import tempfile
from pathlib import Path

import requests

from content_pipeline.db import _maybe_presign_s3_url


def download_to_temp(url: str, suffix: str, temp_dir: Path) -> Path:
    """URL에서 파일 다운로드하여 임시 경로 반환. S3 URL이면 presign 후 다운로드."""
    temp_dir.mkdir(parents=True, exist_ok=True)
    presigned = _maybe_presign_s3_url(url)
    resp = requests.get(presigned, timeout=120)
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=suffix, delete=False) as f:
        f.write(resp.content)
        return Path(f.name)


def parse_json_from_llm(text: str) -> dict:
    """LLM 응답에서 JSON 추출. regex로 {...} 블록 추출 후 json.loads()"""
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {text[:200]}")
    return json.loads(match.group())
