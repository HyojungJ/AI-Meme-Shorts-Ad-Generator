"""
시나리오 생성 에이전트 그래프 구성
LangGraph를 사용한 노드 연결 및 실행 흐름 정의
"""
from langgraph.graph import StateGraph, START, END
from content_pipeline.scenario.scenario_state import ScenarioState
from content_pipeline.scenario.scenario_nodes import (
    generate_scenario_node,
    review_scenario_node,
    regenerate_scenario_node,
    save_scenario_node
)


def create_scenario_graph():
    """
    시나리오 생성 그래프 (검수 + 재생성 포함)
    
    Returns:
        컴파일된 LangGraph 그래프
    """
    # StateGraph 초기화
    graph = StateGraph(ScenarioState)
    
    # 노드 추가
    graph.add_node("generate_scenario", generate_scenario_node)
    graph.add_node("review_scenario", review_scenario_node)  
    graph.add_node("regenerate_scenario", regenerate_scenario_node)
    graph.add_node("save_scenario", save_scenario_node)
    
    # 엣지 연결
    graph.add_edge(START, "generate_scenario")
    graph.add_edge("generate_scenario", "review_scenario")  # 생성 후 바로 검수

    # 조건부 엣지: 검수 결과에 따라 분기
    graph.add_conditional_edges(
        "review_scenario",
        should_regenerate,
        {
            "end": "save_scenario",           # 승인 또는 실패 -> 저장
            "regenerate": "regenerate_scenario"  # 재생성
        }
    )

    graph.add_edge("regenerate_scenario", "review_scenario")
    graph.add_edge("save_scenario", END)  # 저장 후 종료

    # 그래프 컴파일
    return graph.compile()


def should_regenerate(state: ScenarioState) -> str:
    """검수 결과에 따라 재생성 여부 결정 (라우팅만, state 수정 금지)"""
    if not state.get("review_result"):
        return "end"

    review = state["review_result"]
    feedback_type = review.get("feedback_type")

    if feedback_type == "human_feedback":
        return "regenerate"

    if feedback_type == "llm_review":
        if review.get("approved"):
            return "end"
        if state.get("retry_count", 0) >= 3:
            return "end"
        return "regenerate"

    return "end"
