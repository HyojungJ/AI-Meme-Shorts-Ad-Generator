"""2026년 한국 밈만 수집하여 JSON으로 저장"""
import json
import logging
from datetime import datetime

from meme_collector.tools.namuwiki import fetch_meme_list
from meme_collector.agent import MemeAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    # 2026년 한국 밈만 가져오기
    memes = fetch_meme_list(year=2026, region="korea")
    log.info(f"2026년 한국 밈 {len(memes)}개 발견: {memes}")

    agent = MemeAgent()
    results = []

    for i, name in enumerate(memes, 1):
        log.info(f"[{i}/{len(memes)}] 수집 중: {name}")
        try:
            result = agent.process(name)
            score = result.get("verification", {}).get("score", 0)
            if result.get("meta", {}).get("success"):
                log.info(f"✓ {name} 완료 (점수: {score})")
            else:
                log.warning(f"✗ {name} 실패")
            results.append(result)
        except Exception as e:
            log.error(f"✗ {name} 오류: {e}")
            results.append({"meta": {"meme_name": name, "success": False}, "error": str(e)})

    # JSON 저장
    output_file = f"meme_2026_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    success = sum(1 for r in results if r.get("meta", {}).get("success"))
    log.info(f"=== 완료: {success}/{len(results)} 성공, 저장: {output_file} ===")

    return results


if __name__ == "__main__":
    main()
