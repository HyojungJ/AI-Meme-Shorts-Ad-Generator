import argparse

from content_pipeline.voice.runner import run_voice_generation


def main() -> None:
    parser = argparse.ArgumentParser(description="ElevenLabs voice generate test (graph)")

    # 필수 입력 항목들
    parser.add_argument("--text", help="Text to synthesize.")

    # 음성 소스 선택 (기존 음성 ID 또는 새 음성 디자인)
    voice_source = parser.add_mutually_exclusive_group(required=True)
    voice_source.add_argument("--voice-id", help="Existing ElevenLabs voice ID.")
    voice_source.add_argument("--voice-description", help="Description for text-to-voice design (triggers voice creation).", )

    # 디자인용 추가 옵션
    parser.add_argument("--voice-name", help="Required when using --voice-description.")
    parser.add_argument("--design-text", help="Design prompt text (defaults to --text).")
    parser.add_argument("--preview-index", type=int, default=0)
    parser.add_argument("--ttv-model-id", help="Override ELEVENLABS_TTV_MODEL_ID for voice design.")
    parser.add_argument(
        "--prefer-existing-voice",
        action="store_true",
        default=True,
        help="Prefer existing company_characters.elevenlabs_voice_id when available.",
    )
    parser.add_argument(
        "--force-new-voice",
        action="store_true",
        help="Create a new voice even if an existing voice_id is available.",
    )

    # 선택 입력 항목들 (기본값 있음)
    parser.add_argument("--user-id", default="test-user", help="Storage user ID.")
    parser.add_argument("--stability", type=float, default=0.5)
    parser.add_argument("--similarity-boost", type=float, default=0.5)
    parser.add_argument("--style", type=float, default=0.0)
    parser.add_argument("--use-speaker-boost", action="store_true", default=True)
    parser.add_argument("--speed", type=float, default=1.0)

    parser.add_argument("--script-id", type=int, help="Scenario script_id for DB linkage")
    parser.add_argument("--character-id", type=int, help="Character ID for DB linkage")
    parser.add_argument("--scene-number", type=int, help="Scene number for scene_key")
    parser.add_argument("--scene-key", help="Scene key for DB linkage (overrides scene-number)")
    parser.add_argument("--use-db-text", action="store_true", help="Fill missing text from scenario_scripts/ad_requests. (default on)",)
    parser.add_argument("--no-db-text", action="store_true", help="Disable DB text auto-fill.",)
    args = parser.parse_args()

    if args.voice_description and not args.voice_name:
        parser.error("--voice-name is required when using --voice-description.")

    settings = {
        "stability": args.stability,
        "similarity_boost": args.similarity_boost,
        "style": args.style,
        "use_speaker_boost": args.use_speaker_boost,
        "speed": args.speed,
    }

    use_db_text = args.use_db_text or not args.no_db_text
    try:
        result = run_voice_generation(
            text=args.text,
            voice_id=args.voice_id,
            voice_description=args.voice_description,
            voice_name=args.voice_name,
            design_text=args.design_text,
            preview_index=args.preview_index,
            ttv_model_id=args.ttv_model_id,
            user_id=args.user_id,
            settings=settings,
            script_id=args.script_id,
            character_id=args.character_id,
            scene_number=args.scene_number,
            scene_key=args.scene_key,
            use_db_text=use_db_text,
            prefer_existing_voice=(not args.force_new_voice),
        )
    except ValueError as exc:
        parser.error(str(exc))

    print("--- 생성 완료 ---")
    for key in ("status", "error", "db_error", "db_voice_gen_id", "db_scene_asset_id"):
        if key in result:
            print(f"{key}:", result.get(key))
    print("오디오 URL:", result.get("audio_url"))
    print("저장 경로:", result.get("storage_path"))
    print("파일 크기(bytes):", result.get("size_bytes"))


if __name__ == "__main__":
    main()
