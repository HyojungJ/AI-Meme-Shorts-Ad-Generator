"""
시나리오 생성 에이전트 노드 함수들
각 노드는 State를 입력받아 수정된 State를 반환
"""
import os
from langchain_openai import ChatOpenAI

from content_pipeline.scenario.scenario_state import ScenarioState
from content_pipeline.scenario.scenario_schemas import Scenario, ReviewResult
from content_pipeline.scenario.scenario_database import (
    load_company_data,
    load_meme_data,
    save_scenario_to_db,
    update_review_result_to_db,
)

def _use_finetuned() -> bool:
    return os.getenv("USE_FINETUNED_SCENARIO", "false").lower() == "true"


def generate_scenario_node(state: ScenarioState) -> ScenarioState:
    """
    데이터 로드 + 시나리오 생성
    
    Args:
        state: 현재 상태 (ad_id, meme_id 필요)
        
    Returns:
        업데이트된 state (company_data, meme_data, scenarios 추가)
    """
    try:
        # 1. DB에서 데이터 로드
        company_data = load_company_data(state["ad_id"])
        
        state["meme_id"] = company_data["meme_id"]
        
        meme_data = load_meme_data(
            state["meme_id"],
            state["meme_example_template"]
        )
        
        # 2. 프롬프트 포매팅
        prompt = state["generate_template"].format(
            **company_data,
            **meme_data
        )
        
        # 3. LLM으로 시나리오 생성
        if _use_finetuned():
            from content_pipeline.scenario.finetuned_client import (
                generate_with_finetuned,
                FINETUNED_SYSTEM_PROMPT,
            )
            from content_pipeline.scenario.finetuned_prompts import (
                INSTRUCTION_VARIANTS,
                USER_PROMPT_TEMPLATES,
            )

            instruction = INSTRUCTION_VARIANTS[0]
            template = USER_PROMPT_TEMPLATES[0]
            finetuned_prompt = template.format(
                company_name=company_data["company_name"],
                item_name=company_data["item_name"],
                item_category=company_data["item_category"],
                item_description=company_data["item_description"],
                voice_design_prompt=company_data["voice_design_prompt"],
                meme_name=meme_data["meme_name"],
                definition=meme_data["definition"],
                key_phrase=meme_data["key_phrase"],
                usage_examples=meme_data["usage_examples"],
                instruction=instruction,
            )
            result = generate_with_finetuned(system_prompt=FINETUNED_SYSTEM_PROMPT, user_prompt=finetuned_prompt)
            scenario = result.scenario
            state["system_prompt"] = result.system_prompt
            state["user_prompt"] = result.user_prompt
            state["full_response"] = result.full_response
            state["thinking"] = result.thinking
        else:
            llm = ChatOpenAI(temperature=0, model="gpt-4o")
            structured_llm = llm.with_structured_output(Scenario)
            scenario = structured_llm.invoke(prompt)
            state["system_prompt"] = None
            state["user_prompt"] = None
            state["full_response"] = None
            state["thinking"] = None

        # 4. State 업데이트
        state["company_data"] = company_data
        state["meme_data"] = meme_data
        state["formatted_prompt"] = prompt
        state["scenario"] = scenario
        state["generation_type"] = "initial"
        state["status"] = "scenario_generated"
        
    except Exception as e:
        state["error"] = f"시나리오 생성 실패: {str(e)}"
        state["status"] = "failed"
    
    return state


def save_scenario_node(state: ScenarioState) -> ScenarioState:
    """
    생성된 시나리오를 DB에 저장
    
    Args:
        state: 현재 상태 (scenario 필요)
        
    Returns:
        업데이트된 state (script_id 추가)
    """
    # review_result 기반 최종 상태 결정 (should_regenerate에서 이관)
    review = state.get("review_result")
    if review and review.get("feedback_type") == "llm_review":
        if review.get("approved"):
            state["status"] = "completed"
        elif state.get("retry_count", 0) >= 3:
            state["error"] = "최대 재시도 횟수 초과"
            state["status"] = "failed"

    # 이전 단계 실패 시 스킵
    if state["status"] == "failed" or state["scenario"] is None:
        return state

    try:
        scenario = state["scenario"]

        # initial일 때만 used_templates 전달
        used_templates = state["used_templates"] if state["generation_type"] == "initial" else None

        # 파인튜닝 모델 사용 시 모델명 변경
        model = "finetuned" if _use_finetuned() else "gpt-4o"

        # DB 저장
        script_id = save_scenario_to_db(
            scenario=scenario.model_dump(),
            ad_id=state["ad_id"],
            meme_id=state["meme_id"],
            generation_type=state["generation_type"],
            used_templates=used_templates,
            model=model,
            system_prompt=state.get("system_prompt"),
            user_prompt=state.get("user_prompt"),
            full_response=state.get("full_response"),
            thinking=state.get("thinking"),
        )

        # State 업데이트
        state["script_id"] = script_id
        state["status"] = "saved"

        # 리뷰 결과가 있으면 함께 저장
        if state.get("review_result"):
            update_review_result_to_db(script_id, state["review_result"])

    except Exception as e:
        state["error"] = f"DB 저장 실패: {str(e)}"
        state["status"] = "failed"
    
    return state


