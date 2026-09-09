import re
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

MEME_TIMELINE_URL = "https://namu.wiki/w/%EB%B0%88(%EC%9D%B8%ED%84%B0%EB%84%B7%20%EC%9A%A9%EC%96%B4)/%EC%8B%9C%EA%B8%B0%EB%B3%84"


def fetch_meme_list(year: int = 2026, region: str = "korea") -> list[dict]:
    """나무위키 밈/시기별 페이지에서 특정 연도의 밈 목록을 크롤링합니다.

    Args:
        year: 연도 (기본값 2026)
        region: "korea" 또는 "foreign" (기본값 korea)

    Returns:
        list of {"name": 밈이름, "link": 나무위키링크 or None}
    """
    response = requests.get(MEME_TIMELINE_URL, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    section_prefix = "1.1" if region == "korea" else "1.2"
    target_header = None

    for h in soup.find_all("h4"):
        text = h.get_text()
        if section_prefix in text and f"{year}년" in text:
            target_header = h
            break

    if not target_header:
        return []

    # 헤더 다음 콘텐츠에서 밈과 링크 추출
    meme_div = None
    for elem in target_header.find_all_next():
        if elem.name == "h4":
            break
        if "월:" in elem.get_text():
            meme_div = elem
            break

    if not meme_div:
        return []

    # 링크 정보 수집: {링크텍스트: href}
    link_map = {}
    for link in meme_div.find_all("a"):
        href = link.get("href", "")
        link_text = link.get_text(strip=True)
        if href.startswith("/w/") and link_text and len(link_text) > 1:
            link_map[link_text] = href

    # 텍스트에서 밈 이름 파싱
    meme_text = meme_div.get_text(strip=True)
    meme_names = _parse_meme_text(meme_text)

    # 밈 이름과 링크 매칭
    result = []
    for name in meme_names:
        link = link_map.get(name)
        result.append({"name": name, "link": link})

    return result


def _parse_meme_text(text: str) -> list[str]:
    """밈 목록 텍스트를 파싱합니다."""
    memes = []
    seen = set()

    # "X월:"을 쉼표로 치환 (월 경계에서 밈 이름이 붙는 문제 방지)
    text = re.sub(r"\d+월:", ",", text)

    # 괄호 내용 처리: "흑백요리사 2(안성재옷 입히기,아기 맹수)" -> 각각 추출
    paren_matches = re.findall(r"\(([^)]+)\)", text)
    for match in paren_matches:
        for item in match.split(","):
            item = item.strip()
            if _is_valid_meme_name(item) and item not in seen:
                seen.add(item)
                memes.append(item)

    # 괄호와 대괄호 제거
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)

    # 쉼표로 분리
    for item in text.split(","):
        item = item.strip()
        if _is_valid_meme_name(item) and item not in seen:
            seen.add(item)
            memes.append(item)

    return memes


def _is_valid_meme_name(name: str) -> bool:
    """유효한 밈 이름인지 확인합니다."""
    if len(name) < 2 or len(name) > 50:
        return False
    if re.match(r"^[\d\s]+$", name):
        return False
    if re.match(r"^[~\-\s]+$", name):
        return False
    return True


def fetch_meme_content(link: str, meme_name: str = "") -> str:
    """나무위키 링크에서 밈 관련 콘텐츠를 추출합니다.

    Args:
        link: 나무위키 링크 (예: "/w/김동현(1981)#밈")
        meme_name: 밈 이름 (앵커가 없을 때 관련 섹션 찾기용)

    Returns:
        밈 관련 콘텐츠 텍스트
    """
    # 앵커 분리
    if "#" in link:
        path, anchor = link.split("#", 1)
        anchor = unquote(anchor)
    else:
        path, anchor = link, None

    url = f"https://namu.wiki{path}"
    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # 앵커가 있으면 해당 섹션 추출
    if anchor:
        return _extract_section_by_anchor(soup, anchor, meme_name)

    # 앵커 없으면 밈 이름으로 관련 섹션 찾기
    if meme_name:
        return _extract_section_by_keyword(soup, meme_name)

    # 둘 다 없으면 전체 요약
    return _extract_full_summary(soup)


