"""OpenCV 기반 생성물 품질 검증.

LLM/VLM 검증 앞단에서 돌리는 값싸고 결정적인 1차 게이트.
디코드 가능 여부, 해상도/종횡비, 블러, 노출, 단색/검은 프레임 같은
"명백히 깨진 산출물"을 모델 호출 없이 걸러낸다.

입력은 로컬 파일 경로 또는 S3/HTTP URL 모두 허용한다.
URL인 경우 presign 후 임시 파일로 내려받아 OpenCV로 읽는다.
"""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 임계값 (환경변수로 override 가능)
# ---------------------------------------------------------------------------
def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "") or default)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except (TypeError, ValueError):
        return default


# 이미지 임계값
IMAGE_MIN_WIDTH = _env_int("OPENCV_IMAGE_MIN_WIDTH", 256)
IMAGE_MIN_HEIGHT = _env_int("OPENCV_IMAGE_MIN_HEIGHT", 256)
# 세로형(9:16) 광고용 — 기대 종횡비(w/h)와 허용 오차
IMAGE_TARGET_ASPECT = _env_float("OPENCV_IMAGE_TARGET_ASPECT", 9.0 / 16.0)
IMAGE_ASPECT_TOLERANCE = _env_float("OPENCV_IMAGE_ASPECT_TOLERANCE", 0.15)
# 라플라시안 분산이 이 값보다 작으면 흐릿한 이미지로 간주
IMAGE_BLUR_MIN_VARIANCE = _env_float("OPENCV_IMAGE_BLUR_MIN_VARIANCE", 60.0)
# 평균 밝기(0~255) 허용 범위 — 벗어나면 과소/과다 노출
IMAGE_BRIGHTNESS_MIN = _env_float("OPENCV_IMAGE_BRIGHTNESS_MIN", 15.0)
IMAGE_BRIGHTNESS_MAX = _env_float("OPENCV_IMAGE_BRIGHTNESS_MAX", 245.0)
# 표준편차가 이 값보다 작으면 사실상 단색(깨진 프레임)
IMAGE_MIN_STDDEV = _env_float("OPENCV_IMAGE_MIN_STDDEV", 5.0)

# 비디오 임계값
VIDEO_MIN_WIDTH = _env_int("OPENCV_VIDEO_MIN_WIDTH", 256)
VIDEO_MIN_HEIGHT = _env_int("OPENCV_VIDEO_MIN_HEIGHT", 256)
VIDEO_MIN_FRAMES = _env_int("OPENCV_VIDEO_MIN_FRAMES", 2)
VIDEO_MIN_DURATION_SEC = _env_float("OPENCV_VIDEO_MIN_DURATION_SEC", 0.3)
# 샘플링한 프레임 중 검은 프레임 비율이 이 값을 넘으면 실패
VIDEO_MAX_BLACK_FRAME_RATIO = _env_float("OPENCV_VIDEO_MAX_BLACK_FRAME_RATIO", 0.5)
VIDEO_BLACK_FRAME_BRIGHTNESS = _env_float("OPENCV_VIDEO_BLACK_FRAME_BRIGHTNESS", 10.0)
# 검사할 프레임 샘플 개수
VIDEO_SAMPLE_FRAMES = _env_int("OPENCV_VIDEO_SAMPLE_FRAMES", 12)
VIDEO_BLUR_MIN_VARIANCE = _env_float("OPENCV_VIDEO_BLUR_MIN_VARIANCE", 25.0)


@dataclass
class OpenCVCheckResult:
    """OpenCV 검증 결과.

    passed: 모든 검사를 통과했는지 여부
    issues: 발견된 문제 설명 리스트 (실패 사유)
    metrics: 측정된 수치 (해상도, 블러 분산 등)
    """

    passed: bool
    issues: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": list(self.issues),
            "metrics": dict(self.metrics),
        }


# ---------------------------------------------------------------------------
# 미디어 로드 헬퍼
# ---------------------------------------------------------------------------
def _looks_like_url(source: str) -> bool:
    return source.startswith(("http://", "https://", "s3://"))


