# 시나리오 생성 파인튜닝 설계

## 개요

### 목표
시나리오 생성의 GPT-4o API 호출을 파인튜닝된 로컬 모델로 완전 대체.

- **비용**: API 호출 비용 → 추론 서버 운영 비용 (대폭 절감)
- **품질**: 밈 광고 시나리오에 특화된 스타일 학습
- **출력 형식**: Pydantic 스키마 (Scenario) 100% 준수 필수

### 적용 지점

```python
# content_pipeline/scenario/scenario_nodes.py:43
# Before
llm = ChatOpenAI(temperature=0, model="gpt-4o")

# After
llm = get_scenario_llm()  # 환경변수/설정에 따라 파인튜닝 모델 반환
```

### 범위
- 시나리오 생성 (`generate_scenario_node`)만 대상
- 다른 LLM 호출 (MemeAgent 등)은 현재 범위 밖

---

## 학습 데이터 파이프라인

### 방법: Knowledge Distillation + CoT

- **Teacher**: GPT-4o
- **Student**: Llama 3.1 8B 등
- **방식**: Teacher의 reasoning + output을 Student가 학습

### 데이터 양 목표

| 단계 | 양 | 용도 |
|------|-----|------|
| GPT-4o 생성 | 2,000개 | 원본 |
| 큐레이션 후 | 1,500개 | 학습 가능 품질 |
| Train | 1,200개 (80%) | 학습 |
| Validation | 150개 (10%) | 검증/early stopping |
| Test | 150개 (10%) | 최종 평가 |

### 다양성 확보 전략

**밈 분포:**
```
DB에 있는 밈 N개 → 각 밈당 최소 20개 시나리오
예: 100개 밈 × 20개 = 2,000개
```

**기업/업종 분포:**

| 업종 | 비율 | 예시 |
|------|------|------|
| 식음료 | 25% | 음료, 과자, 배달앱 |
| IT/앱 | 20% | 핀테크, 게임, SaaS |
| 뷰티/패션 | 15% | 화장품, 의류 |
| 금융 | 15% | 카드, 보험, 은행 |
| 기타 | 25% | 가전, 자동차, 교육 |

**톤/분위기 분포:**

| 톤 | 비율 |
|-----|------|
| 유쾌 | 40% |
| 병맛 | 30% |
| 감동 | 15% |
| 진지 | 15% |

**중복 방지:**

```python
# 같은 (밈, 기업, 톤) 조합 중복 방지
seen_combinations = set()

def generate_unique_combination(meme, companies, tones):
    for _ in range(100):  # 최대 100번 시도
        company = random.choice(companies)
        tone = random.choice(tones)
        key = (meme["meme_name"], company["company_name"], tone)
        if key not in seen_combinations:
            seen_combinations.add(key)
            return company, tone
    return None  # 조합 소진
```

- 동일 조합 재생성 방지
- Instruction 템플릿은 랜덤 변형 (오버피팅 방지)

### 데이터 형식 (Chat)

```json
{
  "messages": [
    {
      "role": "system",
      "content": "당신은 밈 광고 시나리오 전문가입니다. 먼저 <thinking> 태그 안에 사고 과정을 작성하고, 그 다음 JSON 시나리오를 출력하세요."
    },
    {
      "role": "user",
      "content": "밈: 무야호 (기쁨/흥분 표현)\n기업: OO에너지 (에너지드링크)\n톤: 유쾌\n..."
    },
    {
      "role": "assistant",
      "content": "<thinking>\n무야호는 신나거나 기쁠 때 외치는 밈이다. 에너지드링크와 연결하려면...\n</thinking>\n\n{\"hook\": {...}, \"body\": [...], \"close\": {...}}"
    }
  ]
}
```

### 큐레이션 기준

| 기준 | 설명 |
|------|------|
| 자연스러움 | 밈이 억지로 끼워맞춰지지 않음 |
| 광고 적합성 | 브랜드/제품이 잘 녹아듦 |
| 재미 | 밈 본연의 유머 살림 |
| 스키마 준수 | hook/body/close 구조, 필드 완전성 |

### 큐레이션 방법 (2단계)

**1단계: 자동 필터링 (LLM-as-Judge)**

