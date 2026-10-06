from __future__ import annotations

from content_pipeline.db import (
    load_ad_request_item_images,
    load_character_image_url,
    load_character_prompt,
    load_latest_script_id_by_ad_id,
    load_scene_prompt,
)
from content_pipeline.image import (
    generate_character_image_node,
    generate_scene_image_node,
    get_image_graph,
    get_initial_state,
)


def run_image_generation(
    *,
    mode: str,
    script_id: int | None,
    ad_id: int | None,
    character_id: int | None,
    scene_number: int | None,
    scene_key: str | None,
    prompt: str | None,
    scenario_prompt: str | None,
    character_prompt: str | None,
    character_image_path: str | None,
    character_image_url: str | None,
    product_image_path: str | None,
    product_image_url: str | None,
    aspect_ratio: str,
    output_dir: str | None,
    output_path: str | None,
    use_db_prompts: bool,
) -> dict:
    resolved_scenario_prompt = scenario_prompt or prompt
    resolved_character_prompt = character_prompt
    resolved_script_id = script_id
    if use_db_prompts:
        if not resolved_script_id and ad_id:
            resolved_script_id = load_latest_script_id_by_ad_id(ad_id)
        if not resolved_character_prompt and character_id:
            resolved_character_prompt = load_character_prompt(character_id)
        if not resolved_scenario_prompt and resolved_script_id:
            scene_index = (scene_number - 1) if scene_number else 0
            resolved_scenario_prompt = load_scene_prompt(resolved_script_id, scene_index)
        if mode != "character" and not character_image_url and not character_image_path and character_id:
            character_image_url = load_character_image_url(character_id)
        if not product_image_url and not product_image_path and ad_id:
            items = load_ad_request_item_images(ad_id)
            if items:
                product_image_url = items[0]

    state = get_initial_state(
        script_id=resolved_script_id,
        character_id=character_id,
        scene_number=scene_number,
        scene_key=scene_key,
        prompt=prompt,
        character_prompt=resolved_character_prompt,
        scenario_prompt=resolved_scenario_prompt,
        product_image_path=product_image_path,
        product_image_url=product_image_url,
        character_image_path=character_image_path,
        character_image_url=character_image_url,
        aspect_ratio=aspect_ratio,
        output_dir=output_dir,
        output_path=output_path,
    )

    if mode == "character":
        return generate_character_image_node(state)
    if mode == "scene":
        return generate_scene_image_node(state)
    graph = get_image_graph()
    return graph.invoke(state)



def run_image_regeneration_with_verification(
    *,
    modification_request: str,
    original_image_url: str,
    script_id: int | None,
    scene_number: int | None,
    scene_key: str | None,
    character_id: int | None,
    scenario_prompt: str | None,
    character_image_path: str | None,
    character_image_url: str | None,
    product_image_path: str | None,
    product_image_url: str | None,
    aspect_ratio: str = "9:16",
    output_dir: str | None = None,
    output_path: str | None = None,
) -> dict:
    """
    이미지 재생성 + 검증 + 자동 재시도
    - 수정 요청을 반영하여 이미지를 재생성하고 VLM으로 검증
    - 점수가 낮으면 자동으로 재시도 (최대 2회)
    - 반환값에 retry_count 포함
    """
    from content_pipeline.image.nodes import (
        verify_image_modification_node,
        verify_image_opencv_node,
    )
    
    max_retries = 2
    verification_result = None
    opencv_result = None
    
    for retry_count in range(max_retries + 1):
        # 1. 재생성
        state = get_initial_state(
            script_id=script_id,
            scene_number=scene_number,
            scene_key=scene_key,
            character_id=character_id,
            scenario_prompt=scenario_prompt,
            product_image_path=product_image_path,
            product_image_url=product_image_url,
            character_image_path=character_image_path,
            character_image_url=character_image_url,
            aspect_ratio=aspect_ratio,
            output_dir=output_dir,
            output_path=output_path,
        )
        state["retry_count"] = retry_count
        
        result = generate_scene_image_node(state)
        
        if result.get("status") == "failed":
            return {
                **result,
                "retry_count": retry_count,
            }
        
        state.update(result)
        state["modification_request"] = modification_request
        state["original_image_url"] = original_image_url

        # 2. OpenCV 1차 검증 (모델 호출 전 결정적 품질 게이트)
        opencv_result = verify_image_opencv_node(state)
        if (
            opencv_result.get("status") == "ok"
            and not opencv_result.get("opencv_passed", True)
            and opencv_result.get("decision") == "auto_retry"
            and retry_count < max_retries
        ):
            # 명백히 깨진 산출물 → VLM 호출 생략하고 바로 재생성
            continue

        # 3. VLM 검증
        verification_result = verify_image_modification_node(state)
        
        if verification_result.get("status") == "failed":
            # 검증 실패 시 재생성 결과만 반환
            return {
                **result,
                "retry_count": retry_count,
                "verification_error": verification_result.get("error"),
            }
        
        # 4. 점수 판단
        decision = verification_result.get("decision")

        if decision == "show_to_user":
            # ≥50점 또는 재시도 한도 초과 - 사용자에게 제시
            break
        elif decision == "auto_retry" and retry_count < max_retries:
            # <50점 - 자동 재시도
            continue
        else:
            break
    
    # 5. 최종 결과 반환
    return {
        **result,
        "opencv_passed": (opencv_result or {}).get("opencv_passed"),
        "opencv_result": (opencv_result or {}).get("opencv_result"),
        "verification_score": verification_result.get("score"),
        "verification_decision": verification_result.get("decision"),
        "verification_message": verification_result.get("message"),
        "retry_count": retry_count,
    }
