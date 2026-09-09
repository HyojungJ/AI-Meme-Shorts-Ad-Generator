# Reference Code

기존 구현 원본 코드. **실행 시 import 경로 수정 필요**.

## 구조

```
_ref/
├── meme_collector/          # 밈 수집 Agent (파이프라인 담당 참고)
│   ├── agent.py             # MemeAgentV8 메인 클래스
│   ├── state.py             # AgentV8State, Phase 순서
│   ├── schema.py            # Pydantic 스키마
│   ├── config.py            # 설정
│   ├── prompts.py           # 프롬프트
│   ├── tools_v8.py          # LangChain 도구
│   └── nodes/               # 10개 Phase 노드
│       ├── definition.py
│       ├── risk_info.py
│       ├── usage_search.py
│       ├── crawl_examples.py
│       ├── youtube_search.py
│       ├── video_analysis.py
│       ├── meme_typing.py
│       ├── audio_analysis.py
│       ├── ssml_generation.py
│       └── finalize.py
│
├── scenario/                # 시나리오 Agent (시나리오 담당 참고)
│   ├── agent.py             # ScenarioAgent 메인
│   ├── graph.py             # LangGraph 구성
│   ├── state.py             # ScenarioState
│   ├── schema.py            # ScenarioOutput 등
│   ├── nodes/               # 5개 노드
│   │   ├── skeleton.py      # 골격 생성
│   │   ├── dialogue.py      # 대사 생성
│   │   ├── finalizer.py     # 최종 조합
│   │   ├── evaluate.py      # 품질 평가
│   │   └── save.py          # DB 저장
│   ├── generators/          # 생성 로직
│   ├── prompts/             # 프롬프트 관리
│   └── evaluation/          # 평가 시스템
│
└── video/                   # 영상 생성 (영상 담당 참고)
    ├── generator.py         # VideoGenerator 메인
    ├── graph.py             # LangGraph 구성
    ├── state.py             # VideoState
    ├── tts.py               # OpenAI TTS
    ├── sora.py              # Sora API
    ├── composer.py          # FFmpeg 합성
    ├── nodes/               # 5개 노드
    │   ├── prepare.py
    │   ├── tts.py
    │   ├── sora.py
    │   ├── compose.py
    │   └── finalize.py
    └── prompts/             # Sora 프롬프트 생성
```

## 핵심 파일 요약

### meme_collector
- **agent.py**: 10 Phase LangGraph 파이프라인
- **state.py**: Phase 순서, 조건부 분기 (needs_audio)
- **nodes/**: 각 Phase 실제 구현

### scenario
- **graph.py**: skeleton → dialogue → finalizer → evaluate → save
- **nodes/evaluate.py**: 5항목 품질 평가 (100점)
- **nodes/save.py**: script 테이블 저장

### video
- **graph.py**: prepare → tts → sora → compose → finalize
- **tts.py**: OpenAI TTS, duration 측정
- **sora.py**: Sora API 호출
- **composer.py**: FFmpeg filter_complex 합성

## 사용 시 주의

1. **import 경로 수정 필요**
   - `from scripts.agent.` → `from _ref.meme_collector.`
   - `from backend.scenario.` → `from _ref.scenario.`
   - `from backend.video.` → `from _ref.video.`

2. **외부 의존성**
   - DB 연결 (common/db.py 구현 필요)
   - OpenAI API, Gemini API 키
   - FFmpeg 설치

3. **실행 불가** - 참고용으로만 사용
