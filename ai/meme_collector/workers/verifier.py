from typing import Literal

from langgraph.types import Command

from common import config, get_openai, is_valid_korean_definition
from meme_collector.schema import VerificationResult
from meme_collector.state import MemeState
from meme_collector.prompts.verifier_prompts import (
    VERIFIER_PROMPT_V1,
    VERIFIER_PROMPT_V2
)

# 피드백에서 retry_target 결정을 위한 키워드 매핑
RETRY_TARGET_KEYWORDS = {
    "text": ["key_phrase", "definition", "origin", "creator", "source", "유래", "정의", "키프레이즈"],
    "media": ["motion_prompt", "video", "movement", "dance", "동작", "영상", "모션"],
    "usage": ["usage_example", "usage", "context", "활용", "예시", "사용법"],
}




def run_verifier(state: MemeState) -> Command[Literal["supervisor", "finalize", "__end__"]]:
    analysis = state.get("analysis", {})
    collected_info = state.get("collected_info", {})
    attempt = state.get("attempt", 0)

    meme_type = analysis.get("meme_type", "quotable")
    key_phrase = analysis.get("key_phrase")
    motion_prompt = analysis.get("motion_prompt", "")
    emotion = analysis.get("emotion")
    origin = analysis.get("origin")
    risk_level = analysis.get("risk_level", "low")
    prosody = analysis.get("prosody")

    # Definition은 text_researcher > analysis 우선순위
    text_research = collected_info.get("_text_researcher", {})
    definition = text_research.get("definition") or analysis.get("definition", "")

    # Definition 한국어 검증 (LLM 호출 전에 체크)
    is_valid_def, def_reason = is_valid_korean_definition(definition)
    if not is_valid_def:
        # 자동 RETRY 또는 FAIL
        if attempt < config.agent.max_attempts:
            return Command(
                goto="supervisor",
                update={
                    "verification_score": 0.0,
                    "verification_decision": "RETRY",
                    "reflections": [f"[Attempt {attempt + 1}] Definition 문제: {def_reason}. 한국어로 정의를 다시 수집하세요."],
                    "attempt": attempt + 1,
                    "retry_target": "text",
                },
            )
        else:
            return Command(
                goto="__end__",
                update={
                    "verification_score": 0.0,
                    "verification_decision": "FAIL",
                },
            )

    client = get_openai()

    response = client.beta.chat.completions.parse(
        model=config.models.default,
        messages=[
            {"role": "system", "content": VERIFIER_PROMPT_V2},
            {
                "role": "user",
                "content": f"""## Analysis to Verify

meme_type: {meme_type}
key_phrase: {key_phrase}
definition: {definition[:200]}...
motion_prompt: {motion_prompt}
motion_prompt_length: {len(motion_prompt.split())} words
emotion: {emotion}
origin: {origin}
risk_level: {risk_level}
prosody: {prosody}

Attempt: {attempt + 1}/{config.agent.max_attempts + 1}

Evaluate for VIDEO PRODUCTION readiness.""",
            },
        ],
        response_format=VerificationResult,
    )

    output = response.choices[0].message.parsed
    decision = _decide(output.score, attempt, meme_type, key_phrase, emotion)

    update = {
        "verification_score": output.score,
        "verification_decision": decision,
    }

    if decision == "PASS":
        return Command(goto="finalize", update=update)
    elif decision == "RETRY":
        retry_target = _determine_retry_target(output.feedback, analysis)

        # 피드백 + 이전 분석 컨텍스트를 함께 저장 (targeted retry 시 analyzer가 참고)
        new_reflection = f"[Attempt {attempt + 1}] {output.feedback}"
        if retry_target != "analyzer":
            # researcher 재실행 시 이전 분석 결과 요약 추가 (동일 실패 방지)
            prev_context = _summarize_analysis_for_retry(analysis)
            if prev_context:
                new_reflection += f"\n[Previous Analysis] {prev_context}"

        update["reflections"] = [new_reflection]  # reducer가 누적 처리
        update["attempt"] = attempt + 1
        update["retry_target"] = retry_target
        # supervisor로 보내서 targeted research 또는 analyzer 재실행
        return Command(goto="supervisor", update=update)
    else:
        return Command(goto="__end__", update=update)


def _decide(
    score: float,
    attempt: int,
    meme_type: str,
    key_phrase: str | None,
    emotion: str | None,
) -> Literal["PASS", "RETRY", "FAIL"]:
    # quotable/hybrid는 key_phrase 필수 - 없으면 추가 조사 필요 (RETRY)
    # 단, max_attempts 초과 시 FAIL
    if meme_type in ("quotable", "hybrid") and not key_phrase:
        if attempt < config.agent.max_attempts:
            return "RETRY"  # 추가 조사 시도
        return "FAIL"

    # quotable/hybrid에서 emotion 없으면 점수 패널티 적용 후 판단
    adjusted_score = score
    if meme_type in ("quotable", "hybrid") and not emotion:
        adjusted_score = max(0, score - 10)

    if adjusted_score >= 70:
        return "PASS"
    if adjusted_score >= 50 and attempt < config.agent.max_attempts:
        return "RETRY"
    return "FAIL"


def _summarize_analysis_for_retry(analysis: dict) -> str:
    """이전 분석 결과를 요약하여 다음 analyzer가 참고할 수 있게 함."""
    parts = []

    if analysis.get("meme_type"):
        parts.append(f"meme_type={analysis['meme_type']}")

    if analysis.get("key_phrase"):
        parts.append(f"key_phrase='{analysis['key_phrase']}'")
    else:
        parts.append("key_phrase=MISSING")

    if analysis.get("emotion"):
        parts.append(f"emotion={analysis['emotion']}")

    motion_prompt = analysis.get("motion_prompt", "")
    word_count = len(motion_prompt.split()) if motion_prompt else 0
    parts.append(f"motion_prompt_words={word_count}")

    return ", ".join(parts) if parts else ""


def _determine_retry_target(
    feedback: str, analysis: dict
) -> Literal["text", "media", "usage", "analyzer"]:
    """피드백을 분석하여 추가 조사가 필요한 영역을 결정합니다.

    - 정보 자체가 부족한 경우: 해당 researcher 재실행
    - 분석만 부족한 경우: analyzer만 재실행
    """
    feedback_lower = feedback.lower()

    # 각 영역별 키워드 매칭 점수 계산
    scores = {"text": 0, "media": 0, "usage": 0}

    for target, keywords in RETRY_TARGET_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in feedback_lower:
                scores[target] += 1

    # 필수 필드 누락 체크 (더 강한 신호)
    meme_type = analysis.get("meme_type", "quotable")

    # quotable/hybrid인데 key_phrase 없음 → text researcher 필요
    if meme_type in ("quotable", "hybrid") and not analysis.get("key_phrase"):
        scores["text"] += 5

    # motion_prompt가 너무 짧음 → media researcher 필요
    motion_prompt = analysis.get("motion_prompt", "")
    if len(motion_prompt.split()) < 50:
        scores["media"] += 3

    # 가장 높은 점수의 영역 선택
    max_score = max(scores.values())

    if max_score == 0:
        # 키워드 매칭 없음 → analyzer만 재실행
        return "analyzer"

    # 점수가 가장 높은 영역 반환
    for target, score in scores.items():
        if score == max_score:
            return target

    return "analyzer"
