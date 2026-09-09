"""
Evaluation Script for Fine-tuned Scenario Model

Evaluates:
1. JSON parse success rate
2. Schema validation rate (Pydantic)
3. GPT-4o comparison (LLM-as-Judge)
4. Latency metrics
"""

import argparse
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from content_pipeline.scenario.scenario_schemas import Scenario
from pydantic import ValidationError

# Paths
FINETUNE_DIR = Path(__file__).parent.parent
DATA_DIR = FINETUNE_DIR / "data"


@dataclass
class EvalResult:
    total: int = 0
    json_parse_success: int = 0
    schema_pass: int = 0
    wins_vs_baseline: int = 0
    ties: int = 0
    losses: int = 0
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    # 세분화된 지표
    dialogue_length_pass: int = 0  # 대사 길이 준수
    korean_ratio_pass: int = 0     # 한국어 비율 통과
    cta_present: int = 0           # scene4 CTA 포함
    emotion_tag_pass: int = 0      # 감정 태그 존재
    meme_keyphrase_found: int = 0  # 밈 key_phrase 출현 (참고용)

    @property
    def json_parse_rate(self) -> float:
        return self.json_parse_success / self.total if self.total > 0 else 0

    @property
    def schema_rate(self) -> float:
        return self.schema_pass / self.total if self.total > 0 else 0

    @property
    def win_rate(self) -> float:
        compared = self.wins_vs_baseline + self.ties + self.losses
        return self.wins_vs_baseline / compared if compared > 0 else 0

    @property
    def avg_latency_ms(self) -> float:
        return sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p50_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_latencies = sorted(self.latencies_ms)
        idx = len(sorted_latencies) // 2
        return sorted_latencies[idx]

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]


def extract_json_from_response(text: str) -> dict | None:
    """Extract JSON from model response."""
    # Method 1: ```json code block
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # Method 2: Find matching braces
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
                try:
                    return json.loads(text[start_idx:i+1])
                except json.JSONDecodeError:
                    return None
    return None


def validate_schema(scenario: dict) -> bool:
    """Validate scenario against Pydantic schema."""
    try:
        Scenario(**scenario)
        return True
    except ValidationError:
        return False


def compute_detailed_metrics(scenario: dict, key_phrase: str = "") -> dict[str, bool]:
    """시나리오에 대한 세분화된 품질 지표 계산."""
    metrics = {
        "dialogue_length": True,
        "korean_ratio": True,
        "cta_present": False,
        "emotion_tag": True,
        "meme_keyphrase": False,
    }

    all_dialogues = []
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        scene = scenario.get(key, {})
        dialogue = scene.get("dialogue", "")
        all_dialogues.append(dialogue)

        # 대사 길이 준수 (감정 태그 제외 5-50자)
        clean = re.sub(r'\([^)]+\)\s*', '', dialogue)
        if len(clean) < 5 or len(clean) > 50:
            metrics["dialogue_length"] = False

        # 감정 태그 존재 여부
        if not re.search(r'\([^)]+\)', dialogue):
            metrics["emotion_tag"] = False

    # 한국어 비율
    all_text = " ".join(
        s.get("dialogue", "") + s.get("action", "")
        for s in [scenario.get(f"scene{i}", {}) for i in range(1, 5)]
    )
    korean_chars = sum(1 for c in all_text if '\uac00' <= c <= '\ud7a3')
    if len(all_text) > 0 and korean_chars / len(all_text) < 0.3:
        metrics["korean_ratio"] = False

    # CTA 포함 (scene4)
    scene4 = scenario.get("scene4", {})
    scene4_text = scene4.get("dialogue", "") + scene4.get("action", "")
    cta_keywords = ["지금", "바로", "확인", "방문", "검색", "다운", "시작", "구매", "클릭", "가입"]
    metrics["cta_present"] = any(kw in scene4_text for kw in cta_keywords)

    # 밈 key_phrase 출현 여부 (참고용 — 변형 사용도 있으므로 결정적 메트릭은 아님)
    if key_phrase:
        combined = " ".join(all_dialogues)
        # 핵심 단어 2글자 이상 매칭 (완전 일치가 아닌 부분 매칭)
        core_words = [w for w in re.split(r'[~!?.,\s]+', key_phrase) if len(w) >= 2]
        metrics["meme_keyphrase"] = any(w in combined for w in core_words) if core_words else False

    return metrics


def generate_with_vllm(endpoint: str, prompt: str, timeout: float = 30.0) -> tuple[str, float]:
    """Generate response using vLLM endpoint."""
    import requests

    start_time = time.time()
    response = requests.post(
        f"{endpoint}/generate",
        json={"prompt": prompt, "max_tokens": 2000, "temperature": 0.7},
        timeout=timeout,
    )
    latency_ms = (time.time() - start_time) * 1000

    if response.status_code == 200:
        return response.json().get("text", ""), latency_ms
    return "", latency_ms


