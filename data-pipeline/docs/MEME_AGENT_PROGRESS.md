# Meme-fluencer Agent 개발 진행 상황

## 프로젝트 개요

AI 기반 밈 콘텐츠 생성 시스템 "Meme-fluencer" 개발
- 목표: 밈 데이터를 수집하여 캐릭터가 밈을 따라할 수 있는 영상 스크립트 생성
- 핵심: 실제 밈 사용 맥락을 정확히 파악하여 자연스러운 콘텐츠 제작

## 현재 구현된 시스템

### 파일 구조
```
/Users/kimjm/Desktop/Data/
├── scripts/agent/
│   ├── tools.py              # LangChain 도구들 (6개)
│   ├── meme_agent_v4.py      # 유형별 분류 Agent (이전 버전)
│   └── meme_agent_v5.py      # 강화된 Agent (현재 버전)
├── data/
│   ├── agent_output/         # v4 출력
│   └── agent_output_v5/      # v5 출력
└── docs/
    └── MEME_AGENT_PROGRESS.md  # 이 문서
```

### tools.py - 7개 도구
```python
ALL_TOOLS = [
    search_namuwiki,      # 나무위키 검색 (Serper API)
    search_google,        # 구글 검색 (Serper API)
    crawl_webpage,        # 웹페이지 크롤링
    get_youtube_info,     # 유튜브 영상 정보
    get_youtube_transcript,  # 유튜브 자막 추출 (수정됨: 인스턴스 기반 API)
    get_youtube_stats,    # 유튜브 조회수/통계 (NEW - 페이지 스크래핑)
    search_youtube,       # 유튜브 검색
]
```

### meme_agent_v5.py - 현재 버전

#### 밈 유형 분류 (6가지)
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

#### Agent 흐름 (v5)
```
initial_collect -> tools_initial -> classify -> collect -> tools -> next_phase -> ... -> finalize
     |                                  |
     v                                  v
 나무위키/구글 검색              수집된 정보 기반 분류
 (분류 전 정보 수집)            (hallucination 방지)
```

#### 수집 단계
1. Phase 0: Initial Collection (기본 정보 - 분류 전)
2. Phase 1: Background Story (배경 스토리, 유행 이유)
3. Phase 2: Popular Content Analysis (인기 콘텐츠 분석, 톤/뉘앙스) - NEW
4. Phase 3: Usage Examples (활용 예시 5개 이상)
5. Phase 4: Script Templates (스크립트 템플릿 3개 이상)
6. Phase 5: Finalize (JSON 정리)

## 해결된 문제들

### 1. YouTube Transcript API 변경
```python
# 기존 (오류)
YouTubeTranscriptApi.get_transcript(video_id)

# 수정 (정상)
ytt = YouTubeTranscriptApi()
ytt.fetch(video_id, languages=['ko', 'en'])
```

### 2. Hallucination 문제
- 문제: "영포티"를 "영어 잘하는 40대"로 잘못 해석 (실제: Young Forty, 젊은 40대)
- 원인: 분류가 검색 전에 발생하여 LLM이 추측함
- 해결:
  1. 순서 변경: 초기수집 -> 분류 -> 추가수집
  2. 프롬프트 강화: "수집된 원문만 사용", "추측하지 마세요"

### 3. 그래프 재귀 문제
- 문제: LangGraph recursion limit 도달
- 해결: 단계별 1회 도구 호출 후 다음 단계로 이동하는 단순 구조

## 현재 출력 스키마 (catchphrase 예시)

