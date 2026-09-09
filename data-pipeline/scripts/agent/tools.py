"""
LangChain Agent Tools

밈 데이터 수집을 위한 커스텀 도구들
"""

import os
import re
import time
import random
from typing import Optional
from urllib.parse import urlparse, quote

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()


# 공통 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


@tool
def search_namuwiki(query: str) -> str:
    """
    나무위키에서 밈 문서를 검색하고 내용을 가져옵니다.
    밈의 정의, 유래, 사용법 등 기본 정보를 얻을 수 있습니다.

    Args:
        query: 검색할 밈 이름

    Returns:
        나무위키 문서 내용 (섹션별 텍스트)
    """
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

        # 외부 링크 추출
        youtube_links = []
        for a in soup.select("a[href*='youtube.com'], a[href*='youtu.be']"):
            href = a.get("href", "")
            if href and href not in youtube_links:
                youtube_links.append(href)

        if youtube_links:
            content_parts.append(f"\n## 관련 유튜브 링크")
            for link in youtube_links[:5]:
                content_parts.append(f"- {link}")

        result = "\n".join(content_parts)
        return result[:4000] if result else "내용을 추출할 수 없습니다."

    except Exception as e:
        return f"나무위키 검색 오류: {str(e)}"


@tool
def search_google(query: str, num_results: int = 5) -> str:
    """
    구글에서 밈 관련 정보를 검색합니다.
    나무위키에 없는 추가 정보, 최신 트렌드, 사용 예시 등을 찾을 수 있습니다.

    Args:
        query: 검색어 (예: "골반통신 밈 뜻", "매끈매끈하다 챌린지")
        num_results: 검색 결과 개수 (기본 5개)

    Returns:
        검색 결과 목록 (제목, URL, 스니펫)
    """
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
    """
    웹페이지의 본문 내용을 크롤링합니다.
    검색 결과에서 찾은 URL의 상세 내용을 가져올 때 사용합니다.

    Args:
        url: 크롤링할 웹페이지 URL

    Returns:
        페이지 본문 텍스트
    """
    # 나무위키는 별도 도구 사용
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
def get_youtube_info(url: str) -> str:
    """
    유튜브 영상의 정보를 가져옵니다.
    영상 제목, 설명, 조회수 등 밈의 원본 영상 정보를 얻을 수 있습니다.

    Args:
        url: 유튜브 영상 URL

    Returns:
        영상 정보 (제목, 설명 등)
    """
    try:
        # URL 정규화
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "shorts/" in url:
                video_id = url.split("shorts/")[1].split("?")[0]
            elif "embed/" in url:
                video_id = url.split("embed/")[1].split("?")[0]
            else:
                return "지원하지 않는 YouTube URL 형식입니다."
        else:
            return "YouTube URL이 아닙니다."

        # oEmbed API 사용 (API 키 불필요)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            title = data.get("title", "")
            author = data.get("author_name", "")

            # 영상 페이지에서 추가 정보 추출 시도
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            page_response = requests.get(video_url, headers=HEADERS, timeout=10)

            description = ""
            if page_response.status_code == 200:
                # 간단한 설명 추출 시도
                soup = BeautifulSoup(page_response.text, "html.parser")
                meta_desc = soup.find("meta", {"name": "description"})
                if meta_desc:
                    description = meta_desc.get("content", "")

            return f"""## YouTube 영상 정보
- 제목: {title}
- 채널: {author}
- URL: {video_url}
- 설명: {description[:500] if description else '(추출 불가)'}
"""
        else:
            return f"영상 정보를 가져올 수 없습니다. (video_id: {video_id})"

    except Exception as e:
        return f"YouTube 정보 추출 오류: {str(e)}"


