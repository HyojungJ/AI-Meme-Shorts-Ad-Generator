"""
vLLM Guided JSON 평가 스크립트

Usage:
    # 1. 추론 (A100에서 실행)
    python vllm_eval.py infer --model exp_e --test-path ../data/splits/test.jsonl
    python vllm_eval.py infer --model exp_f --test-path ../data/splits/test.jsonl
    python vllm_eval.py infer --model exp_h --test-path ../data/splits/test.jsonl

    # 2. 메트릭 계산
    python vllm_eval.py metrics --results-dir outputs/

    # 3. Pairwise 비교
    python vllm_eval.py pairwise --results-dir outputs/

    # wandb 비활성화
    python vllm_eval.py infer --model exp_e --test-path test.jsonl --no-wandb
"""

import argparse
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

# ==============================================================================
# W&B 설정 (optional)
# ==============================================================================

WANDB_PROJECT = "scenario-finetuning"
WANDB_ENTITY = "kzong252-personal"
wandb = None  # lazy import

# ==============================================================================
# 모델 설정
# ==============================================================================

MODEL_CONFIGS = {
    "exp_e": {
        "name": "Exp E (A.X-4.0-Light)",
        "model_path": "/workspace/merged_models/exp_e_merged",
    },
    "exp_f": {
        "name": "Exp F (A.X-3.1-Light)",
        "model_path": "/workspace/merged_models/exp_f_merged",
    },
    "exp_h": {
        "name": "Exp H (Qwen3-8B)",
        "model_path": "/workspace/merged_models/exp_h_merged",
    },
}

# ==============================================================================
# JSON 스키마
# ==============================================================================

SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "thinking": {"type": "string"},
        "scenario": {
            "type": "object",
            "properties": {
                "scene1": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string"},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene2": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string"},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene3": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string"},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene4": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string"},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["scene1", "scene2", "scene3", "scene4", "title", "description", "hashtags"],
        },
    },
    "required": ["thinking", "scenario"],
}


# ==============================================================================
# 1. 추론 (infer)
# ==============================================================================


def run_inference(args):
    """vLLM으로 merged model 추론 실행"""
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams

    config = MODEL_CONFIGS[args.model]
    print(f"=== {config['name']} 추론 시작 ===")
    print(f"Model path: {config['model_path']}")

    # W&B 초기화
    if not args.no_wandb:
        import wandb
        wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            name=f"eval-infer-{args.model}",
            job_type="inference",
            config={
                "model": args.model,
                "model_path": config["model_path"],
                "test_path": args.test_path,
                "limit": args.limit,
            },
        )

    # 데이터 로드
    test_data = []
    with open(args.test_path) as f:
        for line in f:
            if line.strip():
                test_data.append(json.loads(line))

    if args.limit:
        test_data = test_data[: args.limit]
    print(f"Test samples: {len(test_data)}")

    # vLLM 모델 로드 (merged model, no LoRA)
    llm = LLM(
        model=config["model_path"],
        max_model_len=4096,
        trust_remote_code=True,
        gpu_memory_utilization=0.9,
    )

    # Sampling params with structured outputs (JSON schema)
    sampling_params = SamplingParams(
        temperature=0.7,
        top_p=0.9,
        max_tokens=2048,
        structured_outputs=StructuredOutputsParams(json=SCENARIO_SCHEMA),
    )

    # 프롬프트 준비
    tokenizer = llm.get_tokenizer()
    prompts = []
    for item in test_data:
        messages = item.get("messages", [])
        input_msgs = [m for m in messages if m["role"] != "assistant"]
        prompt = tokenizer.apply_chat_template(input_msgs, tokenize=False, add_generation_prompt=True)
        prompts.append(prompt)

    # 추론 실행
    print(f"\n추론 시작 ({len(prompts)}개)...")
    start_time = time.time()
    outputs = llm.generate(prompts, sampling_params)
    total_time = time.time() - start_time
    print(f"추론 완료: {total_time:.1f}s (평균 {total_time / len(prompts):.2f}s/sample)")

    # 결과 저장
    results = []
    for i, (item, output) in enumerate(zip(test_data, outputs)):
        response_text = output.outputs[0].text
        metadata = item.get("metadata", {})

        # JSON 파싱 시도
        try:
            parsed = json.loads(response_text)
            json_ok = True
        except json.JSONDecodeError:
            parsed = None
            json_ok = False

        results.append(
            {
                "index": i,
                "meme_name": metadata.get("meme_name", ""),
                "company_name": metadata.get("company_name", ""),
                "response": response_text,
                "parsed": parsed,
                "json_ok": json_ok,
                "reference": item.get("messages", [{}])[-1].get("content", ""),
            }
        )

    # 출력 디렉토리 생성
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{args.model}_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model": args.model,
                "config": config,
                "total_samples": len(results),
                "total_time_s": round(total_time, 2),
                "avg_time_s": round(total_time / len(prompts), 2),
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n결과 저장: {output_path}")
    json_ok_count = sum(1 for r in results if r["json_ok"])
    json_ok_rate = json_ok_count / len(results) * 100
    print(f"JSON 파싱 성공: {json_ok_count}/{len(results)} ({json_ok_rate:.1f}%)")

    # W&B 로깅
    if not args.no_wandb:
        wandb.log({
            "total_samples": len(results),
            "total_time_s": round(total_time, 2),
            "avg_time_s": round(total_time / len(prompts), 2),
            "json_ok_count": json_ok_count,
            "json_ok_rate": json_ok_rate,
        })
        wandb.finish()


