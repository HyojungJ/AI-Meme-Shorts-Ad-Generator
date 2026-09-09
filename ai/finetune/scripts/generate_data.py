"""
학습 데이터 생성 스크립트

GPT-4o를 Teacher 모델로 사용하여 CoT + Scenario 학습 데이터 생성

사전 요구사항 (--save-db 사용 시):
    uv run python finetune/scripts/seed_finetune_data.py
"""

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from pydantic import ValidationError
from tqdm import tqdm

# Add parent paths for imports
# AI-finetune/ → common, finetune 패키지
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# AI/ → content_pipeline 패키지 (프로덕션 스키마 사용)
_ai_root = Path(__file__).parent.parent.parent.parent / "AI"
if _ai_root.exists():
    sys.path.insert(0, str(_ai_root))

from common.config import config
from common.db import MemeRepository, MemeExampleRepository, get_connection
from finetune.scripts.company_templates import COMPANY_TEMPLATES
from finetune.scripts.instruction_variants import (
    SYSTEM_PROMPT,
    format_user_prompt,
)


# 파인튜닝용 계정 이메일
FINETUNE_ACCOUNT_EMAIL = "finetune@meme-fluencer.ai"


# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
SEEDS_DIR = DATA_DIR / "seeds"
PROGRESS_FILE = RAW_DIR / ".progress.json"


def load_memes_from_db(status: str = "PROCESSED", exclude_high_risk: bool = True) -> list[dict]:
    """DB에서 밈 목록 로드 (high risk 밈 제외)"""
    with get_connection() as conn:
        meme_repo = MemeRepository(conn)
        example_repo = MemeExampleRepository(conn)

        with conn.cursor() as cur:
            if exclude_high_risk:
                cur.execute(
                    "SELECT meme_id, meme_name, definition, key_phrase FROM memes WHERE status = %s AND risk_info != 'high'",
                    (status,)
                )
            else:
                cur.execute(
                    "SELECT meme_id, meme_name, definition, key_phrase FROM memes WHERE status = %s",
                    (status,)
                )
            rows = cur.fetchall()

        memes = []
        for row in rows:
            meme_id, meme_name, definition, key_phrase = row
            examples = example_repo.get_by_meme(meme_id)
            memes.append({
                "meme_id": meme_id,
                "meme_name": meme_name,
                "definition": definition,
                "key_phrase": key_phrase,
                "examples": examples,
            })

        return memes


def generate_combinations(
    memes: list[dict],
    samples_per_meme: int = 20,
) -> list[dict]:
    """밈 × 기업 조합 생성 (중복 방지)"""
    combinations = []
    seen = set()

    for meme in memes:
        meme_combinations = 0
        max_attempts = samples_per_meme * 10
        attempts = 0

        while meme_combinations < samples_per_meme and attempts < max_attempts:
            attempts += 1
            company = random.choice(COMPANY_TEMPLATES)

            # 중복 체크: (밈이름, 기업이름)
            key = (meme["meme_name"], company["company_name"])
            if key in seen:
                continue

            seen.add(key)
            combinations.append({
                "meme": meme,
                "company": company,
            })
            meme_combinations += 1

        if meme_combinations < samples_per_meme:
            print(f"  [Warning] {meme['meme_name']}: only {meme_combinations}/{samples_per_meme} unique combinations")

    random.shuffle(combinations)
    return combinations


def format_meme_examples(examples: list[dict]) -> str:
    """밈 예시를 프로덕션 형식으로 포맷 (MEME_EXAMPLE_TEMPLATE_V1)"""
    if not examples:
        return "예시 없음"

    lines = []
    for i, ex in enumerate(examples[:3], 1):  # 최대 3개
        # 프로덕션 템플릿과 동일한 형식
        lines.append(f"\n## 활용 예시 {i}")
        lines.append(f"- 사용 맥락: {ex.get('situation', '정보 없음')}")
        lines.append(f"- 사용 예시: {ex.get('dialogue_example', '정보 없음')}")
        lines.append(f"- 예시 분류: {ex.get('example_type', 'good')}")
        lines.append(f"- 예시 분류가 bad일 경우 사유: {ex.get('note', 'N/A')}")
        lines.append(f"- 예시 톤: {ex.get('tone', 'neutral')}")

    return "\n".join(lines)


