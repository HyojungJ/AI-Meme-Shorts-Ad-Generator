#!/usr/bin/env python
import argparse
from content_pipeline.video.runner import run_video_from_scenes


def main() -> int:
    parser = argparse.ArgumentParser(description="Run video graph using scenes.jsonl as inputs.")
    parser.add_argument("--scenes", default="data/scenes/scenes.jsonl", help="Path to scenes.jsonl.",)
    parser.add_argument("--title", default="Scene merge test", help="Scenario title.",)
    parser.add_argument("--description", default="", help="Scenario description.",)
    parser.add_argument("--company-id", type=int, required=True, help="Company ID for videos table linkage.",)
    parser.add_argument("--ad-id", type=int, help="Ad ID for videos table linkage.",)
    parser.add_argument("--account-id", type=int, help="Account ID for videos table linkage.",)
    parser.add_argument("--script-id", type=int, help="Scenario script_id for DB linkage.",)
    parser.add_argument("--use-db-prompts", action="store_true", help="Fill missing scene prompts from scenario_scripts.scenes. (default on)")
    parser.add_argument("--no-db-prompts", action="store_true", help="Disable DB prompt auto-fill.",)
    parser.add_argument("--crossfade", type=float, default=0.3, help="Crossfade seconds for merge.",)
    parser.add_argument("--merged-output-path", default="data/video/merged.mp4", help="Output path for merged video.",)
    args = parser.parse_args()

    use_db_prompts = args.use_db_prompts or not args.no_db_prompts
    if not args.script_id and not args.ad_id:
        parser.error("--script-id is required (or provide --ad-id to resolve latest script_id).")

    result = run_video_from_scenes(
        scenes_path=args.scenes,
        script_id=args.script_id,
        title=args.title,
        description=args.description,
        company_id=args.company_id,
        ad_id=args.ad_id,
        account_id=args.account_id,
        use_db_prompts=use_db_prompts,
        crossfade=args.crossfade,
        merged_output_path=args.merged_output_path,
    )
    print("--- 생성 완료 ---")
    for key in ("status", "error"):
        if key in result:
            print(f"{key}: {result[key]}")
    if "scene_outputs" in result:
        print("장면 영상 결과:", result["scene_outputs"])
    for key in ("최종 영상 결과 경로", "merged_video_url", "merged_storage_path"):
        if key in result:
            print(f"{key}: {result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
