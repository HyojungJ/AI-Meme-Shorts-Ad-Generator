import logging
import os
import tempfile
from typing import Literal

import cv2
import yt_dlp
from google.genai import types
from langchain_core.tools import tool
from PIL import Image
from pydantic import BaseModel, Field

from common import config, get_gemini, has_quoted_dialogue, retry, RetryError
from meme_collector.prompts.usage_context_prompts import (
    USAGE_CONTEXT_PROMPT_V1,
    USAGE_CONTEXT_PROMPT_V2
)
log = logging.getLogger(__name__)


class UsageContextResponse(BaseModel):
    """Gemini structured output for usage context extraction."""

    is_relevant: bool = Field(description="True if video is about this meme, False otherwise")
    context: str = Field("", description="구체적인 사용 상황 (한국어)")
    usage: str = Field("", description="밈 대사/표현을 따옴표로 인용한 사용 방법 (한국어)")
    tone: Literal["playful", "sarcastic", "aggressive", "friendly", "neutral"] = "playful"
    example_type: Literal["good", "bad"] = Field(
        "good", description="적절한 활용(good) vs 부적절한 활용(bad)"
    )

VISION_PROMPT = """You are a video motion analyst for meme recreation.

Analyze these frames from a Korean meme video and describe the EXACT movements for AI video generation.

## Output Format (English only)

### 1. Motion Sequence
Describe the movement frame-by-frame:
- Starting pose (body position, hand placement, facial expression)
- Key movements in order (be SPECIFIC: "raises right arm 45 degrees", not "moves arm")
- Ending pose
- Timing hints (quick snap, slow raise, etc.)

### 2. Camera Angle
- Shot type (close-up, medium, full body, etc.)
- Camera movement if any (static, pan, zoom)
- Framing (centered, off-center, etc.)

### 3. Performance Style
- Energy level (calm, energetic, explosive)
- Expression type (deadpan, exaggerated, playful)
- Body language characteristics

### 4. Key Visual Elements
- Distinctive gestures or poses
- Repeated motions (if any)
- Sync points with audio (if apparent)

Be extremely specific - this will be used to generate AI video that recreates the exact movements."""



