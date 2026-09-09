"""
학습 데이터 큐레이션 스크립트 — Pairwise Comparison

같은 밈+상품 조합으로 생성된 2개 시나리오를 A/B 비교하여 승자만 남김.
- GPT-4o-mini judge
- Position bias 제거: 50% 확률로 A/B 순서 swap
- Tier 1: rule-based 자동 필터링 (JSON, 스키마, 감정 태그, 한국어 비율, 대사 길이)
- Tier 2: pairwise 큐레이션
"""

import argparse
import json
import random
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.config import config


DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
CURATED_DIR = DATA_DIR / "curated"
REJECTED_DIR = DATA_DIR / "rejected"
PROGRESS_FILE = DATA_DIR / ".curate_progress.json"


PAIRWISE_JUDGE_PROMPT = """당신은 밈 광고 시나리오 품질 평가 전문가입니다.
두 시나리오를 비교하여 밈을 더 자연스럽게 활용한 쪽을 선택하세요.

## 평가 기준
1. **밈 필연성**: 밈을 빼면 스토리가 무너지는가? (장식이 아닌 핵심인가?)
2. **밈 배치**: scene1에만 기계적으로 밈을 넣지 않고 창의적으로 배치했는가?
3. **자연스러움**: 밈이 스토리 흐름에 자연스럽게 녹아드는가?
4. **재미**: 밈 본연의 유머/임팩트가 살아있는가?

## 밈 정보
- 밈 이름: {meme_name}

## 기업 정보
- 회사: {company_name}

## 시나리오 A
{scenario_a}

## 시나리오 B
{scenario_b}

## 응답 형식
반드시 다음 중 하나로만 응답하세요:
- "A" (시나리오 A가 더 나음)
- "B" (시나리오 B가 더 나음)
- "TIE" (비슷함)

응답:"""


@dataclass
class PairResult:
    meme_name: str
    company_name: str
    winner_idx: int  # 0 or 1 in original order, -1 for tie
    judgment: str  # "A", "B", "TIE" (after swap correction)


def extract_json_from_response(text: str) -> dict | None:
    """응답에서 JSON 추출"""
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

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


def extract_scenario_from_record(record: dict) -> dict | None:
    """레코드에서 시나리오 JSON 추출"""
    messages = record.get("messages", [])
    if len(messages) < 3:
        return None
    return extract_json_from_response(messages[2].get("content", ""))


def tier1_filter(record: dict) -> tuple[bool, str]:
    """Tier 1: rule-based 자동 필터링"""
    scenario = extract_scenario_from_record(record)
    if not scenario:
        return False, "json_parse_fail"

    # 스키마 필수 필드 체크
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        scene = scenario.get(key)
        if not scene or not isinstance(scene, dict):
            return False, f"missing_{key}"
        if not scene.get("dialogue"):
            return False, f"{key}_no_dialogue"

    # 감정 태그 체크: 모든 dialogue에 (감정) 패턴
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        dialogue = scenario[key].get("dialogue", "")
        if not re.search(r'\([^)]+\)', dialogue):
            return False, f"{key}_no_emotion_tag"

    # 대사 길이 체크 (감정 태그 제외 5~50자)
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        dialogue = scenario[key].get("dialogue", "")
        clean = re.sub(r'\([^)]+\)\s*', '', dialogue)
        if len(clean) < 5 or len(clean) > 50:
            return False, f"{key}_dialogue_len_{len(clean)}"

    # 한국어 비율 ≥ 30%
    all_text = " ".join(
        scenario[f"scene{i}"].get("dialogue", "") + scenario[f"scene{i}"].get("action", "")
        for i in range(1, 5)
    )
    korean_chars = sum(1 for c in all_text if '\uac00' <= c <= '\ud7a3')
    if len(all_text) > 0 and korean_chars / len(all_text) < 0.3:
        return False, "korean_ratio_low"

    return True, "ok"


