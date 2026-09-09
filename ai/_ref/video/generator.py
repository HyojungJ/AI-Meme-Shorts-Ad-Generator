from dataclasses import dataclass, field
from typing import List

from backend.video.state import get_initial_state
from backend.video.graph import get_video_graph
from backend.video.config import config


@dataclass
class GenerationResult:
    script_id: int
    gen_id: int = None
    final_video_path: str = None
    total_duration: float = 0.0
    total_cost: float = 0.0
    status: str = "pending"
    clips_generated: int = 0
    clips_total: int = 0
    errors: List[str] = field(default_factory=list)


class VideoGenerator:
    def __init__(
        self,
        sora_model: str = None,
        tts_model: str = None,
        output_dir: str = None,
        use_sora_audio: bool = False
    ):
        self.sora_model = sora_model or config.sora_model
        self.tts_model = tts_model or config.tts_model
        self.output_dir = output_dir or config.output_dir
        self.use_sora_audio = use_sora_audio
        self.graph = get_video_graph()

    def generate(self, script_id: int) -> GenerationResult:
        initial_state = get_initial_state(
            script_id=script_id,
            sora_model=self.sora_model,
            tts_model=self.tts_model,
            output_dir=self.output_dir,
            use_sora_audio=self.use_sora_audio
        )

        final_state = self.graph.invoke(initial_state)

        result = GenerationResult(
            script_id=script_id,
            gen_id=final_state.get("gen_id"),
            final_video_path=final_state.get("final_video_path"),
            total_duration=final_state.get("total_duration", 0.0),
            total_cost=final_state.get("total_cost", 0.0),
            status=final_state.get("status", "failed"),
            clips_total=len(final_state.get("scene_clips", [])),
            clips_generated=len([c for c in final_state.get("composed_clips", []) if c]),
            errors=final_state.get("errors", [])
        )

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="영상 생성 (LangGraph)")
    parser.add_argument("--script-id", type=int, required=True, help="시나리오 ID")
    parser.add_argument("--sora-model", default="sora-2", help="Sora 모델")
    parser.add_argument("--tts-model", default="tts-1", help="TTS 모델")
    parser.add_argument("--output-dir", default="data/output", help="출력 디렉토리")
    parser.add_argument("--sora-audio", action="store_true", help="Sora 네이티브 오디오 사용 (TTS 건너뛰기)")
    args = parser.parse_args()

    generator = VideoGenerator(
        sora_model=args.sora_model,
        tts_model=args.tts_model,
        output_dir=args.output_dir,
        use_sora_audio=args.sora_audio
    )

    result = generator.generate(args.script_id)

    print(f"\n=== 생성 결과 ===")
    print(f"상태: {result.status}")
    print(f"gen_id: {result.gen_id}")
    print(f"씬 클립: {result.clips_generated}/{result.clips_total}")
    print(f"길이: {result.total_duration:.1f}초")
    print(f"비용: ${result.total_cost:.2f}")

    if result.final_video_path:
        print(f"영상: {result.final_video_path}")

    if result.errors:
        print(f"에러: {result.errors}")


if __name__ == "__main__":
    main()
