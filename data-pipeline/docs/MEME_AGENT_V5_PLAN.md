# Meme Agent v5 개선 계획 및 진행 상황

## 현재 상태: 진행 중

---

## 해결된 문제점

### 1. 예시 개수 부족 - 해결됨
- **문제**: popular_examples 1개, usage_examples 1개만 생성
- **해결**: finalize 프롬프트 맨 앞에 개수 규칙 강조
- **결과**: 모든 테스트에서 개수 요구사항 충족 (3개/5개/3개)

### 2. 톤/뉘앙스 미반영 - 해결됨
- **문제**: 조롱 밈인데 "긍정적"으로 표시
- **해결**: 톤 감지 키워드 규칙 추가
- **결과**: 영포티 → "조롱/풍자", 랫댄스 → "긍정적" 정확

### 3. 프롬프트 예시 복사 문제 - 해결됨
- **문제**: 프롬프트 예시가 다른 밈에 그대로 복사됨
- **해결**: 구체적 예시 제거, 규칙만 명시
- **결과**: 각 밈별로 고유한 예시 생성

### 4. Rate Limit 오류 - 해결됨
- **문제**: 병렬 실행 시 OpenAI API Rate Limit 오류
- **해결**: `invoke_with_retry` 함수 추가 (20초 대기 후 재시도)

### 5. 하드코딩된 예시 제거 - 해결됨
- **문제**: "스윗 영포티" 같은 특정 밈 예시가 프롬프트에 있음
- **해결**: 일반화된 설명으로 변경

---

## 진행 중인 문제

### usage_examples가 크롤링 데이터 기반이 아닌 문제
- **문제**: usage_examples 3-5번이 "파티에서", "SNS에서" 같은 일반적 상황
- **원인**: 크롤링된 기사에서 구체적 사례가 5개 미만일 때 LLM이 일반적 상황 생성
- **부분 해결**: 프롬프트에 금지 규칙 추가
  ```
  다음과 같은 예시는 절대 생성하지 마세요:
  - "파티에서 친구들과 함께"
  - "온라인 게임에서 사용"
  ```
- **결과**: 일부 개선 (1-2개는 크롤링 기반으로 생성)
- **추가 필요**: 크롤링 소스 확대 또는 개수 요구사항 유연화

---

## 테스트 결과 (2026-01-05)

### 기본 테스트 (개수 검증)

| 밈 | 유형 | popular | usage | scripts | tone | 상태 |
|---|------|---------|-------|---------|------|------|
| 영포티 | catchphrase | 3 | 5 | 3 | 조롱/풍자 | 통과 |
| 앱솔루트 시네마 | reference | 3 | 5 | 3 | 조롱/풍자 | 통과 |
| 랫댄스 | video_dance | 3 | 5 | 3 | 긍정적 | 통과 |

### 2025년 밈 테스트 (최신 밈)

| 밈 | 유형 | popular | usage | scripts | origin 정확도 | 상태 |
|---|------|---------|-------|---------|--------------|------|
| 트랄랄레로 트랄랄라 | catchphrase | 3 | 5 | 3 | burger677, 2025년 1월 | 통과 |
| 스키비디 토일렛 | catchphrase | 3 | 5 | 3 | DaFuq!?Boom!, 2023년 2월 | 통과 |
| 괜찮아 딩딩딩 | catchphrase | 3 | 5 | 3 | 알딘 테가르, 2023년 말 | 통과 |
| 퀸 네버 크라이 | catchphrase | 3 | 5 | 3 | 기자매 웹툰, 2024년 11월 | 통과 |

---

## 구현된 기능

### Phase 구조 (9단계)
```
1. initial_collect  - 기본 정보 수집 (나무위키, 구글)
2. classify         - 밈 유형 분류
3. background       - 배경 스토리, 유행 이유
4. popular_content  - 인기 콘텐츠 분석, 톤/뉘앙스
5. examples_search  - 뉴스/블로그 검색
6. examples_crawl   - 텍스트 기반 페이지 크롤링
7. examples_extract - 구체적 예시 추출 (GPT-4)
8. scripts          - 스크립트 템플릿
9. finalize         - 최종 JSON 정리 (GPT-4)
```

### 도구 (7개)
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

### 모델 사용
- **gpt-4o-mini**: 검색, 분류, 크롤링 (빠르고 저렴)
- **gpt-4o**: examples_extract, finalize (정확도 필요)

---

## 핵심 수정 사항

### 1. finalize 프롬프트 (개수 강조)
```
#######################################
#  필수 개수 규칙 (절대 준수!)  #
#######################################

이 규칙을 어기면 출력이 무효 처리됩니다:

1. popular_examples 배열: 최소 3개 객체
2. usage_examples 배열: 최소 5개 객체
3. script_templates 배열: 최소 3개 객체
```

### 2. usage_examples 규칙 (크롤링 기반 강조)
```
### 필수: 크롤링한 기사에서 직접 인용
usage_examples는 **크롤링한 뉴스/블로그에서 발견한 실제 사례**만 포함하세요.

### 금지: LLM이 생성한 일반적 상황
다음과 같은 예시는 절대 생성하지 마세요:
- "파티에서 친구들과 함께"
- "온라인 게임에서 사용"
- "SNS에 게시"
- "학교에서 친구들과"
```

### 3. 톤 감지 규칙
```
"조롱", "비꼼", "놀림", "비하", "논란", "비판" 키워드가 하나라도 있으면:
→ tone: "조롱/풍자" 사용
```

### 4. 크롤링 우선순위
```
1순위: 뉴스 기사 (bbc.com, hankyung.com, donga.com 등)
2순위: 블로그 글 (blog.naver.com, brunch.co.kr, tistory.com 등)
3순위: 나무위키 문서
금지: 커뮤니티 이미지 게시물 (ruliweb.com, dcinside.com)
```

### 5. Rate Limit 재시도
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

## 파일 구조

```
/Users/kimjm/Desktop/Data/
├── scripts/agent/
│   ├── tools.py              # 7개 도구
│   └── meme_agent_v5.py      # 개선된 Agent
├── data/agent_output_v5/     # 출력 결과
│   ├── meme_catchphrase_영포티_20260105_001622.json
│   ├── meme_reference_앱솔루트 시네마_20260105_001808.json
│   ├── meme_video_dance_랫댄스_20260105_001958.json
│   ├── meme_catchphrase_트랄랄레로 트랄랄라_20260105_003101.json
│   ├── meme_catchphrase_스키비디 토일렛_20260105_003309.json
│   ├── meme_catchphrase_괜찮아 딩딩딩_20260105_091138.json
│   └── meme_catchphrase_퀸 네버 크라이_20260105_091404.json
└── docs/
    └── MEME_AGENT_V5_PLAN.md     # 이 문서
```

---

## 사용법

```bash
uv run python scripts/agent/meme_agent_v5.py "밈이름"
```

---

## 다음 단계 (TODO)

1. **usage_examples 크롤링 기반 강화**
   - 크롤링 소스 확대 (더 많은 블로그/기사)
   - 또는 개수 요구사항 유연화 (크롤링 데이터 부족 시 3개로 제한)

2. **톤 감지 정확도 향상**
   - "괜찮아 딩딩딩"이 긍정적 밈인데 "조롱/풍자"로 판정됨
   - 긍정적 키워드도 추가 필요

---

최종 업데이트: 2026-01-05 09:15
