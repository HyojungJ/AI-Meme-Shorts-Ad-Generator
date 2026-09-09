import json
from scripts.agent.config import get_config


def get_definition_prompt(meme_name):
    config = get_config().definition
    return f"""'{meme_name}' 밈의 정의와 기원을 수집하세요.

## 1단계: 검색 (병렬 호출)
- search_namuwiki("{meme_name}")
- search_google("{meme_name} 밈 뜻 유래")

## 2단계: 크롤링
검색 결과에서 밈 정의가 상세히 설명된 URL을 {config.crawl_count}개 선택하여 crawl_webpage로 크롤링하세요.

크롤링 대상 선정 기준:
- 블로그, 뉴스 기사 우선 (상세 설명 가능성 높음)
- 나무위키는 이미 search_namuwiki로 수집하므로 제외
- 커뮤니티 이미지 게시물 (dcinside, ruliweb 등) 제외

## 필수 수집 정보
1. 정확한 정의 (밈이 무엇인지, 3-5문장으로 상세히)
2. 출처 (어디서 시작됐는지)
3. 제작자/원작자
4. 시작 시점
5. 핵심 대사 (있다면)

중요: 검색 결과와 크롤링한 내용에서 정의와 유래를 원문 그대로 기록하세요."""


def get_definition_extract_prompt(meme_name, search_result):
    return f"""'{meme_name}' 밈의 정의와 기원을 검색 결과에서 추출하세요.

## 검색 결과
{search_result[:6000]}

## definition 작성 요구사항
다음 내용을 모두 포함한 종합적 설명 (5-10문장):
- 밈의 정의와 의미
- 기원/유래 (어디서, 누가, 언제)
- 원래 의미 → 현재 밈으로의 변화 (해당 시)
- 현재 용법과 톤 (긍정/부정/조롱 등)
- 주요 사용 커뮤니티/플랫폼

## 규칙
- 검색 결과에 없는 내용 만들지 말 것
- creator는 실명만 (별명 X)
- 정보 없으면 null"""


def get_risk_info_prompt(meme_name):
    return f"""'{meme_name}' 밈의 위험 정보를 분석하세요.

## 수집 항목
- controversies: 관련 논란/사건
- sensitive_topics: 정치/종교/인종/성별 연관성
- risk_level: low(가벼운 유머) / medium(일부 비판) / high(심각한 논란, 혐오/차별)
- news_summary: 최근 뉴스 요약

논란 없으면 risk_level은 low."""


def get_usage_search_prompt(meme_name):
    config = get_config()
    domain_config = config.domain

    # config에서 우선 도메인으로 site: 검색어 생성
    site_searches = "\n".join([
        f'- search_google("site:{domain} {meme_name} 밈 활용")'
        for domain in domain_config.priority_domains[:2]
    ])

    return f"""'{meme_name}' 밈이 실제로 어떻게 활용되는지 블로그/뉴스를 검색하세요.

병렬로 다음 도구들을 호출하세요:
{site_searches}
- search_google("{meme_name} 챌린지 예시 후기")

활용 예시가 **구체적으로 설명된** 블로그나 뉴스 기사를 찾으세요."""


def get_crawl_examples_prompt(meme_name):
    config = get_config()
    domain_config = config.domain
    usage_config = config.usage_search

    # config에서 동적으로 값 가져오기
    priority_domains = ", ".join(domain_config.priority_domains[:3])
    usage_keywords = ", ".join([f'"{kw}"' for kw in usage_config.usage_keywords[:4]])
    blocked_domains = ", ".join(domain_config.blocked_domains[:4])

    return f"""이전 검색 결과에서 **밈 활용 예시가 상세히 설명된** URL을 크롤링하세요.

## 크롤링 대상 선정 기준
1. 블로그 ({priority_domains}) 우선
2. {usage_keywords} 키워드가 있는 페이지
3. 밈의 정의만 설명하는 페이지는 제외

## 금지
- 커뮤니티 이미지 게시물 ({blocked_domains} 등)
- 밈 사전/위키 페이지 (정의만 있음)

**최소 {usage_config.min_urls}개, 최대 {usage_config.max_urls}개** URL을 crawl_webpage로 크롤링하세요.
각 페이지에서 밈이 **어떻게 활용되는지** 구체적인 내용을 찾아야 합니다."""


def get_meme_typing_prompt(meme_name, definition, motion_prompt_hint="", detected_text=""):
    return f"""밈 유형을 분류하세요.

## 밈 정보
- 이름: {meme_name}
- 정의: {definition}
- 영상 분석: {motion_prompt_hint if motion_prompt_hint else "N/A"}
- 감지된 대사: {detected_text if detected_text else "N/A"}

## 유형 정의
**quotable**: 대사/발음/말투가 핵심. 예: "나니가 스키", "야 데이터", "영포티"
**performable**: 춤/제스처/표정이 핵심 (무성 영상도 OK). 예: 랫댄스, 카이사 댄스
**hybrid**: 대사+동작이 모두 필요. 예: "매끈매끈하다" (춤추며 말해야 완성)

## 판단 기준
1. 대사만으로 밈이 성립? → quotable
2. 동작만으로 밈이 성립? → performable
3. 대사+동작 둘 다 있어야 밈이 완성? → hybrid"""


