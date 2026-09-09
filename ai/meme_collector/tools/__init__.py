from meme_collector.tools.namuwiki import search_namuwiki, search_namuwiki_section
from meme_collector.tools.naver_search import search_naver_blog, search_naver_news
from meme_collector.tools.usage_extractor import extract_usage_examples
from meme_collector.tools.video_analyzer import analyze_meme_video
from meme_collector.tools.web_search import search_web
from meme_collector.tools.youtube import search_youtube_shorts, search_youtube_videos

COLLECTOR_TOOLS = [
    search_namuwiki,
    search_namuwiki_section,
    search_naver_blog,
    search_naver_news,
    search_youtube_videos,
    search_youtube_shorts,
    analyze_meme_video,
    extract_usage_examples,
    search_web,
]

__all__ = [
    "analyze_meme_video",
    "extract_usage_examples",
    "search_namuwiki",
    "search_namuwiki_section",
    "search_naver_blog",
    "search_naver_news",
    "search_web",
    "search_youtube_videos",
    "search_youtube_shorts",
    "COLLECTOR_TOOLS",
]
