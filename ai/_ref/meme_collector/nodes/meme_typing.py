from langchain_core.messages import HumanMessage
from scripts.agent.state import AgentV8State
from scripts.agent.schema import MemeTypeOutput
from scripts.agent.prompts import get_meme_typing_prompt


def meme_typing_node(state: AgentV8State, llm) -> AgentV8State:
    meme_name = state["meme_name"]
    video_analysis = state.get("video_analysis", {})

    detected_text_raw = video_analysis.get("time_stamp", {}).get("detected_text")

    if isinstance(detected_text_raw, dict):
        detected_text = detected_text_raw.get("korean") or detected_text_raw.get("original") or ""
    elif isinstance(detected_text_raw, str):
        detected_text = detected_text_raw
    else:
        detected_text = ""

    definition = state.get("definition", "")
    motion_prompt_hint = video_analysis.get("motion_prompt_hint", "")

    prompt = get_meme_typing_prompt(
        meme_name=meme_name,
        definition=definition,
        motion_prompt_hint=motion_prompt_hint,
        detected_text=detected_text or ""
    )

    structured_llm = llm.with_structured_output(MemeTypeOutput)

    try:
        result: MemeTypeOutput = structured_llm.invoke([HumanMessage(content=prompt)])
    except Exception as e:
        return {
            "meme_type": "performable",
            "key_phrase": None,
            "needs_audio": False,
            "phase": "meme_typing",
            "tool_called": False,
            "errors": state.get("errors", []) + [f"meme_typing LLM 오류: {str(e)}"]
        }

    return {
        "meme_type": result.meme_type,
        "key_phrase": result.key_phrase,
        "needs_audio": result.meme_type in ("quotable", "hybrid"),
        "meme_typing_reason": result.reason,
        "meme_typing_confidence": result.confidence,
        "phase": "meme_typing",
        "tool_called": False
    }