def get_finalize_prompt(
    crawled_sources,
    risk_info=None,
    youtube_shorts=None,
    video_analysis=None,
    meme_type="",
    key_phrase=None,
    audio_analysis=None
):
    sources_text = ""
    for i, source in enumerate(crawled_sources, 1):
        sources_text += f"""
---
[소스 {i}]
URL: {source.get('url', 'N/A')}
제목: {source.get('title', 'N/A')}
내용:
{source.get('content', '')[:2000]}
---
"""

    schema = {
        "meta": {
            "agent_version": "v8",
            "processed_at": "ISO timestamp"
        },
        "basic_info": {
            "name": "밈 이름",
            "definition": "밈에 대한 상세한 정의 (3-5문장)",
            "origin": {
                "source": "출처",
                "creator": "제작자",
                "date": "시작 시점",
                "platform": "플랫폼"
            },
            "keywords": ["검색 키워드"]
        },
        "risk_info": {
            "controversies": ["논란 목록"],
            "sensitive_topics": ["민감 주제"],
            "risk_level": "low|medium|high",
            "news_summary": "최근 뉴스 요약",
            "collected_at": "ISO timestamp"
        },
        "usage_examples": [
            {
                "source_url": "크롤링한 원본 URL (필수)",
                "source_title": "원본 페이지 제목",
                "context": "어떤 상황/맥락에서 사용되는지",
                "description": "밈이 어떻게 활용되는지 (원문 인용 포함, 3-5문장)",
                "original_quote": "원문에서 직접 발췌한 문장",
                "example_type": "챌린지 | 패러디 | 상황극 | 짤 | 댓글 | 기타"
            }
        ],
        "youtube_shorts": [
            {
                "video_id": "영상 ID",
                "youtube_url": "YouTube URL",
                "video_title": "영상 제목",
                "view_count": 0
            }
        ],
        "meme_classification": {
            "meme_type": "quotable|performable",
            "key_phrase": "핵심 대사 (quotable인 경우)",
            "needs_audio": True
        },
        "video_analysis": {
            "source_video_id": "분석한 영상 ID",
            "time_stamp": {
                "start": 0.0,
                "end": 0.0,
                "detected_text": "감지된 대사"
            },
            "motion_prompt_hint": "Runway/Pika용 motion prompt",
            "style_keywords": ["스타일 키워드"],
            "duration_seconds": 0.0,
            "movement_analysis": {}
        },
        "audio_analysis": {
            "enabled": True,
            "audio_file": "오디오 파일 경로",
            "segment": {
                "start": 0.0,
                "end": 0.0
            },
            "prosody": {},
            "ssml": "<speak>...</speak>"
        },
        "video_generation": {
            "motion_prompt": "최종 motion prompt",
            "style_keywords": [],
            "negative_prompt": "",
            "duration_seconds": 0.0
        }
    }

    # 수집된 데이터 요약
    collected_data = f"""
## 수집된 데이터 요약

### Risk Info
{json.dumps(risk_info, ensure_ascii=False, indent=2) if risk_info else "수집되지 않음"}

### YouTube Shorts
{json.dumps(youtube_shorts[:3] if youtube_shorts else [], ensure_ascii=False, indent=2)}

### Video Analysis
{json.dumps(video_analysis, ensure_ascii=False, indent=2) if video_analysis else "분석되지 않음"}

### Meme Classification
- Type: {meme_type or "미분류"}
- Key Phrase: {key_phrase or "없음"}

### Audio Analysis
{json.dumps(audio_analysis, ensure_ascii=False, indent=2) if audio_analysis else "분석되지 않음 (performable 밈)"}
"""

    return f"""수집된 모든 정보를 바탕으로 최종 JSON을 생성하세요.

## 크롤링된 소스 (원문)
{sources_text if sources_text else "(크롤링된 소스 없음)"}

{collected_data}

## 필수 규칙 (매우 중요!)

### 1. usage_examples는 반드시 크롤링된 소스에서만 추출
- **위 소스에 없는 내용은 절대 포함하지 마세요**
- 각 예시의 `source_url`은 반드시 위 소스의 URL 중 하나여야 함
- `original_quote`는 원문에서 **그대로 복사**한 문장

### 2. 검증 체크리스트
- [ ] source_url이 위 소스 목록에 있는가?
- [ ] original_quote가 해당 소스 내용에 실제로 존재하는가?
- [ ] description이 원문 내용을 정확히 반영하는가?

### 3. 수집된 데이터 통합
- risk_info, youtube_shorts, video_analysis, audio_analysis는 위 데이터를 그대로 포함
- 누락된 데이터는 기본값 또는 빈 객체로 처리

## JSON 스키마
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```

중요: 크롤링된 소스에서 활용 예시를 찾을 수 없다면, usage_examples를 빈 배열로 반환하세요.
**없는 내용을 만들어내지 마세요.**

JSON만 출력하세요."""