def call_pairwise_judge(
    client: OpenAI,
    meme_name: str,
    company_name: str,
    scenario_a: dict,
    scenario_b: dict,
    max_retries: int = 3,
) -> str:
    """GPT-4o-mini pairwise 비교. Position bias 제거를 위해 50% 확률로 swap."""
    swap = random.random() < 0.5

    if swap:
        a_json, b_json = scenario_b, scenario_a
    else:
        a_json, b_json = scenario_a, scenario_b

    prompt = PAIRWISE_JUDGE_PROMPT.format(
        meme_name=meme_name,
        company_name=company_name,
        scenario_a=json.dumps(a_json, ensure_ascii=False, indent=2),
        scenario_b=json.dumps(b_json, ensure_ascii=False, indent=2),
    )

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=10,
            )
            result = response.choices[0].message.content.strip().upper()

            if "A" in result and "B" not in result:
                return "B" if swap else "A"
            elif "B" in result and "A" not in result:
                return "A" if swap else "B"
            return "TIE"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [Error] Judge call failed: {e}")
                return "TIE"  # 에러 시 둘 다 보존


def group_by_combination(records: list[dict]) -> dict[tuple[str, str], list[tuple[int, dict]]]:
    """(밈이름, 기업이름) 조합으로 그룹핑"""
    groups = defaultdict(list)
    for idx, record in enumerate(records):
        metadata = record.get("metadata", {})
        key = (metadata.get("meme_name", "unknown"), metadata.get("company_name", "unknown"))
        groups[key].append((idx, record))
    return groups


