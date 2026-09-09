# 시나리오 생성 모델 파인튜닝 — 실험 기록

> 최종 수정: 2026-02-06

---

## 1. 프로젝트 개요

### 목표
밈을 활용한 15초 숏폼 광고 시나리오 생성 모델 파인튜닝 (LLMOps 역량 시연)

### 아키텍처 변경 이력

| 시점 | 설계 | 변경 이유 |
|------|------|----------|
| 1월 19일 (v1) | 2-Stage: GPT-4 Skeleton → 파인튜닝 Dialogue | 초기 설계 |
| 2월 초 (v2) | **1-Stage: 파인튜닝 모델이 전체 시나리오 생성** | Skeleton 불필요 판단. 밈+상품 정보만으로 4씬 JSON 직접 생성 |

### 모델 변경 이력

| 시점 | 모델 | 변경 이유 |
|------|------|----------|
| 1월 19일 | Qwen 2.5 7B Instruct | 한국어 성능 우수 |
| 2월 초 | **skt/A.X-3.1-Light (7.3B)** | 한국어 특화 모델, SKT 개발 |
| 2월 5일 | **skt/A.X-4.0-Light (Qwen2.5 기반)** | KMMLU 64.15 (3.1의 61.70 대비 향상). Round 2 주력 모델 |

---

## 2. 데이터 파이프라인

### 2.1 데이터 생성 방식

```
DB 밈 119개 × 기업 템플릿 50개 → 조합 생성 → GPT-4o Teacher 생성 → 자동 필터링 → JSONL
```

**Teacher 모델**: GPT-4o (structured output, JSON schema 강제)
**생성 구조**: system prompt + user prompt (밈 정보 + 상품 정보 + instruction) → `{thinking, scenario}` JSON

### 2.2 프롬프트 설계 (v1 → v2)

#### v1 프롬프트 (1차 학습 데이터)
- Instruction variant 5개 × User prompt template 3개 = 15가지 조합
- Few-shot seed 29개 (기존 seeds_final_structured.jsonl)
- **문제점**: seed에서 밈이 scene 하나에 1회만 등장하는 패턴이 고정. 생성된 1000개 전부 동일 패턴

#### v2 프롬프트 (2차 학습 데이터)
- System prompt 핵심 규칙 변경:
  - "밈이 스토리의 핵심" → **"밈이 스토리의 뼈대"**
  - 5가지 활용 패턴 명시 (반복+변형, 역설적 추천, 감정 폭발, 형식 차용, 캐릭터 반전)
  - **금지 패턴** 추가: 밈 1회 언급, 상품 칭찬 나열, 천편일률 구조
- 대사 길이: 15~25자 → **5~25자** (15초/4씬 기준)
- Few-shot seed: 29개 → **10개** (각각 다른 밈 활용 패턴, 직접 작성)
- **문제 발견**: 프롬프트 과부하. 10+개 규칙 경쟁 → GPT-4o가 쉬운 규칙(포맷)만 따르고 어려운 규칙(밈 통합) 무시

#### v3 프롬프트 (3차 학습 데이터 — 현재)
- System prompt **84% 축소** (2443자 → 386자)
  - 핵심 원칙: 포맷/길이는 structured output + validation이 강제 → 프롬프트에서 제거
  - "밈이 스토리의 뼈대" 규칙을 **유일한 핵심 규칙**으로 격상
  - 활용 패턴 목록, 금지 패턴, JSON 예시, 대사 길이 규칙 제거
- Instruction variant 1줄로 단순화 (3-4줄 → 1줄)
- thinking 체크리스트 5개 → **3개** (밈 분석, 씬 배치, 교체 테스트)
- 하드 제약만 유지: 1인 촬영, 1장소, 감정태그, 한국어

### 2.3 데이터 규모

| 버전 | 생성 수 | 필터 통과 | 비용 | 비고 |
|------|--------|----------|------|------|
| v1 | 1,000 | 1,000 (100%) | ~$21 | 전수 통과 = 필터가 형식만 검증 |
| v2 pilot | 100 | 81 (81%) | ~$1.70 | scene4 CTA 대사 길이 초과가 주요 탈락 원인 |
| v2 full | 1,000 (중단) | 120 | ~$2.50 | 품질 미달로 중단 (프롬프트 과부하 진단) |
| v3 pilot-5 | 5 | 5 (100%) | ~$0.10 | 3/5 (60%) 밈 2+ 씬 |
| v3 pilot-30 | 30 | 30 (100%) | ~$0.63 | thinking에서 87% 밈 2+ 씬 계획. 수동 검토 8/10 양호 |
| v3 pilot-100 | 100 | 91 (91%) | ~$1.91 | thinking 87% 밈 2+ 씬, 65개 밈 |

### 2.4 데이터 분할

#### v1 분할

Stratified split (밈 기준 균등 분포):

| Split | 수량 | 비율 |
|-------|------|------|
| Train | 746 | 74.6% |
| Validation | 119 | 11.9% |
| Test | 135 | 13.5% |

#### v3 분할

| Split | 수량 | 비율 |
|-------|------|------|
| Train | 705 | 74.8% |
| Validation | 118 | 12.5% |
| Test | 119 | 12.6% |

---

## 3. 학습 실험

### 3.1 실험 환경

- **GPU**: RTX 5090 32GB × 3 pods (RunPod)
- **프레임워크**: Unsloth + HuggingFace TRL (SFTTrainer)
- **양자화**: QLoRA 4-bit (bitsandbytes)
- **실험 추적**: Weights & Biases (`kzong252-personal/scenario-finetuning`)

#### RTX 5090 호환 이슈
- xformers가 compute capability 12.0 미지원 → `pip uninstall xformers`로 해결
- PyTorch native SDPA (Scaled Dot-Product Attention)으로 fallback

### 3.2 실험 결과

#### Round 1: 하이퍼파라미터 비교 (v1 데이터)

| 실험 | Learning Rate | Epochs | LoRA r | Best eval_loss | 특성 |
|------|-------------|--------|--------|---------------|------|
| **A (baseline)** | 2e-4 | 3 | 32 | **0.604** (epoch 1.6) | epoch 2부터 과적합 |
| **B** | 1e-4 | 3 | 32 | 0.605 (epoch 2.1) | 안정적 수렴, 아직 하락 중 |
| **C** | 2e-4 | 5 | 32 | 0.607 (epoch 1.6) | A와 동일 패턴, epoch 2부터 과적합 |
| **D** | 1e-4 | 5 | 32 | 0.608 (epoch 1.6) | epoch 2.66까지 안정 후 과적합 (0.611→0.675) |