@retry(max_attempts=3, delay=1.0, exceptions=(Exception,))
def _download_video(url: str, output_dir: str) -> str:
    # Try multiple format strategies for YouTube Shorts compatibility
    format_options = [
        "best[height<=720]",  # Default
        "bestvideo[height<=720]+bestaudio/best[height<=720]",  # Separate streams
        "best",  # Fallback to any best
    ]

    last_error = None
    for fmt in format_options:
        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(output_dir, "video.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                ext = info.get("ext", "mp4")
                video_path = os.path.join(output_dir, f"video.{ext}")

                if not os.path.exists(video_path):
                    # Check for merged mp4
                    video_path = os.path.join(output_dir, "video.mp4")

                if not os.path.exists(video_path):
                    last_error = FileNotFoundError(f"Downloaded video not found: {video_path}")
                    continue

                # Check if file is not empty
                file_size = os.path.getsize(video_path)
                if file_size < 1000:  # Less than 1KB is likely empty/corrupt
                    last_error = ValueError(f"Downloaded file is empty or too small: {file_size} bytes")
                    os.remove(video_path)  # Clean up empty file
                    continue

                return video_path
        except Exception as e:
            last_error = e
            continue

    raise last_error or FileNotFoundError("Failed to download video with any format")


def _extract_frames(video_path: str, num_frames: int = 8) -> list[Image.Image]:
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        log.warning(f"Video has 0 frames (possibly corrupt): {video_path}")
        cap.release()
        return []

    if total_frames < num_frames:
        frame_indices = list(range(total_frames))
    else:
        frame_indices = [int(i * total_frames / num_frames) for i in range(num_frames)]

    expected_frames = len(frame_indices)
    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            pil_image = pil_image.resize((512, 512), Image.Resampling.LANCZOS)
            frames.append(pil_image)

    cap.release()

    if len(frames) < expected_frames:
        log.warning(
            f"Extracted fewer frames than expected: {len(frames)}/{expected_frames} from {video_path}"
        )

    return frames


def _analyze_with_gemini(frames: list[Image.Image], meme_name: str = "", prompt: str = VISION_PROMPT) -> str:
    client = get_gemini()

    contents = [f"Meme name: {meme_name}\n\n{prompt}\n\nAnalyze these {len(frames)} frames:"]

    for i, frame in enumerate(frames):
        contents.append(f"\nFrame {i + 1}:")
        contents.append(frame)

    try:
        response = client.models.generate_content(
            model=config.models.vision,
            contents=contents,
        )
        return response.text
    except Exception as e:
        log.warning(f"Gemini analysis failed: {e}")
        return f"Error analyzing video: {str(e)}"


def _extract_usage_context(frames: list[Image.Image], meme_name: str) -> dict | None:
    """Extract usage context using Gemini structured output."""
    client = get_gemini()

    contents = [
        f"Meme name: {meme_name}\n\n{USAGE_CONTEXT_PROMPT_V2}\n\nAnalyze these {len(frames)} frames:"
    ]
    for i, frame in enumerate(frames):
        contents.append(f"\nFrame {i + 1}:")
        contents.append(frame)

    try:
        response = client.models.generate_content(
            model=config.models.vision,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=UsageContextResponse,
            ),
        )
        parsed = UsageContextResponse.model_validate_json(response.text)

        if not parsed.is_relevant:
            return None

        if len(parsed.context) < 5 or len(parsed.usage) < 5:
            return None

        if not has_quoted_dialogue(parsed.usage):
            return None

        return {
            "context": parsed.context,
            "usage": parsed.usage,
            "tone": parsed.tone,
            "example_type": parsed.example_type,
        }
    except Exception as e:
        log.warning(f"Usage context extraction failed: {e}")
        return None


@tool
def analyze_meme_video(youtube_url: str, meme_name: str = "") -> dict:
    """YouTube 영상을 다운로드하고 Gemini Vision으로 동작을 분석합니다. Sora 프롬프트 생성에 사용됩니다."""
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            video_path = _download_video(youtube_url, tmpdir)
        except RetryError as e:
            log.warning(f"Video download failed: {youtube_url} - {e.last_error}")
            return {"error": "Failed to download video"}

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        frames = _extract_frames(video_path, num_frames=8)
        if not frames:
            return {"error": "Failed to extract frames"}

        analysis = _analyze_with_gemini(frames, meme_name)

        return {
            "motion_analysis": analysis,
            "frame_count": len(frames),
            "duration": round(duration, 2),
            "source_url": youtube_url,
        }


def extract_usage_from_videos(videos: list[dict], meme_name: str, max_videos: int = 3) -> list[dict]:
    """여러 유튜브 영상에서 밈 활용 예시를 추출합니다.

    Args:
        videos: YouTube 영상 목록 [{"video_id": ..., "url": ..., "title": ...}, ...]
        meme_name: 밈 이름
        max_videos: 분석할 최대 영상 수

    Returns:
        list of {"context": ..., "usage": ..., "tone": ..., "source": ...}
    """
    usage_examples = []

    for video in videos[:max_videos]:
        url = video.get("url", "")
        if not url:
            continue

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = _download_video(url, tmpdir)

                frames = _extract_frames(video_path, num_frames=6)
                if not frames:
                    continue

                parsed = _extract_usage_context(frames, meme_name)
                if parsed is None:
                    continue

                usage_examples.append({
                    "context": parsed["context"],
                    "usage": parsed["usage"],
                    "tone": parsed["tone"],
                    "example_type": parsed.get("example_type", "good"),
                    "source_url": url,
                })
        except RetryError as e:
            log.warning(f"Video analysis skipped: {url} - {e.last_error}")
            continue

    return usage_examples
