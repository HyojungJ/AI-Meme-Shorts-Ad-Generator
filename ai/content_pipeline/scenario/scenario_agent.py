"""
시나리오 생성 에이전트 실행
"""
from dotenv import load_dotenv
from typing import List
from content_pipeline.scenario.scenario_graph import create_scenario_graph
from content_pipeline.scenario.scenario_state import ScenarioState
from content_pipeline.scenario.scenario_schemas import Scenario
from content_pipeline.scenario.scenario_database import (
    load_latest_scenario_for_regeneration,
    load_company_data,
    load_meme_data
)
from content_pipeline.scenario.scenario_nodes import (
    regenerate_scenario_node, 
    save_scenario_node
)


def run_scenario_agent(
        ad_id: int, 
        generate_template: str,
        review_template: str,
        regenerate_template: str,
        meme_example_template: str,
        used_templates: List[str]
    ) -> ScenarioState:
    """
    시나리오 생성 에이전트 실행
    
    Args:
        ad_id: 광고 ID (company 테이블)
        meme_id: 밈 ID
        
    Returns:
        최종 State (script_id 포함)
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 초기 State 생성
    initial_state: ScenarioState = {
        "ad_id": ad_id,
        "meme_id": None,
        "company_data": None,
        "meme_data": None,
        "scenario": None,
        "generation_type": "initial",
        "review_result": None,
        "retry_count": 0,
        "human_retry_count": 0,
        "script_id": None,
        "generate_template": generate_template,
        "review_template": review_template,
        "regenerate_template": regenerate_template,
        "meme_example_template": meme_example_template,
        "used_templates": used_templates,
        "formatted_prompt": None,
        "error": None,
        "status": "running",
        # 프롬프트 저장용
        "system_prompt": None,
        "user_prompt": None,
        "full_response": None,
        "thinking": None,
    }

    # 그래프 생성
    graph = create_scenario_graph()
    
    # 실행
    result = graph.invoke(initial_state)
    
    return result


def regenerate_from_feedback(
        ad_id: int,
        regenerate_template: str,
        meme_example_template: str
    ) -> int:
    """
    휴먼 피드백 기반 시나리오 재생성
    
    Args:
        ad_id: 광고 ID
        regenerate_template: 재생성 프롬프트 템플릿
        meme_example_template: 밈 예시 템플릿
        
    Returns:
        새로 생성된 script_id
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 1. DB에서 데이터 로드
    latest_script = load_latest_scenario_for_regeneration(ad_id)
    company_data = load_company_data(ad_id)
    meme_data = load_meme_data(
        latest_script["meme_id"],
        meme_example_template
    )
    
    # 2. 기존 시나리오를 Pydantic 객체로 변환
    scenario = Scenario(
        **latest_script["scenes"],
        title=latest_script["title"],
        description=latest_script["description"],
        hashtags=latest_script["hashtags"],
    )
    
    # 3. State 구성
    state: ScenarioState = {
        "ad_id": ad_id,
        "meme_id": latest_script["meme_id"],
        "company_data": company_data,
        "meme_data": meme_data,
        "scenario": scenario,
        "generation_type": "human_v1",
        "review_result": latest_script["review_result"],
        "retry_count": 0,
        "human_retry_count": 1,
        "script_id": None,
        "generate_template": "",
        "review_template": "",
        "regenerate_template": regenerate_template,
        "meme_example_template": meme_example_template,
        "used_templates": [],
        "formatted_prompt": None,
        "error": None,
        "status": "running",
        # 프롬프트 저장용
        "system_prompt": None,
        "user_prompt": None,
        "full_response": None,
        "thinking": None,
    }
    
    # 4. regenerate → save 실행
    state = regenerate_scenario_node(state)
    
    if state["status"] == "failed":
        raise RuntimeError(f"재생성 실패: {state.get('error')}")
    
    state = save_scenario_node(state)
    
    if state["status"] == "failed":
        raise RuntimeError(f"저장 실패: {state.get('error')}")
    
    return state["script_id"]


if __name__ == "__main__":
    from content_pipeline.scenario.prompts.generate_scenario_templates import GENERATE_SCENARIO_TEMPLATE_V4
    from content_pipeline.scenario.prompts.review_scenario_templates import REVIEW_SCENARIO_TEMPLATE_V3
    from content_pipeline.scenario.prompts.regenerate_scenario_templates import REGENERATE_SCENARIO_TEMPLATE_V3
    from content_pipeline.scenario.prompts.meme_example_templates import MEME_EXAMPLE_TEMPLATE_V1
    
    # 초기 생성 예시
    result = run_scenario_agent(
        ad_id=1,
        generate_template=GENERATE_SCENARIO_TEMPLATE_V4,
        review_template=REVIEW_SCENARIO_TEMPLATE_V3,
        regenerate_template=REGENERATE_SCENARIO_TEMPLATE_V3,
        meme_example_template=MEME_EXAMPLE_TEMPLATE_V1,
        used_templates=[
            "scenario_generation:v4",
            "scenario_review:v3",
            "scenario_regeneration:v3",
            "meme_example:v1"
        ]
    )
    
    # 휴먼 피드백 재생성 예시
    new_script_id = regenerate_from_feedback(
        ad_id=1,
        regenerate_template=REGENERATE_SCENARIO_TEMPLATE_V3,
        meme_example_template=MEME_EXAMPLE_TEMPLATE_V1
    )