```json
{
  "name": "밈 이름",
  "type": "catchphrase",
  "definition": "5문장 이상 상세 정의 (변천사 포함)",
  "origin": {
    "source": "원본 출처",
    "url": "URL",
    "creator": "제작자",
    "date": "시작 시점",
    "platform": "플랫폼"
  },
  "background_story": {
    "why_viral": "유행 이유 (3문장 이상)",
    "spread_path": "확산 경로",
    "key_moments": ["주요 순간"],
    "what_makes_it_funny": "임팩트 포인트",
    "related_trends": ["연관 트렌드"]
  },
  "real_usage_context": {
    "popular_examples": [
      {
        "title": "인기 콘텐츠 제목",
        "url": "URL",
        "view_count": "조회수",
        "how_meme_used": "밈이 어떻게 사용되었는지",
        "context": "상황 설정",
        "why_funny": "왜 재미있었는지"
      }
    ],
    "common_patterns": ["공통 사용 패턴"],
    "tone": "밈의 톤/뉘앙스 (긍정/부정/조롱/풍자)",
    "best_timing": "최적 사용 타이밍",
    "audience_reaction": "시청자들의 반응"
  },
  "usage_examples": [
    {
      "situation": "사용 상황",
      "description": "사용 방법",
      "platform": "플랫폼",
      "why_effective": "효과적인 이유"
    }
  ],
  "script_templates": [
    {
      "name": "템플릿 이름",
      "setup": "상황 설정",
      "action": "실행",
      "punchline": "포인트",
      "example": "예시"
    }
  ],
  "phrase": {
    "original": "원본 문구",
    "pattern": "패턴",
    "pronunciation": "발음",
    "tone": "말투 (조롱/풍자 등)"
  },
  "variations": [{"text": "", "context": ""}],
  "keywords": [],
  "source_urls": []
}
```

## 테스트된 밈들

### v4 테스트 (5개)
| 밈 | 유형 | 결과 |
|---|------|------|
| 랫 댄스 | video_dance | 성공 |
| 앱솔루트 시네마 | catchphrase | 성공 |
| 햄부기햄북 햄북어 | sound | 성공 |
| Chill guy | character | 성공 |
| 오징어 게임 2 | reference | 성공 |

### v5 테스트 (2개)
| 밈 | 유형 | 결과 |
|---|------|------|
| 스핔이 | catchphrase | 성공 |
| 영포티 | catchphrase | 성공 (hallucination 수정 후) |

## 해결된 과제 (2026-01-04)

### 실제 밈 사용 맥락 수집 강화 ✓

구현된 기능:
1. **real_usage_context 필드 추가**
   - 인기 콘텐츠 예시 수집
   - 톤/뉘앙스 분석 (긍정/부정/조롱/풍자)
   - 시청자 반응 패턴

2. **톤/뉘앙스 자동 감지**
   - 검색 결과에서 "조롱", "풍자", "논란", "비판" 키워드 감지
   - finalize 프롬프트에 톤 결정 기준 추가
   - 예: 영포티 → tone: "조롱/풍자" 정확히 감지

3. **Popular Content Analysis 단계 추가**
   - Phase 2로 인기 콘텐츠 분석 단계 추가
   - 검색 쿼리: "{밈} 레전드", "{밈} 조롱 풍자 논란"

## 남은 과제

### 추가 개선 가능 사항

1. **구체적 스크립트 부족**
   - 현재: setup/action/punchline 구조
   - 필요: 바로 읽을 수 있는 대사, 연출 노트

2. **YouTube 조회수 수집 개선**
   - get_youtube_stats 도구 추가됨 (스크래핑 방식)
   - 현재: Agent가 항상 호출하지는 않음
   - 개선: 자동으로 상위 N개 영상 조회수 수집

3. **스크립트 생성 모듈 추가**
   - 수집된 맥락 기반 대사 생성
   - 연출 가이드 자동 생성

## 환경 설정

### 필요한 API 키 (.env)
```
OPENAI_API_KEY=...
SERPER_API_KEY=...
```

### 실행 방법
```bash
# v5 Agent 실행
python3 scripts/agent/meme_agent_v5.py "밈이름"

# 옵션
--output, -o  : 출력 디렉토리 (기본: data/agent_output_v5)
--quiet, -q   : 조용한 모드
```

## 주요 코드 위치

| 기능 | 파일 | 함수/클래스 |
|------|------|------------|
| 도구 정의 | tools.py | ALL_TOOLS |
| 유튜브 자막 | tools.py | get_youtube_transcript |
| 유튜브 조회수 | tools.py | get_youtube_stats (NEW) |
| 수집 프롬프트 | meme_agent_v5.py | get_collect_prompt() |
| 인기콘텐츠 분석 | meme_agent_v5.py | get_collect_prompt("popular_content") (NEW) |
| 최종 정리 프롬프트 | meme_agent_v5.py | get_finalize_prompt() |
| Agent 그래프 | meme_agent_v5.py | create_agent() |
| 메인 클래스 | meme_agent_v5.py | EnhancedMemeAgent |

---
최종 업데이트: 2026-01-04 18:55
