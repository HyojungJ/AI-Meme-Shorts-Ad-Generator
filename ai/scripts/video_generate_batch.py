#!/usr/bin/env python
import argparse
import json
import shutil
import subprocess
from pathlib import Path

from content_pipeline.video import VideoService, load_video_config


def _read_scenes(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"scenes file not found: {path}")
    scenes: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"scene entry must be a JSON object: {line}")
        if not payload.get("prompt"):
            raise ValueError(f"scene entry missing prompt: {line}")
        scenes.append(payload)
    if not scenes:
        raise ValueError("scenes file contains no valid entries")
    return scenes


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required tool not found in PATH: {name}")
    return path


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _extract_last_frame(ffmpeg: str, input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-sseof",
        "-0.01",
        "-i",
        str(input_path),
        "-frames:v",
        "1",
        str(output_path),
    ]
    _run(cmd)


def _write_result(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch generate scene videos from a JSONL file."
    )
    parser.add_argument(
        "--scenes",
        default="scenes.jsonl",
        help="Path to scenes.jsonl (one JSON object per line).",
    )
    parser.add_argument(
        "--result-path",
        help="Append results to this JSONL file.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue when a scene fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print scenes without generating videos.",
    )
    parser.add_argument(
        "--use-last-frame",
        action="store_true",
        help="Use previous scene last frame when reference image is missing.",
    )
    parser.add_argument(
        "--last-frame-dir",
        default="data/images",
        help="Directory to store extracted last-frame images.",
    )
    args = parser.parse_args()

    scenes_path = Path(args.scenes)
    scenes = _read_scenes(scenes_path)

    if args.dry_run:
        for idx, scene in enumerate(scenes, start=1):
            print(f"[dry-run] scene {idx}: {scene.get('prompt')}")
        return 0

    config = load_video_config()
    service = VideoService(config)
    result_path = Path(args.result_path) if args.result_path else None

    last_frame_path: Path | None = None
    for idx, scene in enumerate(scenes, start=1):
        scene_data = dict(scene)
        if (
            args.use_last_frame
            and last_frame_path
            and not scene_data.get("reference_image_path")
            and not scene_data.get("reference_image_url")
        ):
            scene_data["reference_image_path"] = str(last_frame_path)
        try:
            result = service.generate_video(
                prompt=scene_data["prompt"],
                audio_path=scene_data.get("audio_path"),
                audio_url=scene_data.get("audio_url"),
                reference_image_path=scene_data.get("reference_image_path"),
                reference_image_url=scene_data.get("reference_image_url"),
                duration_seconds=scene_data.get("duration_seconds"),
                output_path=scene_data.get("output_path"),
                mock_sample_path=scene_data.get("mock_sample_path"),
            )
            output = {
                "index": idx,
                "prompt": scene_data["prompt"],
                "output_path": result.storage_path,
                "video_url": result.video_url,
                "duration_seconds": result.duration_seconds,
                "size_bytes": result.size_bytes,
            }
            print(f"[ok] scene {idx}: {result.storage_path}")
            if result_path:
                _write_result(result_path, output)
            if args.use_last_frame:
                source = scene_data.get("output_path") or result.storage_path
                if "://" in str(source):
                    raise RuntimeError(
                        f"cannot extract last frame from non-local path: {source}"
                    )
                source_path = Path(source)
                if not source_path.exists():
                    raise FileNotFoundError(f"video not found: {source_path}")
                ffmpeg = _require_tool("ffmpeg")
                last_frame_path = Path(args.last_frame_dir) / f"{source_path.stem}_last.png"
                _extract_last_frame(ffmpeg, source_path, last_frame_path)
        except Exception as exc:
            print(f"[error] scene {idx}: {exc}")
            if not args.continue_on_error:
                raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
