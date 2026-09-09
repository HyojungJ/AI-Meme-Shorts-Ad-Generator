import os

from pathlib import Path
from typing import Literal
from dataclasses import dataclass

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TTSResult:
    audio_path: str
    duration_seconds: float
    text_length: int
    cost_usd: float
    error: str = None


CHARACTER_VOICES = {
    "부장": "onyx",    # 저음, 무게감
    "사원": "alloy",   # 중성, 젊음
}


class TTSGenerator:
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    COSTS = {
        "tts-1": 15.0,
        "tts-1-hd": 30.0,
    }

    def __init__(
        self,
        model: Literal["tts-1", "tts-1-hd"] = "tts-1",
        default_voice: str = "alloy",
        output_dir: str = "data/audio",
        api_key: str = None
    ):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.default_voice = default_voice
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        text: str,
        output_path: str = None,
        voice: str = None,
        character: str = None,
        speed: float = 1.0
    ) -> TTSResult:
        if character and character in CHARACTER_VOICES:
            voice = CHARACTER_VOICES[character]
        voice = voice or self.default_voice

        if not output_path:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            output_path = self.output_dir / f"tts_{text_hash}.mp3"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3"
            )

            response.stream_to_file(str(output_path))
            duration = self._get_audio_duration(str(output_path))
            cost = (len(text) / 1_000_000) * self.COSTS[self.model]

            return TTSResult(
                audio_path=str(output_path),
                duration_seconds=duration,
                text_length=len(text),
                cost_usd=cost
            )

        except Exception as e:
            return TTSResult(
                audio_path="",
                duration_seconds=0,
                text_length=len(text),
                cost_usd=0,
                error=str(e)
            )

    def generate_and_concat(
        self,
        items: list[dict],
        output_path: str,
        temp_dir: str = None
    ) -> TTSResult:
        import subprocess
        import tempfile

        if not items:
            return TTSResult("", 0, 0, 0, "No items to generate")

        temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.mkdtemp())
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_files = []
        total_cost = 0
        total_length = 0

        for i, item in enumerate(items):
            temp_path = temp_dir / f"part_{i}.mp3"
            result = self.generate(
                text=item["text"],
                output_path=str(temp_path),
                character=item.get("character")
            )
            if result.error:
                return TTSResult("", 0, 0, 0, f"TTS failed for item {i}: {result.error}")

            temp_files.append(str(temp_path))
            total_cost += result.cost_usd
            total_length += result.text_length

        output_path = str(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        if len(temp_files) == 1:
            import shutil
            shutil.copy(temp_files[0], output_path)
        else:
            list_file = temp_dir / "concat_list.txt"
            with open(list_file, "w") as f:
                for tf in temp_files:
                    abs_path = str(Path(tf).resolve())
                    f.write(f"file '{abs_path}'\n")

            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c", "copy", output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return TTSResult("", 0, 0, 0, f"FFmpeg concat failed: {result.stderr}")

        duration = self._get_audio_duration(output_path)

        return TTSResult(
            audio_path=output_path,
            duration_seconds=duration,
            text_length=total_length,
            cost_usd=total_cost
        )

    def _get_audio_duration(self, audio_path: str) -> float:
        try:
            from mutagen.mp3 import MP3
            audio = MP3(audio_path)
            return audio.info.length
        except ImportError:
            try:
                import subprocess
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
                return len(open(audio_path, "rb").read()) / 16000
        except Exception:
            return 0.0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI TTS 생성")
    parser.add_argument("--text", type=str, required=True, help="텍스트")
    parser.add_argument("--character", type=str, help="캐릭터 (부장/사원)")
    parser.add_argument("--voice", type=str, help="음성 (alloy, onyx 등)")
    parser.add_argument("--output", "-o", help="출력 경로")
    parser.add_argument("--model", default="tts-1", help="모델")
    args = parser.parse_args()

    generator = TTSGenerator(model=args.model)

    print(f"[TTS] 생성 중: '{args.text[:30]}...'")
    result = generator.generate(
        text=args.text,
        output_path=args.output,
        character=args.character,
        voice=args.voice
    )

    if result.error:
        print(f"  → 에러: {result.error}")
    else:
        print(f"  → 저장: {result.audio_path}")
        print(f"  → 길이: {result.duration_seconds:.1f}초")
        print(f"  → 비용: ${result.cost_usd:.4f}")


if __name__ == "__main__":
    main()
