from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DefinitionConfig:
    extraction_keywords: list = field(default_factory=lambda: [
        "정의", "뜻", "의미", "~은", "~는", "개요", "설명"
    ])
    max_lines: int = 5
    max_chars: int = 1000
    min_valid_length: int = 50
    llm_extraction: bool = True
    crawl_count: int = 2


@dataclass
class DomainConfig:
    priority_domains: list = field(default_factory=lambda: [
        "blog.naver.com", "tistory.com", "brunch.co.kr", "velog.io"
    ])
    allowed_domains: list = field(default_factory=lambda: [
        "blog.naver.com", "tistory.com", "brunch.co.kr", "velog.io",
        "hankyung.com", "donga.com", "mt.co.kr", "news.naver.com", "zdnet.co.kr"
    ])
    blocked_domains: list = field(default_factory=lambda: [
        "ruliweb.com", "dcinside.com", "fmkorea.com", "dogdrip.net",
        "theqoo.net", "instiz.net", "pinterest.com", "instagram.com"
    ])
    wiki_domains: list = field(default_factory=lambda: [
        "namu.wiki", "knowyourmeme.com", "ko.wikipedia.org"
    ])


@dataclass
class UsageSearchConfig:
    usage_keywords: list = field(default_factory=lambda: [
        "활용", "사용법", "예시", "후기", "따라하기", "챌린지"
    ])
    min_urls: int = 3
    max_urls: int = 5
    search_results_count: int = 5


@dataclass
class RiskSearchConfig:
    risk_query_patterns: list = field(default_factory=lambda: [
        "{meme_name} 논란 OR 사건 OR 문제",
        "{meme_name} 비판 OR 혐오 OR 차별",
        "{meme_name} 불쾌 OR 부적절"
    ])
    risk_keywords: list = field(default_factory=lambda: [
        "논란", "비판", "혐오", "차별", "불쾌", "부적절", "사과", "삭제"
    ])
    search_results_count: int = 5


@dataclass
class MemeTypingConfig:
    pass


@dataclass
class AgentConfig:
    definition: DefinitionConfig = field(default_factory=DefinitionConfig)
    domain: DomainConfig = field(default_factory=DomainConfig)
    usage_search: UsageSearchConfig = field(default_factory=UsageSearchConfig)
    risk_search: RiskSearchConfig = field(default_factory=RiskSearchConfig)
    meme_typing: MemeTypingConfig = field(default_factory=MemeTypingConfig)
    primary_model: str = "gpt-4o-mini-2024-07-18"
    strong_model: str = "gpt-4o-2024-08-06"
    agent_output_dir: Path = field(default_factory=lambda: Path("data/agent_output"))
    audio_output_dir: Path = field(default_factory=lambda: Path("data/raw/audio"))
    video_cache_dir: Path = field(default_factory=lambda: Path("data/raw/video_cache"))


_default_config = None


def get_config():
    global _default_config
    if _default_config is None:
        _default_config = AgentConfig()
    return _default_config


def set_config(config):
    global _default_config
    _default_config = config


def reset_config():
    global _default_config
    _default_config = None