# ==============================================================================
# 2. 메트릭 계산 (metrics)
# ==============================================================================


def compute_pass_at_1(result: dict) -> dict:
    """Pass@1: JSON 파싱 + 스키마 준수 + 감정태그"""
    metrics = {
        "json_ok": False,
        "schema_ok": False,
        "emotion_tag": False,
        "dialogue_length": False,
        "korean_ratio": False,
        "cta": False,
        "pass": False,
    }

    if not result.get("json_ok") or not result.get("parsed"):
        return metrics

    metrics["json_ok"] = True
    parsed = result["parsed"]
    scenario = parsed.get("scenario", {})

    # 스키마 검증
    required_scenes = ["scene1", "scene2", "scene3", "scene4"]
    required_fields = ["scene_type", "dialogue", "action", "visual_description"]
    schema_ok = True

    for skey in required_scenes:
        scene = scenario.get(skey)
        if not scene:
            schema_ok = False
            continue
        for f in required_fields:
            if f not in scene:
                schema_ok = False

    for k in ["title", "description", "hashtags"]:
        if k not in scenario:
            schema_ok = False

    metrics["schema_ok"] = schema_ok

    # 감정 태그 검증
    emotion_ok = True
    for skey in required_scenes:
        scene = scenario.get(skey, {})
        dialogue = scene.get("dialogue", "")
        if not re.search(r"\(.*?\)", dialogue):
            emotion_ok = False
    metrics["emotion_tag"] = emotion_ok

    # 대사 길이 검증
    length_ok = True
    for skey in required_scenes:
        scene = scenario.get(skey, {})
        dialogue = scene.get("dialogue", "")
        clean = re.sub(r"\(.*?\)", "", dialogue).strip().strip('"')
        if len(clean) < 3 or len(clean) > 80:
            length_ok = False
    metrics["dialogue_length"] = length_ok

    # 한국어 비율
    all_text = " ".join(scenario.get(f"scene{i}", {}).get("dialogue", "") for i in range(1, 5))
    kr_chars = sum(1 for c in all_text if "\uac00" <= c <= "\ud7a3")
    metrics["korean_ratio"] = len(all_text) > 0 and kr_chars / len(all_text) >= 0.3

    # CTA 검증
    s4_dialogue = scenario.get("scene4", {}).get("dialogue", "")
    cta_keywords = ["지금", "바로", "확인", "방문", "검색", "다운", "시작", "구매", "클릭", "가입"]
    metrics["cta"] = any(k in s4_dialogue for k in cta_keywords)

    # Pass@1 = JSON + 스키마 + 감정태그
    metrics["pass"] = metrics["json_ok"] and metrics["schema_ok"] and metrics["emotion_tag"]

    return metrics


