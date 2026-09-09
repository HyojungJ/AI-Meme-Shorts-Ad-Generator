"""source_video가 비어있는 밈들에 영상 정보만 채우는 스크립트"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.db import get_connection
from meme_collector.deep_research.researchers.media import run_media_researcher


def get_empty_source_video_memes(limit: int = 100) -> list[dict]:
    """source_video가 비어있는 PROCESSED 밈 목록"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT meme_id, meme_name FROM memes
                WHERE status = 'PROCESSED'
                AND (source_video IS NULL OR source_video = '[]')
                ORDER BY meme_id
                LIMIT %s
            """, (limit,))
            return [{"meme_id": row[0], "meme_name": row[1]} for row in cur.fetchall()]


def update_source_video(meme_id: int, videos: list[dict]):
    """DB에 source_video 업데이트"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE memes
                SET source_video = %s, updated_at = CURRENT_TIMESTAMP
                WHERE meme_id = %s
            """, (json.dumps(videos[:5]), meme_id))
            conn.commit()


def main():
    memes = get_empty_source_video_memes(limit=100)

    if not memes:
        print("source_video가 비어있는 밈이 없습니다.")
        return

    print(f"처리할 밈: {len(memes)}개")
    print("=" * 60)

    success = 0
    fail = 0

    for i, meme in enumerate(memes, 1):
        meme_id = meme["meme_id"]
        meme_name = meme["meme_name"]

        print(f"[{i}/{len(memes)}] {meme_name}...", end=" ", flush=True)

        start = time.time()
        try:
            # MediaResearcher 실행 (state 최소 구성)
            state = {
                "meme_name": meme_name,
                "collected_info": {},
            }
            result = run_media_researcher(state)

            # youtube_videos 추출
            collected = result.get("collected_info", {})
            videos = collected.get("youtube_videos", [])

            if videos:
                update_source_video(meme_id, videos)
                elapsed = time.time() - start
                print(f"✓ {len(videos)}개 ({elapsed:.1f}s)")
                success += 1
            else:
                elapsed = time.time() - start
                print(f"✗ 영상 없음 ({elapsed:.1f}s)")
                fail += 1

        except Exception as e:
            elapsed = time.time() - start
            print(f"✗ 에러: {e} ({elapsed:.1f}s)")
            fail += 1

    print("=" * 60)
    print(f"완료! 성공: {success}, 실패: {fail}")


if __name__ == "__main__":
    main()