def curate_file(
    client: OpenAI,
    file_path: Path,
    resume: bool = True,
    dry_run: bool = False,
) -> dict:
    """파일 큐레이션: Tier 1 필터링 → Tier 2 pairwise"""
    # 레코드 로드
    records = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    records.append(None)

    stats = {
        "total": len(records),
        "tier1_pass": 0, "tier1_fail": 0,
        "pairwise_compared": 0, "winners": 0, "ties": 0,
        "final_count": 0,
        "tier1_reasons": defaultdict(int),
    }

    if dry_run:
        print(f"\n[Dry run] {file_path.name}: {len(records)} records")
        return stats

    # Tier 1: rule-based 필터링
    print(f"\n[Tier 1] Rule-based filtering...")
    tier1_passed = []

    for idx, record in enumerate(records):
        if record is None:
            stats["tier1_fail"] += 1
            stats["tier1_reasons"]["parse_error"] += 1
            continue

        passed, reason = tier1_filter(record)
        if passed:
            tier1_passed.append(record)
            stats["tier1_pass"] += 1
        else:
            stats["tier1_fail"] += 1
            stats["tier1_reasons"][reason] += 1

    print(f"  Tier 1: {stats['tier1_pass']}/{stats['total']} passed")
    for reason, count in sorted(stats["tier1_reasons"].items(), key=lambda x: -x[1])[:5]:
        print(f"    - {reason}: {count}")

    # Tier 2: pairwise 큐레이션
    print(f"\n[Tier 2] Pairwise comparison...")
    groups = group_by_combination(tier1_passed)

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    curated_path = CURATED_DIR / file_path.name
    rejected_path = REJECTED_DIR / file_path.name

    winners = []
    losers = []

    # 조합별로 pair 비교
    pair_items = [(key, group) for key, group in groups.items() if len(group) >= 2]
    singles = [group[0][1] for key, group in groups.items() if len(group) == 1]

    pbar = tqdm(pair_items, desc="Pairwise comparing")
    for (meme_name, company_name), group in pbar:
        # 그룹 내에서 랜덤 2개씩 페어링하여 토너먼트
        random.shuffle(group)
        surviving = [record for _, record in group]

        while len(surviving) > 1:
            next_round = []
            for i in range(0, len(surviving) - 1, 2):
                a, b = surviving[i], surviving[i + 1]
                scenario_a = extract_scenario_from_record(a)
                scenario_b = extract_scenario_from_record(b)

                if not scenario_a or not scenario_b:
                    next_round.append(a if scenario_a else b)
                    continue

                judgment = call_pairwise_judge(
                    client, meme_name, company_name, scenario_a, scenario_b,
                )
                stats["pairwise_compared"] += 1

                if judgment == "A":
                    next_round.append(a)
                    losers.append(b)
                    stats["winners"] += 1
                elif judgment == "B":
                    next_round.append(b)
                    losers.append(a)
                    stats["winners"] += 1
                else:
                    # TIE: 둘 다 보존
                    next_round.append(a)
                    next_round.append(b)
                    stats["ties"] += 1

            # 홀수면 마지막 하나는 자동 통과
            if len(surviving) % 2 == 1:
                next_round.append(surviving[-1])

            surviving = next_round

        winners.extend(surviving)
        pbar.set_postfix({"winners": len(winners), "compared": stats["pairwise_compared"]})

    # 단독 조합은 그대로 통과
    winners.extend(singles)

    stats["final_count"] = len(winners)

    # 저장
    with open(curated_path, "w") as f:
        for record in winners:
            record["curation"] = {
                "method": "pairwise",
                "curated_at": datetime.now().isoformat(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    with open(rejected_path, "w") as f:
        for record in losers:
            record["curation"] = {
                "method": "pairwise",
                "result": "loser",
                "curated_at": datetime.now().isoformat(),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return stats


def print_report(stats: dict, file_path: Path):
    """큐레이션 결과 리포트"""
    print("\n" + "=" * 60)
    print("PAIRWISE CURATION REPORT")
    print("=" * 60)
    print(f"File: {file_path.name}")
    print(f"Total records: {stats['total']}")
    print(f"\n[Tier 1 - Rule-based]")
    print(f"  Passed: {stats['tier1_pass']} ({stats['tier1_pass']/max(stats['total'],1)*100:.1f}%)")
    print(f"  Failed: {stats['tier1_fail']}")
    print(f"\n[Tier 2 - Pairwise]")
    print(f"  Pairs compared: {stats['pairwise_compared']}")
    print(f"  Clear winners: {stats['winners']}")
    print(f"  Ties (both kept): {stats['ties']}")
    print(f"\n[Final]")
    print(f"  Curated: {stats['final_count']} ({stats['final_count']/max(stats['total'],1)*100:.1f}% of total)")
    print("=" * 60)


def estimate_cost(file_path: Path) -> float:
    """비용 추정 (GPT-4o-mini pairwise)"""
    count = 0
    with open(file_path) as f:
        for line in f:
            if line.strip():
                count += 1
    # 대략 count/2 쌍 비교, 입력 ~2000 tokens, 출력 ~10 tokens
    pairs = count // 2
    input_cost = pairs * 2000 / 1_000_000 * 0.15
    output_cost = pairs * 10 / 1_000_000 * 0.60
    return input_cost + output_cost


def main():
    parser = argparse.ArgumentParser(description="Curate fine-tuning data with pairwise comparison")
    parser.add_argument("--path", type=str, help="Path to JSONL file")
    parser.add_argument("--raw", action="store_true", help="Curate all files in raw/")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from progress")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--estimate-cost", action="store_true", help="Estimate cost only")

    args = parser.parse_args()

    # 파일 경로 결정
    if args.path:
        files = [Path(args.path)]
    elif args.raw:
        files = list(RAW_DIR.glob("*.jsonl"))
    else:
        print("Specify --path or --raw")
        sys.exit(1)

    if not files:
        print("No JSONL files found")
        sys.exit(1)

    # 비용 추정
    if args.estimate_cost:
        total_cost = 0
        for f in files:
            cost = estimate_cost(f)
            print(f"{f.name}: ${cost:.4f}")
            total_cost += cost
        print(f"\nTotal estimated cost: ${total_cost:.4f}")
        sys.exit(0)

    # 클라이언트 초기화
    if not args.dry_run:
        client = OpenAI(api_key=config.openai_api_key)
    else:
        client = None

    # 큐레이션 실행
    for file_path in files:
        print(f"\n[Curating] {file_path}")
        stats = curate_file(
            client,
            file_path,
            resume=not args.no_resume,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            print_report(stats, file_path)

    if not args.dry_run:
        print(f"\nCurated files saved to: {CURATED_DIR}")
        print(f"Rejected files saved to: {REJECTED_DIR}")


if __name__ == "__main__":
    main()