def compute_distinct_n(texts: list[str], n: int) -> float:
    """Distinct-n: unique n-grams / total n-grams"""
    all_ngrams = []
    for text in texts:
        tokens = text.split()
        ngrams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
        all_ngrams.extend(ngrams)

    if not all_ngrams:
        return 0.0

    return len(set(all_ngrams)) / len(all_ngrams)


def extract_all_dialogues(results: list[dict]) -> list[str]:
    """모든 시나리오에서 대사 추출"""
    dialogues = []
    for r in results:
        if not r.get("parsed"):
            continue
        scenario = r["parsed"].get("scenario", {})
        for i in range(1, 5):
            dialogue = scenario.get(f"scene{i}", {}).get("dialogue", "")
            if dialogue:
                dialogues.append(dialogue)
    return dialogues


def run_metrics(args):
    """자동 메트릭 계산"""
    from bert_score import score as bert_score
    from rouge_score import rouge_scorer

    results_dir = Path(args.results_dir)
    result_files = list(results_dir.glob("*_results.json"))

    if not result_files:
        print(f"결과 파일 없음: {results_dir}")
        return

    print(f"=== 메트릭 계산 ===")
    print(f"결과 파일: {[f.name for f in result_files]}")

    # W&B 초기화
    if not args.no_wandb:
        import wandb
        wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            name="eval-metrics",
            job_type="metrics",
            config={"results_dir": str(results_dir)},
        )

    all_metrics = {}

    for result_file in result_files:
        with open(result_file) as f:
            data = json.load(f)

        model_name = data["model"]
        results = data["results"]
        print(f"\n--- {model_name} ({len(results)}개) ---")

        # Pass@1
        pass_metrics = [compute_pass_at_1(r) for r in results]
        pass_rate = sum(1 for m in pass_metrics if m["pass"]) / len(pass_metrics)
        json_rate = sum(1 for m in pass_metrics if m["json_ok"]) / len(pass_metrics)
        schema_rate = sum(1 for m in pass_metrics if m["schema_ok"]) / len(pass_metrics)
        emotion_rate = sum(1 for m in pass_metrics if m["emotion_tag"]) / len(pass_metrics)
        cta_rate = sum(1 for m in pass_metrics if m["cta"]) / len(pass_metrics)

        print(f"  Pass@1: {pass_rate * 100:.1f}%")
        print(f"    - JSON OK: {json_rate * 100:.1f}%")
        print(f"    - Schema OK: {schema_rate * 100:.1f}%")
        print(f"    - Emotion Tag: {emotion_rate * 100:.1f}%")
        print(f"    - CTA: {cta_rate * 100:.1f}%")

        # Distinct-1, Distinct-2
        dialogues = extract_all_dialogues(results)
        distinct_1 = compute_distinct_n(dialogues, 1)
        distinct_2 = compute_distinct_n(dialogues, 2)
        print(f"  Distinct-1: {distinct_1:.4f}")
        print(f"  Distinct-2: {distinct_2:.4f}")

        # ROUGE-L, BERTScore (vs reference)
        predictions = []
        references = []
        for r in results:
            if r.get("parsed") and r.get("reference"):
                pred_scenario = r["parsed"].get("scenario", {})
                pred_text = " ".join(
                    pred_scenario.get(f"scene{i}", {}).get("dialogue", "") for i in range(1, 5)
                )
                predictions.append(pred_text)

                # reference에서 scenario 추출
                try:
                    ref_parsed = json.loads(r["reference"])
                    ref_scenario = ref_parsed.get("scenario", {})
                    ref_text = " ".join(
                        ref_scenario.get(f"scene{i}", {}).get("dialogue", "") for i in range(1, 5)
                    )
                except (json.JSONDecodeError, AttributeError):
                    ref_text = r["reference"][:500]
                references.append(ref_text)

        # ROUGE-L
        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
        rouge_scores = [scorer.score(ref, pred)["rougeL"].fmeasure for ref, pred in zip(references, predictions)]
        rouge_l = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0
        print(f"  ROUGE-L: {rouge_l:.4f}")

        # BERTScore
        if predictions and references:
            P, R, F1 = bert_score(predictions, references, lang="ko", verbose=False)
            bert_f1 = F1.mean().item()
            print(f"  BERTScore F1: {bert_f1:.4f}")
        else:
            bert_f1 = 0

        all_metrics[model_name] = {
            "pass_at_1": round(pass_rate, 4),
            "json_ok": round(json_rate, 4),
            "schema_ok": round(schema_rate, 4),
            "emotion_tag": round(emotion_rate, 4),
            "cta": round(cta_rate, 4),
            "distinct_1": round(distinct_1, 4),
            "distinct_2": round(distinct_2, 4),
            "rouge_l": round(rouge_l, 4),
            "bert_score_f1": round(bert_f1, 4),
        }

    # 요약 테이블 출력
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    headers = ["Model", "Pass@1", "JSON", "Schema", "Emotion", "CTA", "D-1", "D-2", "ROUGE-L", "BERT-F1"]
    print(f"{headers[0]:<25} " + " ".join(f"{h:>8}" for h in headers[1:]))
    print("-" * 80)

    for model, m in all_metrics.items():
        print(
            f"{model:<25} "
            f"{m['pass_at_1'] * 100:>7.1f}% "
            f"{m['json_ok'] * 100:>7.1f}% "
            f"{m['schema_ok'] * 100:>7.1f}% "
            f"{m['emotion_tag'] * 100:>7.1f}% "
            f"{m['cta'] * 100:>7.1f}% "
            f"{m['distinct_1']:>8.4f} "
            f"{m['distinct_2']:>8.4f} "
            f"{m['rouge_l']:>8.4f} "
            f"{m['bert_score_f1']:>8.4f}"
        )

    # 메트릭 저장
    metrics_path = results_dir / "metrics_summary.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    print(f"\n메트릭 저장: {metrics_path}")

    # W&B 로깅
    if not args.no_wandb:
        # 모델별 메트릭 로깅
        for model, m in all_metrics.items():
            wandb.log({f"{model}/{k}": v for k, v in m.items()})

        # 비교 테이블 생성
        table = wandb.Table(columns=["model", "pass_at_1", "json_ok", "schema_ok",
                                      "emotion_tag", "cta", "distinct_1", "distinct_2",
                                      "rouge_l", "bert_score_f1"])
        for model, m in all_metrics.items():
            table.add_data(model, m["pass_at_1"], m["json_ok"], m["schema_ok"],
                          m["emotion_tag"], m["cta"], m["distinct_1"], m["distinct_2"],
                          m["rouge_l"], m["bert_score_f1"])
        wandb.log({"metrics_comparison": table})
        wandb.finish()


