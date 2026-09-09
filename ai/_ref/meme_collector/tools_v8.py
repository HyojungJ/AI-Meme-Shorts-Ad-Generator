import os
import re
import time
import random
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@tool
def search_namuwiki(query: str) -> str:
    """나무위키에서 밈 문서를 검색합니다."""
    try:
        encoded_query = quote(query, safe="")
        url = f"https://namu.wiki/w/{encoded_query}"

        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return f"문서를 찾을 수 없습니다: {query}"

        soup = BeautifulSoup(response.text, "html.parser")

        # 문서 내용 추출
        content_parts = []

        # 제목
        title_elem = soup.select_one("h1.title")
        if title_elem:
            content_parts.append(f"# {title_elem.get_text(strip=True)}")

        # 섹션별 내용 추출
        for header in soup.select("h2, h3, h4"):
            header_text = header.get_text(strip=True)
            # [편집] 제거
            clean_header = re.sub(r"\[.*?\]", "", header_text).strip()
            clean_header = re.sub(r"^\d+\.?\s*", "", clean_header).strip()

            if not clean_header:
                continue

            content_parts.append(f"\n## {clean_header}")

            # 섹션 내용 수집
            section_content = []
            for elem in header.find_all_next():
                if elem.name in ["h2", "h3", "h4"]:
                    break
                text = elem.get_text(strip=True)
                if text and len(text) > 20:
                    section_content.append(text)

            if section_content:
                # 가장 긴 텍스트 선택 (본문일 가능성 높음)
                best_content = max(section_content, key=len)
                content_parts.append(best_content[:1000])

        result = "\n".join(content_parts)
        return result[:4000] if result else "내용을 추출할 수 없습니다."

    except Exception as e:
        return f"나무위키 검색 오류: {str(e)}"


@tool
def search_google(query: str, num_results: int = 5) -> str:
    """구글에서 밈 관련 정보를 검색합니다."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "SERPER_API_KEY가 설정되지 않았습니다."

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "q": query,
                "gl": "kr",
                "hl": "ko",
                "num": num_results
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("organic", []):
            title = item.get("title", "")
            url = item.get("link", "")
            snippet = item.get("snippet", "")
            results.append(f"- [{title}]({url})\n  {snippet}")

        return "\n\n".join(results) if results else "검색 결과가 없습니다."

    except Exception as e:
        return f"구글 검색 오류: {str(e)}"


@tool
def crawl_webpage(url: str) -> str:
    """웹페이지의 본문 내용을 크롤링합니다."""
    if "namu.wiki" in url:
        return "나무위키는 search_namuwiki 도구를 사용하세요."

    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 불필요한 요소 제거
        for tag in soup.select("script, style, nav, footer, header, aside, .ad"):
            tag.decompose()

        # 제목
        title = ""
        title_elem = soup.find("title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # 본문 추출
        content = ""
        for selector in ["article", "main", "#content", ".content", ".post-content"]:
            content_area = soup.select_one(selector)
            if content_area:
                content = content_area.get_text(separator=" ", strip=True)
                if len(content) > 200:
                    break

        if not content:
            body = soup.find("body")
            if body:
                content = body.get_text(separator=" ", strip=True)

        result = f"# {title}\n\n{content[:3000]}"
        return result

    except Exception as e:
        return f"페이지 크롤링 오류: {str(e)}"


@tool
def search_risk_info(meme_name: str) -> str:
    """밈의 위험 정보(논란, 민감 주제)를 검색합니다."""
    from scripts.agent.config import get_config

    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "SERPER_API_KEY가 설정되지 않았습니다."

    try:
        config = get_config().risk_search

        # config에서 쿼리 패턴 가져오기
        queries = [
            pattern.format(meme_name=meme_name)
            for pattern in config.risk_query_patterns
        ]

        all_results = []

        for query in queries:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query,
                    "gl": "kr",
                    "hl": "ko",
                    "num": config.search_results_count
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("organic", []):
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                all_results.append(f"- {title}: {snippet}")

        if not all_results:
            return "위험 정보 검색 결과 없음. 밈이 안전한 것으로 보입니다."

        return "\n".join(all_results[:10])

    except Exception as e:
        return f"위험 정보 검색 오류: {str(e)}"


BASIC_TOOLS = [search_namuwiki, search_google, crawl_webpage]
RISK_TOOLS = [search_google, search_risk_info]
ALL_TOOLS = [search_namuwiki, search_google, crawl_webpage, search_risk_info]
