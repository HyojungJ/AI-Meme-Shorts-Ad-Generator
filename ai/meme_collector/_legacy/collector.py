from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from meme_collector.state import MemeState
from meme_collector.tools import COLLECTOR_TOOLS

COLLECTOR_PROMPT = """You are a Meme Research Agent for Korean internet memes.

Your goal: Collect information needed for VIDEO PRODUCTION and SCENARIO GENERATION.

## MUST COLLECT (Priority Order)
1. **key_phrase** - The EXACT catchphrase/quote (e.g., "무야호~!", "어쩔티비")
2. **definition** - What the meme means (2-3 sentences, NO markdown)
3. **origin** - Where/when/who created it (creator name is CRITICAL for YouTube search)
4. **motion_analysis** - EXACT movements from video analysis
5. **usage_examples** - How the meme is used in different situations

## Tools Strategy (FOLLOW THIS ORDER STRICTLY)
1. search_namuwiki → Get definition, origin, key_phrase
   - IMPORTANT: Extract the CREATOR NAME (인물/출연자 이름)
2. search_naver_blog → Get context, additional info
3. extract_usage_examples → Get usage examples
4. search_youtube_shorts → MUST pass creator parameter!
   - meme_name: 밈 이름
   - creator: 나무위키에서 찾은 인물 이름 (예: "김동현", "박명수")
   - Example: search_youtube_shorts(meme_name="운동 많이 된다", creator="김동현")
5. analyze_meme_video → Use the FIRST video URL from search_youtube_shorts

## CRITICAL Rules
- ALWAYS search namuwiki FIRST to find the creator/origin
- When calling search_youtube_shorts, ALWAYS pass the creator parameter
- For dance/performable memes, use analyze_meme_video with the top result
- Extract the EXACT key_phrase in quotes from sources
- NO markdown formatting in your summary

When done, provide a clean summary with all collected information."""


def run_collector(state: MemeState) -> Command[Literal["analyzer"]]:
    meme_name = state["meme_name"]

    agent = create_agent(
        model="openai:gpt-4o-mini",
        tools=COLLECTOR_TOOLS,
        system_prompt=COLLECTOR_PROMPT,
        middleware=[
            SummarizationMiddleware(
                model="openai:gpt-4o-mini",
                trigger=("tokens", 4000),
                keep=("messages", 10),
            ),
        ],
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": f"'{meme_name}' 밈 정보를 수집하세요. 특히 key_phrase(핵심 대사)와 시각적 특징을 반드시 찾아주세요."}]
    })

    messages = result.get("messages", [])
    collected_info = _extract_collected_info(messages, meme_name)

    return Command(
        goto="analyzer",
        update={"messages": messages, "collected_info": collected_info},
    )


def _extract_collected_info(messages: list, meme_name: str) -> dict:
    namuwiki_content = ""
    naver_results = []
    youtube_videos = []
    video_analysis = None
    usage_examples = []
    sources = []
    summary = ""

    for msg in messages:
        if isinstance(msg, ToolMessage):
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            tool_name = getattr(msg, "name", "")

            if tool_name == "search_namuwiki":
                namuwiki_content = content
                sources.append("나무위키")
            elif tool_name in ["search_naver_blog", "search_naver_news"]:
                naver_results.append({"content": content})
                sources.append("네이버")
            elif tool_name == "search_youtube_shorts":
                if isinstance(msg.content, list):
                    youtube_videos = msg.content
                else:
                    import json
                    try:
                        youtube_videos = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        pass
                sources.append("YouTube")
            elif tool_name == "analyze_meme_video":
                if isinstance(msg.content, dict):
                    video_analysis = msg.content
                else:
                    import json
                    try:
                        video_analysis = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        pass
                sources.append("Video Analysis")
            elif tool_name == "extract_usage_examples":
                if isinstance(msg.content, list):
                    usage_examples = msg.content
                else:
                    import json
                    try:
                        usage_examples = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        pass
                sources.append("Usage Examples")

    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg.content, str):
            if not hasattr(msg, "tool_calls") or not msg.tool_calls:
                if len(msg.content) > 50:
                    summary = msg.content
                    break

    return {
        "meme_name": meme_name,
        "namuwiki_content": namuwiki_content,
        "naver_results": naver_results,
        "youtube_videos": youtube_videos,
        "video_analysis": video_analysis,
        "usage_examples": usage_examples,
        "sources": list(set(sources)),
        "summary": summary,
    }
