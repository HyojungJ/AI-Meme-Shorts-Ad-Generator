"""Open Deep Research Graph: Supervisor + 3 Researchers + Analyzer + Verifier (LangGraph 2025)

아키텍처:
- Supervisor 패턴: 중앙 라우터가 동적으로 다음 노드 결정
- Map-Reduce: Command(goto=[...])로 병렬 실행, merge_dicts reducer로 결과 병합
- Self-Reflection: Verifier가 품질 검증 후 targeted retry

워크플로우:
1. supervisor → text_researcher (creator, key_phrase 수집)
2. supervisor → [media_researcher, usage_researcher] 병렬 (Command.goto 리스트)
3. supervisor → analyzer (research_notes 기반 분석)
4. supervisor → verifier (품질 검증)
5. supervisor → finalize or retry (targeted research)

기술 포인트:
- Command(goto=[...]): 여러 노드 병렬 실행 (Map 단계)
- merge_dicts reducer: 병렬 결과 자동 병합 (Reduce 단계)
- 순차 의존성: text → media/usage (media가 text의 creator, key_phrase 활용)
"""
from langgraph.graph import END, StateGraph

from meme_collector.deep_research.researchers import (
    run_media_researcher,
    run_text_researcher,
    run_usage_researcher,
)
from meme_collector.deep_research.supervisor import route
from meme_collector.nodes.finalize import finalize_node
from meme_collector.state import MemeState
from meme_collector.workers.analyzer import run_analyzer
from meme_collector.workers.verifier import run_verifier


def supervisor_node(state: MemeState):
    """Supervisor: 라우팅만 담당, Command 반환"""
    return route(state)


def compile_graph(checkpointer=None):
    """Open Deep Research 패턴의 StateGraph 컴파일"""
    graph = StateGraph(MemeState)

    # 노드 등록
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("text_researcher", run_text_researcher)
    graph.add_node("media_researcher", run_media_researcher)
    graph.add_node("usage_researcher", run_usage_researcher)
    graph.add_node("analyzer", run_analyzer)
    graph.add_node("verifier", run_verifier)
    graph.add_node("finalize", finalize_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Researchers → supervisor (결과 반환 후 다시 라우팅)
    graph.add_edge("text_researcher", "supervisor")
    graph.add_edge("media_researcher", "supervisor")
    graph.add_edge("usage_researcher", "supervisor")

    # Analyzer, Verifier는 Command로 라우팅하므로 edge 불필요
    # Finalize → END
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer) if checkpointer else graph.compile()