def review_scenario_node(state: ScenarioState) -> ScenarioState:
    """
    시나리오 검수 노드 (브랜드 안전성 및 품질 평가)
    
    Args:
        state: 현재 상태 (scenario 필요)
        
    Returns:
        업데이트된 state (review_result 추가)
    """
    # 이전 단계 실패 시 스킵
    if state["status"] == "failed" or state["scenario"] is None:
        return state
    
    try:
        # 첫 번째 시나리오 검수
        scenario = state["scenario"]
        
        # 검수 프롬프트 포매팅
        review_prompt = state["review_template"].format(
            company_name=state["company_data"]["company_name"],
            item_name=state["company_data"]["item_name"],
            item_description=state["company_data"]["item_description"],
            voice_design_prompt=state["company_data"]["voice_design_prompt"],    
            meme_name=state["meme_data"]["meme_name"],
            definition=state["meme_data"]["definition"],               
            key_phrase=state["meme_data"]["key_phrase"],               
            scenario_json=scenario.model_dump_json(indent=2)
        )
        
        # LLM으로 검수 실행
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        structured_llm = llm.with_structured_output(ReviewResult)
        review_result = structured_llm.invoke(review_prompt)
        
        # LLM 검수 결과를 통일된 형식으로 변환
        scene_feedback = {}
        for scene_review in review_result.scene_reviews:
            if scene_review.feedback_items:
                # 각 씬의 모든 피드백을 하나의 문자열로 합침
                feedback_text = ". ".join(
                    item.description for item in scene_review.feedback_items
                )
                scene_feedback[scene_review.scene_key] = feedback_text


        # State 업데이트
        state["review_result"] = {
            "feedback_type": "llm_review",
            "scene_reviews": [sr.model_dump() for sr in review_result.scene_reviews],
            "scene_feedback": scene_feedback,
            "approved": review_result.approved,
            "total_score": review_result.total_score
        }
        state["status"] = "reviewed"

        if state.get("script_id"):
            update_review_result_to_db(state["script_id"], state["review_result"])

    except Exception as e:
        state["error"] = f"검수 실패: {str(e)}"
        state["status"] = "failed"
    
    return state


def regenerate_scenario_node(state: ScenarioState) -> ScenarioState:
    """
    피드백 기반 시나리오 재생성
    
    Args:
        state: 현재 상태 (scenario, review_result 필요)
        
    Returns:
        업데이트된 state (scenario 갱신, retry_count 증가)
    """
    # 이전 단계 실패 시 스킵
    if state["status"] == "failed" or state["scenario"] is None:
        return state
    
    try:
        review_result = state["review_result"]
        
        # 재생성 횟수 및 타입 설정
        if review_result["feedback_type"] == "llm_review":
            state["retry_count"] += 1
            state["generation_type"] = f"llm_review_v{state['retry_count']}"
        elif review_result["feedback_type"] == "human_feedback":
            state["human_retry_count"] += 1
            state["generation_type"] = f"human_v{state['human_retry_count']}"

        # 이전 시나리오
        previous_scenario = state["scenario"]
        
        # 피드백 텍스트 생성 (씬별)
        scene_feedback = review_result.get("scene_feedback", {})
        feedback_lines = [
            f"{scene_key}: {feedback}"
            for scene_key, feedback in scene_feedback.items()
        ]
        
        feedback_text = "\n".join(feedback_lines)

        # 재생성 프롬프트 포매팅
        regenerate_prompt = state["regenerate_template"].format(
            original_scenario=previous_scenario.model_dump_json(indent=2),
            feedback=feedback_text,
            company_name=state["company_data"]["company_name"],
            item_name=state["company_data"]["item_name"],
            item_category=state["company_data"]["item_category"],
            item_description=state["company_data"]["item_description"],
            voice_design_prompt=state["company_data"]["voice_design_prompt"],
            meme_name=state["meme_data"]["meme_name"],
            definition=state["meme_data"]["definition"],
            key_phrase=state["meme_data"]["key_phrase"],
            usage_examples=state["meme_data"]["usage_examples"]  
        )
        
        # LLM으로 재생성
        if _use_finetuned():
            from content_pipeline.scenario.finetuned_client import (
                generate_with_finetuned,
                FINETUNED_SYSTEM_PROMPT,
            )
            from content_pipeline.scenario.finetuned_prompts import (
                INSTRUCTION_VARIANTS,
                USER_PROMPT_TEMPLATES,
            )

            instruction = INSTRUCTION_VARIANTS[0]
            template = USER_PROMPT_TEMPLATES[0]
            finetuned_prompt = template.format(
                company_name=state["company_data"]["company_name"],
                item_name=state["company_data"]["item_name"],
                item_category=state["company_data"]["item_category"],
                item_description=state["company_data"]["item_description"],
                voice_design_prompt=state["company_data"]["voice_design_prompt"],
                meme_name=state["meme_data"]["meme_name"],
                definition=state["meme_data"]["definition"],
                key_phrase=state["meme_data"]["key_phrase"],
                usage_examples=state["meme_data"]["usage_examples"],
                instruction=instruction,
            )
            if feedback_text.strip():
                finetuned_prompt += f"\n\n# 수정 요청 사항\n{feedback_text}"
            result = generate_with_finetuned(
                system_prompt=FINETUNED_SYSTEM_PROMPT, user_prompt=finetuned_prompt,
            )
            regenerated_scenario = result.scenario
            state["system_prompt"] = result.system_prompt
            state["user_prompt"] = result.user_prompt
            state["full_response"] = result.full_response
            state["thinking"] = result.thinking
        else:
            llm = ChatOpenAI(temperature=0.3, model="gpt-4o")
            structured_llm = llm.with_structured_output(Scenario)
            regenerated_scenario = structured_llm.invoke(regenerate_prompt)
            state["system_prompt"] = None
            state["user_prompt"] = None
            state["full_response"] = None
            state["thinking"] = None

        # State 업데이트
        state["scenario"] = regenerated_scenario
        state["status"] = "scenario_regenerated"
        
    except Exception as e:
        state["error"] = f"재생성 실패: {str(e)}"
        state["status"] = "failed"
    
    return state