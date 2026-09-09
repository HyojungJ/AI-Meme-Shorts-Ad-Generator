# 멀티모달 검수 시스템 구현 (최종)

## 개요
콘텐츠 생성 파이프라인에 VLM 기반 자동 검수 시스템 구축
- 이미지: 사용자 수정 요청 반영 여부 검증
- 영상: 물리 법칙 준수 여부 자동 검증

## 플로우

### 이미지 검수 플로우
```
사용자 입력
  ↓
이미지 생성
  ↓
사용자 수정 요청 (피드백 전달)
  ↓
이미지 재생성
  ↓
검수 (verify_image_modification_node)
  ↓
├─ 점수 ≥50 → 사용자에게 제시
└─ 점수 <50 & retry_count < 2 → 재생성
  ↓
사용자 최종 승인
```

**특징**:
- 사용자 피드백 기반 검증
- 수정 요청이 제대로 반영되었는지 확인
- 최대 2회 재생성

### 영상 검수 플로우
```
영상 생성 (generate_video_node)
  ↓
영상 병합 (merge_video_node)
  ↓
자동 검수 (verify_video_node) ← 자동 실행!
  ↓
├─ 점수 ≥60 → 사용자에게 제시
└─ 점수 <60 & retry_count < 3 → 재생성
  ↓
사용자 수정 요청 (선택)
  ↓
영상 재생성 (프롬프트에 피드백 반영)
  ↓
자동 검수 (반복)
```

**특징**:
- 생성 직후 자동 검증 (사용자 피드백 무관)
- 물리 법칙 위반, 해부학적 오류 탐지
- 최대 3회 재생성
- 사용자 피드백은 재생성 프롬프트에 반영

---

## 구현 내용

### 1. 이미지 검증 (`content_pipeline/image/nodes.py`)

**함수**: `verify_image_modification_node(state: ImageState) -> dict`

**모델**: GPT-5 Vision (팀원 구현)

**검증 대상**:
- 캐릭터 생김새 (얼굴형, 헤어스타일, 눈 모양 등)
- 그림체/화풍 (애니메이션, 수채화, 사실적 등)
- 분위기/느낌 (귀여움, 어두움, 몽환적 등)
- 색감/톤 (따뜻함, 차가움, 채도 등)

**점수 기준**:
- ≥50점: 사용자에게 제시
- <50점: 재생성 (최대 2회)

**필수 입력**:
```python
{
    "original_image_url": "원본 이미지 URL",
    "image_url": "수정된 이미지 URL",
    "modification_request": "사용자 수정 요청 내용",
    "retry_count": 0  # 재생성 시도 횟수
}
```

**반환값**:
```python
{
    "status": "ok",
    "verification_result": {
        "score": 65,
        "confidence": 0.85,
        "analysis": "색감이 따뜻하게 변경되었으나 헤어스타일은 미반영",
        "missing_elements": ["헤어스타일 변경"]
    },
    "decision": "show_to_user",  # or "auto_retry"
    "message": "AI 분석 점수: 65점. 이대로 괜찮으신가요?",
    "score": 65,
    "confidence": 0.85,
    "retry_count": 0
}
```

---

### 2. 영상 검증 (`content_pipeline/video/nodes.py`)

**함수**: `verify_video_node(state: VideoState) -> dict`

**모델**: Gemini 2.5 Pro

**검증 대상**:
- 해부학적 오류 (손가락 6개, 팔 3개 등)
- 물리 법칙 위반 (음료를 코로 마심, 중력 무시 등)
- 불가능한 동작/자세
- 부자연스러운 움직임

**점수 기준**:
- 81-100점: 거의 완벽하거나 완벽함
- 61-80점: 약간의 이상함
- 41-60점: 눈에 띄는 부자연스러움
- 21-40점: 명확한 오류
- 0-20점: 심각한 오류

**재생성 기준**:
- ≥60점: 사용자에게 제시
- <60점: 재생성 (최대 3회)

**필수 입력**:
```python
{
    "merged_video_url": "생성된 영상 URL",
    "retry_count": 0  # 재생성 시도 횟수
}
```

**반환값**:
```python
{
    "status": "ok",
    "verification_result": {
        "score": 45,
        "analysis": "음료를 코로 마시는 장면 발견 (0:05초)"
    },
    "decision": "auto_retry",  # or "present_to_user"
    "message": "물리적 오류 발견 (점수: 45점). 자동으로 재생성합니다.",
    "score": 45,
    "analysis": "음료를 코로 마시는 장면 발견 (0:05초)",
    "retry_count": 0
}
```

**주의사항**:
- 영상 품질(해상도, 프레임 수)은 평가하지 않음
- 정지 이미지로 구성된 영상도 감점 대상 아님
- 오직 내용의 물리적/해부학적 오류만 검증