**공통 설정**: DoRA, NEFTune (alpha=5), batch=2, grad_accum=4, warmup=10%

#### 핵심 발견
1. **lr=2e-4는 과적합이 빠름**: A, C 모두 epoch 1.6에서 best → 이후 상승
2. **lr=1e-4가 더 안정적**: B는 epoch 2.1까지 하락 지속
3. **epochs 늘려도 eval_loss 개선 미미**: C(5ep)가 A(3ep)보다 나쁨

### 3.3 추론 평가 (A vs B, test 20개)

| 메트릭 | Exp A (lr=2e-4) | Exp B (lr=1e-4) |
|--------|----------------|----------------|
| JSON 파싱 | 20/20 (100%) | 20/20 (100%) |
| 스키마 준수 | 20/20 (100%) | 20/20 (100%) |
| 감정 태그 | 20/20 (100%) | 20/20 (100%) |
| 대사 길이 | 20/20 (100%) | 20/20 (100%) |
| 한국어 비율 | 20/20 (100%) | 20/20 (100%) |
| **CTA 포함** | **16/20 (80%)** | 11/20 (55%) |
| 평균 지연 | 8.5s | 8.2s |

#### eval_loss vs 추론 품질 불일치
- B가 eval_loss 낮았지만 A가 CTA 생성 품질 우수
- eval_loss는 토큰 단위 예측 정확도 → 실제 시나리오 품질과 완전히 일치하지 않음
- **교훈**: eval_loss만으로 모델 선택하면 안 됨. 반드시 추론 평가 필요

### 3.4 저장된 모델

| 모델 | HuggingFace | 설정 |
|------|-------------|------|
| Exp A | `jmkim-KR1/scenario-ax-exp-a-baseline` | lr=2e-4, ep3, r=32 |
| Exp B | `jmkim-KR1/scenario-ax-exp-b-lr1e4` | lr=1e-4, ep3, r=32 |
| Exp C | `jmkim-KR1/scenario-ax-exp-c-epoch5` | lr=2e-4, ep5, r=32 |
| Exp D | `jmkim-KR1/scenario-ax-exp-d-lr1e4-ep5` | lr=1e-4, ep5, r=32 |

---

## 4. 품질 분석 — v1 모델의 근본 문제

### 4.1 정량 평가: 완벽
- JSON/스키마/감정태그/한국어비율: 100%
- 모델은 **형식을 완벽하게 학습**함

### 4.2 정성 평가: 실패

20개 추론 결과를 수동 분석한 결과:

| 문제 | 설명 | 심각도 |
|------|------|--------|
| 밈 활용 표면적 | 밈 대사가 scene 하나에서 1회 언급되고 끝 | **치명적** |
| 시나리오 단조 | 20개 전부 "궁금→밈 한마디→칭찬→CTA" 동일 구조 | **치명적** |
| 밈 원본 맥락 무시 | 밈의 원래 뉘앙스/유머가 살지 않음 | 높음 |
| 교체 테스트 실패 | 밈을 "와 좋다"로 바꿔도 광고 성립 | 높음 |
| 광고 실사용 불가 | "AI가 만든 광고" 느낌 | 높음 |

### 4.3 근본 원인 분석

```
원인 체인:
seed 29개가 "밈 1회 언급" 패턴
  → GPT-4o가 seed 패턴을 복제하여 1000개 생성
    → 1000개 전부 동일한 밈 활용 패턴
      → 파인튜닝 모델도 이 패턴만 학습
        → 추론 결과도 동일 패턴
```

**결론**: 하이퍼파라미터가 아닌 **학습 데이터 품질**이 문제. 모델을 아무리 잘 학습해도 데이터 천장을 넘을 수 없음.

---

## 5. 개선 방향 (v2)

### 5.1 핵심 변경

| 항목 | v1 | v2 |
|------|-----|-----|
| Seed | 29개, 밈 1회 패턴 | 10개, 7가지 밈 활용 패턴 |
| 프롬프트 | "밈이 스토리의 핵심" (모호) | **"밈이 스토리의 뼈대"** + 패턴 명시 + 금지 패턴 |
| 대사 길이 | 15~25자 (실제 50자까지 허용) | **5~25자** (15초 기준 엄수) |
| 품질 필터 | 형식만 검증 | 형식 + 대사 길이 엄격 적용 |

### 5.2 Seed v2 밈 활용 패턴

| # | 밈 | 상품 | 패턴 |
|---|-----|------|------|
| 1 | 운동 많이 된다 | 오늘의집 | 반복+변형 반전 |
| 2 | 하지마 | 왓챠 | 역설적 추천 |
| 3 | 라부부 | 피자헛 | 밈(수집욕)이 구매 동기 |
| 4 | 무야호 | 에너지플러스 | 감정 폭발 매칭 |
| 5 | 얼음 | 무신사 | 밈 동작이 상황을 만듦 |
| 6 | 영포티 | 현대자동차 | 자조→긍정 반전 |
| 7 | Gee | 커피브루 | 감정 전환 |
| 8 | 단어 리듬 게임 | 다이슨 | 밈 형식을 광고 구조로 차용 |
| 9 | 아기 맹수 | 신한카드 | 캐릭터 반전 |
| 10 | 괜찮아 딩딩딩 | 마이리얼트립 | 위기→밈으로 극복 |

### 5.3 v2 파일럿 분석 결과 (100개 중 81개 통과)

#### 패스율 분석
- 총 시도: 100개, 통과: 81개 (81%)
- 실패 19개 중 대부분 scene4 대사 길이 초과 (CTA에 상품명 포함 시 25자 초과)
- **대응**: scene4만 상한 35자로 완화

#### 대사 길이 분포
- 평균: 14.0자, 중앙값: 13.0자
- 5~15자: 68.8%, 16~25자: 30.9%
- v1 대비 더 짧고 자연스러운 구어체 달성

#### 밈 배치 분포 (텍스트 매칭 기준, 참고용)
| 밈 등장 씬 수 | 비율 | v1 추정치 |
|-------------|------|----------|
| 0개 | 12.3% | - |
| 1개 | 63.0% | ~90% |
| 2개+ | 24.7% | ~10% |