SEEDS_FILE = SEEDS_DIR / "seeds_v2.jsonl"


def load_seeds() -> list[dict]:
    """seeds_final_structured.jsonl에서 few-shot 예시 로드"""
    seeds = []
    if not SEEDS_FILE.exists():
        print(f"  [Warning] Seeds file not found: {SEEDS_FILE}")
        return seeds

    with open(SEEDS_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    seeds.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return seeds


def format_few_shot_examples(seeds: list[dict], n: int = 2) -> str:
    """seed에서 n개를 랜덤 샘플링하여 few-shot 프롬프트 구성"""
    if not seeds or n <= 0:
        return ""

    sampled = random.sample(seeds, min(n, len(seeds)))
    parts = ["\n\n---\n## 참고: 좋은 시나리오 예시\n아래는 밈을 자연스럽게 활용한 우수 시나리오 예시입니다.\n"]

    for i, seed in enumerate(sampled, 1):
        metadata = seed.get("metadata", {})
        messages = seed.get("messages", [])
        assistant_msg = messages[2]["content"] if len(messages) > 2 else ""

        # assistant 응답에서 scenario 추출
        scenario_json = extract_scenario_from_response(assistant_msg)
        if not scenario_json:
            continue

        parts.append(f"\n### 예시 {i}: {metadata.get('meme_name', '?')} × {metadata.get('company_name', '?')}")
        parts.append(f"```json\n{json.dumps(scenario_json, ensure_ascii=False, indent=2)}\n```")

    return "\n".join(parts) if len(parts) > 1 else ""


def _build_structured_schema() -> dict:
    """structured output용 JSON 스키마 (thinking + scenario).

    OpenAI strict mode 요구사항:
    - $ref/$defs 불가 → 인라인
    - 모든 object에 additionalProperties: false
    """
    scene_schema = {
        "type": "object",
        "properties": {
            "scene_type": {"type": "string", "enum": ["hook", "body", "close"]},
            "dialogue": {"type": "string"},
            "action": {"type": "string"},
            "visual_description": {"type": "string"},
        },
        "required": ["scene_type", "dialogue", "action", "visual_description"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "thinking": {"type": "string"},
            "scenario": {
                "type": "object",
                "properties": {
                    "scene1": scene_schema,
                    "scene2": scene_schema,
                    "scene3": scene_schema,
                    "scene4": scene_schema,
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["scene1", "scene2", "scene3", "scene4", "title", "description", "hashtags"],
                "additionalProperties": False,
            },
        },
        "required": ["thinking", "scenario"],
        "additionalProperties": False,
    }


def call_gpt4o(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_retries: int = 3,
) -> str | None:
    """GPT-4o 호출 with structured output (thinking + scenario JSON)"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=2000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "scenario_with_thinking",
                        "schema": _build_structured_schema(),
                        "strict": True,
                    },
                },
            )
            return response.choices[0].message.content
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [Error] GPT-4o call failed: {e}")
                return None


def extract_scenario_from_response(response: str) -> dict | None:
    """structured output 응답에서 scenario 추출.

    {"thinking": "...", "scenario": {...}} → scenario dict 반환.
    """
    try:
        parsed = json.loads(response)
        if "scenario" in parsed:
            return parsed["scenario"]
        # 레거시: scenario 키 없이 scene1이 바로 있는 경우
        if "scene1" in parsed:
            return parsed
        return None
    except json.JSONDecodeError:
        return None


def validate_scenario_quality(scenario_json: dict) -> tuple[bool, str]:
    """시나리오 품질 기본 검증"""
    from content_pipeline.scenario.scenario_schemas import Scenario

    # 1. Pydantic 스키마 검증
    try:
        Scenario(**scenario_json)
    except ValidationError as e:
        return False, f"schema: {e}"

    # 2. 대사 길이 검증 (감정 태그 제외)
    # scene4(CTA)는 상품명 포함으로 길어지므로 35자 허용
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        scene = scenario_json.get(key, {})
        dialogue = scene.get("dialogue", "")
        clean = re.sub(r'\([^)]+\)\s*', '', dialogue)
        max_len = 35 if key == "scene4" else 25
        if len(clean) < 5 or len(clean) > max_len:
            return False, f"{key} dialogue length: {len(clean)}"

    # 3. 한국어 비율 체크
    all_text = " ".join(
        s.get("dialogue", "") + s.get("action", "")
        for s in [scenario_json.get(f"scene{i}", {}) for i in range(1, 5)]
    )
    korean_chars = sum(1 for c in all_text if '\uac00' <= c <= '\ud7a3')
    if len(all_text) > 0 and korean_chars / len(all_text) < 0.3:
        return False, "korean ratio too low"

    return True, "ok"


def load_progress() -> dict:
    """진행 상황 로드"""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"completed": [], "last_index": 0}


def save_progress(progress: dict):
    """진행 상황 저장"""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def get_finetune_account_id() -> int | None:
    """파인튜닝용 계정 ID 조회"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT account_id FROM accounts WHERE email = %s",
                (FINETUNE_ACCOUNT_EMAIL,)
            )
            row = cur.fetchone()
            return row[0] if row else None


def get_company_and_character_ids(company_name: str) -> tuple[int, int] | None:
    """회사명으로 company_id, character_id 조회"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.company_id, cc.character_id
                FROM companies c
                JOIN company_characters cc ON c.company_id = cc.company_id
                WHERE c.company_name = %s
                LIMIT 1
            """, (company_name,))
            row = cur.fetchone()
            return row if row else None


