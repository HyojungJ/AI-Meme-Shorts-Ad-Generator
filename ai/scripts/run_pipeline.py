"""E2E Pipeline Test Script

Usage:
    uv run python -m scripts.run_pipeline --ad-id 1 --meme-id 1 --voice-id xxx
    uv run python -m scripts.run_pipeline --scenario --ad-id 1 --meme-id 1
    uv run python -m scripts.run_pipeline --character --prompt "친근한 캐릭터"
    uv run python -m scripts.run_pipeline --voice --name "테스터" --desc "밝은 목소리"
"""
import argparse

from content_pipeline.pipeline import (
    run_content_generation_step,
    run_scenario_step,
    run_character_step,
    run_voice_design_step,
    run_tts_step,
    run_scene_image_step,
)


def test_scenario_step(ad_id: int, meme_id: int):
    """시나리오 모듈 테스트."""
    print("\n=== Scenario Step Test ===")

    result = run_scenario_step(ad_id=ad_id, meme_id=meme_id)

    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Total Duration: {result.get('total_duration')}")

    scenes = result.get("scenes", [])
    print(f"Scenes: {len(scenes)}")
    for scene in scenes:
        dialogue = scene.get("dialogue", "")[:30]
        print(f"  - {scene.get('scene_key')}: {dialogue}...")

    return result


def test_character_step(prompt: str):
    """캐릭터 이미지 생성 테스트."""
    print("\n=== Character Step Test ===")

    result = run_character_step(prompt=prompt, aspect_ratio="9:16")

    print(f"Status: {result.get('status')}")
    print(f"Image URL: {result.get('image_url')}")
    print(f"Image Path: {result.get('image_path')}")

    return result


def test_voice_design_step(voice_name: str, voice_description: str):
    """Voice Design 테스트."""
    print("\n=== Voice Design Step Test ===")

    result = run_voice_design_step(
        voice_name=voice_name,
        voice_description=voice_description,
    )

    print(f"Status: {result.get('status')}")
    print(f"Voice ID: {result.get('voice_id')}")

    return result


def test_tts_step(text: str, voice_id: str):
    """TTS 생성 테스트."""
    print("\n=== TTS Step Test ===")

    result = run_tts_step(text=text, voice_id=voice_id)

    print(f"Status: {result.get('status')}")
    print(f"Audio URL: {result.get('audio_url')}")
    print(f"Duration: {result.get('duration_seconds')}s")

    return result


def test_full_pipeline(ad_id: int, meme_id: int, voice_id: str, character_image_url: str = None):
    """전체 파이프라인 테스트."""
    print("\n=== Full Pipeline Test ===")

    result = run_content_generation_step(
        ad_id=ad_id,
        meme_id=meme_id,
        voice_id=voice_id,
        character_image_url=character_image_url,
    )

    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Meme: {result.get('meme_name')}")
    print(f"Total Duration: {result.get('total_duration')}")

    scenes = result.get("scenes", [])
    print(f"Scenes: {len(scenes)}")

    assets = result.get("scene_assets", [])
    print(f"Assets: {len(assets)}")
    for asset in assets:
        print(f"  - {asset.get('scene_key')}: audio={bool(asset.get('audio_url'))}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Content Pipeline Test")
    parser.add_argument("--ad-id", type=int, help="ad_request ID")
    parser.add_argument("--meme-id", type=int, help="meme ID")
    parser.add_argument("--voice-id", type=str, help="ElevenLabs voice ID")
    parser.add_argument("--character-url", type=str, help="Character image URL")

    # Step-specific tests
    parser.add_argument("--scenario", action="store_true", help="Test scenario step only")
    parser.add_argument("--character", action="store_true", help="Test character step only")
    parser.add_argument("--voice", action="store_true", help="Test voice design step only")
    parser.add_argument("--tts", action="store_true", help="Test TTS step only")

    # Step-specific params
    parser.add_argument("--prompt", type=str, help="Character prompt")
    parser.add_argument("--name", type=str, help="Voice name")
    parser.add_argument("--desc", type=str, help="Voice description")
    parser.add_argument("--text", type=str, help="TTS text")

    args = parser.parse_args()

    if args.scenario:
        if not args.ad_id or not args.meme_id:
            print("Error: --ad-id and --meme-id required for scenario test")
            return
        test_scenario_step(args.ad_id, args.meme_id)

    elif args.character:
        if not args.prompt:
            print("Error: --prompt required for character test")
            return
        test_character_step(args.prompt)

    elif args.voice:
        if not args.name or not args.desc:
            print("Error: --name and --desc required for voice test")
            return
        test_voice_design_step(args.name, args.desc)

    elif args.tts:
        if not args.text or not args.voice_id:
            print("Error: --text and --voice-id required for TTS test")
            return
        test_tts_step(args.text, args.voice_id)

    elif args.ad_id and args.meme_id and args.voice_id:
        test_full_pipeline(args.ad_id, args.meme_id, args.voice_id, args.character_url)

    else:
        print("Usage examples:")
        print("  # Full pipeline")
        print("  uv run python -m scripts.run_pipeline --ad-id 1 --meme-id 1 --voice-id xxx")
        print()
        print("  # Scenario only")
        print("  uv run python -m scripts.run_pipeline --scenario --ad-id 1 --meme-id 1")
        print()
        print("  # Character only")
        print('  uv run python -m scripts.run_pipeline --character --prompt "친근한 캐릭터"')
        print()
        print("  # Voice design only")
        print('  uv run python -m scripts.run_pipeline --voice --name "테스터" --desc "밝은 목소리"')
        print()
        print("  # TTS only")
        print('  uv run python -m scripts.run_pipeline --tts --text "안녕하세요" --voice-id xxx')


if __name__ == "__main__":
    main()