```python
CURATION_PROMPT = """
시나리오 품질을 1-5점으로 평가하세요.

[평가 기준]
1. 밈 활용 자연스러움 (1-5)
2. 광고 효과 (1-5)
3. 재미/몰입도 (1-5)

[시나리오]
{scenario}

평균 3.5점 이상이면 PASS, 미만이면 FAIL
출력: {"score": 평균점수, "decision": "PASS/FAIL", "reason": "이유"}
"""
```

- GPT-4o-mini로 자동 평가 (비용 절감)
- 평균 3.5점 이상만 통과 → curated/로 이동
- 예상 통과율: 70-80%

**2단계: 샘플 수동 검토**

- curated 데이터 중 랜덤 50개 수동 검토
- 품질 이상 시 1단계 프롬프트 조정 후 재실행
- 최종 승인 후 splits/ 생성

### 데이터 생성 비용 추정

```
GPT-4o 입력: ~1,000 tokens/요청
GPT-4o 출력: ~800 tokens/요청 (CoT 포함)

2,000개 × (1,000 + 800) tokens = 3.6M tokens
GPT-4o 비용: $5/1M input + $15/1M output
예상 비용: ~$17 (입력) + ~$24 (출력) = ~$41
```

---

## 모델 학습

### 베이스 모델 후보

**한국어 모델 벤치마크 (동일 조건 측정):**

| 모델 | 파라미터 | KMMLU | CLIcK | Ko-IFEval | 특징 |
|------|----------|-------|-------|-----------|------|
| Qwen 3 8B | 8B | **63.53** | 63.31 | 73.39 | KMMLU 1위, 중국어 섞임 이슈 |
| **SKT A.X 3.1 Light** | 7B | 61.70 | **71.22** | 70.04 | 한국 특화, from-scratch |
| EXAONE 3.5 7.8B | 7.8B | 53.76 | 64.11 | 65.01 | LG AI, 한국어 특화 |
| Qwen 2.5 7B | 7B | 49.56 | 58.30 | 60.73 | 다국어, 중국어 섞임 이슈 |
| Kanana 1.5 8B | 8B | 48.28 | 61.30 | 69.96 | 카카오, 128K 컨텍스트 |
| Trillion-7B | 7.8B | 48.09 | - | 66.58 | from-scratch, Apache 2.0 |
| **Mi:dm 2.0 Mini** | 2.3B | - | - | 73.3 | KT, 경량화, K-Refer 70.8 |
| Llama 3.1 8B | 8B | ~42 | - | - | 범용, 생태계 좋음 |

> - KMMLU: 한국어 지식 평가 (45개 분야)
> - CLIcK: 한국 문화/상식 추론
> - Ko-IFEval: 한국어 지시사항 준수 능력
> - 출처: SKT A.X-3.1-Light 모델 카드 (동일 조건 비교)

**Qwen 중국어 섞임 이슈:**
- 중국어 기반 학습 데이터 비중이 높아 한국어 응답에 중국어가 간헐적으로 섞임
- 시스템 프롬프트로 완전히 해결 안 됨
- 파인튜닝 후에도 잔존 가능성 있음

