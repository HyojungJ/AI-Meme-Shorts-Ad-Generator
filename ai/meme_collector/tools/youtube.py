import json
import logging
import subprocess

import requests
from langchain_core.tools import tool

from common import config, get_openai

log = logging.getLogger(__name__)


def _search_ytdlp(query: str, max_results: int = 10, shorts_only: bool = False) -> list[dict]:
    """yt-dlp로 YouTube 검색 (API 할당량 초과 시 fallback)"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", f"ytsearch{max_results * 2}:{query}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.warning(f"yt-dlp 검색 실패: {result.stderr[:100]}")
            return []

        data = json.loads(result.stdout)
        entries = data.get("entries", [])

        # 쇼츠만 필터링 (60초 이하)
        if shorts_only:
            entries = [e for e in entries if e.get("duration") and e["duration"] <= 60]

        return entries[:max_results]
    except subprocess.TimeoutExpired:
        log.warning("yt-dlp 검색 타임아웃")
        return []
    except Exception as e:
        log.warning(f"yt-dlp 검색 에러: {e}")
        return []


def _search(query: str, max_results: int, video_duration: str = None) -> list[dict]:
    if not config.youtube_api_key:
        return []

    params = {"part": "snippet", "q": query, "type": "video", "maxResults": max_results, "order": "relevance", "key": config.youtube_api_key}
    if video_duration:
        params["videoDuration"] = video_duration

    response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=config.api.timeout)
    return response.json().get("items", []) if response.status_code == 200 else []


def _get_stats(video_ids: list[str]) -> dict:
    if not video_ids or not config.youtube_api_key:
        return {}

    response = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={"part": "statistics", "id": ",".join(video_ids), "key": config.youtube_api_key},
        timeout=config.api.timeout,
    )
    if response.status_code != 200:
        return {}

    return {item["id"]: item.get("statistics", {}) for item in response.json().get("items", [])}


@tool
def search_youtube_videos(query: str, max_results: int = 5) -> str:
    """YouTube에서 영상을 검색합니다. 밈의 원본 영상이나 패러디를 찾을 때 사용합니다."""
    items = _search(query, max_results)
    if not items:
        return "검색 결과가 없습니다."

    video_ids = [i["id"]["videoId"] for i in items]
    stats = _get_stats(video_ids)

    results = []
    for item in items:
        vid = item["id"]["videoId"]
        title = item["snippet"]["title"]
        views = stats.get(vid, {}).get("viewCount", "N/A")
        results.append(f"- [{title}](https://youtube.com/watch?v={vid}) (조회수: {views})")

    return "\n".join(results)


@tool
def search_youtube_shorts(meme_name: str, creator: str = "", key_phrase: str = "", max_results: int = 10) -> list[dict]:
    """YouTube Shorts에서 밈 원본 영상을 검색합니다. creator, key_phrase가 있으면 정확도가 높아집니다."""
    queries = _build_meme_queries(meme_name, creator, key_phrase)

    seen_ids = set()
    all_items = []

    # 1차: YouTube Data API 시도
    for q in queries:
        items = _search(q, max_results // 2 + 1, "short")
        for item in items:
            vid = item["id"]["videoId"]
            if vid not in seen_ids:
                seen_ids.add(vid)
                all_items.append(item)

    # 2차: API 실패 시 yt-dlp fallback
    if not all_items:
        log.info("YouTube API 실패, yt-dlp fallback 사용")
        for q in queries[:3]:  # 상위 3개 쿼리만 시도
            entries = _search_ytdlp(q, max_results, shorts_only=True)
            for entry in entries:
                vid = entry.get("id", "")
                if vid and vid not in seen_ids:
                    seen_ids.add(vid)
                    all_items.append({
                        "id": {"videoId": vid},
                        "snippet": {"title": entry.get("title", "")},
                        "_duration": entry.get("duration"),
                    })
            if len(all_items) >= max_results:
                break

    if not all_items:
        return []

    video_ids = [i["id"]["videoId"] for i in all_items]
    stats = _get_stats(video_ids)

    results = []
    for item in all_items:
        vid = item["id"]["videoId"]
        title = item["snippet"]["title"]
        view_count = int(stats.get(vid, {}).get("viewCount", 0))
        relevance_score = _calc_relevance(title, meme_name, creator)
        results.append({
            "video_id": vid,
            "url": f"https://youtube.com/shorts/{vid}",
            "title": title,
            "view_count": view_count,
            "_relevance": relevance_score,
        })

    # 관련성 점수로 정렬 (동점이면 조회수)
    results.sort(key=lambda x: (x["_relevance"], x["view_count"]), reverse=True)

    for r in results:
        del r["_relevance"]

    # LLM 기반 관련성 필터 적용
    results = _filter_relevant_videos(results, meme_name, max_results)
    return results


def _filter_relevant_videos(videos: list[dict], meme_name: str, max_results: int = 5) -> list[dict]:
    """LLM으로 밈과 관련된 영상만 필터링. 관련 영상 없으면 fallback으로 상위 2개 반환."""
    if not videos:
        return []

    client = get_openai()
    titles = [f"{i + 1}. {v['title']}" for i, v in enumerate(videos)]

    response = client.chat.completions.create(
        model=config.models.default,
        messages=[{
            "role": "user",
            "content": f"""밈 이름: "{meme_name}"