@contextmanager
def _local_media_path(source: str) -> Iterator[str]:
    """로컬 경로 또는 URL을 받아 OpenCV가 읽을 수 있는 로컬 경로를 돌려준다.

    URL이면 presign 후 임시 파일로 내려받고, 블록을 벗어나면 삭제한다.
    로컬 경로면 그대로 반환한다.
    """
    source = (source or "").strip()
    if not source:
        raise ValueError("media source is empty")

    if not _looks_like_url(source):
        if not os.path.exists(source):
            raise FileNotFoundError(f"local media not found: {source}")
        yield source
        return

    # URL → presign → 다운로드
    try:
        from content_pipeline.db import _maybe_presign_s3_url
        presigned = _maybe_presign_s3_url(source)
    except Exception as exc:  # presign 실패 시 원본 URL로 시도
        logger.warning("presign failed for %s: %s", source, exc)
        presigned = source

    import requests

    suffix = os.path.splitext(source.split("?", 1)[0])[1] or ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        with requests.get(presigned, stream=True, timeout=60) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=1 << 16):
                if chunk:
                    tmp.write(chunk)
        tmp.flush()
        tmp.close()
        yield tmp.name
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def _laplacian_variance(gray: np.ndarray) -> float:
    """라플라시안 분산 — 값이 작을수록 흐릿함(초점 흐림 지표)."""
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


