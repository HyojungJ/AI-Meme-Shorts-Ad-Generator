"""
밈 예시(situation) 임베딩 생성 및 DB 저장.

- backfill_all(): 기존 전체 situation 임베딩 (최초 1회)
- embed_by_meme_id(): 특정 밈의 예시만 임베딩 (밈 수집 후 호출)
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from common.db import get_connection

MODEL_NAME = "dragonkue/BGE-m3-ko"

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _encode(texts: list[str]) -> np.ndarray:
    model = _get_model()
    return model.encode(texts, normalize_embeddings=True)


def _vector_to_pg(vec: np.ndarray) -> str:
    """numpy 벡터를 pgvector 문자열로 변환."""
    return "[" + ",".join(str(float(v)) for v in vec) + "]"


def backfill_all(batch_size: int = 64) -> int:
    """기존 모든 situation 중 임베딩이 없는 것들을 일괄 임베딩.

    Returns:
        임베딩된 행 수
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT example_id, situation
                FROM meme_examples
                WHERE situation_embedding IS NULL
                  AND situation IS NOT NULL
                  AND situation != ''
                ORDER BY example_id
            """)
            rows = cur.fetchall()

        if not rows:
            print("임베딩할 situation이 없습니다.")
            return 0

        total = len(rows)
        print(f"총 {total}개 situation 임베딩 시작...")

        updated = 0
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            ids = [r[0] for r in batch]
            texts = [r[1] for r in batch]

            embeddings = _encode(texts)

            with conn.cursor() as cur:
                for example_id, emb in zip(ids, embeddings):
                    cur.execute(
                        "UPDATE meme_examples SET situation_embedding = %s WHERE example_id = %s",
                        (_vector_to_pg(emb), example_id),
                    )
            conn.commit()
            updated += len(batch)
            print(f"  {updated}/{total} 완료")

        print(f"임베딩 완료: {updated}개")
        return updated


def embed_by_meme_id(meme_id: int) -> int:
    """특정 밈의 예시들만 임베딩. 밈 수집 완료 후 호출.

    Returns:
        임베딩된 행 수
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT example_id, situation
                FROM meme_examples
                WHERE meme_id = %s
                  AND situation_embedding IS NULL
                  AND situation IS NOT NULL
                  AND situation != ''
                ORDER BY example_id
            """, (meme_id,))
            rows = cur.fetchall()

        if not rows:
            return 0

        ids = [r[0] for r in rows]
        texts = [r[1] for r in rows]

        embeddings = _encode(texts)

        with conn.cursor() as cur:
            for example_id, emb in zip(ids, embeddings):
                cur.execute(
                    "UPDATE meme_examples SET situation_embedding = %s WHERE example_id = %s",
                    (_vector_to_pg(emb), example_id),
                )
        conn.commit()
        print(f"meme_id={meme_id}: {len(rows)}개 situation 임베딩 완료")
        return len(rows)


if __name__ == "__main__":
    backfill_all()
