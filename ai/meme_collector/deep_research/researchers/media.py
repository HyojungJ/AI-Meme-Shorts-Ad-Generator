"""MediaResearcher: True ReAct Agent for video-based meme research.

Uses create_react_agent from LangGraph for dynamic tool selection and reasoning.
"""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from common import config
from meme_collector.state import MemeState
from meme_collector.tools.video_analyzer import analyze_meme_video
from meme_collector.tools.youtube import search_youtube_shorts

MEDIA_TOOLS = [search_youtube_shorts, analyze_meme_video]

MEDIA_SYSTEM_PROMPT = """당신은 밈 영상 분석 전문가입니다.

목표: 밈의 원본 영상을 찾아 동작과 표현을 분석하세요. 이 정보는 AI 영상 생성(Sora)에 사용됩니다.

전략:
1. search_youtube_shorts 도구 사용 시 **반드시** creator, key_phrase 파라미터도 함께 전달하세요
   - creator: 밈의 원작자 (예: "유야호", "버벌진트")
   - key_phrase: 밈의 핵심 대사 (예: "무야호", "답장 아직이려나")
2. 영상을 찾으면 동작 분석을 수행하세요
3. 영상이 없으면 다른 검색어로 재시도하세요"""


class MediaNotes(BaseModel):
    has_video: bool = Field(default=False, description="참조할 영상이 있으면 True")
    motion_description: str = Field("", description="영상에서 관찰된 동작 (Sora 프롬프트용)")
    camera_info: str = Field("", description="카메라 앵글/구도")
    style_hints: list[str] = Field(default_factory=list, description="영상 스타일 키워드 5-7개")
    top_video_url: str = Field("", description="가장 관련성 높은 영상 URL")
    top_video_title: str = Field("", description="해당 영상 제목")


def run_media_researcher(state: MemeState) -> dict:
    """MediaResearcher: True ReAct Agent로 영상 기반 밈 정보 수집"""
    meme_name = state["meme_name"]
    collected_info = state.get("collected_info", {})

    # TextResearcher에서 추출한 creator 정보 활용
    text_data = collected_info.get("_text_researcher", {})
    creator = text_data.get("creator", "")

    # TextResearcher에서 추출한 key_phrase 정보 활용
    key_phrase = text_data.get("key_phrase", "")

    # 컨텍스트 구성 (ReAct 에이전트에게 전달)
    context_parts = [f"밈 이름: {meme_name}"]
    if creator:
        context_parts.append(f"관련 인물 (creator): {creator}")
    if key_phrase:
        context_parts.append(f"핵심 대사 (key_phrase): {key_phrase}")

    context = "\n".join(context_parts)

    agent = create_react_agent(
        model=ChatOpenAI(model=config.models.default),
        tools=MEDIA_TOOLS,
        prompt=SystemMessage(content=MEDIA_SYSTEM_PROMPT),
        response_format=MediaNotes,
    )

    result = agent.invoke({
        "messages": [HumanMessage(content=context)]
    })

    notes: MediaNotes = result["structured_response"]

    # 영상 정보 추출 (에이전트 대화에서)
    videos_found = []
    video_analysis = {}

    for msg in result["messages"]:
        content = str(msg.content) if hasattr(msg, "content") else str(msg)

        # ToolMessage에서 영상 목록 추출 시도 (JSON 배열 전체 매칭)
        if "video_id" in content and "url" in content and not videos_found:
            try:
                # 전체 content가 JSON 배열인 경우
                if content.strip().startswith("["):
                    videos_found = json.loads(content)
                else:
                    # 배열 전체를 greedy하게 매칭
                    match = re.search(r"\[.*\]", content, re.DOTALL)
                    if match:
                        videos_found = json.loads(match.group())
            except (json.JSONDecodeError, Exception):
                pass

        # 분석 결과 추출
        if "motion_analysis" in content and not video_analysis:
            try:
                # 전체 content가 JSON 객체인 경우
                if content.strip().startswith("{"):
                    video_analysis = json.loads(content)
                else:
                    match = re.search(r"\{.*\}", content, re.DOTALL)
                    if match:
                        video_analysis = json.loads(match.group())
            except (json.JSONDecodeError, Exception):
                pass

    # structured_response에서 top_video 정보로 보완
    if not videos_found and notes.top_video_url:
        videos_found = [{
            "video_id": notes.top_video_url.split("/")[-1],
            "url": notes.top_video_url,
            "title": notes.top_video_title,
            "view_count": 0,
        }]

    notes_text = f"""## 참조 영상
{'있음' if notes.has_video else '없음'}
{notes.top_video_title}
{notes.top_video_url}

## 동작 분석
{notes.motion_description or '(분석 불가)'}

## 카메라
{notes.camera_info or '(정보 없음)'}

## 스타일 키워드
{', '.join(notes.style_hints) if notes.style_hints else '(없음)'}"""

    # collected_info 업데이트 (reducer가 병합 처리)
    collected_update = {
        "youtube_videos": videos_found,
        "video_analysis": video_analysis,
    }
    if notes.top_video_url:
        collected_update["sources"] = [{"name": "YouTube", "url": notes.top_video_url}]

    return {
        "research_notes": {"media": notes_text},
        "researcher_status": {"media": "done"},
        "collected_info": collected_update,
    }