# ---------------------------------------------------------------------------
# 이미지 검증
# ---------------------------------------------------------------------------
def verify_image_opencv(source: str) -> OpenCVCheckResult:
    """이미지 산출물에 대한 OpenCV 1차 품질 검증.

    검사 항목:
      - 디코드 가능 여부
      - 최소 해상도
      - 세로형(9:16) 종횡비
      - 블러(라플라시안 분산)
      - 노출(평균 밝기 과소/과다)
      - 단색/깨진 프레임(표준편차)
    """
    issues: list[str] = []
    metrics: dict = {}

    try:
        with _local_media_path(source) as path:
            img = cv2.imread(path, cv2.IMREAD_COLOR)
    except FileNotFoundError as exc:
        return OpenCVCheckResult(False, [str(exc)], {})
    except Exception as exc:
        return OpenCVCheckResult(False, [f"이미지 로드 실패: {exc}"], {})

    if img is None or img.size == 0:
        return OpenCVCheckResult(False, ["이미지 디코드 실패 (손상되었거나 지원되지 않는 형식)"], {})

    height, width = img.shape[:2]
    metrics["width"] = int(width)
    metrics["height"] = int(height)

    # 해상도
    if width < IMAGE_MIN_WIDTH or height < IMAGE_MIN_HEIGHT:
        issues.append(
            f"해상도 미달: {width}x{height} (최소 {IMAGE_MIN_WIDTH}x{IMAGE_MIN_HEIGHT})"
        )

    # 종횡비 (세로형 기대)
    aspect = width / height if height else 0.0
    metrics["aspect_ratio"] = round(aspect, 4)
    if abs(aspect - IMAGE_TARGET_ASPECT) > IMAGE_ASPECT_TOLERANCE:
        issues.append(
            f"종횡비 벗어남: {aspect:.3f} (기대 {IMAGE_TARGET_ASPECT:.3f} "
            f"±{IMAGE_ASPECT_TOLERANCE})"
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 단색/깨진 프레임
    stddev = float(gray.std())
    metrics["stddev"] = round(stddev, 3)
    if stddev < IMAGE_MIN_STDDEV:
        issues.append(f"단색/깨진 이미지 의심: 픽셀 표준편차 {stddev:.2f} < {IMAGE_MIN_STDDEV}")

    # 노출 (평균 밝기)
    brightness = float(gray.mean())
    metrics["brightness"] = round(brightness, 3)
    if brightness < IMAGE_BRIGHTNESS_MIN:
        issues.append(f"과소 노출: 평균 밝기 {brightness:.1f} < {IMAGE_BRIGHTNESS_MIN}")
    elif brightness > IMAGE_BRIGHTNESS_MAX:
        issues.append(f"과다 노출: 평균 밝기 {brightness:.1f} > {IMAGE_BRIGHTNESS_MAX}")

    # 블러 (단색이 아닐 때만 의미 있음)
    blur_var = _laplacian_variance(gray)
    metrics["blur_variance"] = round(blur_var, 3)
    if stddev >= IMAGE_MIN_STDDEV and blur_var < IMAGE_BLUR_MIN_VARIANCE:
        issues.append(
            f"흐릿한 이미지 의심: 라플라시안 분산 {blur_var:.1f} < {IMAGE_BLUR_MIN_VARIANCE}"
        )

    return OpenCVCheckResult(passed=not issues, issues=issues, metrics=metrics)


# ---------------------------------------------------------------------------
# 비디오 검증
# ---------------------------------------------------------------------------
def verify_video_opencv(source: str) -> OpenCVCheckResult:
    """비디오 산출물에 대한 OpenCV 1차 품질 검증.

    검사 항목:
      - 디코드/열기 가능 여부
      - 최소 프레임 수 / 길이
      - 최소 해상도
      - 검은 프레임 비율
      - 평균 블러(샘플 프레임)
    """
    issues: list[str] = []
    metrics: dict = {}

    try:
        with _local_media_path(source) as path:
            return _verify_video_file(path, issues, metrics)
    except FileNotFoundError as exc:
        return OpenCVCheckResult(False, [str(exc)], {})
    except Exception as exc:
        return OpenCVCheckResult(False, [f"비디오 로드 실패: {exc}"], metrics)


def _verify_video_file(path: str, issues: list[str], metrics: dict) -> OpenCVCheckResult:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        cap.release()
        return OpenCVCheckResult(False, ["비디오 열기 실패 (손상되었거나 지원되지 않는 코덱)"], metrics)

    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

        metrics["frame_count"] = frame_count
        metrics["fps"] = round(fps, 3)
        metrics["width"] = width
        metrics["height"] = height

        duration = frame_count / fps if fps > 0 else 0.0
        metrics["duration_sec"] = round(duration, 3)

        # 해상도
        if width < VIDEO_MIN_WIDTH or height < VIDEO_MIN_HEIGHT:
            issues.append(
                f"해상도 미달: {width}x{height} (최소 {VIDEO_MIN_WIDTH}x{VIDEO_MIN_HEIGHT})"
            )

        # 프레임 수 / 길이
        if frame_count < VIDEO_MIN_FRAMES:
            issues.append(f"프레임 수 부족: {frame_count} < {VIDEO_MIN_FRAMES}")
        if fps > 0 and duration < VIDEO_MIN_DURATION_SEC:
            issues.append(f"길이 부족: {duration:.2f}s < {VIDEO_MIN_DURATION_SEC}s")

        # 프레임 샘플링 → 검은 프레임 / 블러
        sample_result = _sample_video_frames(cap, frame_count)
        read_frames = sample_result["read_frames"]
        metrics["sampled_frames"] = read_frames

        if read_frames == 0:
            issues.append("프레임을 하나도 읽지 못함 (디코드 실패)")
        else:
            black_ratio = sample_result["black_frames"] / read_frames
            metrics["black_frame_ratio"] = round(black_ratio, 3)
            metrics["mean_brightness"] = round(sample_result["mean_brightness"], 3)
            metrics["mean_blur_variance"] = round(sample_result["mean_blur_variance"], 3)

            if black_ratio > VIDEO_MAX_BLACK_FRAME_RATIO:
                issues.append(
                    f"검은 프레임 과다: 비율 {black_ratio:.2f} > {VIDEO_MAX_BLACK_FRAME_RATIO}"
                )
            if sample_result["mean_blur_variance"] < VIDEO_BLUR_MIN_VARIANCE:
                issues.append(
                    f"전반적으로 흐릿함: 평균 라플라시안 분산 "
                    f"{sample_result['mean_blur_variance']:.1f} < {VIDEO_BLUR_MIN_VARIANCE}"
                )
    finally:
        cap.release()

    return OpenCVCheckResult(passed=not issues, issues=issues, metrics=metrics)


def _sample_video_frames(cap: "cv2.VideoCapture", frame_count: int) -> dict:
    """비디오에서 균등 간격으로 프레임을 샘플링해 밝기/블러 통계를 낸다."""
    if frame_count > 0:
        n = min(VIDEO_SAMPLE_FRAMES, frame_count)
        indices = np.linspace(0, frame_count - 1, n).astype(int)
    else:
        # 프레임 수 미상 → 순차 읽기로 샘플
        indices = None

    read_frames = 0
    black_frames = 0
    brightness_sum = 0.0
    blur_sum = 0.0

    if indices is not None:
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            read_frames += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            brightness_sum += brightness
            blur_sum += _laplacian_variance(gray)
            if brightness < VIDEO_BLACK_FRAME_BRIGHTNESS:
                black_frames += 1
    else:
        max_read = VIDEO_SAMPLE_FRAMES
        while read_frames < max_read:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            read_frames += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = float(gray.mean())
            brightness_sum += brightness
            blur_sum += _laplacian_variance(gray)
            if brightness < VIDEO_BLACK_FRAME_BRIGHTNESS:
                black_frames += 1

    return {
        "read_frames": read_frames,
        "black_frames": black_frames,
        "mean_brightness": (brightness_sum / read_frames) if read_frames else 0.0,
        "mean_blur_variance": (blur_sum / read_frames) if read_frames else 0.0,
    }
