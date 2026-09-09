import requests
from langchain_core.tools import tool

from common import clean_html, config


def _search(query: str, search_type: str, display: int = 5) -> list[dict]:
    if not config.naver_client_id or not config.naver_client_secret:
        return []

    response = requests.get(
        f"https://openapi.naver.com/v1/search/{search_type}.json",
        headers={"X-Naver-Client-Id": config.naver_client_id, "X-Naver-Client-Secret": config.naver_client_secret},
        params={"query": query, "display": display, "sort": "sim"},
        timeout=config.api.timeout,
    )
    return response.json().get("items", []) if response.status_code == 200 else []


@tool
def search_naver_blog(query: str, count: int = 5) -> str:
    """네이버 블로그에서 검색합니다. 밈의 실제 사용 예시와 맥락을 찾을 때 유용합니다."""
    items = _search(query, "blog", count)
    if not items:
        return "검색 결과가 없습니다."

    return "\n\n".join([f"- [{clean_html(i['title'])}]({i['link']})\n  {clean_html(i['description'])}" for i in items])


@tool
def search_naver_news(query: str, count: int = 5) -> str:
    """네이버 뉴스에서 검색합니다. 밈의 최신 트렌드와 화제성을 확인할 때 사용합니다."""
    items = _search(query, "news", count)
    if not items:
        return "검색 결과가 없습니다."

    return "\n\n".join([f"- [{clean_html(i['title'])}]({i.get('originallink') or i['link']})\n  {clean_html(i['description'])}" for i in items])
