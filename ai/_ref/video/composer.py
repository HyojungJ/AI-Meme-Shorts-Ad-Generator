import subprocess
from pathlib import Path
from typing import List
from dataclasses import dataclass


@dataclass
class ComposeResult:
    output_path: str
    duration_seconds: float
    success: bool
    error: str = None


class VideoComposer:
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str = None,
        replace_audio: bool = True
    ) -> ComposeResult:
        video_path = Path(video_path)
        audio_path = Path(audio_path)

        if not video_path.exists():
            return ComposeResult("", 0, False, f"Video not found: {video_path}")
        if not audio_path.exists():
            return ComposeResult("", 0, False, f"Audio not found: {audio_path}")

        if not output_path:
            output_path = self.output_dir / f"{video_path.stem}_with_audio.mp4"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            video_duration = self._get_duration(str(video_path))
            audio_duration = self._get_audio_duration(str(audio_path))

            if replace_audio:
                if audio_duration > video_duration:
                    pad_duration = audio_duration - video_duration + 0.1
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", str(video_path),
                        "-i", str(audio_path),
                        "-vf", f"tpad=stop_mode=clone:stop_duration={pad_duration}",
                        "-c:v", "libx264", "-preset", "fast",
                        "-c:a", "aac",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-shortest",
                        str(output_path)
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", str(video_path),
                        "-i", str(audio_path),
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-shortest",
                        str(output_path)
                    ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(video_path),
                    "-i", str(audio_path),
                    "-c:v", "copy",
                    "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]",
                    "-map", "0:v:0",
                    "-map", "[a]",
                    "-shortest",
                    str(output_path)
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ComposeResult("", 0, False, result.stderr)

            duration = self._get_duration(str(output_path))

            return ComposeResult(
                output_path=str(output_path),
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def concat(
        self,
        clips: List[str],
        output_path: str = None,
        transition: str = None
    ) -> ComposeResult:
        if not clips:
            return ComposeResult("", 0, False, "No clips provided")

        valid_clips = []
        for clip in clips:
            if Path(clip).exists():
                valid_clips.append(clip)
            else:
                print(f"[WARNING] Clip not found: {clip}")

        if not valid_clips:
            return ComposeResult("", 0, False, "No valid clips found")

        if not output_path:
            output_path = self.output_dir / "final_output.mp4"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if transition:
                return self._concat_with_transition(valid_clips, str(output_path), transition)
            else:
                return self._concat_simple(valid_clips, str(output_path))

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def _concat_simple(self, clips: List[str], output_path: str) -> ComposeResult:
        try:
            inputs = []
            for clip in clips:
                inputs.extend(["-i", str(Path(clip).resolve())])

            n = len(clips)
            filter_parts = "".join([f"[{i}:v][{i}:a]" for i in range(n)])
            filter_complex = f"{filter_parts}concat=n={n}:v=1:a=1[outv][outa]"

            cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filter_complex,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ComposeResult("", 0, False, result.stderr)

            duration = self._get_duration(output_path)

            return ComposeResult(
                output_path=output_path,
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def _concat_with_transition(
        self,
        clips: List[str],
        output_path: str,
        transition: str = "fade",
        duration: float = 0.5
    ) -> ComposeResult:
        if len(clips) < 2:
            return self._concat_simple(clips, output_path)

        filter_parts = []
        inputs = ""

        for i, clip in enumerate(clips):
            inputs += f"-i {clip} "

        filter_parts.append(f"[0:v][1:v]xfade=transition={transition}:duration={duration}[v]")

        try:
            cmd = f"ffmpeg -y {inputs} -filter_complex \"{';'.join(filter_parts)}\" -map \"[v]\" {output_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                return self._concat_simple(clips, output_path)

            duration_sec = self._get_duration(output_path)

            return ComposeResult(
                output_path=output_path,
                duration_seconds=duration_sec,
                success=True
            )

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def resize(
        self,
        video_path: str,
        output_path: str = None,
        width: int = 720,
        height: int = 1280
    ) -> ComposeResult:
        video_path = Path(video_path)

        if not output_path:
            output_path = self.output_dir / f"{video_path.stem}_{width}x{height}.mp4"
        output_path = Path(output_path)

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
                "-c:a", "copy",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ComposeResult("", 0, False, result.stderr)

            duration = self._get_duration(str(output_path))

            return ComposeResult(
                output_path=str(output_path),
                duration_seconds=duration,
                success=True
            )

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def image_to_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None,
        duration: float = None
    ) -> ComposeResult:
        image_path = Path(image_path)
        audio_path = Path(audio_path)

        if not image_path.exists():
            return ComposeResult("", 0, False, f"Image not found: {image_path}")
        if not audio_path.exists():
            return ComposeResult("", 0, False, f"Audio not found: {audio_path}")

        if not output_path:
            output_path = self.output_dir / f"{image_path.stem}_video.mp4"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            audio_duration = self._get_audio_duration(str(audio_path))
            video_duration = duration or audio_duration or 5.0

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", str(video_duration),
                "-shortest",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ComposeResult("", 0, False, result.stderr)

            duration_sec = self._get_duration(str(output_path))

            return ComposeResult(
                output_path=str(output_path),
                duration_seconds=duration_sec,
                success=True
            )

        except Exception as e:
            return ComposeResult("", 0, False, str(e))

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def _get_duration(self, video_path: str) -> float:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="영상 합성")
    subparsers = parser.add_subparsers(dest="command")

    audio_parser = subparsers.add_parser("add-audio", help="영상에 오디오 추가")
    audio_parser.add_argument("--video", required=True, help="영상 경로")
    audio_parser.add_argument("--audio", required=True, help="오디오 경로")
    audio_parser.add_argument("--output", "-o", help="출력 경로")

    concat_parser = subparsers.add_parser("concat", help="클립 연결")
    concat_parser.add_argument("--clips", nargs="+", required=True, help="클립 경로들")
    concat_parser.add_argument("--output", "-o", help="출력 경로")
    concat_parser.add_argument("--transition", help="트랜지션 (fade, dissolve)")

    args = parser.parse_args()
    composer = VideoComposer()

    if args.command == "add-audio":
        print(f"[Composer] 오디오 합성: {args.video} + {args.audio}")
        result = composer.add_audio(args.video, args.audio, args.output)
    elif args.command == "concat":
        print(f"[Composer] 클립 연결: {len(args.clips)}개")
        result = composer.concat(args.clips, args.output, args.transition)
    else:
        parser.print_help()
        return

    if result.success:
        print(f"  → 저장: {result.output_path}")
        print(f"  → 길이: {result.duration_seconds:.1f}초")
    else:
        print(f"  → 에러: {result.error}")


if __name__ == "__main__":
    main()
