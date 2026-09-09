from scripts.agent.state import AgentV8State


def video_analysis_node(state: AgentV8State, skip=False) -> AgentV8State:
    video_id = state.get("selected_video_id")
    meme_name = state["meme_name"]

    if skip:
        return {
            "video_analysis": {
                "enabled": False,
                "reason": "Skipped by flag"
            },
            "phase": "video_analysis",
            "tool_called": False
        }

    if not video_id:
        return {
            "video_analysis": {
                "enabled": False,
                "reason": "No video found"
            },
            "phase": "video_analysis",
            "tool_called": False
        }

    try:
        from scripts.analysis.video.analyzer import generate_motion_prompt
        key_phrase = state.get("key_phrase")
        result = generate_motion_prompt(
            video_id=video_id,
            meme_name=meme_name,
            key_phrase=key_phrase
        )

        time_stamp = result.get("time_stamp", {})
        detected_text = time_stamp.get("detected_text", {})

        if isinstance(detected_text, dict):
            detected_text_obj = detected_text
        elif isinstance(detected_text, str) and detected_text:
            detected_text_obj = {"original": detected_text, "korean": detected_text, "language": "unknown"}
        else:
            detected_text_obj = None

        video_gen = result.get("video_generation", {})
        motion_prompt_raw = video_gen.get("motion_prompt", {})

        if isinstance(motion_prompt_raw, dict):
            motion_prompt_full = motion_prompt_raw.get("full_prompt", "")
            motion_sequence = motion_prompt_raw.get("sequence", [])
            body_parts = motion_prompt_raw.get("body_parts", {})
        elif isinstance(motion_prompt_raw, str):
            motion_prompt_full = motion_prompt_raw
            motion_sequence = []
            body_parts = {}
        else:
            motion_prompt_full = ""
            motion_sequence = []
            body_parts = {}

        video_analysis = {
            "enabled": True,
            "source_video_id": video_id,
            "time_stamp": {
                "start": time_stamp.get("start", 0),
                "end": time_stamp.get("end", 0),
                "detected_text": detected_text_obj
            },
            # 새 구조: 상세 motion_prompt
            "motion_prompt_hint": motion_prompt_full,
            "motion_sequence": motion_sequence,
            "body_parts": body_parts,
            "style_keywords": video_gen.get("style_keywords", []),
            "negative_prompt": video_gen.get("negative_prompt", ""),
            "duration_seconds": video_gen.get("duration_seconds", 5.0),
            "camera_motion": video_gen.get("camera_motion", "static"),
            "background_suggestion": video_gen.get("background_suggestion", ""),
            "movement_analysis": result.get("movement_analysis", {})
        }

        key_phrase = None
        if detected_text_obj:
            key_phrase = detected_text_obj.get("korean") or detected_text_obj.get("original")

        return {
            "video_analysis": video_analysis,
            "phase": "video_analysis",
            "tool_called": False,
            "key_phrase": key_phrase if key_phrase else state.get("key_phrase")
        }

    except Exception as e:
        error_msg = f"영상 분석 오류: {str(e)}"
        return {
            "video_analysis": {
                "enabled": False,
                "error": str(e)
            },
            "phase": "video_analysis",
            "tool_called": False,
            "errors": state.get("errors", []) + [error_msg]
        }
