import argparse
import json
from pathlib import Path

from content_pipeline.video import VideoService, load_video_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a scene video with the video service.")
    parser.add_argument("--prompt", required=True, help="Scene prompt text.")
    parser.add_argument("--reference-image-path", help="Local reference image path.")
    parser.add_argument("--reference-image-url", help="Reference image URL.")
    parser.add_argument("--audio-path", help="Local audio path.")
    parser.add_argument("--audio-url", help="Audio URL.")
    parser.add_argument("--duration-seconds", type=float, default=5.0)
    parser.add_argument("--output-path", help="Override output path for the video file.")
    parser.add_argument("--mock-sample-path", help="Use a real mp4 as mock output.")
    args = parser.parse_args()

    config = load_video_config()
    service = VideoService(config)

    result = service.generate_video(
        prompt=args.prompt,
        audio_path=args.audio_path,
        audio_url=args.audio_url,
        reference_image_path=args.reference_image_path,
        reference_image_url=args.reference_image_url,
        duration_seconds=args.duration_seconds,
        output_path=args.output_path,
        mock_sample_path=args.mock_sample_path,
    )

    print("--- video generated ---")
    print("video_url:", result.video_url)
    print("storage_path:", result.storage_path)
    print("duration_seconds:", result.duration_seconds)
    print("size_bytes:", result.size_bytes)


if __name__ == "__main__":
    main()
