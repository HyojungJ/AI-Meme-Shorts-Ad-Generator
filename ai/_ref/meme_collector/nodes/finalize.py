import json
import time
from datetime import datetime
from langchain_core.messages import HumanMessage
from scripts.agent.state import AgentV8State
from scripts.agent.prompts import get_finalize_prompt


def finalize_node(state: AgentV8State, llm_strong) -> AgentV8State:
    crawled_sources = state.get("crawled_sources", [])
    risk_info = state.get("risk_info", {})
    youtube_shorts = state.get("youtube_shorts", [])
    video_analysis = state.get("video_analysis", {})
    meme_type = state.get("meme_type", "")
    key_phrase = state.get("key_phrase")
    audio_analysis = state.get("audio_analysis", {})

    prompt = get_finalize_prompt(
        crawled_sources=crawled_sources,
        risk_info=risk_info,
        youtube_shorts=youtube_shorts,
        video_analysis=video_analysis,
        meme_type=meme_type,
        key_phrase=key_phrase,
        audio_analysis=audio_analysis
    )
    response = _invoke_with_retry(
        llm_strong,
        state["messages"] + [HumanMessage(content=prompt)]
    )

    return {
        "messages": [response],
        "phase": "done",
        "tool_called": False
    }


def _invoke_with_retry(llm, messages, max_retries=3, base_delay=20):
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                delay = base_delay * (attempt + 1)
                time.sleep(delay)
            else:
                raise
    return llm.invoke(messages)


def parse_final_result(final_state, meme_name):
    result = {
        "meta": {
            "agent_version": "v8",
            "processed_at": datetime.now().isoformat()
        },
        "basic_info": {
            "name": meme_name,
            "definition": "",
            "origin": {},
            "keywords": []
        },
        "risk_info": {},
        "usage_examples": [],
        "youtube_shorts": [],
        "meme_classification": {},
        "video_analysis": {},
        "audio_analysis": {},
        "video_generation": {}
    }

    if not final_state:
        return result

    collected_data = {}
    for node_state in final_state.values():
        if "definition" in node_state and node_state["definition"]:
            collected_data["definition"] = node_state["definition"]
        if "origin" in node_state and node_state["origin"]:
            collected_data["origin"] = node_state["origin"]
        if "keywords" in node_state and node_state["keywords"]:
            collected_data["keywords"] = node_state["keywords"]
        if "youtube_shorts" in node_state and node_state["youtube_shorts"]:
            collected_data["youtube_shorts"] = node_state["youtube_shorts"]
        if "video_analysis" in node_state and node_state["video_analysis"]:
            va = node_state["video_analysis"]
            if va.get("enabled", True) and va.get("source_video_id"):
                collected_data["video_analysis"] = va
        if "audio_analysis" in node_state and node_state["audio_analysis"]:
            aa = node_state["audio_analysis"]
            if aa.get("enabled"):
                collected_data["audio_analysis"] = aa
        if "meme_type" in node_state and node_state["meme_type"]:
            collected_data["meme_type"] = node_state["meme_type"]
        if "key_phrase" in node_state and node_state["key_phrase"]:
            collected_data["key_phrase"] = node_state["key_phrase"]
        if "needs_audio" in node_state:
            collected_data["needs_audio"] = node_state["needs_audio"]
        if "risk_info" in node_state and node_state["risk_info"]:
            collected_data["risk_info"] = node_state["risk_info"]
        if "crawled_sources" in node_state and node_state["crawled_sources"]:
            collected_data["crawled_sources"] = node_state["crawled_sources"]

    llm_parsed = None
    for node_state in final_state.values():
        if "messages" not in node_state:
            continue

        for msg in node_state["messages"]:
            if not hasattr(msg, "content"):
                continue

            content = str(msg.content)
            json_str = None
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]

            if json_str:
                try:
                    llm_parsed = json.loads(json_str)
                    break
                except json.JSONDecodeError:
                    continue
        if llm_parsed:
            break

    if llm_parsed:
        if "basic_info" in llm_parsed:
            result["basic_info"] = llm_parsed["basic_info"]
            result["basic_info"]["name"] = meme_name
        if "usage_examples" in llm_parsed:
            result["usage_examples"] = llm_parsed["usage_examples"]

    if collected_data.get("definition"):
        result["basic_info"]["definition"] = collected_data["definition"]
    if collected_data.get("origin"):
        result["basic_info"]["origin"] = collected_data["origin"]
    if collected_data.get("keywords"):
        result["basic_info"]["keywords"] = collected_data["keywords"]

    if collected_data.get("youtube_shorts"):
        result["youtube_shorts"] = collected_data["youtube_shorts"]

    if collected_data.get("video_analysis"):
        va = collected_data["video_analysis"]
        result["video_analysis"] = {
            "enabled": True,
            "source_video_id": va.get("source_video_id", ""),
            "time_stamp": va.get("time_stamp", {}),
            "motion_prompt_hint": va.get("motion_prompt_hint", ""),
            "motion_sequence": va.get("motion_sequence", []),
            "body_parts": va.get("body_parts", {}),
            "style_keywords": va.get("style_keywords", []),
            "duration_seconds": va.get("duration_seconds", 5.0),
            "camera_motion": va.get("camera_motion", "static"),
            "background_suggestion": va.get("background_suggestion", ""),
            "movement_analysis": va.get("movement_analysis", {})
        }
        result["video_generation"] = {
            "motion_prompt": va.get("motion_prompt_hint", ""),
            "motion_sequence": va.get("motion_sequence", []),
            "body_parts": va.get("body_parts", {}),
            "style_keywords": va.get("style_keywords", []),
            "negative_prompt": va.get("negative_prompt", "static, stiff, realistic, blurry, distorted"),
            "duration_seconds": va.get("duration_seconds", 5.0),
            "camera_motion": va.get("camera_motion", "static"),
            "background_suggestion": va.get("background_suggestion", "")
        }

    if collected_data.get("audio_analysis"):
        result["audio_analysis"] = collected_data["audio_analysis"]

    if collected_data.get("risk_info"):
        result["risk_info"] = collected_data["risk_info"]

    # meme_classification
    if collected_data.get("meme_type"):
        result["meme_classification"] = {
            "meme_type": collected_data.get("meme_type"),
            "key_phrase": collected_data.get("key_phrase"),
            "needs_audio": collected_data.get("needs_audio", False)
        }

    return result
