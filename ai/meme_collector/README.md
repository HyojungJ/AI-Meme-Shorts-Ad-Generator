# MemeCollector

한국 인터넷 밈 정보를 수집하여 **영상 제작에 필요한 데이터**를 생성하는 Multi-Agent 시스템.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MemeAgent.process(meme_name)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              SUPERVISOR                                  │
│                         연구원 상태 체크 & 라우팅                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
         ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
         │    TEXT      │ │    MEDIA     │ │    USAGE     │
         │  RESEARCHER  │ │  RESEARCHER  │ │  RESEARCHER  │
         │   (ReAct)    │ │   (ReAct)    │ │   (ReAct)    │
         └──────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              ANALYZER                                   │
│              research_notes → AnalyzerOutput (structured output)        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              VERIFIER                                   │
│                         품질 검증 (100점 만점)                            │
│         PASS (≥80) → finalize | RETRY (60-79) → analyzer | FAIL → end  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                              [ FINALIZE ]
                          MemeOutput → DB 저장
```

## Agents

| Agent | 파일 | 역할 | 패턴 |
|-------|------|------|------|
| **Supervisor** | `deep_research/supervisor.py` | 연구원 라우팅 및 상태 관리 | Orchestrator |
| **Text Researcher** | `deep_research/researchers/text.py` | 밈 정의, origin, key_phrase 수집 | ReAct |
| **Media Researcher** | `deep_research/researchers/media.py` | YouTube 검색 + 영상 분석 | ReAct |
| **Usage Researcher** | `deep_research/researchers/usage.py` | 사용 예시 추출 | ReAct |
| **Analyzer** | `workers/analyzer.py` | 영상 제작용 스키마 생성 | Structured Output |
| **Verifier** | `workers/verifier.py` | 품질 검증 + 재시도 판단 | Reflexion |

## Tools

| Tool | 파일 | 사용 Agent | 용도 |
|------|------|------------|------|
| `search_namuwiki` | `tools/namuwiki.py` | Text | 나무위키 밈 정의 크롤링 |
| `search_naver_blog` | `tools/naver_search.py` | Text | 네이버 블로그 검색 |
| `search_naver_news` | `tools/naver_search.py` | Text | 네이버 뉴스 검색 |
| `search_youtube_shorts` | `tools/youtube.py` | Media | YouTube Shorts 검색 |
| `analyze_meme_video` | `tools/video_analyzer.py` | Media | Gemini Vision 영상 분석 |
| `extract_usage_examples` | `tools/usage_extractor.py` | Usage | 블로그에서 사용 예시 추출 |

## 워크플로우

```
1. Supervisor
   └─ 3개 Researcher 병렬 실행

2. Text Researcher (ReAct)
   ├─ search_namuwiki → 밈 정의, origin 파악
   └─ search_naver_blog → 사용 맥락, 추가 정보
   → research_notes["text"] 업데이트

3. Media Researcher (ReAct)
   ├─ search_youtube_shorts → 레퍼런스 영상 검색
   └─ analyze_meme_video → Gemini Vision 동작 분석
   → research_notes["media"] 업데이트

4. Usage Researcher (ReAct)
   └─ extract_usage_examples → 블로그/영상에서 사용 예시 추출
   → research_notes["usage"] 업데이트

5. Analyzer
   └─ research_notes 기반 structured output 생성
      - meme_type: quotable / performable / hybrid
      - key_phrase: 핵심 대사 (quotable/hybrid 필수)
      - motion_prompt: Sora 호환 프롬프트 (80+ words)
      - definition: 5-8문장 설명 (마크다운 금지)
      - emotion: TTS 톤 힌트

6. Verifier
   ├─ PASS (≥80점)  → finalize → DB 저장
   ├─ RETRY (60-79) → targeted research 또는 analyzer 재실행
   └─ FAIL (<60 또는 max_attempts 초과) → 종료
```

## Targeted Retry (RETRY 시 추가 조사)

RETRY 발생 시 피드백을 분석하여 부족한 영역을 판단하고 추가 조사를 실행합니다.

```
Verifier RETRY
     │
     ▼
피드백 분석 (_determine_retry_target)
     │
     ├─ key_phrase 부족 → Text Researcher 추가 실행
     ├─ motion_prompt 부족 → Media Researcher 추가 실행
     ├─ usage_examples 부족 → Usage Researcher 추가 실행
     └─ 분석만 부족 → Analyzer만 재실행
     │
     ▼
