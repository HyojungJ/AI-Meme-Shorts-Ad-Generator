"""
제품 설명과 밈 situation 임베딩 간 유사도 비교 후 밈 정렬.

사전에 meme_examples.situation_embedding이 채워져 있어야 한다.
(embed_situations.py의 backfill_all 또는 embed_by_meme_id로 생성)
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


def sort_memes_by_similarity(
    item_description: str,
    top_n: int = 10,
) -> list[dict]:
    """제품 설명과 가장 유사한 밈을 정렬하여 반환.

    Args:
        item_description: 제품 설명 텍스트
        top_n: 반환할 밈 개수

    Returns:
        [{"meme_id", "meme_name", "situation", "example_id", "similarity"}, ...]
    """
    # 1. 제품 설명 임베딩
    model = _get_model()
    item_emb = model.encode([item_description], normalize_embeddings=True)[0]

    # 2. DB에서 임베딩이 있는 예시들 조회
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.meme_id, e.example_id, e.situation, m.meme_name,
                       e.situation_embedding
                FROM meme_examples e
                JOIN memes m ON e.meme_id = m.meme_id
                WHERE e.situation_embedding IS NOT NULL
            """)
            rows = cur.fetchall()

    if not rows:
        print("임베딩된 situation이 없습니다. embed_situations.py를 먼저 실행하세요.")
        return []

    # 3. 코사인 유사도 계산 (normalize 되어 있으므로 dot product)
    meme_ids = []
    example_ids = []
    situations = []
    meme_names = []
    embeddings = []

    for row in rows:
        meme_ids.append(row[0])
        example_ids.append(row[1])
        situations.append(row[2])
        meme_names.append(row[3])
        # pgvector는 문자열로 반환 → numpy 변환
        emb_str = row[4]
        if isinstance(emb_str, str):
            emb = np.fromstring(emb_str.strip("[]"), sep=",", dtype=np.float32)
        else:
            emb = np.array(emb_str, dtype=np.float32)
        embeddings.append(emb)

    sit_embs = np.stack(embeddings)
    sims = sit_embs @ item_emb  # dot product (normalized = cosine sim)

    # 4. 밈별 최고 유사도 example 추출
    best_per_meme = {}
    for i in range(len(rows)):
        mid = meme_ids[i]
        sim = float(sims[i])
        if mid not in best_per_meme or sim > best_per_meme[mid]["similarity"]:
            best_per_meme[mid] = {
                "meme_id": mid,
                "meme_name": meme_names[i],
                "example_id": example_ids[i],
                "situation": situations[i],
                "similarity": sim,
            }

    # 5. 유사도 내림차순 정렬
    sorted_memes = sorted(
        best_per_meme.values(),
        key=lambda x: x["similarity"],
        reverse=True,
    )

    return sorted_memes[:top_n]


if __name__ == "__main__":
    test_items = [
        "초경량 무선 블루투스 이어폰, 노이즈캔슬링 기능 탑재, 운동할 때 안 빠지는 이어폰",
        "유기농 수제 강아지 간식, 연어와 고구마로 만든 건강한 펫 트릿",
        "레트로 감성 필름 카메라, 감성 사진 찍기 좋은 빈티지 디자인",
    ]

    for item in test_items:
        print(f"\n{'='*60}")
        print(f"제품: {item}")
        print(f"{'='*60}")
        results = sort_memes_by_similarity(item, top_n=10)
        for rank, m in enumerate(results, 1):
            print(f"  {rank:>2}. [{m['similarity']:.4f}] {m['meme_name']:<20} | {m['situation']}")
