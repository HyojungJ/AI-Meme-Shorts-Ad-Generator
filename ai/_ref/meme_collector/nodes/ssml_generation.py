from scripts.agent.state import AgentV8State


def ssml_generation_node(state: AgentV8State) -> AgentV8State:
    audio_analysis = state.get("audio_analysis", {})

    if not audio_analysis.get("enabled", False):
        return {
            "audio_analysis": {
                **audio_analysis,
                "ssml": None,
                "ssml_method": None
            },
            "phase": "ssml_generation",
            "tool_called": False
        }

    key_phrase = state.get("key_phrase", "")
    prosody_data = audio_analysis.get("prosody", {})

    if not key_phrase:
        return {
            "audio_analysis": {
                **audio_analysis,
                "ssml": None,
                "ssml_method": None,
                "reason": "key_phrase 없음"
            },
            "phase": "ssml_generation",
            "tool_called": False
        }

    try:
        from scripts.analysis.tts.ssml_generator import SSMLGenerator
        generator = SSMLGenerator()
        meme_context = {
            "meme_name": state.get("meme_name", ""),
            "meme_type": state.get("meme_type", "quotable"),
            "video_analysis": state.get("video_analysis", {})
        }
        ssml = generator.generate_ssml(
            text=key_phrase,
            prosody_data=prosody_data,
            meme_context=meme_context
        )
        updated_audio = {
            **audio_analysis,
            "ssml": ssml,
            "ssml_method": "llm",
            "key_phrase": key_phrase
        }

        return {
            "audio_analysis": updated_audio,
            "phase": "ssml_generation",
            "tool_called": False
        }

    except Exception as e:
        ssml = _generate_fallback_ssml(key_phrase, prosody_data)

        updated_audio = {
            **audio_analysis,
            "ssml": ssml,
            "ssml_method": "fallback",
            "key_phrase": key_phrase,
            "error": str(e)
        }

        return {
            "audio_analysis": updated_audio,
            "phase": "ssml_generation",
            "tool_called": False
        }


def _generate_fallback_ssml(text, prosody_data):
    characteristics = prosody_data.get("overall_characteristics", {})
    rate = "medium"
    pitch = "+0%"

    tempo_class = characteristics.get("tempo_class", "medium")
    if tempo_class == "fast":
        rate = "fast"
    elif tempo_class == "slow":
        rate = "slow"

    pitch_variation = characteristics.get("pitch_variation", "moderate")
    if pitch_variation == "dramatic":
        pitch = "+15%"
    elif pitch_variation == "monotone":
        pitch = "+0%"
    else:
        pitch = "+5%"

    ssml = f'''<speak>
    <prosody rate="{rate}" pitch="{pitch}">
        {text}
    </prosody>
</speak>'''

    return ssml
