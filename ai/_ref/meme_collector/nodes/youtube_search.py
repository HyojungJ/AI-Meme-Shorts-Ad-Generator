from scripts.agent.state import AgentV8State


def youtube_search_node(state: AgentV8State) -> AgentV8State:
    meme_name = state["meme_name"]
    try:
        from scripts.analysis.video.search import search_shorts_with_details
        shorts = search_shorts_with_details(meme_name, num_results=3)
        selected_video_id = shorts[0].get("video_id") if shorts else None
        return {
            "youtube_shorts": shorts,
            "selected_video_id": selected_video_id,
            "phase": "youtube_search",
            "tool_called": False
        }
    except Exception as e:
        return {
            "youtube_shorts": [],
            "selected_video_id": None,
            "phase": "youtube_search",
            "tool_called": False,
            "errors": state.get("errors", []) + [f"YouTube 검색 오류: {e}"]
        }
