"""
Content Pipeline - feedback-based regeneration functions.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

from content_pipeline.pipeline_helpers import (
    _build_product_context,
    convert_to_scenes,
    GENERATE_SCENARIO_TEMPLATE_V4,
    REVIEW_SCENARIO_TEMPLATE_V3,
    REGENERATE_SCENARIO_TEMPLATE_V3,
    MEME_EXAMPLE_TEMPLATE_V1,
)
from content_pipeline.pipeline_steps import (
    run_tts_step,
    run_scene_image_step,
    run_video_step,
)


# === 피드백 기반 재생성 함수 ===


def run_scenario_regenerate_step(ad_id: int) -> dict:
    """
    피드백 기반 시나리오 재생성 (DB에 저장된 human_feedback 사용).

    사전 조건:
        - Backend에서 scenario_scripts.review_result에 human_feedback 저장 완료
        - review_result.feedback_type == "human_feedback"

    Args:
        ad_id: 광고 요청 ID

    Returns:
        {
            "status": "ok",
            "script_id": 새로 생성된 script_id,
            "scenes": 재생성된 씬 리스트,
            "title": 시나리오 제목,
            ...
        }
    """
    from content_pipeline.scenario.scenario_database import (
        get_db_connection, load_company_data, load_meme_data,
        save_scenario_to_db,
    )
    from content_pipeline.scenario.scenario_schemas import Scenario
    from content_pipeline.scenario.scenario_nodes import regenerate_scenario_node
    from psycopg2.extras import RealDictCursor

    try:
        # 1. 가장 최근 시나리오 + human_feedback 로드
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT script_id, title, description, hashtags, scenes,
                       meme_id, review_result
                FROM scenario_scripts
                WHERE ad_id = %s
                ORDER BY created_at DESC, script_id DESC
                LIMIT 1
            """, (ad_id,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if not row:
            return {"status": "failed", "error": f"ad_id={ad_id}의 시나리오를 찾을 수 없음"}

        # scenes 데이터 처리 (리스트 또는 딕셔너리)
        scenes_data = row["scenes"]
        if isinstance(scenes_data, list):
            # 리스트를 딕셔너리로 변환 (scene1, scene2, ... - 언더스코어 없음)
            scenes_dict = {}
            for scene in scenes_data:
                if isinstance(scene, dict) and "scene_number" in scene:
                    scene_key = f"scene{scene['scene_number']}"  # scene_1 → scene1
                    # 필수 필드 추가
                    if "scene_type" not in scene:
                        scene_num = scene['scene_number']
                        if scene_num == 1:
                            scene["scene_type"] = "hook"
                        elif scene_num == 4:
                            scene["scene_type"] = "close"
                        else:
                            scene["scene_type"] = "body"
                    scenes_dict[scene_key] = scene
            scenes_data = scenes_dict if scenes_dict else {}
        elif isinstance(scenes_data, dict):
            # 딕셔너리인 경우 키 형식 변환 (scene_1 → scene1)
            scenes_dict = {}
            for key, value in scenes_data.items():
                # scene_1, scene_2 → scene1, scene2
                new_key = key.replace("scene_", "scene") if "scene_" in key else key
                # 필수 필드 추가
                if isinstance(value, dict) and "scene_type" not in value:
                    # scene 번호 추출
                    scene_num = int(new_key.replace("scene", "")) if new_key.startswith("scene") else 0
                    if scene_num == 1:
                        value["scene_type"] = "hook"
                    elif scene_num == 4:
                        value["scene_type"] = "close"
                    else:
                        value["scene_type"] = "body"
                scenes_dict[new_key] = value
            scenes_data = scenes_dict
        else:
            scenes_data = {}

        # hashtags 최소 3개 보장
        hashtags = row.get("hashtags") or []
        if not hashtags or len(hashtags) < 3:
            hashtags = ["#광고", "#추천", "#필수템"]

        previous_scenario = Scenario(
            **scenes_data,
            title=row["title"],
            description=row.get("description") or "",
            hashtags=hashtags,
        )
        review_result = row.get("review_result") or {}

        # 2. company/meme 데이터 로드
        company_data = load_company_data(ad_id)
        meme_id = company_data.pop("meme_id", row["meme_id"])
        meme_data = load_meme_data(meme_id, MEME_EXAMPLE_TEMPLATE_V1)

        # 3. 재생성 노드에 전달할 state 구성
        state = {
            "ad_id": ad_id,
            "meme_id": meme_id,
            "company_data": company_data,
            "meme_data": meme_data,
            "scenario": previous_scenario,
            "generation_type": "human_v1",
            "review_result": review_result,
            "retry_count": 0,
            "human_retry_count": 0,
            "script_id": row["script_id"],
            "generate_template": GENERATE_SCENARIO_TEMPLATE_V4,
            "review_template": REVIEW_SCENARIO_TEMPLATE_V3,
            "regenerate_template": REGENERATE_SCENARIO_TEMPLATE_V3,
            "meme_example_template": MEME_EXAMPLE_TEMPLATE_V1,
            "used_templates": [],
            "error": None,
            "status": "reviewed",
            # 프롬프트 저장용
            "system_prompt": None,
            "user_prompt": None,
            "full_response": None,
            "thinking": None,
        }

        # 4. 재생성 실행
        state = regenerate_scenario_node(state)
        if state["status"] == "failed":
            return {"status": "failed", "error": state.get("error")}

        # 5. 새 시나리오 DB 저장
        new_scenario = state["scenario"]

        # 파인튜닝 모델 사용 여부 확인
        use_finetuned = os.getenv("USE_FINETUNED_SCENARIO", "false").lower() == "true"
        model = "finetuned" if use_finetuned else "gpt-4o"

        script_id = save_scenario_to_db(
            scenario=new_scenario.model_dump(),
            ad_id=ad_id,
            meme_id=meme_id,
            generation_type=state["generation_type"],
            model=model,
            system_prompt=state.get("system_prompt"),
            user_prompt=state.get("user_prompt"),
            full_response=state.get("full_response"),
            thinking=state.get("thinking"),
        )

        scenes = convert_to_scenes(new_scenario)

        return {
            "status": "ok",
            "script_id": script_id,
            "scenes": scenes,
            "title": new_scenario.title,
            "description": new_scenario.description,
            "total_duration": getattr(new_scenario, "total_duration", None),
            "meme_id": meme_id,
            "meme_name": meme_data.get("meme_name", "Unknown"),
            "company_data": company_data,
            "meme_data": meme_data,
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}


def run_image_regeneration_step(
    modification_request: str,
    original_image_url: str,
    *,
    script_id: int = None,
    scene_number: int = None,
    scene_key: str = None,
    character_id: int = None,
    scenario_prompt: str = None,
    character_image_path: str = None,
    character_image_url: str = None,
    product_image_path: str = None,
    product_image_url: str = None,
    aspect_ratio: str = "9:16",
    output_dir: str = None,
    output_path: str = None,
) -> dict:
    """이미지 재생성 + GPT-4o 검수 + 자동 재시도."""
    from content_pipeline.image.runner import run_image_regeneration_with_verification

    return run_image_regeneration_with_verification(
        modification_request=modification_request,
        original_image_url=original_image_url,
        script_id=script_id,
        scene_number=scene_number,
        scene_key=scene_key,
        character_id=character_id,
        scenario_prompt=scenario_prompt,
        character_image_path=character_image_path,
        character_image_url=character_image_url,
        product_image_path=product_image_path,
        product_image_url=product_image_url,
        aspect_ratio=aspect_ratio,
        output_dir=output_dir,
        output_path=output_path,
    )


def run_video_regeneration_step(
    modification_request: str,
    original_video_url: str,
    *,
    scenes_path: str = None,
    script_id: int = None,
    title: str = "Regenerated Video",
    description: str = "",
    company_id: int = 0,
    ad_id: int = None,
    account_id: int = None,
    use_db_prompts: bool = True,
    crossfade: float = 0.3,
    merged_output_path: str = None,
) -> dict:
    """영상 재생성 + Gemini 검수 + 자동 재시도."""
    from content_pipeline.video.runner import run_video_regeneration_with_verification

    return run_video_regeneration_with_verification(
        modification_request=modification_request,
        original_video_url=original_video_url,
        scenes_path=scenes_path,
        script_id=script_id,
        title=title,
        description=description,
        company_id=company_id,
        ad_id=ad_id,
        account_id=account_id,
        use_db_prompts=use_db_prompts,
        crossfade=crossfade,
        merged_output_path=merged_output_path,
    )


def run_content_regenerate_step(
    ad_id: int,
    voice_id: str,
    character_image_url: str = None,
    character_image_path: str = None,
    product_image_url: str = None,
    company_id: int = None,
    character_id: int = None,
    voice_description: str = None,
    clone_prompt_url: str = None,
    character_description: str = None,
) -> dict:
    """
    피드백 기반 콘텐츠 재생성 (시나리오 + TTS + 영상).

    사전 조건:
        - Backend에서 scenario_scripts.review_result에 human_feedback 저장 완료

    Args:
        ad_id: 광고 요청 ID
        voice_id: 승인된 보이스 ID (1단계에서 받은 것)
        character_image_url: 승인된 캐릭터 이미지 URL
        character_image_path: 승인된 캐릭터 이미지 경로
        product_image_url: 제품 이미지 URL

    Returns:
        {
            "status": "ok",
            "scenes": [...],
            "scene_assets": [...],
            "video_url": "...",
            "script_id": ...,
        }
    """
    if not voice_id:
        return {"status": "failed", "error": "voice_id is required"}

    # 1. 시나리오 재생성
    scenario_result = run_scenario_regenerate_step(ad_id)
    if scenario_result.get("status") == "failed":
        return scenario_result

    scenes = scenario_result["scenes"]
    company_data = scenario_result.get("company_data", {})
    meme_data = scenario_result.get("meme_data", {})
    product_context = _build_product_context(company_data, meme_data)

    # 2. TTS 재생성 (씬별 병렬)
    scene_assets = [{"scene_key": scene["scene_key"]} for scene in scenes]

    def _generate_tts(idx, scene):
        dialogue = scene.get("dialogue", "")
        if not dialogue:
            return idx, None
        tts_result = run_tts_step(
            text=dialogue,
            voice_id=voice_id,
            character_id=character_id,
            script_id=scenario_result.get("script_id"),
            scene_key=scene["scene_key"],
            voice_description=voice_description,
            clone_prompt_url=clone_prompt_url,
        )
        return idx, tts_result

    with ThreadPoolExecutor(max_workers=len(scenes)) as executor:
        futures = [executor.submit(_generate_tts, i, scene) for i, scene in enumerate(scenes)]
        for future in as_completed(futures):
            idx, tts_result = future.result()
            if tts_result and tts_result.get("status") == "ok":
                scene_assets[idx]["audio_url"] = tts_result.get("audio_url")
                scene_assets[idx]["duration_seconds"] = tts_result.get("duration_seconds")
                scene_assets[idx]["db_voice_gen_id"] = tts_result.get("db_voice_gen_id")

    # 3. 첫 씬 이미지 생성 (캐릭터 + 제품 합성, 이후 씬은 ComfyUI가 이전 프레임 사용)
    if character_image_url and scenes:
        scene = scenes[0]
        scenario_prompt = scene.get("scenario_prompt", "") or scene.get("visual_description", "")
        if scenario_prompt:
            try:
                img_result = run_scene_image_step(
                    scenario_prompt=scenario_prompt,
                    character_image_url=character_image_url,
                    product_image_url=product_image_url,
                    script_id=scenario_result.get("script_id"),
                    scene_key=scene["scene_key"],
                    character_id=character_id,
                )
                if img_result.get("status") == "ok" and img_result.get("image_url"):
                    scene_assets[0]["image_url"] = img_result["image_url"]
                    if img_result.get("image_path"):
                        scene_assets[0]["image_path"] = img_result["image_path"]
                    scene_assets[0]["db_image_id"] = img_result.get("db_image_id")
            except Exception as exc:
                logger.warning(f"Scene image generation failed for scene 1: {exc}")

    # 4. 영상 재생성 + 병합
    video_result = run_video_step(
        scenes=scenes,
        scene_assets=scene_assets,
        character_image_url=character_image_url,
        character_image_path=character_image_path,
        script_id=scenario_result.get("script_id"),
        company_id=company_id,
        ad_id=ad_id,
        title=scenario_result.get("title"),
        product_context=product_context,
        character_description=character_description,
    )

    if video_result.get("status") == "failed":
        return video_result

    return {
        "status": "ok",
        "scenes": scenes,
        "scene_assets": scene_assets,
        "video_url": video_result.get("video_url"),
        "video_path": video_result.get("video_path"),
        "scene_videos": video_result.get("scene_videos"),
        "title": scenario_result.get("title"),
        "meme_name": scenario_result.get("meme_name"),
        "total_duration": scenario_result.get("total_duration"),
        "script_id": scenario_result.get("script_id"),
    }
