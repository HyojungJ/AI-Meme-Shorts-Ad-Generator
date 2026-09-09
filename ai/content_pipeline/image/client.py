import json
import random
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image
import requests


# --- 1. 데이터 모델 정의 ---
@dataclass(frozen=True)
class ImageGenerationResult:
    output_path: str
    metadata_path: str
    size_bytes: int
    created_at: str
    model: str
    aspect_ratio: str

# --- 2. 유틸리티 함수 ---
def _download_image(url: str, temp_dir: Path, *, default_suffix: str) -> Path:
    """temp 디렉토리에 이미지를 다운로드하고 경로 반환"""
    # 다운로드 요청
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    # 임시 파일에 저장
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix or default_suffix
    # 임시 디렉토리 생성
    temp_dir.mkdir(parents=True, exist_ok=True)
    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=suffix, delete=False) as tmp:
        tmp.write(response.content)
        return Path(tmp.name)


def _write_metadata(metadata_path: Path, metadata: dict) -> None:
    """메타데이터를 JSON 파일로 저장"""
    # 디렉토리 생성
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    # JSON 파일로 저장
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=True, indent=2)


def _generate_image_from_contents(
    *,
    client: genai.Client,
    contents: list,
    text_input: str,
    aspect_ratio: str,
    output_path: Path,
    model_name: str,
    max_retries: int,
    base_sleep: float,
    max_sleep: float,
) -> ImageGenerationResult:
    """재시도 로직을 포함한 이미지 생성 함수"""
    # 재시도 로직
    for attempt in range(1, max_retries + 1):
        # 이미지 생성 API 호출
        try:
            # 이미지 생성 API 호출
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    )
                ),
            )
            break
        except genai_errors.ServerError:
            # 서버 오류 시 재시도
            if attempt == max_retries:
                raise
            # 너무 길어지지 않도록 최대 대기 시간 제한
            sleep_for = min(max_sleep, base_sleep * (2 ** (attempt - 1)))
            sleep_for += random.uniform(0, 0.5)
            time.sleep(sleep_for)

    saved = False
    for part in response.parts:
        # inline_data가 있는지 확인하고 이미지 저장
        if part.inline_data is not None:
            # 이미지 데이터로 변환
            image = part.as_image()
            image.save(output_path)
            saved = True
            break

    if not saved:
        raise RuntimeError("No image returned from model response.")

    # 메타데이터 작성
    size_bytes = output_path.stat().st_size
    created_at = datetime.now(timezone.utc).isoformat()
    metadata_path = output_path.with_suffix(".json")
    metadata = {
        "model": model_name,
        "aspect_ratio": aspect_ratio,
        "prompt": text_input,
        "output_path": str(output_path),
        "size_bytes": size_bytes,
        "created_at": created_at,
    }
    # 메타데이터 파일로 저장
    _write_metadata(metadata_path, metadata)

    return ImageGenerationResult(
        output_path=str(output_path),
        metadata_path=str(metadata_path),
        size_bytes=size_bytes,
        created_at=created_at,
        model=model_name,
        aspect_ratio=aspect_ratio,
    )


