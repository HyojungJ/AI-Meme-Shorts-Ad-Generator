# Meme Agent v5 Architecture

> Meme-fluencer 프로젝트의 밈 데이터 수집 Agent 아키텍처 문서

## 목차

1. [개요](#1-개요)
2. [그래프 구조](#2-그래프-구조)
3. [Phase 흐름](#3-phase-흐름)
4. [Tools 정의](#4-tools-정의)
5. [State 관리](#5-state-관리)
6. [데이터 스키마](#6-데이터-스키마)
7. [밈 유형별 분류](#7-밈-유형별-분류)

---

## 1. 개요

### 1.1 목적

밈 데이터를 자동으로 수집, 분류, 분석하여 숏폼 콘텐츠 제작에 필요한 완성된 데이터를 제공한다.

### 1.2 기술 스택

| 구성 요소 | 기술 |
|----------|------|
| Agent Framework | LangGraph (StateGraph) |
| LLM (빠른 작업) | GPT-4o-mini |
| LLM (정확한 작업) | GPT-4o |
| Tools | LangChain @tool |

### 1.3 주요 특징

- **단일 Agent 구조**: LangGraph StateGraph 기반
- **9단계 순차 수집**: 효율적인 단계별 정보 수집
- **이중 모델 전략**: 빠른 작업(mini) + 정확한 작업(4o)
- **Rate Limit 처리**: 자동 재시도 로직

---

## 2. 그래프 구조

### 2.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph StateGraph                        │
│                    (단일 Agent, 9단계 수집)                       │
└─────────────────────────────────────────────────────────────────┘

Entry Point
     │
     ▼
┌──────────────────┐
│  initial_collect │ ──▶ 기본 정보 수집 (나무위키, 구글)
└────────┬─────────┘
         │ tool_calls?
         ▼
┌──────────────────┐
│  tools_initial   │ ──▶ ToolNode (도구 실행)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│    classify      │ ──▶ 밈 유형 분류 (6가지)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│    collect       │ ◀──▶│      tools       │
│  (단계별 수집)    │     │   (도구 실행)     │
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│   next_phase     │ ──▶ 다음 단계 결정
└────────┬─────────┘
         │ phase == "examples_extract"?
         ▼
┌──────────────────┐
│    extract       │ ──▶ GPT-4o로 예시 추출
└────────┬─────────┘
         │ phase == "finalize"?
         ▼
┌──────────────────┐
│    finalize      │ ──▶ GPT-4o로 최종 JSON 생성
└────────┬─────────┘
         │
         ▼
       [END]
```

### 2.2 노드 정의

| Node | 역할 | 사용 모델 |
|------|------|----------|
| `initial_collect` | 초기 정보 수집 (분류 전) | gpt-4o-mini |
| `tools_initial` | 초기 도구 실행 | ToolNode |
| `classify` | 밈 유형 분류 | gpt-4o-mini |
| `collect` | 단계별 데이터 수집 | gpt-4o-mini |
| `tools` | 도구 실행 | ToolNode |
| `next_phase` | 다음 단계 전환 | - |
| `extract` | 크롤링 데이터에서 예시 추출 | gpt-4o |
| `finalize` | 최종 JSON 정리 | gpt-4o |

### 2.3 Edge 정의

```python
# Entry Point
workflow.set_entry_point("initial_collect")

# Conditional Edges
workflow.add_conditional_edges("initial_collect", should_continue_initial, {
    "tools_initial": "tools_initial",
    "classify": "classify"
})

workflow.add_conditional_edges("collect", should_continue, {
    "tools": "tools",
    "next_phase": "next_phase"
})

workflow.add_conditional_edges("next_phase", should_finalize, {
    "finalize": "finalize",
    "extract": "extract",
    "collect": "collect"
})

# Direct Edges
workflow.add_edge("tools_initial", "classify")
workflow.add_edge("classify", "collect")
workflow.add_edge("tools", "next_phase")
workflow.add_edge("extract", "next_phase")
workflow.add_edge("finalize", END)
```

---

## 3. Phase 흐름

### 3.1 Phase 순서

```
initial_collect → classify → background → popular_content
    → examples_search → examples_crawl → examples_extract
    → scripts → finalize
```

### 3.2 Phase 상세

| Phase | 단계 | 설명 | 도구 호출 |
|-------|------|------|----------|
| `initial` | 0 | 기본 정보 수집 | search_namuwiki, search_google |
| `classify` | 1 | 밈 유형 분류 | - |
| `background` | 2 | 배경 스토리, 유행 이유 | search_google |
| `popular_content` | 3 | 인기 콘텐츠, 톤/뉘앙스 분석 | search_youtube, search_google |
| `examples_search` | 4a | 뉴스/블로그 URL 검색 | search_google |
| `examples_crawl` | 4b | 텍스트 페이지 크롤링 | crawl_webpage |
| `examples_extract` | 4c | 구체적 예시 추출 (GPT-4) | - |
| `scripts` | 5 | 스크립트 템플릿 수집 | search_google, search_youtube |
| `finalize` | 6 | 최종 JSON 생성 (GPT-4) | - |

### 3.3 Phase별 수집 정보

#### Phase 0: initial_collect
```
수집 대상:
- 밈 정의
- 원본 출처
- 제작자
- 시작 시점
```

#### Phase 2: background
```
수집 대상:
- 유행 이유
- 확산 경로
- 핵심 포인트
- 연관 트렌드
```

#### Phase 3: popular_content
```
수집 대상:
- 인기 콘텐츠 3개 (제목, URL)
- 실제 사용 맥락
- 공통 사용 패턴
- 톤/뉘앙스 (긍정/부정/조롱/풍자)
- 시청자 반응
```

#### Phase 4a-c: examples
```
검색 → 크롤링 → 추출

추출 대상:
- 구체적 행동/대사 예시
- 통계/수치
- 파생 표현/변형
- 특징 묘사
```

#### Phase 5: scripts
```
수집 대상 (유형별):
- video_dance: 가사, 안무 시퀀스, 음악 정보
- catchphrase: 원본 문구, 변형 예시, 발화 방식
- sound: 발음 표기, 톤/속도/억양
- character: 외형 상세, 사용 상황
- reaction: 표정/동작, 타이밍
- reference: 원작 장면/대사, 패러디 방법
```

---

## 4. Tools 정의

### 4.1 도구 목록

```python
ALL_TOOLS = [
    search_namuwiki,         # 나무위키 검색
    search_google,           # 구글 검색
    crawl_webpage,           # 웹페이지 크롤링
    get_youtube_info,        # 유튜브 영상 정보
    get_youtube_transcript,  # 유튜브 자막
    get_youtube_stats,       # 유튜브 조회수
    search_youtube,          # 유튜브 검색
]
```

### 4.2 도구 상세

| Tool | 기능 | 입력 | 출력 |
|------|------|------|------|
| `search_namuwiki` | 나무위키 문서 검색/크롤링 | query: str | 문서 내용 (마크다운) |
| `search_google` | 구글 검색 | query: str | 검색 결과 (제목, URL, snippet) |
| `crawl_webpage` | 웹페이지 텍스트 크롤링 | url: str | 페이지 텍스트 |
| `get_youtube_info` | YouTube 영상 메타데이터 | url: str | 제목, 설명, 채널 |
| `get_youtube_transcript` | YouTube 자막 추출 | url: str | 자막 텍스트 |
| `get_youtube_stats` | YouTube 조회수/좋아요 | url: str | 조회수, 좋아요, 업로드일 |
| `search_youtube` | YouTube 검색 | query: str | 영상 목록 (제목, URL) |

### 4.3 도구 구현 예시

```python
@tool
def search_namuwiki(query: str) -> str:
    """나무위키에서 밈 관련 문서를 검색합니다."""
    # 1. 검색 URL 생성
    # 2. 페이지 요청
    # 3. HTML 파싱 (BeautifulSoup)
    # 4. 마크다운 변환
    pass

@tool
def search_google(query: str) -> str:
    """구글 검색을 수행합니다."""
    # Google Custom Search API 사용
    pass

@tool
def crawl_webpage(url: str) -> str:
    """웹페이지의 텍스트를 크롤링합니다."""
    # 1. User-Agent 설정
    # 2. 페이지 요청
    # 3. 텍스트 추출
    pass
```

---

## 5. State 관리

### 5.1 AgentState 정의

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # 메시지 히스토리
    meme_name: str                            # 밈 이름
    meme_type: str                            # 분류된 유형
    phase: str                                # 현재 단계
    tool_called: bool                         # 도구 호출 여부
    phase_tool_count: int                     # 단계별 도구 호출 횟수
```

### 5.2 State 흐름

```
Initial State
    │
    ▼
┌─────────────────────────────────────┐
│ messages: [초기 메시지]              │
│ meme_name: "영포티"                  │
│ meme_type: ""                        │
│ phase: "classify"                    │
│ tool_called: False                   │
│ phase_tool_count: 0                  │
└─────────────────────────────────────┘
    │
    ▼ (classify 후)
┌─────────────────────────────────────┐
│ meme_type: "catchphrase"             │
│ phase: "background"                  │
└─────────────────────────────────────┘
    │
    ▼ (각 phase 완료 후)
┌─────────────────────────────────────┐
│ phase: "finalize"                    │
│ messages: [모든 수집 정보]            │
└─────────────────────────────────────┘
```

---

## 6. 데이터 스키마

### 6.1 기본 스키마

```json
{
  "name": "밈 이름",
  "type": "catchphrase",
  "definition": "밈에 대한 상세한 정의 (5문장 이상)",
  "origin": {
    "source": "원본 출처",
    "url": "URL",
    "creator": "제작자",
    "date": "시작 시점",
    "platform": "플랫폼"
  },
  "background_story": {
    "why_viral": "왜 유행했는지",
    "spread_path": "확산 경로",
    "key_moments": ["주요 순간"],
    "what_makes_it_funny": "재미 포인트",
    "related_trends": ["연관 트렌드"]
  },
  "real_usage_context": {
    "popular_examples": [
      {
        "title": "제목",
        "url": "URL",
        "view_count": "조회수",
        "how_meme_used": "밈 사용 방식",
        "context": "상황",
        "why_funny": "재미 포인트"
      }
    ],
    "common_patterns": ["패턴"],
    "tone": "조롱/풍자 | 긍정적 | 부정적",
    "best_timing": "사용 타이밍",
    "audience_reaction": "시청자 반응"
  },
  "usage_examples": [
    {
      "situation": "상황",
      "description": "설명",
      "platform": "플랫폼",
      "why_effective": "효과적인 이유"
    }
  ],
  "script_templates": [
    {
      "name": "템플릿 이름",
      "setup": "설정",
      "action": "액션",
      "punchline": "펀치라인",
      "example": "예시"
    }
  ],
  "keywords": ["검색 키워드"],
  "source_urls": ["참고 URL"],
  "collected_at": "수집 시각",
  "collection_method": "enhanced_meme_agent_v5"
}
```

### 6.2 필수 개수 규칙

| 필드 | 최소 개수 |
|------|----------|
| `popular_examples` | 3개 |
| `usage_examples` | 5개 |
| `script_templates` | 3개 |

---

## 7. 밈 유형별 분류

### 7.1 유형 정의

```python
MEME_TYPES = {
    "video_dance": "영상/댄스 밈 - 안무, 챌린지, 음악이 핵심",
    "catchphrase": "유행어/어록 밈 - 특정 문구나 말투가 핵심",
    "sound": "소리/음성 밈 - 특정 소리나 발음이 핵심",
    "character": "캐릭터/이미지 밈 - 특정 캐릭터나 이미지가 핵심",
    "reaction": "리액션 밈 - 특정 상황에 대한 반응이 핵심",
    "reference": "레퍼런스 밈 - 특정 작품/사건 인용이 핵심"
}
```

### 7.2 유형별 추가 스키마

#### video_dance
```json
{
  "script": [{"timestamp": "", "lyrics": "", "voice_style": ""}],
  "choreography": [{
    "sequence": 1,
    "timestamp": "",
    "description": "",
    "body": {"face": "", "arms": "", "hands": "", "torso": "", "legs": ""}
  }],
  "audio": {"music_name": "", "artist": "", "bpm": "", "characteristics": ""},
  "how_to_recreate": {"difficulty": "", "key_points": [], "tips": []}
}
```

#### catchphrase
```json
{
  "phrase": {
    "original": "원본 문구",
    "pattern": "패턴",
    "pronunciation": "발음법",
    "tone": "말투"
  },
  "variations": [{"text": "변형", "context": "맥락"}]
}
```

#### sound
```json
{
  "sound": {
    "transcription": "소리 표기",
    "pronunciation_guide": "발음 가이드",
    "tone": "톤",
    "speed": "속도",
    "rhythm": "리듬"
  },
  "how_to_recreate": {"steps": [], "tips": []}
}
```

#### character
```json
{
  "character": {
    "appearance": "외형",
    "expression": "표정",
    "pose": "포즈",
    "style": "스타일",
    "signature_elements": []
  },
  "meaning": {"represents": "", "emotion": "", "message": ""}
}
```

#### reaction
```json
{
  "reaction": {
    "trigger": "반응 유발 상황",
    "expression": "표정",
    "body_language": "바디랭귀지",
    "emotion": "감정"
  }
}
```

#### reference
```json
{
  "original_work": {
    "title": "원작 제목",
    "type": "유형",
    "scene": "장면 설명",
    "dialogue": "대사"
  },
  "parodies": [{"title": "", "description": "", "url": ""}]
}
```

---

## 부록: Rate Limit 처리

```python
def invoke_with_retry(llm, messages, max_retries=3, base_delay=20):
    """Rate limit 오류 시 재시도하는 래퍼 함수"""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                delay = base_delay * (attempt + 1)
                print(f"  [Rate Limit] Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                raise
    return llm.invoke(messages)
```

---

최종 업데이트: 2026-01-05
