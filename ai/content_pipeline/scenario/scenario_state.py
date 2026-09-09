"""
시나리오 생성 에이전트 State 정의
노드 간 데이터 전달을 위한 상태 구조
"""
from typing import TypedDict, Optional, List, Dict, Any
from content_pipeline.scenario.scenario_schemas import Scenario


class ScenarioState(TypedDict):
    """시나리오 생성 에이전트의 전체 상태"""
    
    # 입력 데이터
    ad_id: int  # 광고 ID (company 테이블 FK)
    meme_id: int  # 밈 ID
    
    # DB에서 로드한 데이터
    company_data: Optional[Dict[str, Any]]  # 회사/상품 정보
    meme_data: Optional[Dict[str, Any]]  # 밈 정보 + 활용 예시

    # 생성 결과
    scenario: Optional[Scenario]  # 생성된 시나리오

    # 프롬프트 저장용 (파인튜닝 모델)
    system_prompt: Optional[str]
    user_prompt: Optional[str]
    full_response: Optional[str]
    thinking: Optional[str]

    # 생성 타입
    generation_type: str  # "initial", "llm_review_v1", "llm_review_v2", "human_v1"

    # 검수 관련
    review_result: Optional[Dict[str, Any]]  # 검수 결과 {"approved": bool, "score": float, "feedback": str}
    retry_count: int  # 재생성 횟수
    human_retry_count: int # 휴먼 피드백 재생성 카운트

    # DB 저장 관련
    script_id: Optional[int]  # 저장된 script_id
    
    # 템플릿 내용
    generate_template: str
    review_template: str
    regenerate_template: str
    meme_example_template: str
    
    # 사용된 템플릿
    used_templates: List[str]
    
    # 포매팅된 프롬프트
    formatted_prompt: Optional[str]

    # 에러 핸들링
    error: Optional[str]  # 에러 발생 시 메시지
    status: str  # 현재 상태 (running, completed, failed)
