"""
밈 수집 스케줄러

사용법:
    # 새 밈 발견만 (DB에 이름만 저장)
    uv run python -m scripts.scheduler discover

    # 미처리 밈 수집 (정보 수집)
    uv run python -m scripts.scheduler collect --limit 5

    # 전체 실행 (발견 + 수집)
    uv run python -m scripts.scheduler run --limit 5

    # cron 예시 (매일 새벽 3시)
    0 3 * * * cd /path/to/AI && uv run python -m scripts.scheduler run --limit 10
"""
import argparse
import logging
from datetime import datetime

from common.db import get_connection, MemeRepository
from meme_collector.tools.namuwiki import fetch_meme_list
from meme_collector.agent import MemeAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def discover_new_memes(year: int = 2026) -> list[str]:
    """나무위키에서 새 밈을 발견하고 DB에 저장합니다."""
    log.info(f"나무위키에서 {year}년 밈 목록 크롤링 중...")
    all_memes = fetch_meme_list(year=year, region="korea")
    log.info(f"나무위키에서 {len(all_memes)}개 밈 발견")

    with get_connection() as conn:
        repo = MemeRepository(conn)
        existing = repo.get_all_names()
        log.info(f"DB에 {len(existing)}개 밈 존재")

        new_memes = [m for m in all_memes if m not in existing]
        log.info(f"새로운 밈 {len(new_memes)}개 발견")

        for name in new_memes:
            repo.insert_name_only(name)

    return new_memes


def collect_memes(limit: int = 5) -> list[dict]:
    """미처리 밈의 정보를 수집합니다."""
    with get_connection() as conn:
        repo = MemeRepository(conn)
        unprocessed = repo.get_unprocessed(limit)

    if not unprocessed:
        log.info("처리할 밈이 없습니다")
        return []

    log.info(f"{len(unprocessed)}개 밈 수집 시작")
    agent = MemeAgent()
    results = []

    for meme in unprocessed:
        name = meme["meme_name"]
        log.info(f"수집 중: {name}")

        try:
            result = agent.process(name)
            if result["meta"]["success"]:
                log.info(f"✓ {name} 수집 완료 (점수: {result['verification']['score']})")
            else:
                log.warning(f"✗ {name} 수집 실패")
            results.append(result)
        except Exception as e:
            log.error(f"✗ {name} 수집 중 오류: {e}")
            results.append({"meta": {"meme_name": name, "success": False}, "error": str(e)})

    return results


def run(limit: int = 5, year: int = 2026):
    """전체 스케줄러 실행: 발견 + 수집"""
    log.info(f"=== 밈 수집 스케줄러 시작 ({datetime.now()}) ===")

    # 1. 새 밈 발견
    new_memes = discover_new_memes(year=year)
    if new_memes:
        log.info(f"새 밈: {new_memes[:10]}{'...' if len(new_memes) > 10 else ''}")

    # 2. 미처리 밈 수집
    results = collect_memes(limit)

    # 3. 결과 요약
    success = sum(1 for r in results if r.get("meta", {}).get("success"))
    log.info(f"=== 완료: {success}/{len(results)} 성공 ===")

    return results


def main():
    parser = argparse.ArgumentParser(description="밈 수집 스케줄러")
    parser.add_argument("command", choices=["discover", "collect", "run"], help="실행할 명령")
    parser.add_argument("--limit", type=int, default=5, help="수집할 밈 개수")
    parser.add_argument("--year", type=int, default=2026, help="밈 연도 (기본값: 2026)")
    args = parser.parse_args()

    if args.command == "discover":
        new_memes = discover_new_memes(year=args.year)
        print(f"새 밈 {len(new_memes)}개 발견")
        for m in new_memes:
            print(f"  - {m}")
    elif args.command == "collect":
        results = collect_memes(args.limit)
        print(f"수집 완료: {len(results)}개")
    else:
        run(args.limit, year=args.year)


if __name__ == "__main__":
    main()