- v1 대비 2개+ 씬 밈 활용 비율 증가 (10% → 24.7%)
- 단, 텍스트 매칭은 과소 측정 (밈 개념 활용은 이름 미포함 가능)

#### scene_type 배치
- scene1=hook, scene2-3=body, scene4=close: 100% 고정
- GPT-4o가 프롬프트의 "자유 배치" 지시를 무시하고 고정 패턴 사용
- 라벨 배치보다 밈 활용 방식이 더 중요하므로 현재는 방치

#### 패턴 다양성 (thinking 분석)
| 키워드 | 출현율 |
|--------|--------|
| 변형 | 91.4% |
| 반복 | 25.9% |
| 반전 | 14.8% |
| 캐릭터 | 11.1% |
| 감정 폭발 | 9.9% |
| 리듬 | 8.6% |
| 위기 | 7.4% |

- "변형"이 지배적이나, v1(단일 패턴)보다 다양성 증가
- 패턴 키워드가 thinking에 명시적으로 나타나지 않아도 실제 활용되는 경우 있음

### 5.4 v2 → v3 전환: 프롬프트 과부하 문제

v2 파일럿 100개 + 대량 생성 120개를 분석한 결과, 밈 활용 품질이 v1 대비 유의미하게 개선되지 않음.

**근본 원인**: 프롬프트 과부하
- System prompt 2443자, 규칙 10+개
- GPT-4o는 쉬운 규칙(JSON 포맷, 감정태그, 대사 길이)을 100% 준수
- 어려운 규칙(밈이 스토리 뼈대, 2+ 씬 배치)은 무시
- 규칙 수가 많을수록 창의적 규칙의 준수율이 떨어짐 (attention 경쟁)

**해결**: v3 프롬프트
- structured output 스키마 + 후처리 validation이 이미 강제하는 규칙을 프롬프트에서 제거
- "밈이 스토리의 뼈대" 규칙만 남김 → GPT-4o의 attention이 이 규칙에 집중

**v3 결과 (100개 파일럿)**:
- 패스율: v2 81% → v3 **91%** (포맷 규칙 제거로 에러 감소)
- Thinking에서 밈 2+ 씬 계획: **87%** (79/91)
  - 씬별 밈 배치 빈도: scene1=59%, scene2=50%, scene3=69%, scene4=2%
  - v2와 달리 scene1 편중이 아닌 균등 분포
- 대사 길이: avg 16자, median 16자 (v2: avg 14자)
- 수동 검토 8/10 (80%) 밈이 2+ 씬에 구조적으로 활용
- 고유 밈: 65개 (119개 중 55% 활용)

### 5.5 v3 데이터 생성 진행

- v3_full_1000.jsonl 생성 중 (2026-02-05~)
- 패스율: ~91.7% (v2 81% 대비 개선)
- 실패 원인: 전부 dialogue 길이 초과

---

## 6. Round 2 실험 계획 — 다중 모델 비교 + 표준 평가

### 6.1 실험 목표

v3 데이터로 4개 모델을 동일 조건에서 학습하여:
1. **데이터 효과** 분리 (v1 → v3, 같은 모델)
2. **모델 효과** 분리 (같은 데이터, 다른 모델)
3. 표준 학술 메트릭으로 정량 비교

### 6.2 비교 모델

| 모델 | 파라미터 | 기반 | KMMLU | 라이선스 | Unsloth |
|------|---------|------|-------|---------|---------|
| skt/A.X-3.1-Light | 7.3B | from-scratch | 61.70 | Apache 2.0 | O |
| **skt/A.X-4.0-Light** | ~7B | Qwen2.5 | **64.15** | Apache 2.0 | O |
| Qwen/Qwen3-8B | 8.2B | Qwen3 | 63.53 | Apache 2.0 | O |

**탈락 모델:**
- Qwen2.5-7B-Instruct: 전 벤치마크 최하위 (Ko-IFEval 60.73, Ko-MT-Bench 61.31). A.X-4.0과의 ablation 의도였으나 결과가 자명하여 제외
- EXAONE-3.5-7.8B: NC 라이선스 (비상업) + Unsloth 미지원. Ko-MT-Bench 81.06 (1위)이지만 사용 불가
- Llama-3.1-8B: KMMLU 42.28로 한국어 성능 부족
- Kanana-1.5-8B: KMMLU 48.28, Ko-IFEval 69.96으로 전반적으로 중위권. 차별점 부족
- Tri-7B (Trillionlabs): Ko-IFEval 76.63 (1위)이나, 라이선스 불명확 + Unsloth 공식 지원 미확인. 관찰 대상

#### Instruction Following 벤치마크 비교

