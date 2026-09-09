"""
데이터 분할 스크립트

- 80/10/10 비율로 train/val/test 분할
- 밈별 stratified split (각 밈이 모든 split에 균등 분포)
"""

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
CURATED_DIR = DATA_DIR / "curated"
SPLITS_DIR = DATA_DIR / "splits"


def load_all_records(dir_path: Path) -> list[dict]:
    """디렉토리의 모든 JSONL 파일에서 레코드 로드"""
    records = []

    jsonl_files = list(dir_path.glob("*.jsonl"))
    if not jsonl_files:
        print(f"No JSONL files found in {dir_path}")
        return []

    for file_path in jsonl_files:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    return records


def stratified_split(
    records: list[dict],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> tuple[list[dict], list[dict], list[dict]]:
    """밈별 stratified split"""
    random.seed(seed)

    # Group by meme
    meme_groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        meme_name = record.get("metadata", {}).get("meme_name", "unknown")
        meme_groups[meme_name].append(record)

    train, val, test = [], [], []

    for meme_name, meme_records in meme_groups.items():
        random.shuffle(meme_records)

        n = len(meme_records)
        n_train = max(1, int(n * train_ratio))
        n_val = max(1, int(n * val_ratio)) if n > 2 else 0
        n_test = n - n_train - n_val

        # Ensure at least 1 in each split if we have enough data
        if n >= 3:
            n_train = max(1, n - 2)
            n_val = 1
            n_test = 1

            # Recalculate with actual ratios for larger groups
            if n >= 10:
                n_train = int(n * train_ratio)
                n_val = int(n * val_ratio)
                n_test = n - n_train - n_val

        train.extend(meme_records[:n_train])
        val.extend(meme_records[n_train:n_train + n_val])
        test.extend(meme_records[n_train + n_val:])

    # Shuffle final splits
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    return train, val, test


def save_split(records: list[dict], file_path: Path):
    """Split을 JSONL 파일로 저장"""
    with open(file_path, "w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def print_stats(train: list, val: list, test: list):
    """분할 통계 출력"""
    total = len(train) + len(val) + len(test)

    print("\n" + "=" * 60)
    print("SPLIT STATISTICS")
    print("=" * 60)
    print(f"Total records: {total}")
    print(f"Train: {len(train)} ({len(train)/total*100:.1f}%)")
    print(f"Val:   {len(val)} ({len(val)/total*100:.1f}%)")
    print(f"Test:  {len(test)} ({len(test)/total*100:.1f}%)")

    # Meme distribution per split
    def count_memes(records):
        from collections import Counter
        return Counter(r.get("metadata", {}).get("meme_name", "unknown") for r in records)

    train_memes = count_memes(train)
    val_memes = count_memes(val)
    test_memes = count_memes(test)

    all_memes = set(train_memes.keys()) | set(val_memes.keys()) | set(test_memes.keys())

    print(f"\nUnique memes: {len(all_memes)}")
    print(f"Memes in train: {len(train_memes)}")
    print(f"Memes in val: {len(val_memes)}")
    print(f"Memes in test: {len(test_memes)}")

    # Check coverage
    memes_in_all = set(train_memes.keys()) & set(val_memes.keys()) & set(test_memes.keys())
    print(f"Memes in all splits: {len(memes_in_all)}")

    # Tone distribution
    def count_tones(records):
        from collections import Counter
        return Counter(r.get("metadata", {}).get("tone", "unknown") for r in records)

    print("\nTone distribution:")
    train_tones = count_tones(train)
    for tone, count in train_tones.most_common():
        train_pct = count / len(train) * 100 if train else 0
        print(f"  {tone}: train {count} ({train_pct:.1f}%)")

    print("=" * 60)


def load_records_from_file(file_path: Path) -> list[dict]:
    """단일 JSONL 파일에서 레코드 로드"""
    records = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def main():
    parser = argparse.ArgumentParser(description="Prepare train/val/test splits")
    parser.add_argument("--source", type=str, default=str(CURATED_DIR), help="Source directory or JSONL file")
    parser.add_argument("--output", type=str, default=str(SPLITS_DIR), help="Output directory")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train ratio")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation ratio")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Test ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    source = Path(args.source)
    output_dir = Path(args.output)

    if not source.exists():
        print(f"Source not found: {source}")
        sys.exit(1)

    if source.is_file():
        print(f"Loading records from file: {source}...")
        records = load_records_from_file(source)
    else:
        print(f"Loading records from directory: {source}...")
        records = load_all_records(source)

    if not records:
        print("No records found")
        sys.exit(1)

    print(f"Loaded {len(records)} records")

    # Validate ratios
    if abs(args.train_ratio + args.val_ratio + args.test_ratio - 1.0) > 0.001:
        print("Error: Ratios must sum to 1.0")
        sys.exit(1)

    print(f"\nSplitting with ratios: train={args.train_ratio}, val={args.val_ratio}, test={args.test_ratio}")
    train, val, test = stratified_split(
        records,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    # Print statistics
    print_stats(train, val, test)

    # Save splits
    output_dir.mkdir(parents=True, exist_ok=True)

    save_split(train, output_dir / "train.jsonl")
    save_split(val, output_dir / "val.jsonl")
    save_split(test, output_dir / "test.jsonl")

    print(f"\nSaved splits to {output_dir}")
    print(f"  - train.jsonl: {len(train)} records")
    print(f"  - val.jsonl: {len(val)} records")
    print(f"  - test.jsonl: {len(test)} records")


if __name__ == "__main__":
    main()
