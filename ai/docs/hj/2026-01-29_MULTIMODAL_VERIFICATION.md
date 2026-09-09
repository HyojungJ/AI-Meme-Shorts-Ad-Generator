# 멀티모달 검수 시스템 구현

## 개요
사용자 수정 요청 후 재생성된 콘텐츠(이미지/음성/영상)의 품질을 VLM으로 자동 검증하는 시스템 구축

## 목적
- 명백한 실패를 자동으로 걸러내서 사용자 불편 최소화
- 재생성 품질을 자동으로 보장
- 최종 승인은 반드시 사용자가 수행

## 플로우
```
사용자 수정 요청
  ↓
재생성
  ↓
VLM 자동 검증 (품질 체크)
  ↓
├─ 점수 높음 → 사용자에게 제시 + "AI 검증 통과" 표시
├─ 점수 낮음 → 자동 재생성 (최대 횟수 제한) → 사용자에게 제시
└─ 점수 중간 → 사용자에게 제시 + "AI 분석: XX점" 표시
  ↓
사용자 최종 승인 필수 ← 여기서 반드시 멈춤!
  ↓
승인되면 다음 단계로
```

## 구현 내용

### 1. 이미지 검증 (`content_pipeline/image/nodes.py`)

**함수**: `verify_image_modification_node(state: ImageState) -> dict`

**모델**: Claude Sonnet 4.5

**검증 대상**:
- 캐릭터 생김새 (얼굴형, 헤어스타일, 눈 모양 등)
- 그림체/화풍 (애니메이션, 수채화, 사실적 등)
- 분위기/느낌 (귀여움, 어두움, 몽환적 등)
- 색감/톤 (따뜻함, 차가움, 채도 등)

**점수 기준**:
- ≥75점: 자동 승인 (사용자에게 제시 + "수정사항이 잘 반영되었습니다.")
- 50-74점: 사용자 확인 필요 (사용자에게 제시 + "AI 분석 점수: XX점. 이대로 괜찮으신가요?")
- <50점: 재생성 (최대 2회)
  - retry_count < 2: 자동 재생성
  - retry_count ≥ 2: 사용자 확인 필요 (재생성 한도 초과)

**필수 입력**:
- `original_image_url`: 원본 이미지 URL
- `image_url`: 수정된 이미지 URL
- `modification_request`: 수정 요청 내용
- `retry_count`: 재생성 시도 횟수 (기본값: 0)

**반환값**:
```python
{
    "status": "ok",
    "verification_result": {
        "score": 85,
        "confidence": 0.9,
        "analysis": "상세 분석 내용",
        "missing_elements": ["미반영된 요소1", "미반영된 요소2"]
    },
    "decision": "auto_approve",  # or "needs_confirmation", "auto_retry"
    "message": "수정사항이 잘 반영되었습니다.",
    "score": 85,
    "confidence": 0.9,
    "retry_count": 0
}
```

**비용**: 
- 생성: $0.50
- 검증: $0.015
- 총 1회 시도: $0.515
- 최대 허용 비용: $2.00 (재생성 2회)

---

### 2. 음성 검증 (`content_pipeline/voice/nodes.py`)

**함수**: `verify_audio_modification_node(state: VoiceState) -> dict`

**모델**: GPT-4o Audio

**검증 대상**:
- 목소리 톤 (높낮이, 음색)
- 감정/분위기 (차분함, 활기찬, 슬픔 등)
- 억양/강세

**점수 기준**:
- ≥80점: 자동 승인
- 55-79점: 사용자 확인 필요
- <55점: 재생성 (최대 2회)

**필수 입력**:
- `original_audio_url`: 원본 음성 URL
- `audio_url`: 수정된 음성 URL
- `modification_request`: 수정 요청 내용
- `retry_count`: 재생성 시도 횟수 (기본값: 0)

**반환값**: 이미지 검증과 동일한 구조

**비용**:
- 생성: $0.30
- 검증: $0.040
- 총 1회 시도: $0.340
- 최대 허용 비용: $1.50 (재생성 2회)

---

### 3. 영상 검증 (`content_pipeline/video/nodes.py`)

**함수**: `verify_video_modification_node(state: VideoState) -> dict`

**모델**: Gemini 3 Pro

**검증 대상**:
- 해부학적 오류 (손가락 6개, 팔 3개 등)
- 물리 법칙 위반 (음료를 코로 마심, 중력 무시 등)
- 불가능한 동작/자세
- 부자연스러운 움직임

