"""
학습 데이터 검증 스크립트

- JSONL 파싱 검증
- Pydantic Scenario 스키마 검증
- 비즈니스 규칙 검증 (hook 1개, body 2개, duration 15-60초)
- 검증 실패 항목 리포트
"""

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from content_pipeline.scenario.scenario_schemas import Scenario, Scene, StructureType
from pydantic import ValidationError


DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
CURATED_DIR = DATA_DIR / "curated"


@dataclass
class ValidationResult:
    index: int
    file_path: str
    status: str  # "pass", "fail"
    errors: list[str]
    meme_name: str | None = None
    company_name: str | None = None


def extract_json_from_response(text: str) -> dict | None:
    """텍스트에서 JSON 추출"""
    # 방법 1: ```json 코드블록
    code_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # 방법 2: 중괄호 매칭
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


def validate_business_rules(scenario: dict) -> list[str]:
    """비즈니스 규칙 검증 (scene1-4 구조)"""
    errors = []

    # scene1-4 존재 확인
    expected_scenes = {
        "scene1": "hook",
        "scene2": "body",
        "scene3": "body",
        "scene4": "close",
    }

    for scene_key, expected_type in expected_scenes.items():
        if scene_key not in scenario:
            errors.append(f"Missing '{scene_key}' field")
        else:
            scene = scenario[scene_key]
            if not isinstance(scene, dict):
                errors.append(f"'{scene_key}' must be a dict")
            else:
                scene_type = scene.get("scene_type")
                if scene_type != expected_type:
                    errors.append(f"{scene_key}.scene_type must be '{expected_type}', got '{scene_type}'")

    # total_duration 확인 (12-20초)
    if "total_duration" in scenario:
        duration = scenario["total_duration"]
        if not isinstance(duration, (int, float)):
            errors.append(f"'total_duration' must be a number, got {type(duration).__name__}")
        elif not (12 <= duration <= 20):
            errors.append(f"'total_duration' must be 12-20s, got {duration}s")

    # title, description, hashtags 확인
    if "title" not in scenario:
        errors.append("Missing 'title' field")
    elif not scenario["title"] or not scenario["title"].strip():
        errors.append("'title' is empty")

    if "description" not in scenario:
        errors.append("Missing 'description' field")

    if "hashtags" not in scenario:
        errors.append("Missing 'hashtags' field")
    elif not isinstance(scenario["hashtags"], list):
        errors.append("'hashtags' must be a list")
    elif len(scenario["hashtags"]) < 3 or len(scenario["hashtags"]) > 5:
        errors.append(f"'hashtags' must have 3-5 items, got {len(scenario['hashtags'])}")

    # 각 씬의 dialogue 비어있지 않은지 확인
    for scene_key in ["scene1", "scene2", "scene3", "scene4"]:
        if scene_key in scenario and isinstance(scenario[scene_key], dict):
            dialogue = scenario[scene_key].get("dialogue", "")
            if not dialogue or not dialogue.strip():
                errors.append(f"{scene_key}.dialogue is empty")

    return errors


def validate_pydantic_schema(scenario: dict) -> list[str]:
    """Pydantic 스키마 검증"""
    try:
        Scenario(**scenario)
        return []
    except ValidationError as e:
        return [str(err) for err in e.errors()]


def validate_record(record: dict, index: int, file_path: str) -> ValidationResult:
    """단일 레코드 검증"""
    errors = []
    meme_name = None
    company_name = None

    # metadata 추출
    metadata = record.get("metadata", {})
    meme_name = metadata.get("meme_name")
    company_name = metadata.get("company_name")

    # messages 구조 확인
    messages = record.get("messages", [])
    if len(messages) != 3:
        errors.append(f"Expected 3 messages (system, user, assistant), got {len(messages)}")
        return ValidationResult(index, file_path, "fail", errors, meme_name, company_name)

    # assistant 메시지에서 JSON 추출
    assistant_msg = messages[2].get("content", "")
    scenario_json = extract_json_from_response(assistant_msg)

    if scenario_json is None:
        errors.append("Could not extract JSON from assistant response")
        return ValidationResult(index, file_path, "fail", errors, meme_name, company_name)

    # Pydantic 스키마 검증
    schema_errors = validate_pydantic_schema(scenario_json)
    if schema_errors:
        errors.extend([f"[Schema] {e}" for e in schema_errors])

    # 비즈니스 규칙 검증
    biz_errors = validate_business_rules(scenario_json)
    if biz_errors:
        errors.extend([f"[Business] {e}" for e in biz_errors])

    status = "pass" if not errors else "fail"
    return ValidationResult(index, file_path, status, errors, meme_name, company_name)


