"""미처리 밈 일괄 처리 스크립트"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from datetime import datetime

from common.db import get_connection, MemeRepository
from meme_collector.agent import MemeAgent


def main():
    # 미처리 밈 가져오기
    with get_connection() as conn:
        repo = MemeRepository(conn)
        memes = repo.get_unprocessed(limit=50)

    if not memes:
        print("처리할 밈이 없습니다.")
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 처리할 밈: {len(memes)}개")
    print("=" * 60)

    agent = MemeAgent(use_postgres=False, enable_tracing=False)

    results = {"pass": 0, "retry": 0, "fail": 0, "error": 0}

    for i, meme in enumerate(memes, 1):
        name = meme["meme_name"]
        print(f"\n[{i}/{len(memes)}] {name} 처리 중...")
        sys.stdout.flush()

        start = time.time()
        try:
            result = agent.process(name)
            elapsed = time.time() - start

            success = result["meta"]["success"]
            score = result.get("verification", {}).get("score", 0)
            decision = result.get("verification", {}).get("decision", "N/A")
            errors = result.get("errors", [])

            if success:
                output = result.get("meme_output") or {}
                key_phrase = output.get("key_phrase") or "없음"
                meme_type = output.get("meme_type", "unknown")
                print(f"  ✓ {decision} (score={score}) - {elapsed:.1f}s")
                print(f"    type={meme_type}, key_phrase={key_phrase[:30]}")

                if decision == "PASS":
                    results["pass"] += 1
                else:
                    results["retry"] += 1
            else:
                print(f"  ✗ FAILED - {elapsed:.1f}s")
                for err in errors[:2]:
                    print(f"    {err[:80]}")
                results["fail"] += 1

        except Exception as e:
            elapsed = time.time() - start
            print(f"  ✗ ERROR: {e} - {elapsed:.1f}s")
            results["error"] += 1

        sys.stdout.flush()

    print("\n" + "=" * 60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 완료!")
    print(f"  PASS: {results['pass']}, FAIL: {results['fail']}, ERROR: {results['error']}")


if __name__ == "__main__":
    main()
