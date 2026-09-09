-- ===============================
-- Database & Schema
-- ===============================

-- (※ createdb memedb 는 psql 밖에서 실행)
-- createdb memedb

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS memedb;

-- ===============================
-- meme 테이블
-- ===============================
CREATE TABLE IF NOT EXISTS memedb.meme (
    meme_id BIGINT PRIMARY KEY,
    meme_name VARCHAR(255) NOT NULL,
    meme_definition TEXT,
    meme_origin TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_processed_v BOOLEAN DEFAULT FALSE,
    is_processed_a BOOLEAN DEFAULT FALSE
);

-- ===============================
-- static_post 테이블
-- ===============================
CREATE TABLE IF NOT EXISTS memedb.static_post (
    post_id BIGINT PRIMARY KEY,
    meme_id BIGINT NOT NULL,
    post_title VARCHAR(255),
    post_url TEXT,
    meme_usage TEXT,

    CONSTRAINT fk_static_post_meme
        FOREIGN KEY (meme_id)
        REFERENCES memedb.meme (meme_id)
        ON DELETE CASCADE
);

-- ===============================
-- youtube 테이블
-- ===============================
CREATE TABLE IF NOT EXISTS memedb.youtube (
    video_id VARCHAR(20) PRIMARY KEY,
    meme_id BIGINT NOT NULL,
    video_title VARCHAR(255),
    youtube_url TEXT,

    CONSTRAINT fk_youtube_meme
        FOREIGN KEY (meme_id)
        REFERENCES memedb.meme (meme_id)
        ON DELETE CASCADE
);

-- ===============================
-- video 테이블 (영상 분석 메타데이터)
-- ===============================
CREATE TABLE IF NOT EXISTS memedb.video (
    video_id VARCHAR(20) PRIMARY KEY,
    time_stamp VARCHAR(50),
    video_description TEXT,

    CONSTRAINT fk_video_youtube
        FOREIGN KEY (video_id)
        REFERENCES memedb.youtube (video_id)
        ON DELETE CASCADE
);

-- ===============================
-- audio 테이블 (오디오 분석 결과)
-- ===============================
CREATE TABLE IF NOT EXISTS memedb.audio (
    video_id VARCHAR(20) PRIMARY KEY,
    audio_json JSONB,      -- 음성 분석 결과(JSON)

    CONSTRAINT fk_audio_youtube
        FOREIGN KEY (video_id)
        REFERENCES memedb.youtube (video_id)
        ON DELETE CASCADE
);