def get_or_create_ad_request(
    company_name: str,
    meme_id: int,
    item_name: str,
    item_category: str,
    item_description: str,
    account_id: int,
) -> int | None:
    """(회사, 밈) 조합의 ad_request 조회 또는 생성"""
    ids = get_company_and_character_ids(company_name)
    if not ids:
        return None

    company_id, character_id = ids

    with get_connection() as conn:
        with conn.cursor() as cur:
            # 기존 ad_request 조회
            cur.execute("""
                SELECT ad_id FROM ad_requests
                WHERE company_id = %s AND meme_id = %s AND item_name = %s
            """, (company_id, meme_id, item_name))
            row = cur.fetchone()

            if row:
                return row[0]

            # 없으면 생성
            cur.execute("""
                INSERT INTO ad_requests (
                    company_id, account_id, character_id,
                    item_name, item_category, item_description,
                    meme_id, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'finetune_data')
                RETURNING ad_id
            """, (
                company_id, account_id, character_id,
                item_name, item_category, item_description, meme_id
            ))
            ad_id = cur.fetchone()[0]
            conn.commit()
            return ad_id


def extract_thinking(response: str) -> str:
    """structured output에서 thinking 필드 추출"""
    try:
        parsed = json.loads(response)
        return parsed.get("thinking", "")
    except json.JSONDecodeError:
        return ""


