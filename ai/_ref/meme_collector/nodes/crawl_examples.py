from langchain_core.messages import HumanMessage
from scripts.agent.state import AgentV8State
from scripts.agent.prompts import get_crawl_examples_prompt


def crawl_examples_node(state: AgentV8State, llm_with_tools) -> AgentV8State:
    meme_name = state["meme_name"]
    prompt = get_crawl_examples_prompt(meme_name)

    response = llm_with_tools.invoke(
        state["messages"] + [HumanMessage(content=prompt)]
    )

    return {
        "messages": state["messages"] + [response],
        "tool_called": True,
        "phase": "crawl_examples"
    }


def extract_urls_from_messages(messages):
    urls = []
    for msg in messages:
        if hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                if tc.get("name") == "crawl_webpage":
                    url = tc.get("args", {}).get("url", "")
                    if url:
                        urls.append(url)

    return urls


def parse_crawled_sources(messages):
    sources = []
    urls = extract_urls_from_messages(messages)

    idx = 0
    for msg in messages:
        if hasattr(msg, "name") and msg.name == "crawl_webpage":
            content = str(msg.content) if hasattr(msg, "content") else ""

            # 제목 추출 (# 으로 시작하는 첫 줄)
            title = ""
            lines = content.split("\n")
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                    break

            url = urls[idx] if idx < len(urls) else ""
            idx += 1

            if content and len(content) > 100:
                sources.append({
                    "url": url,
                    "title": title,
                    "content": content
                })

    return sources
