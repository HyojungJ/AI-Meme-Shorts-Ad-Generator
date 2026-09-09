"""
나무위키 밈 목록 파서

2025년 밈 목록을 파싱하여 parent-child 관계를 포함한 구조화된 데이터로 변환
"""

import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class MemeEntry:
    """밈 엔트리"""
    name: str
    parent: Optional[str] = None
    month: Optional[str] = None
    year: str = "2025"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "parent": self.parent,
            "month": self.month,
            "year": self.year
        }


def fetch_meme_page() -> str:
    """나무위키 밈 시기별 페이지 가져오기"""
    url = "https://namu.wiki/w/%EB%B0%88(%EC%9D%B8%ED%84%B0%EB%84%B7%20%EC%9A%A9%EC%96%B4)/%EC%8B%9C%EA%B8%B0%EB%B3%84"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def parse_meme_entry(raw_text: str, month: str) -> list[MemeEntry]:
    """
    단일 밈 엔트리 파싱

    예시:
    - "흑백요리사 2(안성재 옷 입히기, 아기맹수요. 맹수. 앙!)"
    - "스핔이(스피키 네르지 마세요)"
    - "레제(전부 다 가르쳐줄게, 레제는 그 카페에 가려고 했어)"
    """
    entries = []

    # 각주 제거 [숫자], [N월~]
    text = re.sub(r'\[\d+\]', '', raw_text)
    text = re.sub(r'\[\d+월~?\]', '', text)
    text = text.strip()

    if not text:
        return entries

    # 괄호가 있는 경우: 메인 + 서브밈
    paren_match = re.match(r'^(.+?)\((.+)\)$', text)

    if paren_match:
        main_name = paren_match.group(1).strip()
        sub_content = paren_match.group(2).strip()

        # 메인 밈 추가
        entries.append(MemeEntry(name=main_name, parent=None, month=month))

        # 서브 밈 파싱 (쉼표로 구분)
        # 단, "아기맹수요. 맹수. 앙!" 처럼 문장인 경우는 하나로 처리
        sub_memes = split_sub_memes(sub_content)

        for sub in sub_memes:
            sub = sub.strip()
            if sub and sub != main_name:
                entries.append(MemeEntry(name=sub, parent=main_name, month=month))
    else:
        # 괄호 없는 경우: 단일 밈
        entries.append(MemeEntry(name=text, parent=None, month=month))

    return entries


def split_sub_memes(content: str) -> list[str]:
    """
    괄호 안 내용을 개별 밈으로 분리

    - 쉼표로 구분
    - 단, 짧은 조사/어미로 끝나는 경우 합침
    """
    # 먼저 쉼표로 분리
    parts = [p.strip() for p in content.split(',')]

    result = []
    for part in parts:
        if not part:
            continue

        # 너무 짧은 것은 이전 것과 합치기 (예: "맹수. 앙!")
        if len(part) < 3 and result:
            result[-1] = result[-1] + ', ' + part
        else:
            result.append(part)

    return result


def parse_2025_memes(html: str) -> list[MemeEntry]:
    """2025년 대한민국 밈 목록 파싱"""
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()

    # 2025년 섹션 추출
    match = re.search(
        r'1\.1\.11\.\s*2025년\[\d+\]\[편집\](.*?)1\.1\.12\.\s*2026년',
        text,
        re.DOTALL
    )

    if not match:
        print("2025년 섹션을 찾을 수 없습니다")
        return []

    section = match.group(1).strip()
    section = re.sub(r'\s+', ' ', section)

    # 월별로 분리
    entries = []
    months = re.split(r'(\d+월:)', section)

    current_month = None
    for part in months:
        part = part.strip()

        if re.match(r'\d+월:', part):
            current_month = part.replace(':', '')
        elif current_month and part:
            # 쉼표로 밈 분리
            raw_memes = part.split(',')

            for raw in raw_memes:
                raw = raw.strip()
                if raw:
                    meme_entries = parse_meme_entry(raw, current_month)
                    entries.extend(meme_entries)

    return entries


def get_2025_memes() -> list[MemeEntry]:
    """2025년 밈 목록 가져오기"""
    html = fetch_meme_page()
    return parse_2025_memes(html)


def get_memes_by_month(entries: list[MemeEntry], month: str) -> list[MemeEntry]:
    """특정 월의 밈만 필터링"""
    return [e for e in entries if e.month == month]


def get_unique_memes(entries: list[MemeEntry]) -> list[MemeEntry]:
    """중복 제거 (이름 기준)"""
    seen = set()
    unique = []
    for e in entries:
        if e.name not in seen:
            seen.add(e.name)
            unique.append(e)
    return unique


def main():
    """테스트 실행"""
    print("나무위키 2025년 밈 목록 파싱 중...\n")

    entries = get_2025_memes()

    # 통계
    print(f"총 엔트리 수: {len(entries)}")
    print(f"고유 밈 수: {len(get_unique_memes(entries))}")

    # 월별 통계
    months = {}
    for e in entries:
        if e.month not in months:
            months[e.month] = []
        months[e.month].append(e)

    print("\n=== 월별 통계 ===")
    for month in ['1월', '2월', '3월', '4월', '5월', '6월',
                  '7월', '8월', '9월', '10월', '11월', '12월']:
        if month in months:
            count = len(months[month])
            parents = len([e for e in months[month] if e.parent is None])
            children = count - parents
            print(f"{month}: {count}개 (메인: {parents}, 서브: {children})")

    # Parent-Child 예시 출력
    print("\n=== Parent-Child 관계 예시 ===")
    parents_with_children = {}
    for e in entries:
        if e.parent:
            if e.parent not in parents_with_children:
                parents_with_children[e.parent] = []
            parents_with_children[e.parent].append(e.name)

    for parent, children in list(parents_with_children.items())[:10]:
        print(f"\n{parent}:")
        for child in children:
            print(f"  └─ {child}")


if __name__ == "__main__":
    main()
