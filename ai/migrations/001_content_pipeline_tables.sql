-- Content Pipeline DB Schema Migration
-- Phase 1: New tables creation
-- Phase 2: Existing tables extension
-- Phase 3: Data migration (if needed)

BEGIN;

-- ============================================
-- Phase 1: Create new tables
-- ============================================

-- 1. voice_generations: 씬별 TTS 오디오 저장
CREATE TABLE IF NOT EXISTS voice_generations (
    voice_gen_id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES company_characters(character_id),
    script_id INTEGER REFERENCES scenario_scripts(script_id),
    scene_key VARCHAR(50) NOT NULL,

    -- TTS 입력/출력
    text_content TEXT NOT NULL,
    text_hash VARCHAR(64),                   -- 중복 방지용 해시

    -- 저장 정보
    audio_url TEXT,                          -- S3 URL
    duration_seconds FLOAT,
    size_bytes BIGINT,

    -- 메타데이터
    settings_json JSONB DEFAULT '{}',        -- stability, similarity_boost 등
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 동일 캐릭터 + 동일 대사 = 재사용
    UNIQUE(character_id, text_hash)
);

CREATE INDEX IF NOT EXISTS idx_voice_gen_script ON voice_generations(script_id);
CREATE INDEX IF NOT EXISTS idx_voice_gen_character ON voice_generations(character_id);

-- 2. image_generations: 첫 씬용 합성 이미지 (캐릭터 + 제품)
CREATE TABLE IF NOT EXISTS image_generations (
    image_id SERIAL PRIMARY KEY,
    character_id INTEGER NOT NULL REFERENCES company_characters(character_id),
    script_id INTEGER NOT NULL REFERENCES scenario_scripts(script_id),

    -- 생성 정보
    prompt TEXT,
    model VARCHAR(50),

    -- 저장 정보
    image_url TEXT,                          -- S3 URL
    size_bytes BIGINT,

    -- 메타데이터 (product_image_url, 합성 파라미터 등)
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- script당 1개
    UNIQUE(script_id)
);

CREATE INDEX IF NOT EXISTS idx_image_gen_character ON image_generations(character_id);

-- 3. scene_videos: 씬별 생성 영상 (scene_assets 대체)
CREATE TABLE IF NOT EXISTS scene_videos (
    scene_video_id SERIAL PRIMARY KEY,
    script_id INTEGER NOT NULL REFERENCES scenario_scripts(script_id),
    scene_key VARCHAR(50) NOT NULL,

    -- 연결 (첫 씬만 image_id 존재)
    voice_gen_id INTEGER REFERENCES voice_generations(voice_gen_id),
    image_id INTEGER REFERENCES image_generations(image_id),

    -- 저장 정보
    video_url TEXT,                          -- S3 URL
    duration_seconds FLOAT,
    size_bytes BIGINT,

    -- 생성 정보
    generation_model VARCHAR(50),            -- Sora 등
    generation_cost NUMERIC(10,4),
    generation_metadata JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- script + scene_key 유니크
    UNIQUE(script_id, scene_key)
);

CREATE INDEX IF NOT EXISTS idx_scene_videos_script ON scene_videos(script_id);

-- ============================================
-- Phase 2: Extend existing tables
-- ============================================

-- 4. company_characters 확장: 캐릭터 생성 프롬프트 + voice_id 저장
ALTER TABLE company_characters
    DROP COLUMN IF EXISTS voice_url,
    ADD COLUMN IF NOT EXISTS image_prompt TEXT,
    ADD COLUMN IF NOT EXISTS image_model VARCHAR(50),
    ADD COLUMN IF NOT EXISTS elevenlabs_voice_id TEXT,
    ADD COLUMN IF NOT EXISTS voice_design_prompt TEXT,
    ADD COLUMN IF NOT EXISTS generation_metadata JSONB DEFAULT '{}';

-- 5. ad_requests 확장: 사용자 원본 입력 저장
ALTER TABLE ad_requests
    ADD COLUMN IF NOT EXISTS character_style_raw TEXT,
    ADD COLUMN IF NOT EXISTS notes TEXT;

-- 6. videos 확장: 시나리오-영상 1:1 관계 추적
ALTER TABLE videos
    ADD COLUMN IF NOT EXISTS script_id INTEGER REFERENCES scenario_scripts(script_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_videos_script ON videos(script_id) WHERE script_id IS NOT NULL;

COMMIT;