---

### 3. 영상 그래프 통합 (`content_pipeline/video/graph.py`)

**플로우 구현**:
```python
def _route_after_verify(state: VideoState) -> str:
    """검증 결과에 따라 재생성 또는 종료"""
    verification = state.get("verification_result", {})
    decision = verification.get("decision", "present_to_user")
    
    if decision == "auto_retry":
        return "generate"  # 재생성
    return END  # 사용자에게 제시

graph.add_node("generate", generate_video_node)
graph.add_node("merge", merge_video_node)
graph.add_node("verify", verify_video_node)

graph.set_entry_point("generate")
graph.add_edge("generate", "merge")
graph.add_edge("merge", "verify")
graph.add_conditional_edges(
    "verify",
    _route_after_verify,
    {"generate": "generate", END: END},
)
```

**자동 검수 동작**:
1. 영상 생성 완료
2. 자동으로 `verify_video_node` 실행
3. 점수가 60점 미만이면 자동 재생성 (최대 3회)
4. 점수가 60점 이상이거나 재생성 한도 초과 시 사용자에게 제시

---

### 4. State 확장

#### ImageState (`content_pipeline/image/state.py`)
```python
verification_result: dict  # 검증 결과
modification_request: str  # 수정 요청 내용
original_image_url: str    # 원본 이미지 URL
retry_count: int           # 재생성 시도 횟수
```

#### VideoState (`content_pipeline/video/state.py`)
```python
verification_result: dict  # 검증 결과
modification_request: str  # 수정 요청 내용 (선택)
original_video_url: str    # 원본 영상 URL (선택)
retry_count: int           # 재생성 시도 횟수
```

---

## 의존성

### pyproject.toml
```toml
dependencies = [
    "anthropic>=0.40.0",  # Claude API (이미지 검증 - 미사용)
    "google-genai>=1.0.0",  # Gemini API (영상 검증)
    # ... 기존 의존성
]
```

### 환경 변수 (.env)
```bash
# Google Gemini API (영상 검증)
GOOGLE_API_KEY=...
GEMINI_API_KEY=...
NANO_BANANA_API_KEY=...  # 대체 가능
GEMINI_MODEL=gemini-2.5-pro

# OpenAI API (이미지 검증 - 팀원 구현)
OPENAI_API_KEY=...
```

---

## 비용 분석

### 이미지 검증
- 모델: GPT-5 Vision
- 비용: 팀원 구현 부분 (상세 비용 미확인)
- 최대 재생성: 2회

### 영상 검증
- 모델: Gemini 2.5 Pro
- 검증 비용: 약 $0.05/회 (추정)
- 최대 재생성: 3회
- 최대 허용 비용: 약 $0.20 (검증 4회 = 초기 1회 + 재생성 3회)

---

## 테스트

### 영상 검증 테스트 (`tests/VLM/video_verification.py`)

**사용법**:
```bash
uv run tests/VLM/video_verification.py
```

**테스트 내용**:
- 샘플 영상 업로드
- Gemini 2.5 Pro로 물리 법칙 검증
- JSON 형식 결과 반환

**주요 기능**:
- 파일 업로드 후 ACTIVE 상태 대기
- 물리적/해부학적 오류 탐지
- 영상 품질은 평가하지 않음

---

## 주요 특징

### 이미지 검수
1. **사용자 피드백 기반**: 수정 요청이 반영되었는지 확인
2. **주관적 평가**: 스타일, 느낌, 색감 등
3. **수동 트리거**: 사용자가 수정 요청할 때만 실행

### 영상 검수
1. **자동 실행**: 생성 직후 자동으로 검증
2. **객관적 평가**: 물리 법칙, 해부학적 오류만 검증
3. **사용자 피드백 무관**: 생성된 영상 자체만 평가
4. **자동 재생성**: 점수 낮으면 사용자 개입 없이 재생성

---

## 향후 개선 사항

1. **검증 이력 DB 저장**: 품질 분석 및 모델 성능 개선에 활용
2. **힌트 기반 재생성**: 발견된 오류를 프롬프트에 추가하여 재생성 품질 향상
3. **점수 임계값 조정**: 실제 사용 데이터 기반으로 최적 임계값 튜닝
4. **검증 속도 최적화**: 파일 업로드 및 처리 시간 단축
5. **음성 검증 추가**: 필요 시 GPT-4o Audio로 음성 품질 검증

---

## 작업 일자
2026-01-30

## 작업자
HJ

## 변경 이력
- 2026-01-29: 초기 구현 (이미지/음성/영상 검증 노드)
- 2026-01-30: 최종 수정
  - 음성 검증 제거
  - 영상 검증을 자동 실행으로 변경
  - 영상 그래프에 검증 노드 통합
  - 이미지 검증은 팀원 구현 유지
