from __future__ import annotations

import json
from pathlib import Path
from content_pipeline.db import load_latest_script_id_by_ad_id, load_scenario_prompts
from content_pipeline.video.utils import build_scene_inputs_from_db
from content_pipeline.video.config import load_video_config
from content_pipeline.schema import Scene, ScenarioOutput
from content_pipeline.video import get_initial_state
from content_pipeline.video.nodes import generate_video_node, merge_video_node, verify_video_node


def _read_scenes(path: Path, *, allow_missing_prompt: bool) -> list[dict]:
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
        if not payload.get("prompt") and not allow_missing_prompt:
            raise ValueError(f"scene entry missing prompt: {line}")
        scenes.append(payload)
    if not scenes:
        raise ValueError("scenes file contains no valid entries")
    return scenes


def run_video_from_scenes(
    *,
    scenes_path: str | Path,
    script_id: int | None,
    title: str,
    description: str,
    company_id: int,
    ad_id: int | None,
    account_id: int | None,
    use_db_prompts: bool,
    merged_output_path: str,
) -> dict:
    if not script_id and ad_id:
        script_id = load_latest_script_id_by_ad_id(ad_id)
    if not script_id:
        raise ValueError("script_id is required (or provide ad_id to resolve latest script_id).")
    scenes_data = _read_scenes(Path(scenes_path), allow_missing_prompt=use_db_prompts)
    if use_db_prompts:
        config = load_video_config()
        scenes_data = build_scene_inputs_from_db(script_id=script_id, output_dir=config.output_dir)
    if use_db_prompts:
        db_prompts = load_scenario_prompts(script_id, prompt_kind="action")
        for idx, scene in enumerate(scenes_data):
            if idx < len(db_prompts) and db_prompts[idx]:
                scene["prompt"] = db_prompts[idx]
            else:
                raise ValueError(
                    f"DB prompt missing for scene {idx + 1} (script_id={script_id})"
                )
    total_duration = 0.0
    for item in scenes_data:
        total_duration += float(item.get("duration_seconds") or 5.0)

    scenario_scenes = [
        Scene(
            scene_number=index + 1,
            scene_type="setup",
        )
        for index in range(len(scenes_data))
    ]
    scenario = ScenarioOutput(
        script_id=script_id,
        meme_id=0,
        title=title,
        description=description,
        total_duration=total_duration,
        scenes=scenario_scenes,
    )

    state = get_initial_state(scenario=scenario)
    state["scene_inputs"] = scenes_data
    state["merged_output_path"] = merged_output_path
    state["company_id"] = company_id
    state["ad_id"] = ad_id
    state["account_id"] = account_id
    state["title"] = title
    state["description"] = description

    result = generate_video_node(state)
    if result.get("status") == "ok":
        state.update(result)
        result = merge_video_node(state)

        # 영상 검증 (Gemini 2.5 Pro)
        if result.get("status") == "ok":
            state.update(result)
            try:
                verify_result = verify_video_node(state)
                result["verification_score"] = verify_result.get("score")
                result["verification_decision"] = verify_result.get("decision", "present_to_user")
                result["verification_message"] = verify_result.get("message", "")
            except Exception:
                pass  # 검증 실패해도 영상 결과는 반환

    return result



def run_video_regeneration_with_verification(
    *,
    modification_request: str,
    original_video_url: str,
    scenes_path: str | Path | None = None,
    script_id: int | None = None,
    title: str = "Regenerated Video",
    description: str = "",
    company_id: int = 0,
    ad_id: int | None = None,
    account_id: int | None = None,
    use_db_prompts: bool = True,
    merged_output_path: str | None = None,
) -> dict:
    """
    영상 재생성 + 검증 + 자동 재시도
    - 수정 요청을 반영하여 영상을 재생성하고 Gemini로 검증
    - 점수가 낮으면 자동으로 재시도 (최대 3회)
    - 반환값에 retry_count 포함
    """
    max_retries = 3
    verification_result = None

    if not script_id and ad_id:
        script_id = load_latest_script_id_by_ad_id(ad_id)
    if not script_id:
        return {
            "status": "failed",
            "error": "script_id is required (or provide ad_id to resolve latest script_id).",
            "retry_count": 0,
        }

    for retry_count in range(max_retries + 1):
        # 1. 재생성
        if use_db_prompts:
            config = load_video_config()
            scenes_data = build_scene_inputs_from_db(script_id=script_id, output_dir=config.output_dir)
        elif scenes_path:
            scenes_data = _read_scenes(Path(scenes_path), allow_missing_prompt=False)
        else:
            return {
                "status": "failed",
                "error": "scenes_path is required when use_db_prompts=False",
                "retry_count": retry_count,
            }

        if use_db_prompts:
            db_prompts = load_scenario_prompts(script_id, prompt_kind="action")
            for idx, scene in enumerate(scenes_data):
                if idx < len(db_prompts) and db_prompts[idx]:
                    scene["prompt"] = db_prompts[idx]
                else:
                    return {
                        "status": "failed",
                        "error": f"DB prompt missing for scene {idx + 1} (script_id={script_id})",
                        "retry_count": retry_count,
                    }
        
        total_duration = sum(float(item.get("duration_seconds") or 5.0) for item in scenes_data)
        
        scenario_scenes = [
            Scene(scene_number=index + 1, scene_type="setup")
            for index in range(len(scenes_data))
        ]
        scenario = ScenarioOutput(
            script_id=script_id,
            meme_id=0,
            title=title,
            description=description,
            total_duration=total_duration,
            scenes=scenario_scenes,
        )
        
        state = get_initial_state(scenario=scenario)
        state["scene_inputs"] = scenes_data
        state["merged_output_path"] = merged_output_path
        state["company_id"] = company_id
        state["ad_id"] = ad_id
        state["account_id"] = account_id
        state["title"] = title
        state["description"] = description
        state["retry_count"] = retry_count
        state["modification_request"] = modification_request
        state["original_video_url"] = original_video_url

        # 영상 생성
        result = generate_video_node(state)
        if result.get("status") == "failed":
            return {
                **result,
                "retry_count": retry_count,
            }
        
        state.update(result)
        
        # 영상 병합
        merge_result = merge_video_node(state)
        if merge_result.get("status") == "failed":
            return {
                **merge_result,
                "retry_count": retry_count,
            }
        
        # 2. 검증
        state.update(merge_result)

        verification_result = verify_video_node(state)
        
        if verification_result.get("status") == "failed":
            # 검증 실패 시 재생성 결과만 반환
            return {
                **merge_result,
                "retry_count": retry_count,
                "verification_error": verification_result.get("error"),
            }
        
        # 3. 점수 판단
        decision = verification_result.get("decision")

        if decision == "present_to_user":
            # ≥60점 또는 재시도 한도 초과 - 사용자에게 제시
            break
        elif decision == "auto_retry" and retry_count < max_retries:
            # <60점 - 자동 재시도
            continue
        else:
            break
    
    # 4. 최종 결과 반환
    return {
        **merge_result,
        "verification_score": verification_result.get("score"),
        "verification_decision": verification_result.get("decision"),
        "verification_message": verification_result.get("message"),
        "retry_count": retry_count,
    }