# ==============================================================================
# 3. Pairwise 비교 (pairwise)
# ==============================================================================

PAIRWISE_JUDGE_PROMPT = """당신은 밈 광고 시나리오 품질 평가자입니다.

두 시나리오를 비교하여 **밈을 더 자연스럽고 창의적으로 활용한 시나리오**를 선택하세요.

## 평가 기준
1. 밈이 스토리의 뼈대가 되는가? (밈을 빼면 광고가 성립하지 않는가?)
2. 밈이 2개 이상의 씬에 걸쳐 활용되는가?
3. 밈의 원래 뉘앙스/유머가 살아있는가?
4. 대사가 자연스러운 구어체인가?

## 입력
**밈**: {meme_name}
**상품**: {company_name}

### 시나리오 A
{scenario_a}

### 시나리오 B
{scenario_b}

## 출력
다음 중 하나만 출력하세요:
- "A" (시나리오 A가 더 좋음)
- "B" (시나리오 B가 더 좋음)
- "TIE" (비슷함)

판정:"""


def format_scenario_for_judge(parsed: dict | None) -> str:
    """시나리오를 judge용 텍스트로 포맷"""
    if not parsed:
        return "(파싱 실패)"

    scenario = parsed.get("scenario", {})
    lines = []
    for i in range(1, 5):
        scene = scenario.get(f"scene{i}", {})
        dialogue = scene.get("dialogue", "")
        action = scene.get("action", "")
        lines.append(f"Scene {i}: {dialogue}")
        if action:
            lines.append(f"  (행동: {action})")

    title = scenario.get("title", "")
    if title:
        lines.append(f"제목: {title}")

    return "\n".join(lines)


