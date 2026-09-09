"""
LoRA 모델 A/B 추론 비교 평가

1. 모델 A 로드 → test set 추론 → 결과 저장
2. 모델 B 로드 → test set 추론 → 결과 저장
3. 품질 메트릭 비교 출력
"""

import argparse
import json
import re
import time
from pathlib import Path

import torch

try:
    from unsloth import FastLanguageModel
except ImportError:
    raise RuntimeError("unsloth required")


def load_model(base_model: str, lora_path: str, max_seq_length: int = 4096):
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=lora_path,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def generate(model, tokenizer, messages: list[dict], max_new_tokens: int = 2048) -> str:
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True)


def extract_scenario(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
        if "scenario" in parsed:
            return parsed["scenario"]
        if "scene1" in parsed:
            return parsed
        return None
    except json.JSONDecodeError:
        pass

    # fallback: find JSON block
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, c in enumerate(text[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(text[start:i+1])
                    return parsed.get("scenario", parsed)
                except json.JSONDecodeError:
                    return None
    return None


def compute_metrics(scenario: dict) -> dict:
    metrics = {"json_ok": True, "schema_ok": True, "emotion_tag": True,
               "dialogue_length": True, "korean_ratio": True, "cta": False}

    required_scenes = ["scene1", "scene2", "scene3", "scene4"]
    required_fields = ["scene_type", "dialogue", "action", "visual_description"]

    for skey in required_scenes:
        scene = scenario.get(skey)
        if not scene:
            metrics["schema_ok"] = False
            continue
        for f in required_fields:
            if f not in scene:
                metrics["schema_ok"] = False

        d = scene.get("dialogue", "")
        if not re.search(r"\(.*?\)", d):
            metrics["emotion_tag"] = False
        clean = re.sub(r"\(.*?\)", "", d).strip().strip('"')
        if len(clean) < 5 or len(clean) > 80:
            metrics["dialogue_length"] = False

    for k in ["title", "description", "hashtags"]:
        if k not in scenario:
            metrics["schema_ok"] = False

    # Korean ratio
    all_text = " ".join(
        scenario.get(f"scene{i}", {}).get("dialogue", "")
        for i in range(1, 5)
    )
    kr = sum(1 for c in all_text if "\uac00" <= c <= "\ud7a3")
    if len(all_text) > 0 and kr / len(all_text) < 0.3:
        metrics["korean_ratio"] = False

    # CTA
    s4 = scenario.get("scene4", {}).get("dialogue", "")
    cta_kw = ["지금", "바로", "확인", "방문", "검색", "다운", "시작", "구매", "클릭", "가입"]
    metrics["cta"] = any(k in s4 for k in cta_kw)

    return metrics


def run_inference(model, tokenizer, test_data: list[dict], label: str) -> list[dict]:
    results = []
    for i, item in enumerate(test_data):
        messages = item.get("messages", [])
        metadata = item.get("metadata", {})

        input_msgs = [m for m in messages if m["role"] != "assistant"]

        start = time.time()
        response = generate(model, tokenizer, input_msgs)
        latency = time.time() - start

        scenario = extract_scenario(response)
        metrics = compute_metrics(scenario) if scenario else {
            "json_ok": False, "schema_ok": False, "emotion_tag": False,
            "dialogue_length": False, "korean_ratio": False, "cta": False,
        }

        results.append({
            "index": i,
            "meme_name": metadata.get("meme_name", ""),
            "company_name": metadata.get("company_name", ""),
            "response": response[:500],
            "scenario": scenario,
            "metrics": metrics,
            "latency_s": round(latency, 2),
        })

        status = "OK" if metrics["json_ok"] and metrics["schema_ok"] else "FAIL"
        print(f"  [{label}] {i+1}/{len(test_data)} {metadata.get('meme_name','')} - {status} ({latency:.1f}s)")

    return results


def print_comparison(results_a: list, results_b: list, label_a: str, label_b: str):
    def summarize(results):
        n = len(results)
        return {
            "total": n,
            "json_ok": sum(1 for r in results if r["metrics"]["json_ok"]),
            "schema_ok": sum(1 for r in results if r["metrics"]["schema_ok"]),
            "emotion_tag": sum(1 for r in results if r["metrics"]["emotion_tag"]),
            "dialogue_length": sum(1 for r in results if r["metrics"]["dialogue_length"]),
            "korean_ratio": sum(1 for r in results if r["metrics"]["korean_ratio"]),
            "cta": sum(1 for r in results if r["metrics"]["cta"]),
            "avg_latency": sum(r["latency_s"] for r in results) / n if n else 0,
        }

    sa = summarize(results_a)
    sb = summarize(results_b)
    n = sa["total"]

    print("\n" + "=" * 70)
    print(f"{'METRIC':<25} {label_a:>20} {label_b:>20}")
    print("=" * 70)
    for key in ["json_ok", "schema_ok", "emotion_tag", "dialogue_length", "korean_ratio", "cta"]:
        va = sa[key]
        vb = sb[key]
        winner = " <--" if va > vb else (" -->" if vb > va else "")
        print(f"  {key:<23} {va:>4}/{n} ({va/n*100:5.1f}%)  {vb:>4}/{n} ({vb/n*100:5.1f}%) {winner}")
    print(f"  {'avg_latency':<23} {sa['avg_latency']:>15.1f}s  {sb['avg_latency']:>15.1f}s")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Compare two LoRA models on test set")
    parser.add_argument("--base-model", default="skt/A.X-3.1-Light")
    parser.add_argument("--lora-a", required=True, help="Path to LoRA adapter A")
    parser.add_argument("--lora-b", required=True, help="Path to LoRA adapter B")
    parser.add_argument("--label-a", default="Model A")
    parser.add_argument("--label-b", default="Model B")
    parser.add_argument("--test-path", required=True, help="Test JSONL file")
    parser.add_argument("--limit", type=int, default=20, help="Number of test samples")
    parser.add_argument("--output", default="infer_eval_results.json")
    args = parser.parse_args()

    test_data = []
    with open(args.test_path) as f:
        for line in f:
            if line.strip():
                test_data.append(json.loads(line))
    test_data = test_data[:args.limit]
    print(f"Loaded {len(test_data)} test samples\n")

    # Model A
    print(f"=== Loading {args.label_a}: {args.lora_a} ===")
    model_a, tok_a = load_model(args.base_model, args.lora_a)
    results_a = run_inference(model_a, tok_a, test_data, args.label_a)
    del model_a, tok_a
    torch.cuda.empty_cache()

    # Model B
    print(f"\n=== Loading {args.label_b}: {args.lora_b} ===")
    model_b, tok_b = load_model(args.base_model, args.lora_b)
    results_b = run_inference(model_b, tok_b, test_data, args.label_b)
    del model_b, tok_b
    torch.cuda.empty_cache()

    # Compare
    print_comparison(results_a, results_b, args.label_a, args.label_b)

    # Save
    with open(args.output, "w") as f:
        json.dump({
            args.label_a: results_a,
            args.label_b: results_b,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