def _extract_section_by_anchor(soup: BeautifulSoup, anchor: str, meme_name: str) -> str:
    """앵커로 특정 섹션 추출"""
    parts = []

    # 앵커 형식: "밈" 또는 "s-3.9" 등
    target_header = None

    for header in soup.select("h2, h3, h4, h5"):
        header_text = header.get_text(strip=True)
        # 앵커와 매칭 (밈, s-3.9 등)
        if anchor in header_text or anchor.replace("s-", "") in header_text:
            target_header = header
            break
        # "밈" 앵커는 헤더에 "밈"이 포함되면 매칭
        if anchor == "밈" and "밈" in header_text:
            target_header = header
            break

    if not target_header:
        # 앵커를 못 찾으면 밈 이름으로 검색
        if meme_name:
            return _extract_section_by_keyword(soup, meme_name)
        return ""

    # 해당 섹션 콘텐츠 추출
    section_text = target_header.get_text(strip=True)
    parts.append(f"## {section_text}")

    for elem in target_header.find_all_next():
        if elem.name in ["h2", "h3", "h4", "h5"]:
            # 같은 레벨 이상의 헤더 만나면 중단
            break
        text = elem.get_text(strip=True)
        if text and len(text) > 10:
            parts.append(text)

    result = "\n\n".join(parts)
    return result[:4000] if result else ""


def _extract_section_by_keyword(soup: BeautifulSoup, keyword: str) -> str:
    """키워드가 포함된 섹션 추출"""
    parts = []

    for header in soup.select("h2, h3, h4, h5"):
        header_text = header.get_text(strip=True)

        # 헤더 다음 콘텐츠에서 키워드 검색
        section_content = []
        for elem in header.find_all_next():
            if elem.name in ["h2", "h3", "h4", "h5"]:
                break
            text = elem.get_text(strip=True)
            if text:
                section_content.append(text)

        full_section = " ".join(section_content)
        if keyword in full_section:
            parts.append(f"## {header_text}")
            # 키워드 주변 텍스트 추출
            for text in section_content:
                if keyword in text or len(text) > 50:
                    parts.append(text[:500])
            break  # 첫 번째 매칭 섹션만

    result = "\n\n".join(parts)
    return result[:4000] if result else ""


def _extract_full_summary(soup: BeautifulSoup) -> str:
    """전체 문서 요약 추출 - 유래/출처 섹션 우선"""
    parts = []

    title = soup.select_one("h1.title")
    if title:
        parts.append(f"# {title.get_text(strip=True)}")

    # 유래/출처 관련 섹션을 우선적으로 추출
    priority_keywords = ["유래", "출처", "개요", "원본", "기원"]
    priority_headers = []
    other_headers = []

    for header in soup.select("h2, h3"):
        header_text = header.get_text(strip=True)
        is_priority = any(kw in header_text for kw in priority_keywords)
        if is_priority:
            priority_headers.append(header)
        else:
            other_headers.append(header)

    # 우선 섹션 먼저, 그 다음 일반 섹션 (최대 5개)
    headers_to_process = priority_headers + other_headers[:5 - len(priority_headers)]

    for header in headers_to_process:
        text = re.sub(r"\[.*?\]", "", header.get_text(strip=True)).strip()
        text = re.sub(r"^\d+\.?\s*", "", text).strip()
        if not text:
            continue

        parts.append(f"\n## {text}")

        content = []
        for elem in header.find_all_next():
            if elem.name in ["h2", "h3"]:
                break
            t = elem.get_text(strip=True)
            if t and len(t) > 20:
                content.append(t)

        # 유래/출처 섹션은 더 많은 내용 포함
        is_priority = any(kw in text for kw in priority_keywords)
        if content:
            if is_priority:
                # 유래 섹션은 전체 내용 포함 (최대 1000자)
                parts.append("\n".join(content)[:1000])
            else:
                parts.append(max(content, key=len)[:500])

    result = "\n".join(parts)
    return result[:5000] if result else ""


@tool
def search_namuwiki(query: str) -> str:
    """나무위키에서 밈 문서를 검색합니다. 밈의 정의, 유래, 관련 인물 정보를 찾을 때 사용합니다."""
    # "#" 포함 시 특정 섹션 검색
    if "#" in query:
        link = f"/w/{quote(query.split('#')[0], safe='')}"
        anchor = query.split("#")[1]
        return fetch_meme_content(f"{link}#{anchor}", query.split("#")[0])

    url = f"https://namu.wiki/w/{quote(query, safe='')}"

    response = requests.get(url, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        return f"문서를 찾을 수 없습니다: {query}"

    soup = BeautifulSoup(response.text, "html.parser")
    return _extract_full_summary(soup) or "내용을 추출할 수 없습니다."


@tool
def search_namuwiki_section(doc_path: str, meme_name: str) -> str:
    """나무위키 특정 섹션을 검색합니다. 나무위키 링크가 주어진 경우 사용합니다."""
    if not doc_path.startswith("/w/"):
        doc_path = f"/w/{doc_path}"

    return fetch_meme_content(doc_path, meme_name)