def run_pairwise(args):
    """GPT-4o-mini로 Pairwise 비교"""
    import random

    from openai import OpenAI

    results_dir = Path(args.results_dir)

    # 비교 쌍 정의
    comparison_pairs = [
        ("exp_f", "exp_e", "모델 효과 (3.1→4.0)"),
        ("exp_e", "exp_h", "한국어 특화 vs 범용"),
    ]

    # 결과 파일 로드
    all_results = {}
    for result_file in results_dir.glob("*_results.json"):
        with open(result_file) as f:
            data = json.load(f)
        all_results[data["model"]] = data["results"]

    print(f"=== Pairwise 비교 ===")
    print(f"로드된 모델: {list(all_results.keys())}")

    # W&B 초기화
    if not args.no_wandb:
        import wandb
        wandb.init(
            project=WANDB_PROJECT,
            entity=WANDB_ENTITY,
            name="eval-pairwise",
            job_type="pairwise",
            config={"results_dir": str(results_dir), "limit": args.limit},
        )

    client = OpenAI()
    pairwise_results = {}

    for model_a, model_b, description in comparison_pairs:
        if model_a not in all_results or model_b not in all_results:
            print(f"\n[SKIP] {model_a} vs {model_b}: 결과 파일 없음")
            continue

        results_a = all_results[model_a]
        results_b = all_results[model_b]

        print(f"\n--- {model_a} vs {model_b} ({description}) ---")

        wins_a, wins_b, ties = 0, 0, 0
        comparisons = []

        # 샘플 수 맞추기
        n_samples = min(len(results_a), len(results_b), args.limit or 119)

        for i in range(n_samples):
            ra = results_a[i]
            rb = results_b[i]

            scenario_a = format_scenario_for_judge(ra.get("parsed"))
            scenario_b = format_scenario_for_judge(rb.get("parsed"))

            # Position bias 제거: 50% 확률로 순서 swap
            swapped = random.random() < 0.5
            if swapped:
                scenario_a, scenario_b = scenario_b, scenario_a

            prompt = PAIRWISE_JUDGE_PROMPT.format(
                meme_name=ra.get("meme_name", ""),
                company_name=ra.get("company_name", ""),
                scenario_a=scenario_a,
                scenario_b=scenario_b,
            )

            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0,
                )
                judgment = response.choices[0].message.content.strip().upper()

                # swap 복원
                if swapped:
                    if judgment == "A":
                        judgment = "B"
                    elif judgment == "B":
                        judgment = "A"

                if judgment == "A":
                    wins_a += 1
                elif judgment == "B":
                    wins_b += 1
                else:
                    ties += 1

                comparisons.append(
                    {
                        "index": i,
                        "meme_name": ra.get("meme_name", ""),
                        "judgment": judgment,
                        "swapped": swapped,
                    }
                )

            except Exception as e:
                print(f"  [ERROR] Sample {i}: {e}")
                continue

            if (i + 1) % 20 == 0:
                print(f"  진행: {i + 1}/{n_samples}")

        total = wins_a + wins_b + ties
        win_rate_a = wins_a / total if total > 0 else 0
        win_rate_b = wins_b / total if total > 0 else 0
        tie_rate = ties / total if total > 0 else 0

        print(f"  결과: {model_a} {wins_a}승 ({win_rate_a * 100:.1f}%) | "
              f"{model_b} {wins_b}승 ({win_rate_b * 100:.1f}%) | "
              f"무승부 {ties} ({tie_rate * 100:.1f}%)")

        pairwise_results[f"{model_a}_vs_{model_b}"] = {
            "description": description,
            "model_a": model_a,
            "model_b": model_b,
            "wins_a": wins_a,
            "wins_b": wins_b,
            "ties": ties,
            "total": total,
            "win_rate_a": round(win_rate_a, 4),
            "win_rate_b": round(win_rate_b, 4),
            "comparisons": comparisons,
        }

    # 결과 저장
    pairwise_path = results_dir / "pairwise_results.json"
    with open(pairwise_path, "w", encoding="utf-8") as f:
        json.dump(pairwise_results, f, ensure_ascii=False, indent=2)
    print(f"\nPairwise 결과 저장: {pairwise_path}")

    # 요약 테이블
    print("\n" + "=" * 70)
    print("PAIRWISE SUMMARY")
    print("=" * 70)
    print(f"{'Comparison':<30} {'Model A':>15} {'Model B':>15} {'Tie':>10}")
    print("-" * 70)
    for key, result in pairwise_results.items():
        print(
            f"{result['description']:<30} "
            f"{result['model_a']} {result['win_rate_a'] * 100:>5.1f}%  "
            f"{result['model_b']} {result['win_rate_b'] * 100:>5.1f}%  "
            f"{result['ties']:>5}"
        )

    # W&B 로깅
    if not args.no_wandb:
        # Pairwise 결과 로깅
        for key, result in pairwise_results.items():
            wandb.log({
                f"{key}/wins_a": result["wins_a"],
                f"{key}/wins_b": result["wins_b"],
                f"{key}/ties": result["ties"],
                f"{key}/win_rate_a": result["win_rate_a"],
                f"{key}/win_rate_b": result["win_rate_b"],
            })

        # 비교 테이블
        table = wandb.Table(columns=["comparison", "description", "model_a", "win_rate_a",
                                      "model_b", "win_rate_b", "ties"])
        for key, result in pairwise_results.items():
            table.add_data(key, result["description"], result["model_a"], result["win_rate_a"],
                          result["model_b"], result["win_rate_b"], result["ties"])
        wandb.log({"pairwise_comparison": table})
        wandb.finish()


