"""
Meme Batch Collection Runner

나무위키 2025년 밈 목록을 파싱하여 배치 수집
- Rate Limit 관리
- 진행 상황 저장/재개
- 실패 시 재시도
"""

import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from meme_list_parser import get_2025_memes, get_memes_by_month, MemeEntry
from meme_agent_v5 import EnhancedMemeAgent
from meme_agent_v6 import MemeAgent as MemeAgentV6


class BatchRunner:
    """밈 배치 수집 러너"""

    def __init__(
        self,
        output_dir: str = "data/agent_output_v6",
        progress_file: str = "data/batch_progress.json",
        delay_between_memes: int = 30,  # 밈 간 딜레이 (초)
        max_retries: int = 3,
        version: str = "v6"  # v5 or v6
    ):
        self.output_dir = Path(output_dir)
        self.progress_file = Path(progress_file)
        self.delay = delay_between_memes
        self.max_retries = max_retries
        self.version = version

        # 버전에 따라 에이전트 선택
        if version == "v6":
            self.agent = MemeAgentV6()
        else:
            self.agent = EnhancedMemeAgent()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

    def load_progress(self) -> dict:
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "completed": [],  # 완료된 밈 이름
            "failed": [],     # 실패한 밈 이름
            "last_updated": None
        }

    def save_progress(self, progress: dict):
        """진행 상황 저장"""
        progress["last_updated"] = datetime.now().isoformat()
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def collect_meme(self, entry: MemeEntry, verbose: bool = True) -> Optional[dict]:
        """단일 밈 수집 (재시도 포함)"""
        for attempt in range(self.max_retries):
            try:
                result = self.agent.collect(
                    meme_name=entry.name,
                    parent=entry.parent or "",
                    verbose=verbose
                )
                self.agent.save_result(result, str(self.output_dir))
                return result

            except Exception as e:
                print(f"\n[Error] {entry.name} (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 60 * (attempt + 1)  # 점점 길게 대기
                    print(f"  Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

        return None

    def run(
        self,
        month: Optional[str] = None,
        limit: Optional[int] = None,
        resume: bool = True,
        verbose: bool = True
    ) -> dict:
        """
        배치 수집 실행

        Args:
            month: 특정 월만 수집 (예: "1월", "2월")
            limit: 최대 수집 개수 (테스트용)
            resume: 이전 진행 상황 이어서 수집
            verbose: 상세 로그 출력

        Returns:
            수집 결과 통계
        """
        print("\n" + "=" * 60)
        print("Meme Batch Collection Runner")
        print("=" * 60)

        # 밈 목록 가져오기
        print("\n[1/3] Fetching 2025 meme list from Namu Wiki...")
        all_entries = get_2025_memes()

        if month:
            entries = get_memes_by_month(all_entries, month)
            print(f"  Found {len(entries)} memes for {month}")
        else:
            entries = all_entries
            print(f"  Found {len(entries)} total memes")

        if limit:
            entries = entries[:limit]
            print(f"  Limited to first {limit} memes")

        # 진행 상황 확인
        progress = self.load_progress() if resume else {"completed": [], "failed": [], "last_updated": None}
        completed_names = set(progress["completed"])
        failed_names = set(progress["failed"])

        # 수집 대상 필터링
        pending = [e for e in entries if e.name not in completed_names]
        print(f"\n[2/3] Collection Status:")
        print(f"  - Already completed: {len(completed_names)}")
        print(f"  - Previously failed: {len(failed_names)}")
        print(f"  - Pending: {len(pending)}")

        if not pending:
            print("\n  All memes already collected!")
            return {
                "total": len(entries),
                "completed": len(completed_names),
                "failed": len(failed_names),
                "new_completed": 0,
                "new_failed": 0
            }

        # 수집 시작
        print(f"\n[3/3] Starting collection...")
        print(f"  Delay between memes: {self.delay}s")
        print("-" * 60)

        new_completed = 0
        new_failed = 0
        start_time = datetime.now()

        for i, entry in enumerate(pending):
            # 진행 상황 표시
            elapsed = (datetime.now() - start_time).total_seconds()
            avg_time = elapsed / (i + 1) if i > 0 else 0
            remaining = avg_time * (len(pending) - i - 1)

            parent_info = f" (← {entry.parent})" if entry.parent else ""
            print(f"\n[{i+1}/{len(pending)}] {entry.name}{parent_info}")
            print(f"  Month: {entry.month}")
            if i > 0:
                print(f"  ETA: {remaining/60:.1f} min remaining")

            # 수집
            result = self.collect_meme(entry, verbose=verbose)

            if result:
                progress["completed"].append(entry.name)
                new_completed += 1
                print(f"  ✓ Success: {result.get('type', 'unknown')}")
            else:
                progress["failed"].append(entry.name)
                new_failed += 1
                print(f"  ✗ Failed")

            # 진행 상황 저장
            self.save_progress(progress)

            # 다음 밈 전 딜레이 (마지막 밈 제외)
            if i < len(pending) - 1:
                print(f"  Waiting {self.delay}s before next meme...")
                time.sleep(self.delay)

        # 결과 요약
        total_time = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("Collection Complete!")
        print("=" * 60)
        print(f"  Total time: {total_time/60:.1f} minutes")
        print(f"  New completed: {new_completed}")
        print(f"  New failed: {new_failed}")
        print(f"  Total completed: {len(progress['completed'])}")
        print(f"  Total failed: {len(progress['failed'])}")

        return {
            "total": len(entries),
            "completed": len(progress["completed"]),
            "failed": len(progress["failed"]),
            "new_completed": new_completed,
            "new_failed": new_failed,
            "total_time_seconds": total_time
        }

    def retry_failed(self, verbose: bool = True) -> dict:
        """실패한 밈 재시도"""
        progress = self.load_progress()
        failed_names = progress["failed"]

        if not failed_names:
            print("No failed memes to retry.")
            return {"retried": 0, "success": 0, "still_failed": 0}

        print(f"\nRetrying {len(failed_names)} failed memes...")

        # 실패 목록에서 MemeEntry 재구성
        all_entries = get_2025_memes()
        entries_by_name = {e.name: e for e in all_entries}

        # failed 목록 초기화
        progress["failed"] = []
        self.save_progress(progress)

        success = 0
        still_failed = 0

        for name in failed_names:
            entry = entries_by_name.get(name)
            if not entry:
                print(f"  [Skip] {name} - not found in meme list")
                continue

            print(f"\n[Retry] {name}")
            result = self.collect_meme(entry, verbose=verbose)

            if result:
                progress["completed"].append(name)
                success += 1
                print(f"  ✓ Success")
            else:
                progress["failed"].append(name)
                still_failed += 1
                print(f"  ✗ Still failed")

            self.save_progress(progress)
            time.sleep(self.delay)

        return {"retried": len(failed_names), "success": success, "still_failed": still_failed}

    def status(self) -> dict:
        """현재 진행 상황 출력"""
        progress = self.load_progress()
        all_entries = get_2025_memes()

        print("\n" + "=" * 60)
        print("Batch Collection Status")
        print("=" * 60)
        print(f"  Last updated: {progress.get('last_updated', 'Never')}")
        print(f"  Total memes in 2025: {len(all_entries)}")
        print(f"  Completed: {len(progress['completed'])}")
        print(f"  Failed: {len(progress['failed'])}")
        print(f"  Pending: {len(all_entries) - len(progress['completed'])}")

        if progress["failed"]:
            print(f"\n  Failed memes:")
            for name in progress["failed"][:10]:
                print(f"    - {name}")
            if len(progress["failed"]) > 10:
                print(f"    ... and {len(progress['failed']) - 10} more")

        return progress


def main():
    parser = argparse.ArgumentParser(description="Meme Batch Collection Runner")
    parser.add_argument("command", choices=["run", "retry", "status"],
                       help="Command: run, retry, or status")
    parser.add_argument("--month", "-m", help="Collect specific month only (e.g., '1월')")
    parser.add_argument("--limit", "-l", type=int, help="Limit number of memes (for testing)")
    parser.add_argument("--delay", "-d", type=int, default=30, help="Delay between memes (seconds)")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore previous progress")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less verbose output")
    parser.add_argument("--output", "-o", default="data/agent_output_v6", help="Output directory")
    parser.add_argument("--version", "-v", choices=["v5", "v6"], default="v6",
                       help="Agent version (default: v6)")

    args = parser.parse_args()

    runner = BatchRunner(
        output_dir=args.output,
        delay_between_memes=args.delay,
        version=args.version
    )

    if args.command == "run":
        runner.run(
            month=args.month,
            limit=args.limit,
            resume=not args.no_resume,
            verbose=not args.quiet
        )
    elif args.command == "retry":
        runner.retry_failed(verbose=not args.quiet)
    elif args.command == "status":
        runner.status()


if __name__ == "__main__":
    main()
