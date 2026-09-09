from langchain_core.messages import HumanMessage
from scripts.agent.state import AgentV8State
from scripts.agent.prompts import get_usage_search_prompt


def usage_search_node(state: AgentV8State, llm_with_tools) -> AgentV8State:
    meme_name = state["meme_name"]
    prompt = get_usage_search_prompt(meme_name)

    response = llm_with_tools.invoke(
        state["messages"] + [HumanMessage(content=prompt)]
    )

    return {
        "messages": state["messages"] + [response],
        "tool_called": True,
        "phase": "usage_search"
    }