def validate_file(file_path: Path) -> list[ValidationResult]:
    """파일 전체 검증"""
    results = []

    with open(file_path) as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                results.append(ValidationResult(
                    idx, str(file_path), "fail",
                    [f"JSON parse error: {e}"]
                ))
                continue

            result = validate_record(record, idx, str(file_path))
            results.append(result)

    return results


def validate_directory(dir_path: Path) -> list[ValidationResult]:
    """디렉토리 내 모든 JSONL 파일 검증"""
    all_results = []

    jsonl_files = list(dir_path.glob("*.jsonl"))
    if not jsonl_files:
        print(f"No JSONL files found in {dir_path}")
        return []

    for file_path in jsonl_files:
        print(f"Validating {file_path.name}...")
        results = validate_file(file_path)
        all_results.extend(results)

    return all_results


def print_report(results: list[ValidationResult], verbose: bool = False):
    """검증 결과 리포트 출력"""
    total = len(results)
    passed = sum(1 for r in results if r.status == "pass")
    failed = total - passed

    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)
    print(f"Total records: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)" if total > 0 else "Passed: 0")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)" if total > 0 else "Failed: 0")

    if failed > 0:
        print("\n" + "-" * 60)
        print("ERROR SUMMARY")
        print("-" * 60)

        # Error type distribution
        error_counter = Counter()
        for r in results:
            if r.status == "fail":
                for err in r.errors:
                    # Normalize error messages
                    if "[Schema]" in err:
                        error_counter["Schema validation"] += 1
                    elif "[Business]" in err:
                        error_counter["Business rule"] += 1
                    elif "JSON parse" in err:
                        error_counter["JSON parse"] += 1
                    else:
                        error_counter[err[:50]] += 1

        for err_type, count in error_counter.most_common(10):
            print(f"  {err_type}: {count}")

        if verbose:
            print("\n" + "-" * 60)
            print("FAILED RECORDS (first 10)")
            print("-" * 60)

            failed_records = [r for r in results if r.status == "fail"][:10]
            for r in failed_records:
                print(f"\n[{r.index}] {r.file_path}")
                print(f"  Meme: {r.meme_name}, Company: {r.company_name}")
                for err in r.errors[:5]:
                    print(f"  - {err}")

    # Meme distribution
    meme_counter = Counter(r.meme_name for r in results if r.meme_name)
    if meme_counter:
        print("\n" + "-" * 60)
        print("MEME DISTRIBUTION (top 10)")
        print("-" * 60)
        for meme, count in meme_counter.most_common(10):
            print(f"  {meme}: {count}")

    print("\n" + "=" * 60)


def copy_valid_to_curated(results: list[ValidationResult]):
    """검증 통과 데이터를 curated 폴더로 복사"""
    CURATED_DIR.mkdir(parents=True, exist_ok=True)

    # Group by file
    file_records: dict[str, list[int]] = {}
    for r in results:
        if r.status == "pass":
            if r.file_path not in file_records:
                file_records[r.file_path] = []
            file_records[r.file_path].append(r.index)

    total_copied = 0
    for file_path, valid_indices in file_records.items():
        src_path = Path(file_path)
        dst_path = CURATED_DIR / src_path.name

        valid_set = set(valid_indices)
        with open(src_path) as src, open(dst_path, "w") as dst:
            for idx, line in enumerate(src):
                if idx in valid_set:
                    dst.write(line)
                    total_copied += 1

    print(f"\nCopied {total_copied} valid records to {CURATED_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Validate fine-tuning data")
    parser.add_argument("--path", type=str, help="Path to JSONL file or directory")
    parser.add_argument("--raw", action="store_true", help="Validate raw/ directory")
    parser.add_argument("--curated", action="store_true", help="Validate curated/ directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed errors")
    parser.add_argument("--copy-valid", action="store_true", help="Copy valid records to curated/")

    args = parser.parse_args()

    # Determine path
    if args.path:
        path = Path(args.path)
    elif args.curated:
        path = CURATED_DIR
    else:
        path = RAW_DIR

    if not path.exists():
        print(f"Path not found: {path}")
        sys.exit(1)

    # Validate
    if path.is_file():
        results = validate_file(path)
    else:
        results = validate_directory(path)

    if not results:
        print("No records to validate")
        sys.exit(0)

    # Print report
    print_report(results, verbose=args.verbose)

    # Copy valid records
    if args.copy_valid:
        copy_valid_to_curated(results)

    # Exit with error if any failed
    failed = sum(1 for r in results if r.status == "fail")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