Analyzer 재실행 → Verifier
```

| retry_target | 조건 | 추가 조사 |
|--------------|------|----------|
| `text` | key_phrase/definition/origin 부족 | Text Researcher |
| `media` | motion_prompt 부족 (<50 words) | Media Researcher |
| `usage` | usage_examples 부족 | Usage Researcher |
| `analyzer` | 정보는 충분, 분석만 부족 | Analyzer만 재실행 |

## 검증 기준 (Verifier)

### quotable / hybrid 밈
| 항목 | 배점 | 기준 |
|------|------|------|
| key_phrase | 25점 | null이면 RETRY (추가 조사) |
| motion_prompt | 30점 | 80+ words |
| definition | 20점 | 마크다운 있으면 -10점 |
| emotion | 10점 | null이면 -10점 |
| origin | 15점 | source/creator 식별 |

### performable 밈
| 항목 | 배점 | 기준 |
|------|------|------|
| motion_prompt | 50점 | 100+ words 권장 |
| definition | 20점 | 동작 설명 포함 |
| origin | 30점 | 출처 명시 |

## 출력 스키마

### MemeOutput (최종 출력)

```python
class MemeOutput(BaseModel):
    name: str                           # 밈 이름
    definition: str                     # 5-8문장 설명 (plain text)
    meme_type: Literal["quotable", "performable", "hybrid"]
    key_phrase: str | None              # 핵심 대사
    emotion: str | None                 # TTS 톤 (excited, sarcastic, playful, deadpan, aggressive)
    prosody: Prosody | None             # TTS 설정
    motion_prompt: str                  # Sora 호환 프롬프트 (영어, 80+ words)
    style_keywords: list[str]           # 시각 스타일 키워드
    usage_examples: list[UsageExample]  # 활용 예시
    reference_videos: list[ReferenceVideo]
    origin: OriginInfo | None           # 출처 정보
    risk_level: Literal["low", "medium", "high"]
    confidence: float                   # 신뢰도 (0-1)
```

### Prosody (TTS 설정)

```python
class Prosody(BaseModel):
    pitch: Literal["low", "medium", "high"] = "medium"
    speed: Literal["slow", "medium", "fast"] = "medium"
    emotion: str = "neutral"
    ssml: str | None = None
```

### UsageExample (활용 예시)

```python
class UsageExample(BaseModel):
    context: str   # 상황/맥락 (예: "친구가 황당한 말 할 때")
    usage: str     # 사용 방법 (예: "'어쩔티비~' 하고 무시한다")
    tone: Literal["playful", "sarcastic", "aggressive", "friendly", "neutral"]
```

## meme_type 분류 기준

| 타입 | 설명 | 예시 |
|------|------|------|
| **quotable** | 대사만으로 밈 성립 | "어쩔티비", "운동 많이 된다" |
| **performable** | 동작만으로 밈 성립 | 랫댄스, 카이사댄스 |
| **hybrid** | 대사 + 동작 모두 필요 | "매끈매끈하다", "무야호" |

hybrid 판단 기준:
- 챌린지가 있는가?
- 특정 동작 없이 대사만 써도 밈인가?
- TikTok/YouTube Shorts에서 춤과 함께 유행했는가?

## 적용 기술

| 기술 | 적용 |
|------|------|
| **Multi-Agent** | Supervisor + 3 Researcher 협업 |
| **Parallel Execution** | 3개 Researcher 동시 실행 |
| **ReAct** | Researcher 동적 Tool 선택 |
| **Reflexion** | Verifier 피드백 → Analyzer 재시도 |
| **Command Routing** | LangGraph 동적 라우팅 |
| **State Reducers** | `merge_dicts`로 병렬 상태 병합 |
| **Structured Output** | Pydantic 기반 출력 검증 |
| **Multimodal** | Gemini Vision 영상 분석 |

## 파일 구조

```
meme_collector/
├── agent.py                    # MemeAgent 진입점
├── state.py                    # MemeState TypedDict
├── schema.py                   # Pydantic 출력 스키마
│
├── deep_research/              # Deep Research 패턴
│   ├── graph.py                # LangGraph 워크플로우
│   ├── supervisor.py           # Supervisor 라우팅
│   ├── compressor.py           # research_notes 압축
│   └── researchers/
│       ├── text.py             # 텍스트 정보 수집
│       ├── media.py            # 영상 검색/분석
│       └── usage.py            # 사용 예시 추출
│
├── workers/
│   ├── analyzer.py             # 영상 제작용 분석
│   └── verifier.py             # 품질 검증
│
├── tools/
│   ├── namuwiki.py             # 나무위키 크롤러
│   ├── naver_search.py         # 네이버 검색 API
│   ├── youtube.py              # YouTube Data API
│   ├── video_analyzer.py       # Gemini Vision
│   └── usage_extractor.py      # 사용 예시 추출
│
├── infra/
│   └── checkpointer.py         # PostgresSaver
│
└── _legacy/                    # 기존 코드 (참고용)
    ├── collector.py
    └── graph.py
```

## 실행

```bash
# 단일 밈 수집
uv run python -m meme_collector.agent --meme "매끈매끈하다"

# 코드에서 실행
from meme_collector.agent import MemeAgent

agent = MemeAgent()
result = agent.process("무야호")
print(result)
```

## 환경 변수

```
OPENAI_API_KEY=...
GOOGLE_API_KEY=...          # Gemini Vision
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
YOUTUBE_API_KEY=...
DATABASE_URL=...            # PostgreSQL (checkpointer)
```

## 테스트 결과

| 밈 | 타입 | 점수 | 결과 |
|-----|------|------|------|
| 운동 많이 된다 | quotable | 80 | PASS |
| 카이사 댄스 | performable | 80 | PASS |
| 어쩔티비 | quotable | 95 | PASS |
| 매끈매끈하다 | hybrid | 95 | PASS |