# ==============================================================================
# Main
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(description="vLLM Guided JSON 평가")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # infer
    infer_parser = subparsers.add_parser("infer", help="vLLM + LoRA 추론")
    infer_parser.add_argument("--model", required=True, choices=list(MODEL_CONFIGS.keys()))
    infer_parser.add_argument("--test-path", required=True, help="Test JSONL 파일 경로")
    infer_parser.add_argument("--output-dir", default="outputs", help="출력 디렉토리")
    infer_parser.add_argument("--limit", type=int, help="샘플 수 제한")
    infer_parser.add_argument("--no-wandb", action="store_true", help="W&B 로깅 비활성화")

    # metrics
    metrics_parser = subparsers.add_parser("metrics", help="자동 메트릭 계산")
    metrics_parser.add_argument("--results-dir", required=True, help="추론 결과 디렉토리")
    metrics_parser.add_argument("--no-wandb", action="store_true", help="W&B 로깅 비활성화")

    # pairwise
    pairwise_parser = subparsers.add_parser("pairwise", help="Pairwise 비교 (GPT-4o-mini)")
    pairwise_parser.add_argument("--results-dir", required=True, help="추론 결과 디렉토리")
    pairwise_parser.add_argument("--limit", type=int, help="비교 샘플 수 제한")
    pairwise_parser.add_argument("--no-wandb", action="store_true", help="W&B 로깅 비활성화")

    args = parser.parse_args()

    if args.command == "infer":
        run_inference(args)
    elif args.command == "metrics":
        run_metrics(args)
    elif args.command == "pairwise":
        run_pairwise(args)


if __name__ == "__main__":
    main()