def save_scenario_to_db(
    meme_id: int,
    ad_id: int,
    scenario_json: dict,
    system_prompt: str = "",
    user_prompt: str = "",
    full_response: str = "",
) -> int | None:
    """시나리오를 DB에 저장 (프롬프트 + CoT + JSON)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            scenes_obj = {
                "scene1": scenario_json.get("scene1", {}),
                "scene2": scenario_json.get("scene2", {}),
                "scene3": scenario_json.get("scene3", {}),
                "scene4": scenario_json.get("scene4", {}),
            }
            thinking = extract_thinking(full_response)

            cur.execute('''
                INSERT INTO scenario_scripts (
                    ad_id, meme_id, title, description, hashtags, scenes,
                    used_model, generation_type,
                    system_prompt, user_prompt, full_response, thinking
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING script_id
            ''', (
                ad_id,
                meme_id,
                scenario_json.get("title", ""),
                scenario_json.get("description", ""),
                scenario_json.get("hashtags", []),
                json.dumps(scenes_obj, ensure_ascii=False),
                "gpt-4o",
                "finetuning_data_v2",
                system_prompt,
                user_prompt,
                full_response,
                thinking or None,
            ))
            script_id = cur.fetchone()[0]
            conn.commit()
            return script_id


def generate_data(
    limit: int | None = None,
    samples_per_meme: int = 20,
    output_file: str | None = None,
    resume: bool = True,
    dry_run: bool = False,
    save_db: bool = False,
    few_shot: int = 2,
    temperature: float | None = None,
):
    """학습 데이터 생성 메인 함수"""
    # DB 저장 시 파인튜닝 계정 확인
    account_id = None
    if save_db:
        account_id = get_finetune_account_id()
        if account_id is None:
            print("[Error] 파인튜닝 계정이 없습니다. 먼저 seed 스크립트를 실행하세요:")
            print("  uv run python finetune/scripts/seed_finetune_data.py")
            return
        print(f"[DB] 파인튜닝 계정: {FINETUNE_ACCOUNT_EMAIL} (account_id: {account_id})")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Output file
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = RAW_DIR / f"scenarios_{timestamp}.jsonl"
    else:
        output_file = Path(output_file)

    print(f"[1/5] Loading memes from DB...")
    memes = load_memes_from_db()
    print(f"  Found {len(memes)} memes with PROCESSED status")

    if not memes:
        print("  [Warning] No memes found. Using sample data for testing.")
        memes = [
            {
                "meme_id": 0,
                "meme_name": "무야호",
                "definition": "기쁨이나 흥분을 표현할 때 쓰는 감탄사",
                "key_phrase": "무야호~!",
                "examples": [],
            }
        ]

    # Few-shot seeds 로드
    seeds = load_seeds() if few_shot > 0 else []
    if seeds:
        print(f"  Loaded {len(seeds)} seed examples for few-shot")
    elif few_shot > 0:
        print(f"  No seeds found in {SEEDS_DIR} (few-shot disabled)")

    print(f"\n[2/5] Generating combinations...")
    combinations = generate_combinations(memes, samples_per_meme)

    if limit:
        combinations = combinations[:limit]

    print(f"  Total combinations: {len(combinations)}")

    # Cost estimation
    est_input_tokens = len(combinations) * 1000
    est_output_tokens = len(combinations) * 800
    est_cost = (est_input_tokens / 1_000_000 * 5) + (est_output_tokens / 1_000_000 * 15)
    print(f"  Estimated cost: ${est_cost:.2f}")

    if dry_run:
        print("\n[Dry run] Showing first 3 combinations:")
        for i, combo in enumerate(combinations[:3]):
            print(f"\n--- Combination {i+1} ---")
            print(f"Meme: {combo['meme']['meme_name']}")
            print(f"Company: {combo['company']['company_name']}")
            print(f"Voice design: {combo['company']['voice_design_prompt']}")
        return

    # Resume support
    progress = load_progress() if resume else {"completed": [], "last_index": 0}
    start_index = progress["last_index"]

    if start_index > 0:
        print(f"\n[Resume] Starting from index {start_index}")

    print(f"\n[3/5] Initializing OpenAI client...")
    client = OpenAI(api_key=config.openai_api_key)

    print(f"\n[4/5] Generating scenarios...")
    generated = 0
    failed = 0

    # Use append mode for resume
    mode = "a" if resume and start_index > 0 else "w"

    with open(output_file, mode) as f:
        pbar = tqdm(
            enumerate(combinations[start_index:], start_index),
            total=len(combinations),
            initial=start_index,
            desc="Generating",
        )

        for idx, combo in pbar:
            meme = combo["meme"]
            company = combo["company"]

            # Format usage examples (프로덕션과 동일한 형식)
            usage_examples = format_meme_examples(meme.get("examples", []))

            # Format user prompt with random instruction variant
            user_prompt = format_user_prompt(
                meme_name=meme["meme_name"],
                definition=meme["definition"],
                key_phrase=meme["key_phrase"],
                company_name=company["company_name"],
                item_name=company["item_name"],
                item_category=company["item_category"],
                item_keymessage=company["item_keymessage"],
                voice_design_prompt=company["voice_design_prompt"],
                usage_examples=usage_examples,
            )

            # Few-shot 예시 추가
            few_shot_text = format_few_shot_examples(seeds, n=few_shot)
            if few_shot_text:
                user_prompt += few_shot_text

            # Temperature: 고정값 또는 0.7~0.9 랜덤 (다양성 유도)
            temp = temperature if temperature is not None else random.uniform(0.7, 0.9)

            # Call GPT-4o
            response = call_gpt4o(client, SYSTEM_PROMPT, user_prompt, temperature=temp)

            if response:
                # Validate JSON extraction
                scenario_json = extract_scenario_from_response(response)

                # 품질 필터링
                if scenario_json:
                    valid, reason = validate_scenario_quality(scenario_json)
                    if not valid:
                        failed += 1
                        pbar.set_postfix({"ok": generated, "fail": failed, "reason": reason[:20]})
                        progress["last_index"] = idx + 1
                        continue

                if scenario_json:
                    # Save in chat format
                    data = {
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": response},
                        ],
                        "metadata": {
                            "meme_id": meme["meme_id"],
                            "meme_name": meme["meme_name"],
                            "company_name": company["company_name"],
                            "voice_design_prompt": company["voice_design_prompt"],
                            "generated_at": datetime.now().isoformat(),
                        },
                    }

                    f.write(json.dumps(data, ensure_ascii=False) + "\n")

                    # DB 저장 (옵션)
                    if save_db and account_id:
                        ad_id = get_or_create_ad_request(
                            company_name=company["company_name"],
                            meme_id=meme["meme_id"],
                            item_name=company["item_name"],
                            item_category=company["item_category"],
                            item_description=company["item_keymessage"],
                            account_id=account_id,
                        )
                        if ad_id:
                            script_id = save_scenario_to_db(
                                meme_id=meme["meme_id"],
                                ad_id=ad_id,
                                scenario_json=scenario_json,
                                system_prompt=SYSTEM_PROMPT,
                                user_prompt=user_prompt,
                                full_response=response,
                            )
                            if script_id:
                                pbar.set_postfix({"ok": generated, "db": script_id})

                    generated += 1
                else:
                    failed += 1
                    pbar.set_postfix({"ok": generated, "fail": failed})
            else:
                failed += 1

            # Update progress
            progress["last_index"] = idx + 1
            if idx % 10 == 0:
                save_progress(progress)
                f.flush()

            pbar.set_postfix({"ok": generated, "fail": failed})

    # Final progress save
    save_progress(progress)

    print(f"\n[5/5] Complete!")
    print(f"  Generated: {generated}")
    print(f"  Failed: {failed}")
    print(f"  Output: {output_file}")

    # Actual cost estimation based on generated
    actual_cost = (generated * 1800 / 1_000_000 * 5) + (generated * 800 / 1_000_000 * 15)
    print(f"  Estimated actual cost: ${actual_cost:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Generate fine-tuning data")
    parser.add_argument("--limit", type=int, help="Limit number of samples")
    parser.add_argument("--samples-per-meme", type=int, default=20, help="Samples per meme")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--no-resume", action="store_true", help="Don't resume from progress")
    parser.add_argument("--dry-run", action="store_true", help="Show combinations without generating")
    parser.add_argument("--save-db", action="store_true", help="Save scenarios to DB (seed 먼저 실행 필요)")
    parser.add_argument("--few-shot", type=int, default=2, help="Number of few-shot seeds per generation (0=disable)")
    parser.add_argument("--temperature", type=float, default=None, help="Fixed temperature (default: random 0.7~0.9)")

    args = parser.parse_args()

    generate_data(
        limit=args.limit,
        samples_per_meme=args.samples_per_meme,
        output_file=args.output,
        resume=not args.no_resume,
        dry_run=args.dry_run,
        save_db=args.save_db,
        few_shot=args.few_shot,
        temperature=args.temperature,
    )


if __name__ == "__main__":
    main()
