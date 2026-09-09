# Voice LangGraph 노드/그래프 리팩터링

- 작업 기간: 2026.01.22
- 작업자: 김진
- 관련 이슈 / PR: #24

---

## 개요
### 작업 내용
- 기존 `service.py`/`config.py` 기반 구조를 유지한 채 LangGraph 노드/그래프 레이어 추가
- 에이전트의 흐름 제어 로직과 ElevenLabs TTS 비즈니스 로직 분리

### 주요 기능
1. LangGraph에서 사용할 voice 상태(state) 스키마 정의
2. TTS 생성 로직을 service 레이어로 분리하고, 노드에서는 해당 로직만 호출
3. nodes를 graph로 연결하여 음성 생성 파이프라인 구성

---

## 코드 구성
### 추가/수정 파일
- `content_pipeline/voice/state.py`
- `content_pipeline/voice/nodes.py`
- `content_pipeline/voice/graph.py`
- `content_pipeline/voice/__init__.py`
- `content_pipeline/voice/client.py`

### 유지되는 핵심 로직
- `content_pipeline/voice/service.py` (ElevenLabs 호출 및 저장 로직)
- `content_pipeline/voice/config.py`  (환경 변수 로드)
- `content_pipeline/voice/storage.py` (로컬/S3 저장)

---

## 프로젝트 구조
```bash
content_pipeline/
├── voice/
|   ├── __init__.py             # 모듈 인터페이스
|   ├── config.py               # 환경 변수/설정 로드
|   ├── client.py               # ElevenLabs API 클라이언트
|   ├── service.py              # 음성 생성 로직
|   ├── storage.py              # 로컬/S3 저장 구현
|   ├── state.py                # 입력/출력 스키마
|   ├── nodes.py                # LangGraph 노드
|   └── graph.py                # LangGraph 그래프
└── docs/kj/
    └── 2026-01-22_voice_langgraph_refactor.md
```

---

## 사용 예시
```python
from content_pipeline.voice import get_voice_graph, get_initial_state

graph = get_voice_graph()
state = get_initial_state(
    text="Hello world",
    voice_id="YOUR_VOICE_ID",
    settings={"stability": 0.4, "similarity_boost": 0.6},
)
result = graph.invoke(state)
print(result)
```

---

## 참고
- `voice_id`가 없으면 `design` 노드에서 `voice_name`/`voice_description`을 사용해 생성 후 이어서 `generate`를 수행
