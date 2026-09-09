import os
import time

from pathlib import Path
from typing import Literal
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class VideoResult:
    video_id: str
    status: str
    video_url: str = None
    duration_seconds: float = None
    cost_usd: float = None
    error: str = None


class SoraClient:
    RESOLUTIONS = {
        "portrait": "720x1280",   # 세로 (숏폼)
        "landscape": "1280x720",  # 가로
        "portrait_hd": "1024x1792",
        "landscape_hd": "1792x1024",
    }
    DURATIONS = [4, 8, 12]
    COSTS = {
        "sora-2": 0.10,
        "sora-2-pro": 0.30,
    }

    def __init__(
        self,
        model: Literal["sora-2", "sora-2-pro"] = "sora-2",
        api_key: str = None
    ):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(
        self,
        prompt: str,
        duration: int = 4,
        resolution: str = "portrait",
        wait: bool = True,
        timeout: int = 300
    ) -> VideoResult:
        res = self.RESOLUTIONS.get(resolution, resolution)
        if duration not in self.DURATIONS:
            duration = min(self.DURATIONS, key=lambda x: abs(x - duration))

        try:
            video = self.client.videos.create(
                model=self.model,
                prompt=prompt,
                seconds=str(duration),  # API expects string: "4", "8", "12"
                size=res
            )

            result = VideoResult(
                video_id=video.id,
                status=video.status,
                duration_seconds=duration,
                cost_usd=self.COSTS[self.model] * duration
            )

            if wait and video.status != "completed":
                result = self._wait_for_completion(video.id, timeout)

            return result

        except Exception as e:
            return VideoResult(video_id="", status="failed", error=str(e))

    def generate_from_image(
        self,
        image_path: str,
        prompt: str,
        duration: int = 4,
        resolution: str = "portrait",
        wait: bool = True,
        timeout: int = 300
    ) -> VideoResult:
        image_path = Path(image_path)
        if not image_path.exists():
            return VideoResult(video_id="", status="failed", error=f"Image not found: {image_path}")

        res = self.RESOLUTIONS.get(resolution, resolution)
        if duration not in self.DURATIONS:
            duration = min(self.DURATIONS, key=lambda x: abs(x - duration))

        try:
            suffix = image_path.suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp"
            }.get(suffix, "image/png")

            with open(image_path, "rb") as f:
                image_file = (image_path.name, f.read(), mime_type)

            video = self.client.videos.create(
                model=self.model,
                prompt=prompt,
                input_reference=image_file,
                seconds=str(duration),  # API expects string: "4", "8", "12"
                size=res
            )

            result = VideoResult(
                video_id=video.id,
                status=video.status,
                duration_seconds=duration,
                cost_usd=self.COSTS[self.model] * duration
            )

            if wait and video.status != "completed":
                result = self._wait_for_completion(video.id, timeout)

            return result

        except Exception as e:
            return VideoResult(video_id="", status="failed", error=str(e))

    def get_status(self, video_id: str) -> VideoResult:
        try:
            video = self.client.videos.retrieve(video_id)
            seconds_str = getattr(video, "seconds", None)
            duration = int(seconds_str) if seconds_str else None
            return VideoResult(
                video_id=video.id,
                status=video.status,
                duration_seconds=duration,
                cost_usd=self.COSTS[self.model] * duration if duration else None
            )
        except Exception as e:
            return VideoResult(video_id=video_id, status="failed", error=str(e))

    def _wait_for_completion(
        self,
        video_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> VideoResult:
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_status(video_id)

            if result.status == "completed":
                return result
            elif result.status == "failed":
                return result

            time.sleep(poll_interval)

        return VideoResult(video_id=video_id, status="timeout", error=f"Timeout after {timeout} seconds")

    def download(self, video_id: str, output_path: str) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = self.client.videos.download_content(video_id)

        with open(output_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)

        return str(output_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Sora 영상 생성")
    parser.add_argument("--prompt", type=str, required=True, help="프롬프트")
    parser.add_argument("--image", type=str, help="참조 이미지 경로")
    parser.add_argument("--duration", type=int, default=4, help="길이 (초)")
    parser.add_argument("--model", default="sora-2", help="모델")
    parser.add_argument("--output", "-o", help="출력 경로")
    args = parser.parse_args()

    client = SoraClient(model=args.model)

    if args.image:
        print(f"[Sora] 이미지 → 영상 생성: {args.image}")
        result = client.generate_from_image(
            image_path=args.image,
            prompt=args.prompt,
            duration=args.duration
        )
    else:
        print(f"[Sora] 텍스트 → 영상 생성")
        result = client.generate(
            prompt=args.prompt,
            duration=args.duration
        )

    print(f"  → 상태: {result.status}")
    print(f"  → Video ID: {result.video_id}")
    if result.cost_usd:
        print(f"  → 비용: ${result.cost_usd:.2f}")

    if result.status == "completed" and result.video_id:
        if args.output:
            path = client.download(result.video_id, args.output)
            print(f"  → 저장: {path}")

    if result.error:
        print(f"  → 에러: {result.error}")


if __name__ == "__main__":
    main()