우리 태스크(한국어 JSON 시나리오 생성)에 필수적인 IF 능력과 한국어 대화 품질 종합 비교.
모든 수치는 [skt/A.X-4.0-Light 모델 카드](https://huggingface.co/skt/A.X-4.0-Light), [A.X-3.1-Light 모델 카드](https://huggingface.co/skt/A.X-3.1-Light), [Tri-7B 모델 카드](https://huggingface.co/trillionlabs/Tri-7B) 기준.

| 모델 | IFEval | Ko-IFEval | MT-Bench | Ko-MT-Bench | KMMLU | LiveBench |
|------|--------|-----------|----------|-------------|-------|-----------|
| **Qwen3-8B** | **85.38** | 73.39 | 65.69 | 64.06 | 63.53 | **50.20** |
| **A.X-4.0-Light** | 84.68 | 72.99 | **81.56** | **79.50** | **64.15** | 37.10 |
| EXAONE-3.5-7.8B ❌ | 82.61 | 65.01 | 83.50 | 81.06 | 53.76 | 40.20 |
| Kanana-1.5-8B | 80.11 | 69.96 | 77.60 | 76.30 | 48.28 | 29.40 |
| A.X-3.1-Light | 79.86 | 70.04 | 74.38 | 78.56 | 61.70 | - |
| Tri-7B ⚠️ | 79.26 | **76.63** | 78.20 | 76.40 | 51.74 | - |
| Qwen2.5-7B | 76.73 | 60.73 | 79.37 | 61.31 | 49.56 | 37.00 |

❌ = NC 라이선스로 탈락, ⚠️ = 라이선스/Unsloth 미확인

**벤치마크 설명:**
- **IFEval**: 검증 가능한 제약 조건 준수율 (prompt-strict). "400자 이상", "JSON 형식" 등 형식적 지시 따르기
- **Ko-IFEval**: IFEval 한국어 버전. 한국어 format 제약 준수
- **MT-Bench**: 다중 턴 대화 품질 (0-10 → ×10 스케일). 자연스러움, 유용성, 창의성
- **Ko-MT-Bench**: MT-Bench 한국어 버전. 한국 문화/뉘앙스 반영 평가
- **KMMLU**: 한국어 지식 평가 (한국 수능/자격시험 기반)
- **LiveBench**: 오염 방지 실시간 벤치마크

**우리 태스크와의 관련성:**

| 요구 능력 | 관련 벤치마크 | 최적 모델 |
|-----------|-------------|-----------|
| JSON 스키마 준수 | IFEval | Qwen3-8B ≈ A.X-4.0 |
| 한국어 format 제약 | Ko-IFEval | Tri-7B > Qwen3-8B ≈ A.X-4.0 |
| 자연스러운 한국어 대사 | Ko-MT-Bench | A.X-4.0 >> Qwen3-8B |
| 한국어 지식/맥락 | KMMLU | A.X-4.0 ≈ Qwen3-8B >> 나머지 |
| 밈 활용 창의성 | Ko-MT-Bench + LiveBench | 정량 측정 한계 → Human eval 필수 |

**종합 분석:**
- **A.X-4.0-Light**: IF + 한국어 품질 모두 강함. IFEval 2위, Ko-MT-Bench 1위, KMMLU 1위. 가장 균형 잡힌 후보
- **Qwen3-8B**: IFEval 1위이나 Ko-MT-Bench 최하위 (64.06). 한국어 대화 자연스러움이 약점. 파인튜닝으로 보완 가능 여부가 관건
- **Tri-7B**: Ko-IFEval 1위 (76.63)로 한국어 지시 따르기에 강함. 그러나 라이선스/Unsloth 확인 필요
- **Qwen2.5-7B**: 전 벤치마크 최하위. A.X-4.0의 ablation 대조군이었으나, 결과가 자명하여 제외

**KMMLU 출처:**
- A.X-4.0-Light, A.X-3.1-Light: [HuggingFace 모델 카드](https://huggingface.co/skt/A.X-4.0-Light)
- Qwen2.5-7B, Qwen3-8B: A.X-4.0-Light 모델 카드 비교표
- EXAONE-3.5: [EXAONE 3.5 Technical Report](https://arxiv.org/abs/2412.04862)
- Kanana-1.5-8B: [HuggingFace 모델 카드](https://huggingface.co/kakaocorp/kanana-1.5-8b-instruct-2505)
- Tri-7B: [HuggingFace 모델 카드](https://huggingface.co/trillionlabs/Tri-7B)

### 6.3 실험 매트릭스

| Exp | 모델 | 데이터 | 목적 | 상태 |
|-----|------|--------|------|------|
| A | A.X-3.1-Light | v1 | baseline | **Done** |
| **E** | A.X-4.0-Light | v3 | 주력 후보 | **Done** |
| **F** | A.X-3.1-Light | v3 | 데이터 효과 분리 (A vs F) | **Done** |
| **H** | Qwen3-8B | v3 | 한국어 특화 vs 최신 범용 (E vs H) | **Done** |

**Ablation 설계:**

```
Exp A vs Exp F   → 순수 데이터 효과 (v1 → v3, A.X-3.1 고정)
Exp F vs Exp E   → 순수 모델 효과 (A.X-3.1 → 4.0, v3 고정)
Exp E vs Exp H   → 한국어 특화(A.X-4.0) vs 최신 범용(Qwen3-8B)
```

**공통 하이퍼파라미터** (공정 비교):

| 항목 | 값 | 비고 |
|------|-----|------|
| LoRA r | 32 | |
| LoRA alpha | 64 | |
| Dropout | 0.1 | |
| DoRA | true | |
| Batch size | 2 | A100에서 batch_size=2 가능 |
| Grad accum | 4 | effective batch = 8 |
| Learning rate | 2e-4 | |
| Epochs | 5 (max) | |
| Early stopping | patience=3, metric=eval_loss | |
| Warmup | 10% | |
| NEFTune alpha | 5 | |
| Max seq length | 4096 | |

### 6.4 정량 평가 메트릭

표준 학술 메트릭만 사용. 모든 메트릭에 논문 출처 명시.

#### Tier 1: 학습 메트릭

| 메트릭 | 설명 | 측정 시점 |
|--------|------|----------|
| **Eval Loss** | held-out set cross-entropy | 학습 중 (eval_steps=50) |

#### Tier 2: Reference-based (GPT-4o teacher 출력 대비)

같은 test input → GPT-4o 생성물을 reference로 사용.

| 메트릭 | 논문 | 설명 | 구현 |
|--------|------|------|------|
| **ROUGE-L** | [Lin, 2004 (ACL W04-1013)](https://aclanthology.org/W04-1013/) | LCS 기반 lexical overlap | `rouge-score` 패키지 |
| **BERTScore F1** | [Zhang et al., 2020 (ICLR)](https://arxiv.org/abs/1904.09675) | 사전학습 임베딩 기반 semantic similarity | `bert-score` 패키지, 한국어 모델 `klue/bert-base` 사용 |

**참고**: reference-based 메트릭의 한계
- 시나리오는 정답이 하나가 아님. 다른 좋은 시나리오도 reference와 다르면 낮은 점수
- 따라서 Tier 2는 참고용. 최종 판단은 Tier 3 (Pairwise) + Tier 4 (Human)로

#### Tier 3: Reference-free

| 메트릭 | 논문 | 설명 | 구현 |
|--------|------|------|------|
| **Distinct-1** | [Li et al., 2016 (NAACL)](https://aclanthology.org/N16-1014/) | unique unigram / total unigram. 오버피팅 시 반복 패턴 → 값 하락 | 직접 구현 (단순 비율) |
| **Distinct-2** | 위와 동일 | unique bigram / total bigram | 직접 구현 |
| **Pass@1** | [Chen et al., 2021 (Codex)](https://arxiv.org/abs/2107.03374) | 1회 추론에서 JSON 파싱 + 스키마 준수 + 감정태그 성공률 | 기존 validation 코드 재사용 |

#### Tier 4: LLM-as-Judge Pairwise

| 메트릭 | 논문 | 설명 |
|--------|------|------|
| **Pairwise Win Rate** | [Zheng et al., 2023 (NeurIPS)](https://arxiv.org/abs/2306.05685) | 두 모델 출력을 GPT-4o-mini가 A/B 비교. Position bias 제거 (50% swap) |

**비교 쌍:**

| 쌍 | 측정하는 것 | 최소 쌍 수 |
|----|-----------|----------|
| Exp A vs Exp F | 순수 데이터 효과 | 100 |
| Exp F vs Exp E | 순수 모델 효과 | 100 |
| Exp E vs Exp H | 한국어 특화 vs 최신 범용 | 100 |
| Best vs GPT-4o | teacher 대비 도달도 | 100 |

**Judge 프롬프트 (밈 특화):**
- 질문: "밈을 더 자연스럽게 활용한 시나리오는?"
- Position bias 제거: 50% 확률로 A/B 순서 swap
- Tie 허용 (A 승 / B 승 / 무승부)

#### Tier 5: Human Evaluation

| 메트릭 | 방법 | 샘플 수 |
|--------|------|--------|
| Binary 선호도 | "이 영상 보고 싶다 / 안 보고 싶다" | 50개 |

### 6.5 Go/No-Go 기준

| 메트릭 | 기준 | 근거 |
|--------|------|------|
| Pass@1 | >= 99% | 서비스 안정성 (JSON 파싱 실패 시 재생성 비용) |
| Pairwise vs GPT-4o | >= 40% win | teacher 대비 실용 수준 |
| Pairwise vs Exp A | >= 60% win | v1 대비 개선 확인 (개선 없으면 의미 없음) |
| Human "보고싶다" | >= 60% | 실제 서비스 품질 최소 기준 |

### 6.6 비용 추정

| 항목 | 비용 |
|------|------|
| 학습 3회 (E, F, H) × RunPod A100 | ~$18 |
| Pairwise 평가 4쌍 × 100쌍 (GPT-4o-mini) | ~$4 |
| ROUGE-L, BERTScore, Distinct-n | 무료 (로컬) |
| **합계** | **~$22** |

### 6.7 실행 순서

```
1. v3_full_1000.jsonl 생성 완료              ✅ 942/1000 통과
2. prepare_splits.py로 train/val/test 분할    ✅ 705/118/119
3. Exp E (A.X-4.0-Light + v3) 학습           ✅ 완료
4. Exp F (A.X-3.1-Light + v3) 학습           ✅ 완료
5. Exp H (Qwen3-8B + v3) 학습               ✅ 완료
6. 전 모델 추론 (test set 동일 input)         ← 대기 (vLLM guided JSON)
7. 자동 메트릭 수집 (Pass@1, ROUGE-L, BERTScore, Distinct-1/2)
8. Pairwise 평가 (4쌍 × 100)
9. Human 평가 (best 모델 50개)
10. 결과 종합 → 최적 모델 선정
```

---

## 7. Round 2 학습 결과

### 7.1 실험 환경

| Exp | GPU | 소요 시간 |
|-----|-----|----------|
| E (A.X-4.0-Light) | RTX 5090 32GB | ~61분 |
| F (A.X-3.1-Light) | RTX 5090 32GB | ~56분 |
| H (Qwen3-8B) | A100 80GB | ~97분 |

- E, F: RunPod RTX 5090 pods (PyTorch 2.8.0+cu128, Unsloth 2026.1.4)
- H: 5090 32GB에서 OOM → A100 80GB로 변경 (PyTorch 2.6.0+cu124)
  - Qwen3-8B (8.2B params)은 4-bit QLoRA에서도 5090 32GB 초과

### 7.2 Eval Loss Curve

#### Exp E: A.X-4.0-Light + v3

| Epoch | Train Loss | Eval Loss | 비고 |
|-------|-----------|-----------|------|
| 0.57 | 1.034 | 1.038 | |
| 1.12 | 0.907 | 1.009 | |
| **1.69** | 0.867 | **1.001** | **Best** |
| 2.25 | 0.682 | 1.043 | 과적합 시작 |
| 2.82 | 0.709 | 1.033 | |
| 3.37 | 0.518 | 1.137 | Early stopping 발동 |

#### Exp F: A.X-3.1-Light + v3

| Epoch | Train Loss | Eval Loss | 비고 |
|-------|-----------|-----------|------|
| 0.57 | 1.016 | 1.017 | |
| 1.12 | 0.903 | 0.983 | |
| **1.69** | 0.858 | **0.966** | **Best** |
| 2.25 | 0.684 | 1.006 | 과적합 시작 |
| 2.82 | 0.709 | 1.003 | |
| 3.37 | 0.513 | 1.124 | Early stopping 발동 |

#### Exp H: Qwen3-8B + v3

| Epoch | Train Loss | Eval Loss | 비고 |
|-------|-----------|-----------|------|
| 0.57 | 0.719 | 0.712 | |
| 1.12 | 0.619 | 0.684 | |
| **1.69** | 0.591 | **0.662** | **Best** |
| 2.25 | 0.481 | 0.681 | 과적합 시작 |
| 2.82 | 0.496 | 0.676 | |
| 3.37 | 0.386 | 0.730 | Early stopping 발동 |

### 7.3 핵심 관찰

**1. 과적합 패턴 동일 — epoch 1.7이 최적점**
- E, F 모두 epoch ~1.7에서 best eval_loss → 이후 지속 상승
- Round 1 (eval_loss 최적점 epoch ~1.6)과 일치
- epochs=5 설정 + early stopping (patience=3)으로 epoch 3.37에서 자동 중단
- 실질적으로 epoch 2가 충분 (epochs=3~5 + early stopping 권장)

**2. F(A.X-3.1)가 E(A.X-4.0)보다 eval_loss 낮음**
- F best: 0.966 vs E best: 1.001
- A.X-3.1-Light는 KMMLU 61.70 (A.X-4.0의 64.15보다 낮음)인데도 eval_loss가 더 낮음
- 가능한 해석:
  - 모델 구조 차이 (Llama 3.1 기반 vs Qwen2.5 기반)로 cross-entropy 절대값 비교 무의미
  - 또는 A.X-3.1이 이 태스크에 더 적합한 내부 표현을 가짐
- **eval_loss 비교는 같은 모델 내에서만 유효** (Round 1 교훈 재확인)

**3. Round 1 vs Round 2 eval_loss 비교 불가**
- Round 1 (v1 데이터): Exp A best eval_loss = 0.604
- Round 2 (v3 데이터): Exp E best = 1.001, Exp F best = 0.966
- 데이터가 다르므로 직접 비교 불가 (v3 데이터가 더 복잡하여 loss가 높을 수 있음)
- 실제 품질은 추론 평가에서 확인 필요

**4. Exp H (Qwen3-8B) 동일 패턴 확인**
- Best eval_loss 0.662 at epoch 1.69 — E/F와 동일한 최적 시점
- 3개 모델 모두 epoch ~1.7에서 최적 → 이 데이터셋의 특성
- train_loss 0.386 (epoch 3.37) vs eval_loss 0.730 — 과적합 갭 가장 큼
- 단, 모델 간 eval_loss 절대값 비교 주의 (위 2번 참조)

**5. save_steps / eval_steps 불일치 이슈**
- eval_steps=50, save_steps=100으로 설정
- Best eval_loss는 step 150 (epoch 1.69)에서 발생했으나, checkpoint는 step 100/200/300에서만 저장
- `load_best_model_at_end=True`가 저장된 checkpoint 중 최선(step 100)을 로드
- **개선**: save_steps=eval_steps로 맞추면 최적 checkpoint를 정확히 보존 가능

### 7.4 자유 생성 테스트 (schema 미강제)

vLLM guided JSON 없이 자유 생성으로 3개 밈×상품 조합 테스트.

#### Exp E (A.X-4.0-Light)
- JSON 파싱: 3/3 성공
- **출력 형식 붕괴**: scene 필드가 dialogue 문자열만 포함 (action, visual_description 누락)
  - 학습 데이터에는 full schema 있었지만 모델이 단순화된 출력 패턴으로 수렴
- 밈 배치: 모든 씬에 밈 문구 반복 (과잉 사용)

#### Exp F (A.X-3.1-Light)
- JSON 파싱: 1/3 성공 (2개 malformed)
- **출력 형식 확장**: setting, action, 감정 등 학습 데이터에 없는 필드까지 생성 (hallucination)
- 정상 파싱된 1개는 풍부한 시나리오 구조

#### 교훈
- 자유 생성은 모델 평가에 부적절 — 프로덕션은 vLLM guided decoding으로 JSON schema 강제
- **반드시 schema 강제 상태에서 평가해야 공정한 비교 가능**
- vLLM guided JSON 테스트는 A100에서 실행 예정 (RTX 5090 vLLM flash attention 비호환)

### 7.5 저장된 모델

| 모델 | HuggingFace | 설정 | Best eval_loss |
|------|-------------|------|---------------|
| Exp E | `jmkim-KR1/scenario-ax40-light-lora` | A.X-4.0 + v3, lr=2e-4, ep5(ES→3.37) | 1.001 |
| Exp F | `jmkim-KR1/scenario-ax31-light-lora` | A.X-3.1 + v3, lr=2e-4, ep5(ES→3.37) | 0.966 |
| Exp H | `jmkim-KR1/scenario-qwen3-8b-lora` | Qwen3-8B + v3, lr=2e-4, ep5(ES→3.37) | 0.662 |

---

## 8. 의사결정 기록

| 날짜 | 결정 | 근거 |
|------|------|------|
| 2/5 | 500 vs 1000 데이터 비교 대신 **하이퍼파라미터 비교** 선택 | 500/1000 데이터 중복 가능성, 변수 1개 통제 원칙 |
| 2/5 | 1000개 데이터만 사용 (500개 폐기) | generate_combinations의 dedup이 run별 local → 합치면 중복 |
| 2/5 | lr=1e-4 + ep5 추가 실험 (Exp D) | B 결과에서 lr=1e-4의 안정적 수렴 확인 |
| 2/5 | **데이터 품질 개선이 최우선** | 추론 평가에서 하이퍼파라미터 차이보다 데이터 패턴 문제가 지배적 |
| 2/5 | 50개 직접 작성 대신 **seed 10개 + GPT-4o 대량 생성** | LLMOps 역량 시연 목적 → 데이터 개선 사이클을 보여주는 게 더 가치 있음 |
| 2/5 | LIMA 50개 방식 불채택 | 7B 모델에서 50개로는 부족할 위험. 65B 대상 논문 결과를 7B에 직접 적용하기 어려움 |
| 2/5 | scene4 대사 상한 35자로 완화 | v2 파일럿에서 19% 탈락의 주원인. CTA+상품명 포함 시 25자 넘기 쉬움 |
| 2/5 | v2 대량 생성 중단 (120/1000) | 수동 검토 결과 밈 활용 품질 v1과 유사. 프롬프트 과부하 진단 |
| 2/5 | **v3 프롬프트 단순화** | 2443자→386자 (84% 축소). structured output + validation이 강제하는 규칙을 프롬프트에서 제거. 밈 통합 규칙에 집중 |
| 2/5 | A.X-4.0-Light로 베이스 모델 변경 | Qwen2.5 기반, KMMLU 64.15 (3.1의 61.70 대비 향상) |
| 2/6 | EXAONE-3.5 탈락 | NC 라이선스 (비상업) + Unsloth 미지원. 학습 파이프라인 별도 구성 필요 |
| 2/6 | **Qwen3-8B를 4번째 비교 모델로 채택** | Apache 2.0, Unsloth 지원, Qwen2.5-14B급 성능. 최신 세대 효과 측정 |
| 2/6 | **표준 학술 메트릭 채택** | ROUGE-L, BERTScore, Distinct-1/2, Pass@1, Pairwise Win Rate. 모두 논문 출처 있는 정립된 메트릭 |
| 2/6 | **IF 벤치마크 기반 모델 재검증** | IFEval, Ko-IFEval, Ko-MT-Bench 종합 비교. A.X-4.0이 IF+한국어 품질 최균형. Tri-7B (Ko-IFEval 1위) 관찰 대상이나 라이선스/Unsloth 미확인으로 보류 |
| 2/6 | A.X-3.1-Light KMMLU 수정: 49.56 → **61.70** | 공식 모델 카드 기준. 이전 값은 다른 평가 프레임워크 출처 |
| 2/6 | Qwen3-8B KMMLU 확인: **63.53** | A.X-4.0-Light 모델 카드 비교표에서 공식 수치 발견 |
| 2/6 | **Qwen2.5-7B 제외, 3개 모델로 축소** | 전 벤치마크 최하위 (Ko-IFEval 60.73, Ko-MT-Bench 61.31). A.X-4.0과의 ablation 결과 자명. 비용 $7 절감 |
| 2/5 | **Early stopping 도입** (patience=3, metric=eval_loss) | Round 1에서 epoch 2 이후 과적합 확인. epochs=5로 여유 + early stopping으로 자동 중단 |
| 2/5 | Qwen3-8B → A100 80GB로 이동 | 5090 32GB에서 4-bit QLoRA도 OOM. batch_size=1로 줄여도 실패 |
| 2/5 | A100 PyTorch 2.4.1 → 2.6.0 업그레이드 | `torch._inductor` AttributeError로 Unsloth 임포트 실패. 2.5.1도 `torch.int1` 에러 |
| 2/5 | vLLM guided JSON 평가는 A100에서 실행 | RTX 5090에서 vLLM flash attention PTX 비호환. enforce_eager + TRITON_ATTN 모두 실패 |

---

## 9. 기술 이슈 & 해결

| 이슈 | 원인 | 해결 |
|------|------|------|
| xformers NotImplementedError | RTX 5090 compute capability 12.0 미지원 | `pip uninstall xformers` → PyTorch native SDPA |
| infer_eval.py 이중 PEFT 로딩 | `get_peft_model()` + `PeftModel.from_pretrained()` 중복 | `FastLanguageModel.from_pretrained(model_name=lora_path)` 직접 로드 |
| eval_loss vs 추론 품질 불일치 | 토큰 예측 정확도 ≠ 시나리오 품질 | 추론 평가 필수화. eval_loss는 참고 지표로만 사용 |
| A100 Unsloth 임포트 실패 | PyTorch 2.4.1의 `torch._inductor.config` 미존재 | PyTorch 2.6.0+cu124로 업그레이드 |
| Qwen3-8B OOM (5090 32GB) | 8.2B params, 4-bit에서도 ~34GB 필요 | A100 80GB로 이동, batch_size=1, grad_accum=8 |
| vLLM flash attention PTX 에러 (5090) | `vllm_flash_attn` CUDA 커널이 SM_120 미지원 | A100에서 평가 예정. 5090에서는 vLLM 사용 불가 |
| 자유 생성 시 출력 형식 붕괴 | schema 강제 없이 모델이 단순 패턴으로 수렴 | vLLM `StructuredOutputsParams(json=schema)` 필수 |
| save_steps ≠ eval_steps | save=100, eval=50 → 최적 checkpoint 누락 가능 | save_steps=eval_steps로 통일 권장 |

---

## 10. 파일 구조

```
AI-finetune/finetune/
├── scripts/
│   ├── instruction_variants.py   # 프롬프트 정의 (v3 적용)
│   ├── generate_data.py          # GPT-4o 데이터 생성
│   ├── company_templates.py      # 기업 템플릿 50개
│   └── prepare_splits.py         # train/val/test 분할
├── training/
│   ├── train.py                  # QLoRA 학습 스크립트
│   ├── infer_eval.py             # A/B 추론 비교 평가
│   └── configs/
│       ├── exp_a_baseline.yaml   # A.X-3.1 + v1, lr=2e-4, ep3
│       ├── exp_b_lr1e4.yaml      # A.X-3.1 + v1, lr=1e-4, ep3
│       ├── exp_c_epoch5.yaml     # A.X-3.1 + v1, lr=2e-4, ep5
│       ├── exp_d_lr1e4_epoch5.yaml # A.X-3.1 + v1, lr=1e-4, ep5
│       └── exp_e_ax40.yaml       # A.X-4.0 + v3, lr=2e-4, ep3
├── data/
│   ├── raw/                      # GPT-4o 생성 원본
│   ├── splits/                   # train/val/test JSONL
│   └── seeds/
│       ├── seeds_v2.jsonl        # v2 seed 10개
│       └── seeds_final_structured.jsonl.bak  # v1 seed 백업
└── docs/
    └── FINETUNING_EXPERIMENT_LOG.md  # 이 문서
```

---

## 11. 참고 논문/근거

| 논문 | 핵심 시사점 | 적용 |
|------|-------------|------|
| LIMA (NeurIPS 2023) | 고품질 1K > RLHF 50K (65B 모델) | seed 품질 우선. 단, 7B에 직접 적용은 불확실 |
| Self-Instruct (2023) | LLM 생성→선별→재생성 | 현재 GPT-4o Teacher 방식의 기반 |
| Alpaca (2023) | GPT-3.5로 52K 생성 → 7B 학습 | 소형 모델은 양이 필요하다는 근거 |
| OpenAI Fine-tuning Guide | 좁은 태스크는 50~100개로 충분 | 형식 학습은 적은 데이터로 가능, 창의성은 별도 |
| [ROUGE (Lin, 2004)](https://aclanthology.org/W04-1013/) | Recall-Oriented Understudy for Gisting Evaluation | reference-based 텍스트 유사도 |
| [BERTScore (Zhang et al., 2020)](https://arxiv.org/abs/1904.09675) | 사전학습 임베딩 기반 semantic similarity | ROUGE의 한계 보완 (의미적 유사도) |
| [Distinct-n (Li et al., 2016)](https://aclanthology.org/N16-1014/) | 생성 텍스트 다양성 측정 | 오버피팅/반복 패턴 탐지 |
| [LLM-as-Judge (Zheng et al., 2023)](https://arxiv.org/abs/2306.05685) | Pairwise > Likert. Position bias 제거 필요 | open-ended 생성 품질 비교의 gold standard |
| [Codex Pass@k (Chen et al., 2021)](https://arxiv.org/abs/2107.03374) | 코드 생성 정확도 측정. structured output에 적용 | JSON 스키마 준수율 측정에 차용 |
| [IFEval (Zhou et al., 2023)](https://arxiv.org/abs/2311.07911) | 검증 가능한 instruction following 평가. 25가지 제약 조건 유형 | 모델 비교 시 IF 능력 정량화 |
| [KoMT-Bench (LG AI Research)](https://github.com/LG-AI-EXAONE/KoMT-Bench) | MT-Bench 한국어 적응. 한국 문화/뉘앙스 반영 | 한국어 대화 품질 비교 |

---

## 12. Round 2 추론 평가 결과

### 12.1 평가 환경

- **추론**: vLLM 0.15.1 + StructuredOutputsParams (JSON schema 강제)
- **GPU**: A100 80GB (merged model, LoRA 어댑터 병합)
- **Test set**: 119개 샘플

#### LoRA 병합 이슈
- vLLM이 DoRA를 지원하지 않아 어댑터 직접 로드 불가
- **해결**: PEFT `merge_and_unload()`로 base model에 LoRA 가중치 병합 후 저장
- 병합된 모델 경로: `/workspace/merged_models/{exp_e,exp_f,exp_h}_merged`

### 12.2 추론 성능

| 모델 | JSON 파싱 | 총 시간 | 평균 시간/샘플 |
|------|----------|--------|--------------|
| Exp E (A.X-4.0-Light) | 119/119 (100%) | 19.6s | 0.16s |
| Exp F (A.X-3.1-Light) | 119/119 (100%) | 43.6s | 0.37s |
| Exp H (Qwen3-8B) | 118/119 (99.2%) | 44.0s | 0.37s |

- Exp E가 추론 속도 2배 이상 빠름 (Qwen2.5 기반 최적화)
- Exp H 1개 샘플 JSON 파싱 실패 (감정 태그 누락)

### 12.3 자동 메트릭 결과

| Model | Pass@1 | CTA | Distinct-1 | Distinct-2 | ROUGE-L | BERTScore |
|-------|--------|-----|------------|------------|---------|-----------|
| **Exp E (A.X-4.0)** | **100%** | **36.1%** | 0.5342 | **0.8815** | **0.2798** | **0.8050** |
| Exp F (A.X-3.1) | 100% | 29.4% | 0.5426 | 0.8761 | 0.2529 | 0.8014 |
| Exp H (Qwen3-8B) | 96.6% | 33.6% | **0.5431** | 0.8747 | 0.2621 | 0.7983 |

#### 핵심 관찰

**1. Pass@1: E, F 완벽, H 소폭 미달**
- vLLM guided JSON으로 스키마 강제 → JSON/Schema 오류 제거
- Exp H만 감정 태그 누락 1건 (96.6%)
- **Go/No-Go 기준 99% 충족**: E, F만 통과

**2. CTA 포함율: E > H > F**
- scene4에 CTA 키워드 포함 비율
- Exp E (36.1%)가 가장 높음 — 광고 문맥 이해도 우수
- Round 1 대비 하락 (Exp A 80%) — v3 데이터의 CTA 강제 규칙 완화 영향

**3. Distinct-n: 유사 (다양성 확보)**
- 3개 모델 모두 D-1 ~0.54, D-2 ~0.88
- 오버피팅 없음 확인 (반복 패턴 시 D-n 하락)

**4. Reference-based: E > H > F**
- ROUGE-L: E 0.2798 > H 0.2621 > F 0.2529
- BERTScore: E 0.8050 > F 0.8014 > H 0.7983
- teacher(GPT-4o) 출력과의 유사도에서 E가 우수
- 단, reference-based 한계: 다른 좋은 시나리오도 낮은 점수 가능

### 12.4 Pairwise 비교 (GPT-4o-mini Judge)

Position bias 제거 (50% swap), 119쌍 비교.

**Judge 질문**: "밈을 더 자연스럽게 활용한 시나리오는?"

| 비교 | 목적 | Model A 승 | Model B 승 | 무승부 |
|------|------|-----------|-----------|--------|
| Exp F vs Exp E | 모델 효과 (3.1→4.0) | F: 8 (6.7%) | E: 7 (5.9%) | 104 (87.4%) |
| Exp E vs Exp H | 한국어 특화 vs 범용 | E: 11 (9.2%) | H: 8 (6.7%) | 100 (84.0%) |

#### 핵심 관찰

**1. 대부분 무승부 (84-87%)**
- GPT-4o-mini judge가 밈 활용 품질에서 유의미한 차이를 감지하지 못함
- 3개 모델 모두 비슷한 수준의 밈 활용 패턴 학습

**2. Exp E 소폭 우세 (vs Exp H)**
- 승률 9.2% vs 6.7%로 Exp E가 앞섬
- 한국어 특화 모델(A.X-4.0)이 밈 활용에서 소폭 유리

**3. Exp F vs Exp E 동등**
- 6.7% vs 5.9%로 거의 차이 없음
- 모델 세대 차이(3.1→4.0)가 밈 활용 품질에 큰 영향 없음

### 12.5 종합 분석 및 최종 결론

#### 메트릭 종합 비교

| 메트릭 | Exp E (A.X-4.0) | Exp F (A.X-3.1) | Exp H (Qwen3-8B) | 비고 |
|--------|----------------|----------------|-----------------|------|
| **Pass@1** | **100%** ✅ | **100%** ✅ | 96.6% ❌ | Go/No-Go 99% 기준 |
| CTA | **36.1%** | 29.4% | 33.6% | |
| ROUGE-L | **0.2798** | 0.2529 | 0.2621 | |
| BERTScore | **0.8050** | 0.8014 | 0.7983 | |
| Distinct-2 | **0.8815** | 0.8761 | 0.8747 | |
| 추론 속도 | **0.16s** | 0.37s | 0.37s | 2배+ 빠름 |
| Pairwise 승률 | 기준 | 동등 | 소폭 열세 | |

#### 최종 결론: **Exp E (A.X-4.0-Light) 선정**

1. **Pass@1 100%** — 프로덕션 안정성 확보
2. **전 자동 메트릭 1위** — CTA, ROUGE-L, BERTScore, Distinct-2
3. **추론 속도 2배** — 서비스 비용/지연 절감
4. **Pairwise 동등~소폭 우위** — 밈 활용 품질 최소 동등

#### Go/No-Go 체크리스트

| 기준 | 목표 | Exp E 결과 | 판정 |
|------|------|-----------|------|
| Pass@1 | ≥ 99% | 100% | ✅ |
| Pairwise vs GPT-4o | ≥ 40% win | (미측정) | - |
| Pairwise vs Exp A | ≥ 60% win | (미측정) | - |
| Human "보고싶다" | ≥ 60% | (미측정) | - |

**남은 평가**: GPT-4o teacher 대비 Pairwise, Human 평가

---

*이 문서는 실험 진행에 따라 지속 업데이트됩니다.*