# --- 3. GenAI NanoBanana 이미지 생성 클라이언트 클래스 ---
class ImageClient:

    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("NANO_BANANA_API_KEY is required")
        if not model_name:
            raise ValueError("model_name is required")
        self.api_key = api_key
        self.model_name = model_name
        self._client = genai.Client(api_key=api_key)

    def generate_character_image(
        self,
        *,
        character_prompt: str,
        aspect_ratio: str = "9:16",
        output_path: str | None = None,
        output_dir: Path | None = None,
        model_name: str | None = None,
        max_retries: int = 5,
        base_sleep: float = 1.0,
        max_sleep: float = 8.0,
    ) -> ImageGenerationResult:
        """
        캐릭터 이미지 생성
        - 캐릭터 프롬프트를 기반으로 이미지를 생성하고 저장
        - 반환값: 생성된 이미지와 메타데이터 경로
        """
        # 모델 이름 설정
        if model_name is None:
            model_name = self.model_name
        # 출력 경로 설정
        if output_path:
            target_path = Path(output_path)
        # 출력 디렉토리 설정
        else:
            output_dir = output_dir or Path("data/images")
            target_path = output_dir / f"character_{int(time.time())}.png"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 캐릭터 이미지 생성 API 호출
        result = _generate_image_from_contents(
            client=self._client,
            contents=[character_prompt],
            text_input=character_prompt,
            aspect_ratio=aspect_ratio,
            output_path=target_path,
            model_name=model_name,
            max_retries=max_retries,
            base_sleep=base_sleep,
            max_sleep=max_sleep,
        )

        # 메타데이터 업데이트
        metadata_path = Path(result.metadata_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "character_prompt": character_prompt,
            }
        )
        # 메타데이터 파일로 저장
        _write_metadata(metadata_path, metadata)
        return result


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
        output_dir: Path | None = None,
        model_name: str | None = None,
        temp_dir: Path | None = None,
        max_retries: int = 5,
        base_sleep: float = 1.0,
        max_sleep: float = 8.0,
    ) -> ImageGenerationResult:
        """
        장면 이미지 생성
        - 시나리오 프롬프트와 제품/캐릭터 이미지를 기반으로 장면 이미지를 생성하고 저장
        - 반환값: 생성된 이미지와 메타데이터 경로
        """
        # 모델 이름 설정
        if model_name is None:
            model_name = self.model_name
        # 임시 디렉토리 설정
        if temp_dir is None:
            temp_dir = Path("data/images/tmp")
        # 출력 경로 설정
        if output_path:
            target_path = Path(output_path)
        # 출력 디렉토리 설정
        else:
            output_dir = output_dir or Path("data/images")
            target_path = output_dir / f"scene_{int(time.time())}.png"
        # 출력 디렉토리 생성
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not product_image_path and not product_image_url:
            raise ValueError("product_image_path or product_image_url is required")
        if not character_image_path and not character_image_url:
            raise ValueError("character_image_path or character_image_url is required")

        # 임시 파일 경로 목록
        temp_paths: list[Path] = []

        # 이미지 파일 열기 및 다운로드
        try:
            # 제품 이미지 열기
            if product_image_url:
                temp_path = _download_image(product_image_url, temp_dir, default_suffix=".jpg")
                temp_paths.append(temp_path)
                with Image.open(temp_path) as img:
                    product_image = img.copy()
            else:
                with Image.open(product_image_path) as img:
                    product_image = img.copy()

            # 캐릭터 이미지 열기
            if character_image_url:
                temp_path = _download_image(character_image_url, temp_dir, default_suffix=".png")
                temp_paths.append(temp_path)
                with Image.open(temp_path) as img:
                    character_image = img.copy()
            else:
                with Image.open(character_image_path) as img:
                    character_image = img.copy()

            # 참조 이미지 생성 API 호출
            result = _generate_image_from_contents(
                client=self._client,
                contents=[product_image, character_image, scenario_prompt],
                text_input=scenario_prompt,
                aspect_ratio=aspect_ratio,
                output_path=target_path,
                model_name=model_name,
                max_retries=max_retries,
                base_sleep=base_sleep,
                max_sleep=max_sleep,
            )
        finally:
            # 임시 파일 삭제
            for temp_path in temp_paths:
                if temp_path.exists():
                    temp_path.unlink()

        # 메타데이터 업데이트
        metadata_path = Path(result.metadata_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "scenario_prompt": scenario_prompt,
                "product_image_path": str(product_image_path) if product_image_path else None,
                "product_image_url": product_image_url,
                "character_image_path": str(character_image_path) if character_image_path else None,
                "character_image_url": character_image_url,
            }
        )
        # 메타데이터 파일로 저장
        _write_metadata(metadata_path, metadata)
        return result