@tool
def get_youtube_transcript(url: str) -> str:
    """
    유튜브 영상의 자막/스크립트를 타임스탬프와 함께 추출합니다.
    밈의 정확한 대사, 타이밍, 순서를 파악할 수 있습니다.

    Args:
        url: 유튜브 영상 URL

    Returns:
        타임스탬프별 자막 텍스트
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # video_id 추출
        video_id = None
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "shorts/" in url:
                video_id = url.split("shorts/")[1].split("?")[0]
            elif "embed/" in url:
                video_id = url.split("embed/")[1].split("?")[0]

        if not video_id:
            return "YouTube URL에서 video_id를 추출할 수 없습니다."

        # API 인스턴스 생성
        ytt = YouTubeTranscriptApi()

        # 자막 추출 시도 (한국어 우선)
        transcript = None
        for langs in [['ko'], ['ko', 'en'], ['en']]:
            try:
                transcript = ytt.fetch(video_id, languages=langs)
                break
            except Exception:
                continue

        if not transcript:
            # 사용 가능한 자막 목록 확인
            try:
                transcript_list = ytt.list(video_id)
                for t in transcript_list:
                    transcript = t.fetch()
                    break
            except Exception:
                pass

        if not transcript:
            return "자막을 찾을 수 없습니다."

        # 타임스탬프 포맷팅
        result_lines = ["## YouTube 영상 스크립트\n"]
        for entry in transcript:
            start = getattr(entry, 'start', 0)
            duration = getattr(entry, 'duration', 0)
            text = getattr(entry, 'text', str(entry))

            minutes = int(start // 60)
            seconds = int(start % 60)
            end_seconds = start + duration
            end_min = int(end_seconds // 60)
            end_sec = int(end_seconds % 60)

            time_str = f"[{minutes:02d}:{seconds:02d} - {end_min:02d}:{end_sec:02d}]"
            result_lines.append(f"{time_str} {text}")

        return "\n".join(result_lines[:100])

    except Exception as e:
        return f"자막 추출 오류: {str(e)}"


@tool
def get_youtube_stats(url: str) -> str:
    """
    YouTube 영상의 조회수, 좋아요, 업로드일 등 통계 정보를 가져옵니다.
    인기 콘텐츠 분석에 사용됩니다.

    Args:
        url: YouTube 영상 URL

    Returns:
        영상 통계 (조회수, 좋아요, 업로드일)
    """
    try:
        import json as json_module

        # video_id 추출
        video_id = None
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "youtube.com" in url:
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "shorts/" in url:
                video_id = url.split("shorts/")[1].split("?")[0]

        if not video_id:
            return "YouTube URL에서 video_id를 추출할 수 없습니다."

        # YouTube 페이지 요청
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(video_url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            return f"페이지 요청 실패: {response.status_code}"

        html = response.text

        # 방법 1: JSON-LD에서 추출
        view_count = None
        like_count = None
        upload_date = None
        title = None

        # ytInitialPlayerResponse에서 데이터 추출
        if "ytInitialPlayerResponse" in html:
            try:
                start = html.find("ytInitialPlayerResponse = ") + len("ytInitialPlayerResponse = ")
                end = html.find("};", start) + 1
                json_str = html[start:end]
                data = json_module.loads(json_str)

                video_details = data.get("videoDetails", {})
                title = video_details.get("title", "")
                view_count = video_details.get("viewCount", "")
            except Exception:
                pass

        # 방법 2: 메타 태그에서 추출
        soup = BeautifulSoup(html, "html.parser")

        if not view_count:
            # interactionCount 메타 태그
            meta_views = soup.find("meta", {"itemprop": "interactionCount"})
            if meta_views:
                view_count = meta_views.get("content", "")

        if not title:
            meta_title = soup.find("meta", {"name": "title"})
            if meta_title:
                title = meta_title.get("content", "")

        # 업로드 날짜
        meta_date = soup.find("meta", {"itemprop": "uploadDate"})
        if meta_date:
            upload_date = meta_date.get("content", "")

        # 조회수 포맷팅
        view_count_formatted = ""
        if view_count:
            try:
                vc = int(view_count)
                if vc >= 100000000:
                    view_count_formatted = f"{vc / 100000000:.1f}억회"
                elif vc >= 10000:
                    view_count_formatted = f"{vc / 10000:.1f}만회"
                else:
                    view_count_formatted = f"{vc:,}회"
            except ValueError:
                view_count_formatted = view_count

        return f"""## YouTube 영상 통계
- 제목: {title or '(추출 불가)'}
- 조회수: {view_count_formatted or '(추출 불가)'} (원본: {view_count or 'N/A'})
- 업로드일: {upload_date or '(추출 불가)'}
- URL: {video_url}
"""

    except Exception as e:
        return f"YouTube 통계 추출 오류: {str(e)}"


@tool
def search_youtube(query: str) -> str:
    """
    유튜브에서 밈 관련 영상을 검색합니다.
    원본 영상, 챌린지 영상, 리액션 영상 등을 찾을 수 있습니다.

    Args:
        query: 검색어 (예: "매끈매끈하다 챌린지", "골반통신 원본")

    Returns:
        검색된 영상 목록
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "SERPER_API_KEY가 설정되지 않았습니다."

    try:
        response = requests.post(
            "https://google.serper.dev/videos",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "q": f"{query} site:youtube.com",
                "gl": "kr",
                "hl": "ko",
                "num": 5
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("videos", []):
            title = item.get("title", "")
            link = item.get("link", "")
            channel = item.get("channel", "")
            duration = item.get("duration", "")
            results.append(f"- [{title}]({link})\n  채널: {channel}, 길이: {duration}")

        return "\n\n".join(results) if results else "검색 결과가 없습니다."

    except Exception as e:
        return f"YouTube 검색 오류: {str(e)}"


# 사용 가능한 도구 목록
ALL_TOOLS = [
    search_namuwiki,
    search_google,
    crawl_webpage,
    get_youtube_info,
    get_youtube_transcript,
    get_youtube_stats,
    search_youtube,
]