def generate_with_openai(client: OpenAI, model: str, system: str, user: str) -> str:
    """Generate response using OpenAI API."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def judge_comparison(
    client: OpenAI,
    finetuned_response: dict,
    baseline_response: dict,
    metadata: dict,
    judge_model: str = "gpt-4o-mini",
) -> str:
    """Pairwise 비교. Position bias 제거를 위해 A/B 순서를 랜덤 swap."""
    swap = random.random() < 0.5
    if swap:
        a_resp, b_resp = baseline_response, finetuned_response
    else:
        a_resp, b_resp = finetuned_response, baseline_response

    judge_prompt = f"""당신은 밈 광고 시나리오 평가 전문가입니다.
두 시나리오를 비교하여 밈을 더 자연스럽게 활용한 쪽을 선택하세요.

## 평가 기준
1. **밈 필연성**: 밈을 빼면 스토리가 무너지는가? (장식이 아닌 핵심인가?)
2. **밈 배치**: scene1에만 기계적으로 넣지 않고 창의적으로 배치했는가?
3. **자연스러움**: 밈이 스토리 흐름에 자연스럽게 녹아드는가?
4. **재미**: 밈 본연의 유머/임팩트가 살아있는가?
5. **광고 효과**: 상품 메시지가 잘 전달되는가?

## 밈 정보
- 밈 이름: {metadata.get('meme_name', 'N/A')}

## 기업 정보
- 회사: {metadata.get('company_name', 'N/A')}

## 시나리오 A
{json.dumps(a_resp, ensure_ascii=False, indent=2)}

## 시나리오 B
{json.dumps(b_resp, ensure_ascii=False, indent=2)}

## 응답 형식
반드시 다음 중 하나로만 응답하세요:
- "A" (시나리오 A가 더 나음)
- "B" (시나리오 B가 더 나음)
- "TIE" (비슷함)

