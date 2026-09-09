#!/usr/bin/env python
import argparse
import shutil
import subprocess
from pathlib import Path


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"Required tool not found in PATH: {name}")
    return path


def _read_scenes(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(f"scenes file not found: {path}")
    scenes: list[Path] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        scenes.append(Path(line))
    if not scenes:
        raise ValueError("scenes file contains no valid entries")
    dup = {p for p in scenes if scenes.count(p) > 1}
    if dup:
        raise ValueError(f"duplicate entries: {', '.join(str(p) for p in sorted(dup))}")
    missing = [p for p in scenes if not p.exists()]
    if missing:
        raise FileNotFoundError("missing files: " + ", ".join(str(p) for p in missing))
    return scenes


def _duration_seconds(ffprobe: str, path: Path) -> float:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def _normalize_video(
    ffmpeg: str,
    input_path: Path,
    output_path: Path,
    fps: int,
    size: str,
    audio_rate: int,
    audio_channels: int,
) -> None:
    """Normalize scene video spec."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(input_path),
        "-r",
        str(fps),
        "-s",
        size,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        str(audio_rate),
        "-ac",
        str(audio_channels),
        str(output_path),
    ]
    _run(cmd)


def merge_scenes(
    scenes_path: Path,
    output: Path,
    crossfade: float,
    work: Path,
    *,
    normalize: bool,
    norm_dir: Path,
    norm_fps: int,
    norm_size: str,
    norm_audio_rate: int,
    norm_audio_channels: int,
) -> None:
    ffmpeg = _require_tool("ffmpeg")
    ffprobe = _require_tool("ffprobe")

    scenes = _read_scenes(scenes_path)
    if normalize:
        normalized: list[Path] = []
        for scene in scenes:
            out_name = f"{scene.stem}_norm{scene.suffix}"
            out_path = norm_dir / out_name
            _normalize_video(
                ffmpeg,
                scene,
                out_path,
                fps=norm_fps,
                size=norm_size,
                audio_rate=norm_audio_rate,
                audio_channels=norm_audio_channels,
            )
            normalized.append(out_path)
        scenes = normalized

    work.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(scenes[0], work)
    for next_path in scenes[1:]:
        duration = _duration_seconds(ffprobe, work)
        offset = max(0.0, round(duration - crossfade, 3))
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(work),
            "-i",
            str(next_path),
            "-filter_complex",
            (
                f"[0:v][1:v]xfade=transition=fade:duration={crossfade}:offset={offset}[v];"
                f"[0:a][1:a]acrossfade=d={crossfade}[a]"
            ),
            "-map",
            "[v]",
            "-map",
            "[a]",
            str(work.with_name("merge_tmp.mp4")),
        ]
        _run(cmd)
        work.with_name("merge_tmp.mp4").replace(work)

    work.replace(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge scene videos with crossfade using ffmpeg."
    )
    parser.add_argument(
        "--scenes",
        default="scenes.txt",
        help="Path to scenes.txt (one file per line).",
    )
    parser.add_argument(
        "--output",
        default="merged.mp4",
        help="Output video path.",
    )
    parser.add_argument(
        "--crossfade",
        type=float,
        default=0.3,
        help="Crossfade seconds.",
    )
    parser.add_argument(
        "--work",
        default="merge_work.mp4",
        help="Working file path.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize scenes before merging.",
    )
    parser.add_argument(
        "--norm-fps",
        type=int,
        default=24,
        help="Normalization FPS.",
    )
    parser.add_argument(
        "--norm-size",
        default="1280x720",
        help="Normalization resolution (e.g. 1280x720).",
    )
    parser.add_argument(
        "--norm-audio-rate",
        type=int,
        default=48000,
        help="Normalization audio sample rate.",
    )
    parser.add_argument(
        "--norm-audio-ch",
        type=int,
        default=2,
        help="Normalization audio channels.",
    )
    parser.add_argument(
        "--norm-dir",
        default="normalized",
        help="Directory for normalized outputs.",
    )
    args = parser.parse_args()

    merge_scenes(
        scenes_path=Path(args.scenes),
        output=Path(args.output),
        crossfade=args.crossfade,
        work=Path(args.work),
        normalize=args.normalize,
        norm_dir=Path(args.norm_dir),
        norm_fps=args.norm_fps,
        norm_size=args.norm_size,
        norm_audio_rate=args.norm_audio_rate,
        norm_audio_channels=args.norm_audio_ch,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
