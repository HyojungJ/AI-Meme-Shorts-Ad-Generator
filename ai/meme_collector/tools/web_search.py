"""Web search tool using DuckDuckGo.

Fallback search when Namuwiki/Naver don't have enough information.
"""
from ddgs import DDGS
from langchain_core.tools import tool


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """범용 웹 검색입니다. 다른 도구에서 정보가 부족할 때 사용합니다."""
    ddgs = DDGS()
    results = ddgs.text(query, region="kr-kr", max_results=max_results)

    if not results:
        return "검색 결과가 없습니다."

    formatted = []
    for r in results:
        title = r.get("title", "")
        link = r.get("href", "")
        body = r.get("body", "")
        formatted.append(f"- [{title}]({link})\n  {body[:200]}")

    return "\n\n".join(formatted)