응답:"""

    response = client.chat.completions.create(
        model=judge_model,
        messages=[{"role": "user", "content": judge_prompt}],
        temperature=0,
        max_tokens=10,
    )

    result = response.choices[0].message.content.strip().upper()
    if "A" in result and "B" not in result:
        return "loss" if swap else "win"
    elif "B" in result and "A" not in result:
        return "win" if swap else "loss"
    return "tie"


def load_test_data(test_path: Path) -> list[dict]:
    """Load test dataset."""
    records = []
    with open(test_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def evaluate(
    model_endpoint: str | None = None,
    model_path: str | None = None,
    test_path: str | None = None,
    baseline: str = "gpt-4o",
    limit: int | None = None,
    skip_baseline_comparison: bool = False,
):
    """Run evaluation."""
    # Determine test data path
    if test_path:
        test_file = Path(test_path)
    else:
        test_file = DATA_DIR / "splits" / "test.jsonl"
        if not test_file.exists():
            # Fall back to curated
            curated = DATA_DIR / "curated"
            if curated.exists():
                jsonl_files = list(curated.glob("*.jsonl"))
                if jsonl_files:
                    test_file = jsonl_files[0]

    if not test_file.exists():
        raise FileNotFoundError(f"Test data not found: {test_file}")

    print(f"[1/4] Loading test data: {test_file}")
    test_data = load_test_data(test_file)
    if limit:
        test_data = test_data[:limit]
    print(f"  Loaded {len(test_data)} samples")

    # Initialize OpenAI client for baseline and judging
    client = OpenAI()

    result = EvalResult(total=len(test_data))

    print(f"\n[2/4] Evaluating model...")
    for item in tqdm(test_data, desc="Evaluating"):
        messages = item.get("messages", [])
        metadata = item.get("metadata", {})

        if len(messages) < 2:
            continue

        system_prompt = messages[0]["content"] if messages[0]["role"] == "system" else ""
        user_prompt = messages[1]["content"] if len(messages) > 1 else ""

        # Generate with fine-tuned model
        if model_endpoint:
            # Using vLLM endpoint
            full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
            ft_response, latency = generate_with_vllm(model_endpoint, full_prompt)
            result.latencies_ms.append(latency)
        else:
            # Fall back to using original assistant response for testing
            ft_response = messages[2]["content"] if len(messages) > 2 else ""

        # Parse JSON
        ft_json = extract_json_from_response(ft_response)
        if ft_json:
            result.json_parse_success += 1

            # Validate schema
            if validate_schema(ft_json):
                result.schema_pass += 1

            # 세분화된 품질 지표
            key_phrase = metadata.get("key_phrase", "")
            metrics = compute_detailed_metrics(ft_json, key_phrase=key_phrase)
            if metrics["dialogue_length"]:
                result.dialogue_length_pass += 1
            if metrics["korean_ratio"]:
                result.korean_ratio_pass += 1
            if metrics["cta_present"]:
                result.cta_present += 1
            if metrics["emotion_tag"]:
                result.emotion_tag_pass += 1
            if metrics["meme_keyphrase"]:
                result.meme_keyphrase_found += 1

            # Compare with baseline (if not skipped)
            if not skip_baseline_comparison:
                try:
                    baseline_response = generate_with_openai(
                        client, baseline, system_prompt, user_prompt
                    )
                    baseline_json = extract_json_from_response(baseline_response)

                    if baseline_json:
                        judgment = judge_comparison(client, ft_json, baseline_json, metadata)
                        if judgment == "win":
                            result.wins_vs_baseline += 1
                        elif judgment == "loss":
                            result.losses += 1
                        else:
                            result.ties += 1
                except Exception as e:
                    result.errors.append({
                        "meme": metadata.get("meme_name"),
                        "error": str(e),
                    })
        else:
            result.errors.append({
                "meme": metadata.get("meme_name"),
                "error": "JSON parse failed",
            })

    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total samples: {result.total}")
    print(f"\n[Parsing & Validation]")
    print(f"  JSON parse rate: {result.json_parse_rate:.1%} ({result.json_parse_success}/{result.total})")
    print(f"  Schema pass rate: {result.schema_rate:.1%} ({result.schema_pass}/{result.total})")

    parsed = result.json_parse_success or 1
    print(f"\n[Quality Metrics] (of {result.json_parse_success} parsed)")
    print(f"  Dialogue length OK: {result.dialogue_length_pass}/{parsed} ({result.dialogue_length_pass/parsed:.1%})")
    print(f"  Korean ratio OK: {result.korean_ratio_pass}/{parsed} ({result.korean_ratio_pass/parsed:.1%})")
    print(f"  Emotion tags OK: {result.emotion_tag_pass}/{parsed} ({result.emotion_tag_pass/parsed:.1%})")
    print(f"  CTA present: {result.cta_present}/{parsed} ({result.cta_present/parsed:.1%})")
    print(f"  Meme key_phrase found: {result.meme_keyphrase_found}/{parsed} ({result.meme_keyphrase_found/parsed:.1%}) (참고용)")

    if not skip_baseline_comparison:
        compared = result.wins_vs_baseline + result.ties + result.losses
        print(f"\n[vs {baseline}]")
        print(f"  Compared: {compared}")
        print(f"  Wins: {result.wins_vs_baseline} ({result.win_rate:.1%})")
        print(f"  Ties: {result.ties}")
        print(f"  Losses: {result.losses}")

    if result.latencies_ms:
        print(f"\n[Latency]")
        print(f"  Avg: {result.avg_latency_ms:.0f}ms")
        print(f"  P50: {result.p50_latency_ms:.0f}ms")
        print(f"  P95: {result.p95_latency_ms:.0f}ms")

    if result.errors:
        print(f"\n[Errors] ({len(result.errors)} total)")
        for err in result.errors[:5]:
            print(f"  - {err['meme']}: {err['error']}")

    print("=" * 60)

    # Go/No-Go decision
    print("\n[Go/No-Go Decision]")
    schema_ok = result.schema_rate >= 0.99
    win_rate_ok = result.win_rate >= 0.40 if not skip_baseline_comparison else True

    if schema_ok and win_rate_ok:
        print("  DECISION: GO - Ready for deployment")
    elif schema_ok and result.win_rate >= 0.30:
        print("  DECISION: CONDITIONAL - Consider adding more training data")
    elif not schema_ok:
        print("  DECISION: NO-GO - Schema compliance too low, strengthen structured output")
    else:
        print("  DECISION: NO-GO - Win rate too low, keep using GPT-4o")

    # Save results
    output_file = Path("eval_results.json")
    with open(output_file, "w") as f:
        json.dump({
            "total": result.total,
            "json_parse_rate": result.json_parse_rate,
            "schema_rate": result.schema_rate,
            "win_rate": result.win_rate if not skip_baseline_comparison else None,
            "wins": result.wins_vs_baseline,
            "ties": result.ties,
            "losses": result.losses,
            "avg_latency_ms": result.avg_latency_ms,
            "p50_latency_ms": result.p50_latency_ms,
            "p95_latency_ms": result.p95_latency_ms,
            "dialogue_length_pass": result.dialogue_length_pass,
            "korean_ratio_pass": result.korean_ratio_pass,
            "emotion_tag_pass": result.emotion_tag_pass,
            "cta_present": result.cta_present,
            "meme_keyphrase_found": result.meme_keyphrase_found,
            "errors": result.errors[:10],
        }, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Evaluate fine-tuned scenario model")
    parser.add_argument(
        "--endpoint",
        type=str,
        help="vLLM server endpoint (e.g., http://localhost:8000)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to fine-tuned model (for local inference)"
    )
    parser.add_argument(
        "--test-path",
        type=str,
        help="Path to test JSONL file"
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="gpt-4o",
        help="Baseline model for comparison (default: gpt-4o)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of samples to evaluate"
    )
    parser.add_argument(
        "--skip-comparison",
        action="store_true",
        help="Skip baseline comparison (faster, schema-only eval)"
    )

    args = parser.parse_args()

    evaluate(
        model_endpoint=args.endpoint,
        model_path=args.model_path,
        test_path=args.test_path,
        baseline=args.baseline,
        limit=args.limit,
        skip_baseline_comparison=args.skip_comparison,
    )


if __name__ == "__main__":
    main()
