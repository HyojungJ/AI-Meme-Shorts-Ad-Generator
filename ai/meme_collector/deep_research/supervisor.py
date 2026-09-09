"""Supervisor: Open Deep Research 패턴의 라우팅 로직 (LangGraph 2025)

Workflow:
1. RESEARCH Phase 1: text_researcher (creator, key_phrase 수집)
2. RESEARCH Phase 2: media + usage 병렬 (Command.goto 리스트로 병렬 실행)
3. ANALYZE: Analyzer로 통합 분석
4. VERIFY: Verifier로 품질 검증
5. FINISH or RETRY (targeted research 포함)

기술 포인트:
- Command(goto=[...]) : 여러 노드 병렬 실행
- 순차 의존성: text → media/usage (media가 text의 creator, key_phrase 활용)
"""
import logging
from typing import Literal

from langgraph.types import Command

from meme_collector.state import MemeState

log = logging.getLogger(__name__)

# Type aliases for routing targets
ResearcherNode = Literal["text_researcher", "media_researcher", "usage_researcher"]
AnalysisNode = Literal["analyzer", "verifier", "finalize"]
AllNodes = Literal["text_researcher", "media_researcher", "usage_researcher", "analyzer", "verifier", "finalize", "__end__"]


def route(state: MemeState) -> Command[AllNodes]:
    """Supervisor: 현재 상태를 보고 다음 단계로 라우팅

    Returns:
        Command: 단일 노드 또는 여러 노드로 라우팅 (goto에 리스트 전달 시 병렬 실행)
    """
    researcher_status = state.get("researcher_status", {})
    analysis = state.get("analysis", {})
    verification_decision = state.get("verification_decision", "")
    retry_target = state.get("retry_target")

    # 0. RETRY with targeted research
    if verification_decision == "RETRY" and retry_target:
        return _handle_retry(retry_target, researcher_status)

    # 1. Research Phase 1: text_researcher 먼저 실행 (creator, key_phrase 수집)
    text_status = researcher_status.get("text", "pending")
    if text_status == "pending":
        log.info("Phase 1: text_researcher 실행 (creator, key_phrase 수집)")
        return Command(goto="text_researcher")

    # 2. Research Phase 2: text 완료 후 media/usage 병렬 (Command.goto 리스트)
    if text_status == "done":
        media_status = researcher_status.get("media", "pending")
        usage_status = researcher_status.get("usage", "pending")

        pending_nodes = []
        if media_status == "pending":
            pending_nodes.append("media_researcher")
        if usage_status == "pending":
            pending_nodes.append("usage_researcher")

        if pending_nodes:
            log.info(f"Phase 2: {len(pending_nodes)}개 researcher 병렬 실행")
            return Command(goto=pending_nodes)  # 리스트로 병렬 실행

    # 3. 모든 Research 완료 → Analyze
    all_done = all(
        researcher_status.get(r) == "done" for r in ["text", "media", "usage"]
    )

    if all_done and not analysis:
        log.info("Phase 3: analyzer 실행")
        return Command(goto="analyzer")

    # 4. Analysis 완료 → Verify
    if analysis and not verification_decision:
        log.info("Phase 4: verifier 실행")
        return Command(goto="verifier")

    # 5. Verification 결과에 따라 분기
    if verification_decision == "PASS":
        return Command(goto="finalize")
    elif verification_decision == "FAIL":
        return Command(goto="__end__")

    # 기본: 종료
    return Command(goto="__end__")


def _handle_retry(
    retry_target: str, researcher_status: dict
) -> Command[AllNodes]:
    """RETRY 시 targeted research 또는 analyzer 재실행"""

    if retry_target == "analyzer":
        # 분석만 재실행 (기존 research_notes 유지)
        log.info("RETRY: analyzer만 재실행")
        return Command(
            goto="analyzer",
            update={
                "analysis": {},  # 분석 결과 초기화
                "verification_decision": "",  # 검증 결과 초기화
                "retry_target": None,
            },
        )

    # 특정 researcher 추가 실행
    researcher_name = f"{retry_target}_researcher"
    log.info(f"RETRY: {researcher_name} 추가 조사 실행")

    # NOTE: analysis를 초기화해야 researcher 완료 후 analyzer가 재실행됨
    # 이전 분석 컨텍스트는 verifier가 reflections에 저장해둠 (_summarize_analysis_for_retry)
    return Command(
        goto=researcher_name,
        update={
            "researcher_status": {retry_target: "pending"},  # 해당 researcher만 pending
            "analysis": {},  # 분석 결과 초기화 → researcher 완료 후 analyzer 재실행
            "verification_decision": "",  # 검증 결과 초기화
            "retry_target": None,
        },
    )
