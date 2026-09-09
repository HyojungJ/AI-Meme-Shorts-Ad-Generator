from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages


class ResearchNotes(TypedDict, total=False):
    text: str      # TextResearcher 결과 (정의, 유래, 키프레이즈)
    media: str     # MediaResearcher 결과 (영상 분석, motion_prompt 힌트)
    usage: str     # UsageResearcher 결과 (활용 예시)


class ResearcherStatus(TypedDict, total=False):
    text: Literal["pending", "running", "done"]
    media: Literal["pending", "running", "done"]
    usage: Literal["pending", "running", "done"]


class TextResearchResult(TypedDict, total=False):
    key_phrase: str
    creator: str
    risk_info: str


class VideoAnalysis(TypedDict, total=False):
    motion_analysis: str
    duration: float
    frame_count: int
    source_url: str
    error: str


class YouTubeVideo(TypedDict, total=False):
    video_id: str
    url: str
    title: str
    view_count: int


class NaverResult(TypedDict, total=False):
    content: str


class UsageExampleData(TypedDict, total=False):
    context: str
    usage: str
    tone: str
    example_type: str
    note: str
    source_url: str


class SourceData(TypedDict, total=False):
    name: str
    url: str


class CollectedInfo(TypedDict, total=False):
    _text_researcher: TextResearchResult
    namuwiki_content: str
    naver_results: list[NaverResult]
    youtube_videos: list[YouTubeVideo]
    video_analysis: VideoAnalysis
    usage_examples: list[UsageExampleData]
    sources: list[SourceData]
    summary: str


class OriginData(TypedDict, total=False):
    source: str
    creator: str
    date: str
    platform: str


class ProsodyData(TypedDict, total=False):
    pitch: Literal["low", "medium", "high"]
    speed: Literal["slow", "medium", "fast"]
    emotion: str
    ssml: str


class AnalysisState(TypedDict, total=False):
    meme_type: Literal["quotable", "performable", "hybrid"]
    key_phrase: str
    definition: str
    emotion: str
    prosody: ProsodyData
    motion_prompt: str
    style_keywords: list[str]
    usage_examples: list[UsageExampleData]
    origin: OriginData
    risk_level: Literal["low", "medium", "high"]
    confidence: float


def merge_dicts(left: dict, right: dict) -> dict:
    """두 딕셔너리를 깊은 병합 (병렬 업데이트 지원)"""
    if not left:
        return right
    if not right:
        return left
    result = left.copy()
    for k, v in right.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = merge_dicts(result[k], v)
        elif k in result and isinstance(result[k], list) and isinstance(v, list):
            result[k] = result[k] + v  # 리스트는 병합
        else:
            result[k] = v
    return result


def append_reflections(left: list, right: list | str) -> list:
    """reflection 히스토리 누적 (RETRY 시 피드백 보존)"""
    if not left:
        left = []
    if isinstance(right, str):
        right = [right] if right else []
    return left + right


class MemeState(TypedDict):
    messages: Annotated[list, add_messages]
    meme_name: str
    meme_link: str | None  # 나무위키 링크 (예: "/w/김동현(1981)#밈")

    # Deep Research outputs - 병렬 업데이트를 위한 reducer
    research_notes: Annotated[ResearchNotes, merge_dicts]
    researcher_status: Annotated[ResearcherStatus, merge_dicts]

    # Collected data - 병렬 업데이트를 위한 reducer
    collected_info: Annotated[CollectedInfo, merge_dicts]

    # Analyzer output
    analysis: AnalysisState

    # Verifier (Reflexion)
    reflections: Annotated[list, append_reflections]  # 피드백 히스토리 누적
    attempt: int
    verification_score: float
    verification_decision: Literal["PASS", "RETRY", "FAIL", ""]
    retry_target: Literal["text", "media", "usage", "analyzer"] | None  # 추가 조사 대상

    # Final output
    meme_output: dict
    meme_id: int


def get_initial_state(meme_name: str, meme_link: str | None = None) -> MemeState:
    return {
        "messages": [],
        "meme_name": meme_name,
        "meme_link": meme_link,
        "research_notes": {},
        "researcher_status": {"text": "pending", "media": "pending", "usage": "pending"},
        "collected_info": {},
        "analysis": {},
        "reflections": [],
        "attempt": 0,
        "verification_score": 0.0,
        "verification_decision": "",
        "retry_target": None,
        "meme_output": {},
        "meme_id": 0,
    }
