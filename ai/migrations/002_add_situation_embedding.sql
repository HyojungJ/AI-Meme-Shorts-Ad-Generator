-- Add situation_embedding column to meme_examples
-- Model: dragonkue/BGE-m3-ko (1024 dimensions)

BEGIN;

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- situation 임베딩 컬럼 추가
ALTER TABLE meme_examples
    ADD COLUMN IF NOT EXISTS situation_embedding vector(1024);

-- 임베딩 벡터 검색용 인덱스 (cosine distance)
CREATE INDEX IF NOT EXISTS idx_meme_examples_situation_embedding
    ON meme_examples
    USING ivfflat (situation_embedding vector_cosine_ops)
    WITH (lists = 10);

COMMIT;
