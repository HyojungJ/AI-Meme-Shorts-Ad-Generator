from scripts.agent.state import AgentV8State


def audio_analysis_node(state: AgentV8State) -> AgentV8State:
    if not state.get("needs_audio", False):
        return {
            "audio_analysis": {
                "enabled": False,
                "reason": "performable 밈 - 오디오 분석 불필요"
            },
            "phase": "audio_analysis",
            "tool_called": False
        }

    video_analysis = state.get("video_analysis", {})
    youtube_shorts = state.get("youtube_shorts", [])
    video_id = state.get("selected_video_id")
    if not video_id and youtube_shorts:
        video_id = youtube_shorts[0].get("video_id")

    if not video_id:
        return {
            "audio_analysis": {
                "enabled": False,
                "reason": "분석할 영상 없음"
            },
            "phase": "audio_analysis",
            "tool_called": False
        }

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    time_stamp = video_analysis.get("time_stamp", {})
    start_seconds = time_stamp.get("start", 0)
    end_seconds = time_stamp.get("end", 10)

    try:
        from scripts.analysis.audio.extractor import AudioSegmentExtractor
        from scripts.analysis.audio.voice_analyzer import AdvancedVoiceAnalyzer

        extractor = AudioSegmentExtractor(output_dir="data/raw/audio")

        if start_seconds and end_seconds and start_seconds < end_seconds:
            # 특정 구간 추출
            audio_file = extractor.extract_segment(
                youtube_url=youtube_url,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                padding=0.5
            )
        else:
            # 전체 오디오 (처음 10초)
            audio_file = extractor.extract_full_audio(
                youtube_url=youtube_url,
                max_duration=10
            )

        if not audio_file:
            return {
                "audio_analysis": {"enabled": False, "error": "오디오 추출 실패"},
                "phase": "audio_analysis",
                "tool_called": False
            }

        analyzer = AdvancedVoiceAnalyzer()
        prosody_data = analyzer.analyze_prosody(audio_file)
        detected_text = time_stamp.get("detected_text", "")

        audio_analysis = {
            "enabled": True,
            "audio_file": audio_file,
            "source_video_id": video_id,
            "segment": {
                "start": start_seconds,
                "end": end_seconds
            },
            "prosody": prosody_data,
            "detected_text": detected_text
        }

        return {
            "audio_analysis": audio_analysis,
            "phase": "audio_analysis",
            "tool_called": False
        }

    except Exception as e:
        error_msg = f"오디오 분석 오류: {str(e)}"
        return {
            "audio_analysis": {
                "enabled": False,
                "error": str(e)
            },
            "phase": "audio_analysis",
            "tool_called": False,
            "errors": state.get("errors", []) + [error_msg]
        }