**출처:**
- [SKT A.X-3.1-Light Hugging Face](https://huggingface.co/skt/A.X-3.1-Light)
- [EXAONE 3.5 GitHub](https://github.com/LG-AI-EXAONE/EXAONE-3.5)
- [Kanana 1.5 카카오 공식](https://www.kakaocorp.com/page/detail/11566)
- [Trillion-7B Technical Report](https://arxiv.org/html/2504.15431)
- [Mi:dm 2.0 Hugging Face](https://huggingface.co/K-intelligence/Midm-2.0-Mini-Instruct)

**결론: SKT A.X 3.1 Light 우선, Mi:dm Mini 경량화 대안**

| 순위 | 모델 | 선택 이유 |
|------|------|----------|
| 1순위 | **SKT A.X 3.1 Light** | CLIcK 1위, 한국어 from-scratch, 중국어 섞임 없음 |
| 2순위 | EXAONE 3.5 7.8B | 균형잡힌 성능, LG 지원 |
| 3순위 | Mi:dm 2.0 Mini | 경량화 필요 시 (2.3B), Ko-IFEval 우수 |

**모델 선택 고려사항:**
- **SKT A.X 3.1 Light**: 한국 문화/상식 최강, 중국어 섞임 문제 없음
- **Mi:dm 2.0 Mini**: 2.3B로 경량화 특화, 온디바이스 배포 시 유리
- Qwen은 KMMLU 최고점이나 중국어 섞임 리스크로 제외
- 라이선스: 모두 상업 사용 가능 (Apache 2.0 또는 유사)

### 학습 방식: QLoRA

- Full fine-tuning 대비 메모리 90% 절감
- 단일 GPU (A100 40GB, RTX 4090 24GB)로 학습 가능

### 하이퍼파라미터 실험 계획

**Phase 1: LoRA rank 탐색**

| 실험 | r | alpha | lr | 고정 |
|------|---|-------|-----|------|
| exp-r8 | 8 | 16 | 2e-4 | epochs=3 |
| exp-r16 | 16 | 32 | 2e-4 | epochs=3 |
| exp-r32 | 32 | 64 | 2e-4 | epochs=3 |
| exp-r64 | 64 | 128 | 2e-4 | epochs=3 |

**Phase 2: Learning rate 탐색**

| 실험 | lr | 고정 |
|------|-----|------|
| exp-lr1 | 1e-4 | 최적 r |
| exp-lr2 | 2e-4 | 최적 r |
| exp-lr5 | 5e-4 | 최적 r |
| exp-lr10 | 1e-3 | 최적 r |

### 오버피팅 방지

```python
training_args = TrainingArguments(
    # Early stopping
    evaluation_strategy="steps",
    eval_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,

    # Regularization
    weight_decay=0.01,
    warmup_ratio=0.1,

    # Gradient 안정화
    max_grad_norm=1.0,
    gradient_accumulation_steps=4,

    seed=42,
)

callbacks = [EarlyStoppingCallback(early_stopping_patience=3)]
```

### 모델별 Chat Template

| 모델 | Chat Template |
|------|---------------|
| SKT A.X 3.1 Light | `<\|startoftext\|>[INST]...` |
| EXAONE 3.5 7.8B | `[BOS]System: ...\n\nUser: ...` |
| Mi:dm 2.0 Mini | ChatML 형식 (`<\|im_start\|>...`) |

> 학습 시 tokenizer의 `apply_chat_template()` 사용 권장

### Quantization 설정

```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
```

### 학습 환경

| 항목 | 최소 | 권장 |
|------|------|------|
| GPU | RTX 4090 24GB | A100 40GB |
| RAM | 32GB | 64GB |
| 예상 학습 시간 | ~4시간/모델 | ~2시간/모델 |

---

## 평가 체계

### 평가 지표

| 카테고리 | 지표 | 측정 방법 | 목표 |
|----------|------|----------|------|
| **필수** | Schema 준수율 | Pydantic validation | 100% |
| **필수** | JSON 파싱 성공률 | 파싱 에러 없이 추출 | ≥99% |
| **품질** | GPT-4o 비교 승률 | LLM-as-Judge | ≥45% |
| **품질** | 사람 평가 점수 | 5점 척도 루브릭 | ≥3.5/5 |
| **속도** | Latency p50 | 응답 시간 | <3초 |

### 사람 평가 루브릭 (5점 척도)

**평가 항목 1: 밈 활용 자연스러움**

| 점수 | 기준 |
|------|------|
| 5 | 밈이 시나리오에 완벽히 녹아듦, 필연적 |
| 4 | 자연스럽게 연결됨, 약간의 어색함 |
| 3 | 연결은 되지만 억지스러운 부분 있음 |
| 2 | 밈과 시나리오가 따로 노는 느낌 |
| 1 | 밈 활용이 이해 불가 |

**평가 항목 2: 광고 효과**

| 점수 | 기준 |
|------|------|
| 5 | 제품/브랜드가 매력적으로 각인됨 |
| 4 | 광고 메시지가 잘 전달됨 |
| 3 | 광고임은 알겠으나 임팩트 부족 |
| 2 | 제품이 억지로 끼워맞춰진 느낌 |
| 1 | 광고 효과 전혀 없음 |

**평가 항목 3: 재미/몰입도**

| 점수 | 기준 |
|------|------|
| 5 | 끝까지 보고 싶고, 공유하고 싶음 |
| 4 | 재미있게 볼 수 있음 |
| 3 | 무난함, 지루하지는 않음 |
| 2 | 중간에 스킵하고 싶음 |
| 1 | 보기 힘듦 |

### LLM-as-Judge (자동 비교 평가)

```python
JUDGE_PROMPT = """
두 시나리오를 비교하여 더 나은 것을 선택하세요.

[입력 정보]
밈: {meme_info}
기업: {company_info}

[시나리오 A]
{scenario_a}

[시나리오 B]
{scenario_b}

평가 기준:
1. 밈 활용이 자연스러운가?
2. 광고 효과가 있는가?
3. 재미있는가?

더 나은 시나리오: A 또는 B
"""
```

### Baseline 비교

| 모델 | 역할 |
|------|------|
| GPT-4o (zero-shot) | **Primary Baseline** |
| Base model (no finetune) | Sanity check |

### 평가 프로세스

```
1. Test set 150개
        ↓
2. 각 모델로 생성 (Finetuned × 3 + GPT-4o baseline)
        ↓
3. 자동 평가 (Schema, LLM-as-Judge)
        ↓
4. 사람 평가 (상위 2개 모델, 평가자 3명, 각 50개)
        ↓
5. 최종 선택
```

---

## Structured Output 로버스트화

### 파서 설계

```python
def extract_json(text: str) -> Optional[str]:
    """텍스트에서 JSON 추출 (nested 지원)"""

    # 방법 1: ```json 코드블록
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        return code_block.group(1)

    # 방법 2: 중괄호 매칭 (nested 지원)
    start_idx = text.find('{')
    if start_idx == -1:
        return None

    depth = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start_idx:i+1]

    return None

def parse_scenario_response(response: str) -> Tuple[Scenario, str]:
    # 1. <thinking> 분리
    # 2. JSON 추출
    # 3. JSON 파싱
    # 4. Pydantic 검증
    # 5. 비즈니스 규칙 검증
    ...
```

### 비즈니스 규칙 검증

```python
def validate_scenario_business_rules(scenario: Scenario):
    errors = []

    # hook은 1개
    if not scenario.hook:
        errors.append("hook is required")

    # body는 2개
    if len(scenario.body) != 2:
        errors.append(f"body must have 2 items")

    # 총 duration 15-60초
    if not (15 <= scenario.total_duration <= 60):
        errors.append(f"total_duration must be 15-60s")

    # dialogue 비어있으면 안됨
    ...
```

### 재시도 및 Fallback

```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def generate_scenario_with_retry(llm, prompt):
    response = llm.invoke(prompt)
    return parse_scenario_response(response.content)

def generate_scenario_safe(llm, prompt):
    try:
        return generate_scenario_with_retry(llm, prompt)
    except ScenarioParseError:
        if settings.ENABLE_FALLBACK:
            # GPT-4o fallback
            fallback_llm = ChatOpenAI(model="gpt-4o")
            return generate_scenario_with_retry(fallback_llm, prompt)
        raise
```

### 학습 데이터 품질 검증

```python
def validate_training_data(data_path: str) -> dict:
    """학습 데이터 전수 검증 - valid_rate < 100%이면 학습 진행 안함"""
    ...
```

---

## MLOps 파이프라인

### 도구 스택

| 영역 | 도구 |
|------|------|
| 실험 추적 | W&B |
| 데이터 버전 | DVC |
| 모델 버전 | HuggingFace Hub |
| 평가 | Custom + LLM-as-Judge |
| CI/CD | GitHub Actions |

### 전체 흐름

```
[데이터 생성] → [DVC 버전 관리]
       ↓
[학습] → [W&B 실험 추적]
       ↓
[HuggingFace Hub] → [모델 버전 관리]
       ↓
[자동 평가] → [품질/스키마/속도]
       ↓
[배포]
```

---

## 비용 비교

**GPT-4o API:**

| 월 요청량 | 비용 |
|----------|------|
| 1,000건 | $17 |
| 10,000건 | $170 |
| 100,000건 | $1,700 |

**파인튜닝 (서버리스 - RunPod):**

| 월 요청량 | 비용 |
|----------|------|
| 1,000건 | ~$1 |
| 10,000건 | ~$10 |
| 100,000건 | ~$100 |

**손익분기점:** 서버리스 사용 시 즉시 이득

---

## 추론 배포

### 배포 환경 옵션

| 환경 | 비용 | 지연시간 | 운영 복잡도 |
|------|------|----------|-------------|
| **RunPod Serverless** | $0.00019/초 | Cold start 있음 | ⭐ 낮음 |
| AWS SageMaker | 높음 | 낮음 | ⭐⭐⭐ 높음 |
| 자체 GPU 서버 | 초기 투자 큼 | 가장 낮음 | ⭐⭐ 중간 |

**결정: RunPod Serverless (1차)**

- 초기 트래픽 적을 때 가장 경제적
- vLLM 기반 서버리스 엔드포인트
- Cold start 문제는 keep-warm 옵션으로 해결

### vLLM 서버 설정

```python
# finetune/serving/vllm_server.py
from vllm import LLM, SamplingParams

llm = LLM(
    model="your-finetuned-model",
    tensor_parallel_size=1,
    gpu_memory_utilization=0.9,
)

sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=1024,
    stop=["```", "\n\n\n"],
)
```

---

## 모델 업데이트 계획

### 재학습 트리거

| 트리거 | 조건 | 액션 |
|--------|------|------|
| 새 밈 추가 | 밈 50개 이상 추가 시 | 전체 재학습 |
| 품질 저하 | 주간 모니터링에서 승률 < 35% | 데이터 추가 후 재학습 |
| 정기 업데이트 | 분기 1회 | 최신 밈 반영 재학습 |

### 업데이트 프로세스

```
1. 새 밈으로 추가 데이터 생성 (기존 데이터 + 신규)
2. 전체 데이터로 재학습 (incremental X, full retrain O)
3. 기존 모델과 A/B 비교 평가
4. 승률 유지/상승 시 배포
5. 기존 모델은 롤백용으로 보관
```

**참고:** LoRA는 incremental learning에 적합하지 않음 → 전체 재학습 권장

---

## 리스크 대응

### Go/No-Go 의사결정

```
Phase 1: 데이터 생성 후
├── 큐레이션 품질 OK → Phase 2
└── 품질 낮음 → 프롬프트 수정 후 재생성

Phase 2: 학습 후
├── Schema ≥99% AND 승률 ≥40% → 배포
├── Schema ≥99% AND 승률 30-40% → 데이터 추가
├── Schema <99% → Structured output 강화
└── 전부 실패 → GPT-4o 유지 (파인튜닝 보류)
```

### 최소 성공 기준

| 지표 | 최소 | 목표 |
|------|------|------|
| Schema 준수율 | 99% | 100% |
| GPT-4o 대비 승률 | 40% | 50%+ |
| Latency p50 | <5초 | <3초 |

**이 기준 못 맞추면 → 파인튜닝 배포 안 함, GPT-4o 유지**

---

## 프로젝트 구조

```
AI/
├── finetune/
│   ├── data/
│   │   ├── raw/
│   │   ├── curated/
│   │   └── splits/
│   │
│   ├── scripts/
│   │   ├── generate_data.py
│   │   ├── curate_data.py
│   │   ├── validate_data.py
│   │   └── prepare_splits.py
│   │
│   ├── training/
│   │   ├── train.py
│   │   ├── eval.py
│   │   └── configs/
│   │       ├── skt_ax_7b.yaml
│   │       ├── exaone_7.8b.yaml
│   │       └── midm_mini_2.3b.yaml
│   │
│   ├── serving/
│   │   └── vllm_server.py
│   │
│   └── dvc.yaml
│
├── content_pipeline/
│   └── scenario/
│       ├── llm_factory.py
│       ├── parser.py
│       └── scenario_nodes.py
```

---

## 다음 단계

1. [x] `finetune/` 폴더 구조 생성
2. [x] `generate_data.py` - 다양성 확보 로직 포함
3. [x] `validate_data.py` - 전수 검증
4. [x] `prepare_splits.py` - train/val/test 분할
5. [ ] 밈 데이터 추가 수집 (최소 50개 목표)
6. [ ] GPT-4o로 학습 데이터 생성
7. [ ] 자동 큐레이션 (LLM-as-Judge)
8. [ ] 샘플 수동 검토 (50개)
9. [ ] 하이퍼파라미터 실험 (SKT A.X 3.1 Light 우선)
10. [ ] 모델별 학습 + 비교 평가
11. [ ] Go/No-Go 판단
12. [ ] (통과 시) 파이프라인 통합 + RunPod 배포