아래 YouTube 영상 제목 중 이 **밈과 직접 관련된** 영상 번호만 선택하세요.

판단 기준:
- 밈의 원본/출처 영상
- 밈을 패러디하거나 활용한 영상
- 밈 자체를 설명하는 영상

제외 기준:
- 밈 이름에 포함된 단어가 우연히 겹치는 무관한 콘텐츠
- 밈과 관련 없는 일반 영상

영상 목록:
{chr(10).join(titles)}

관련된 영상 번호만 콤마로 구분하여 출력 (예: 1,3,5)
관련 영상 없으면 "없음" 출력""",
        }],
        temperature=0,
    )

    result = response.choices[0].message.content.strip()
    if result == "없음":
        # Fallback: LLM이 관련 영상 없다고 판단해도 상위 2개는 반환 (검색은 성공했으므로)
        log.info(f"LLM 필터가 관련 영상 없다고 판단, fallback으로 상위 2개 반환")
        return videos[:2]

    try:
        indices = [int(x.strip()) - 1 for x in result.split(",")]
        return [videos[i] for i in indices if 0 <= i < len(videos)][:max_results]
    except Exception as e:
        log.warning(f"Video filtering failed, returning unfiltered: {e}")
        return videos[:max_results]


def _build_meme_queries(meme_name: str, creator: str, key_phrase: str = "") -> list[str]:
    """밈 검색을 위한 다양한 쿼리 생성 (creator, key_phrase 활용으로 정확도 향상)"""
    queries = []

    # 1. creator + meme_name (가장 정확)
    if creator:
        queries.append(f"{creator} {meme_name}")
        queries.append(f"{creator} {meme_name} 밈")

    # 2. key_phrase로 직접 검색 (핵심 대사로 찾기)
    if key_phrase:
        queries.append(key_phrase)
        queries.append(f"{key_phrase} 밈")

    # 3. meme_name + 밈 키워드
    queries.append(f"{meme_name} 밈 원본")
    queries.append(f"{meme_name} 짤")
    queries.append(f"{meme_name} 챌린지")

    return queries


def _calc_relevance(title: str, meme_name: str, creator: str) -> int:
    score = 0
    if meme_name in title:
        score += 50

    # creator 포함
    if creator and creator in title:
        score += 30

    # 밈 관련 키워드
    meme_keywords = ["밈", "짤", "원본", "레전드", "명장면"]
    for kw in meme_keywords:
        if kw in title:
            score += 10

    return score
