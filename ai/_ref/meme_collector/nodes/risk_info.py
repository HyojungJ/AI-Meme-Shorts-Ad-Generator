from datetime import datetime
from langchain_core.messages import HumanMessage
from scripts.agent.state import AgentV8State
from scripts.agent.schema import RiskInfoOutput
from scripts.agent.prompts import get_risk_info_prompt


def risk_info_node(state: AgentV8State, llm_with_tools) -> AgentV8State:
    meme_name = state["meme_name"]
    prompt = get_risk_info_prompt(meme_name)

    structured_llm = llm_with_tools.with_structured_output(RiskInfoOutput)

    try:
        result: RiskInfoOutput = structured_llm.invoke(
            state["messages"] + [HumanMessage(content=prompt)]
        )
    except Exception:
        result = RiskInfoOutput()

    risk_info = result.model_dump()
    risk_info["collected_at"] = datetime.now().isoformat()

    return {
        "messages": state["messages"],
        "risk_info": risk_info,
        "tool_called": True,
        "phase": "risk_info"
    }