**점수 기준**:
- ≥80점: 자동 승인
- 60-79점: 사용자 확인 필요
- <60점: 재생성 (최대 3회)

**필수 입력**:
- `original_video_url`: 원본 영상 URL
- `merged_video_url`: 수정된 영상 URL
- `modification_request`: 수정 요청 내용
- `retry_count`: 재생성 시도 횟수 (기본값: 0)

**반환값**: 이미지 검증과 동일한 구조

**비용**:
- 생성: $0.00 (무료)
- 검증: $0.045
- 총 1회 시도: $0.045
- 최대 허용 비용: $0.50 (재생성 3회, 검증 비용만 발생)

---

## State 확장

각 파이프라인의 State에 검증 관련 필드 추가:

### ImageState (`content_pipeline/image/state.py`)
```python
verification_result: dict  # 검증 결과
modification_request: str  # 수정 요청 내용
original_image_url: str    # 원본 이미지 URL
retry_count: int           # 재생성 시도 횟수
```

### VoiceState (`content_pipeline/voice/state.py`)
```python
verification_result: dict  # 검증 결과
modification_request: str  # 수정 요청 내용
original_audio_url: str    # 원본 음성 URL
retry_count: int           # 재생성 시도 횟수
```

### VideoState (`content_pipeline/video/state.py`)
```python
verification_result: dict  # 검증 결과
modification_request: str  # 수정 요청 내용
original_video_url: str    # 원본 영상 URL
retry_count: int           # 재생성 시도 횟수
```

---

## 의존성 추가

### pyproject.toml
```toml
dependencies = [
    "anthropic>=0.40.0",  # Claude API (이미지 검증)
    # ... 기존 의존성
]
```

### 환경 변수 (.env)
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Claude API 키
OPENAI_API_KEY=sk-...            # GPT-4o Audio API 키
GOOGLE_API_KEY=...               # Gemini API 키
```

---

## API 통합 예시

```python
# API 엔드포인트에서 사용 예시
@app.post("/api/image/regenerate")
def regenerate_image(request: RegenerateRequest):
    state = {
        "modification_request": request.modification_request,
        "original_image_url": request.original_image_url,
        "character_prompt": request.character_prompt,
        "scenario_prompt": request.scenario_prompt,
        "retry_count": 0,
    }
    
    max_retries = 2
    for retry in range(max_retries + 1):
        state["retry_count"] = retry
        
        # 재생성
        result = generate_scene_image_node(state)
        state.update(result)
        
        # 검증
        verification = verify_image_modification_node(state)
        
        # 점수 판단
        if verification["decision"] == "auto_approve":
            return {
                "status": "success",
                "image_url": state["image_url"],
                "message": verification["message"],
                "score": verification["score"]
            }
        elif verification["decision"] == "needs_confirmation":
            return {
                "status": "needs_confirmation",
                "image_url": state["image_url"],
                "score": verification["score"],
                "message": verification["message"],
                "analysis": verification["verification_result"]["analysis"]
            }
        elif verification["decision"] == "auto_retry" and retry < max_retries:
            continue  # 자동 재생성
    
    # 최대 재시도 초과
    return {
        "status": "needs_confirmation",
        "image_url": state["image_url"],
        "score": verification["score"],
        "message": "재생성 한도 초과. 이대로 진행하시겠습니까?"
    }
```

---

## 주요 특징

1. **사용자 최종 승인 필수**: VLM 검증 결과와 관계없이 사용자가 반드시 최종 승인
2. **자동 재생성**: 점수가 낮으면 비용 한도 내에서 자동 재생성
3. **비용 최적화**: 각 미디어 타입별로 비용 기반 재생성 횟수 제한
4. **상세 피드백**: 검증 결과에 점수, 신뢰도, 분석 내용, 미반영 요소 포함

---

## 향후 개선 사항

1. **검증 이력 DB 저장**: 품질 분석 및 모델 성능 개선에 활용
2. **힌트 기반 재생성**: `missing_elements`를 프롬프트에 추가하여 재생성 품질 향상
3. **점수 임계값 조정**: 실제 사용 데이터 기반으로 최적 임계값 튜닝
4. **검증 속도 최적화**: 병렬 처리 또는 캐싱으로 검증 시간 단축

---

## 작업 일자
2026-01-29

## 작업자
HJ
