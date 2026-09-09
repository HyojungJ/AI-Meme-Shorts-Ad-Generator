import argparse

from content_pipeline.image.runner import run_image_generation


def main() -> None:
    # 1. 터미널에서 입력받을 옵션 정의
    parser = argparse.ArgumentParser(description="Nano Banana image generation test")

    # 2. 옵션 추가
    parser.add_argument("--prompt", help="Scenario prompt (legacy)")
    parser.add_argument("--scenario-prompt", help="Scene prompt")
    parser.add_argument("--character-prompt", help="Character prompt")
    parser.add_argument("--character-image-path", help="Local character image path")
    parser.add_argument("--character-image-url", help="Character image URL")
    parser.add_argument("--product-image-path", help="Local product image path")
    parser.add_argument("--product-image-url", help="Product image URL")
    parser.add_argument("--script-id", type=int, help="Scenario script_id for DB linkage")
    parser.add_argument("--ad-id", type=int, help="Ad ID for DB linkage")
    parser.add_argument("--character-id", type=int, help="Character ID for DB linkage")
    parser.add_argument("--scene-number", type=int, help="Scene number for scene_key")
    parser.add_argument("--scene-key", help="Scene key for DB linkage (overrides scene-number)")
    parser.add_argument(
        "--use-db-prompts",
        action="store_true",
        help="Fill missing prompts from DB (scenario_scripts/company_characters). (default on)",
    )
    parser.add_argument(
        "--no-db-prompts",
        action="store_true",
        help="Disable DB prompt auto-fill.",
    )
    parser.add_argument("--aspect-ratio", default="9:16", help="Aspect ratio (default: 9:16)")
    parser.add_argument("--output-dir", help="Output directory (optional)")
    parser.add_argument("--output-path", help="Output path (optional)")
    parser.add_argument(
        "--mode",
        default="both",
        choices=["both", "character", "scene"],
        help="Generation mode: both, character, scene",
    )
    args = parser.parse_args()

    use_db_prompts = args.use_db_prompts or not args.no_db_prompts
    result = run_image_generation(
        mode=args.mode,
        script_id=args.script_id,
        ad_id=args.ad_id,
        character_id=args.character_id,
        scene_number=args.scene_number,
        scene_key=args.scene_key,
        prompt=args.prompt,
        scenario_prompt=args.scenario_prompt,
        character_prompt=args.character_prompt,
        character_image_path=args.character_image_path,
        character_image_url=args.character_image_url,
        product_image_path=args.product_image_path,
        product_image_url=args.product_image_url,
        aspect_ratio=args.aspect_ratio,
        output_dir=args.output_dir,
        output_path=args.output_path,
        use_db_prompts=use_db_prompts,
    )

    # 4. 결과 출력
    print("--- 생성 완료 ---")
    for key in ("status", "error", "db_error", "db_image_id", "db_scene_asset_id"):
        if key in result:
            print(f"{key}:", result.get(key))
    if args.mode == "character":
        print("캐릭터 이미지 저장 경로:", result.get("character_output_path"))
    else:
        print("장면 이미지 저장 경로:", result.get("output_path"))


if __name__ == "__main__":
    main()
