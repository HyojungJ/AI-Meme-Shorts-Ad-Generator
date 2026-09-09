import re
from langchain_core.messages import HumanMessage, AIMessage
from scripts.agent.state import AgentV8State
from scripts.agent.schema import DefinitionOutput
from scripts.agent.prompts import get_definition_extract_prompt
from scripts.agent.tools_v8 import search_namuwiki, search_google, crawl_webpage
from scripts.agent.config import get_config


def definition_node(state: AgentV8State, llm_with_tools, llm=None) -> AgentV8State:
    config = get_config().definition
    meme_name = state["meme_name"]

    search_results = _collect_search_results(meme_name, config)

    if config.llm_extraction:
        extract_llm = llm if llm else llm_with_tools
        structured_llm = extract_llm.with_structured_output(DefinitionOutput)

        extract_prompt = get_definition_extract_prompt(
            meme_name=meme_name,
            search_result=search_results
        )

        try:
            result: DefinitionOutput = structured_llm.invoke([HumanMessage(content=extract_prompt)])
        except Exception:
            result = DefinitionOutput(definition="", origin={}, keywords=[])

        search_msg = AIMessage(content=f"[Definition Search]\n{search_results[:2000]}...")

        return {
            "messages": state["messages"] + [search_msg],
            "definition": result.definition,
            "origin": result.origin.model_dump() if result.origin else {},
            "keywords": result.keywords,
            "key_phrase_from_definition": result.key_phrase,
            "tool_called": True,
            "phase": "definition"
        }

    definition = _extract_definition_legacy(search_results, meme_name, config)

    return {
        "messages": state["messages"],
        "definition": definition,
        "tool_called": True,
        "phase": "definition"
    }


def _collect_search_results(meme_name, config):
    results = []
    try:
        namu_result = search_namuwiki.invoke(meme_name)
        results.append(f"=== 나무위키 ===\n{namu_result}")
    except Exception as e:
        results.append(f"=== 나무위키 ===\n검색 오류: {e}")

    try:
        google_result = search_google.invoke({"query": f"{meme_name} 밈 뜻 유래"})
        results.append(f"=== 구글 검색 ===\n{google_result}")
    except Exception as e:
        results.append(f"=== 구글 검색 ===\n검색 오류: {e}")

    if config.crawl_count > 0:
        try:
            urls = _extract_urls_from_search(google_result, config.crawl_count)
            for url in urls:
                try:
                    crawl_result = crawl_webpage.invoke(url)
                    results.append(f"=== 크롤링: {url} ===\n{crawl_result[:1500]}")
                except Exception:
                    pass
        except Exception:
            pass

    return "\n\n".join(results)


def _extract_urls_from_search(search_result, max_urls):
    urls = []
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, search_result)

    blocked_domains = ['namu.wiki', 'youtube.com', 'dcinside.com', 'ruliweb.com', 'fmkorea.com']

    for title, url in matches:
        if len(urls) >= max_urls:
            break
        if not any(blocked in url for blocked in blocked_domains):
            urls.append(url)

    return urls


def _extract_definition_legacy(response, meme_name, config):
    if not hasattr(response, "content"):
        return ""

    content = str(response.content)
    definition = ""
    extraction_keywords = config.extraction_keywords + [meme_name]
    lines = content.split("\n")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in extraction_keywords):
            extracted = []
            for j in range(i, min(i + config.max_lines, len(lines))):
                if lines[j].strip():
                    extracted.append(lines[j].strip())
            if extracted:
                definition = " ".join(extracted)
                break

    if len(definition) < config.min_valid_length and len(content) > 100:
        definition = content[:500]

    return definition[:config.max_chars]
