-- ============================================
-- 완전한 데이터베이스 스키마
-- 작성일: 2026-01-22
-- ============================================

-- ============================================
-- 기존 테이블 삭제 (역순으로)
-- ============================================

-- 트리거 삭제
DROP TRIGGER IF EXISTS trigger_check_client_account_type ON clients;
DROP TRIGGER IF EXISTS trigger_check_admin_account_type ON admins;
DROP TRIGGER IF EXISTS trigger_check_company_member_client_only ON company_members;

-- 함수 삭제
DROP FUNCTION IF EXISTS check_client_account_type();
DROP FUNCTION IF EXISTS check_admin_account_type();
DROP FUNCTION IF EXISTS check_company_member_client_only();

-- 테이블 삭제 (외래키 의존성 역순)
DROP TABLE IF EXISTS prompt_usage_logs CASCADE;
DROP TABLE IF EXISTS retry_queue CASCADE;
DROP TABLE IF EXISTS workflow_stages CASCADE;
DROP TABLE IF EXISTS workflow_execution CASCADE;
DROP TABLE IF EXISTS performance_metrics CASCADE;
DROP TABLE IF EXISTS admin_video_posts CASCADE;
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS scene_assets CASCADE;
DROP TABLE IF EXISTS scenario_scripts CASCADE;
DROP TABLE IF EXISTS prompt_versions CASCADE;
DROP TABLE IF EXISTS video_projects CASCADE;
DROP TABLE IF EXISTS company_characters CASCADE;
DROP TABLE IF EXISTS meme_examples CASCADE;
DROP TABLE IF EXISTS memes CASCADE;
DROP TABLE IF EXISTS admin_youtube_channels CASCADE;
DROP TABLE IF EXISTS company_members CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS admins CASCADE;
DROP TABLE IF EXISTS clients CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

-- ============================================
-- 1. 사용자 인증 및 권한
-- ============================================

-- 1-1. accounts (공통)
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('client', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 1-2. clients (클라이언트 - 일반 사용자)
CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    account_id INT UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP,
    reset_token TEXT,
    reset_expires_at TIMESTAMP,
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE
);

-- 1-3. admins
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    account_id INT UNIQUE NOT NULL,
    oauth_provider VARCHAR(50) NOT NULL,
    oauth_provider_id VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP,
    last_login_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE,
    
    UNIQUE(oauth_provider, oauth_provider_id)
);

-- 1-4. companies
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 1-5. company_members
CREATE TABLE company_members (
    member_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    account_id INT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'member')),
    member_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_company
        FOREIGN KEY(company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_account
        FOREIGN KEY(account_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_company_members_company ON company_members(company_id);
CREATE INDEX idx_company_members_account ON company_members(account_id);

-- 한 회사당 주 담당자는 1명만 (부분 유니크 인덱스)
CREATE UNIQUE INDEX idx_company_members_primary_unique 
    ON company_members(company_id) 
    WHERE is_primary = TRUE;

-- 1-6. admin_youtube_channels
CREATE TABLE admin_youtube_channels (
    channel_id SERIAL PRIMARY KEY,
    admin_id INT UNIQUE NOT NULL,
    yt_channel_id VARCHAR(255) UNIQUE NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    channel_handle VARCHAR(255),
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_admin_profile
        FOREIGN KEY (admin_id)
        REFERENCES admins(admin_id)
        ON DELETE CASCADE
);

-- ============================================
-- 2. 콘텐츠 생성
-- ============================================

-- 2-1. memes
CREATE TABLE memes (
    meme_id BIGSERIAL PRIMARY KEY,
    meme_name VARCHAR(255) NOT NULL UNIQUE,
    definition TEXT,
    origin JSONB,
    key_phrase TEXT,
    sources JSONB DEFAULT '[]',
    risk_info VARCHAR(20),
    meme_type VARCHAR(50) CHECK (meme_type IN ('Dialogue', 'Motion', 'Hybrid')),
    status VARCHAR(50) DEFAULT 'READY' CHECK (status IN ('READY', 'PROCESSING', 'COMPLETED', 'FAILED')),
    source_video JSONB DEFAULT '{}',
    video_analysis JSONB DEFAULT '{}',
    confidence FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_memes_status ON memes(status);
CREATE INDEX idx_memes_name ON memes(meme_name);
CREATE INDEX idx_memes_origin_gin ON memes USING GIN (origin);

-- 2-2. meme_examples
CREATE TABLE meme_examples (
    example_id SERIAL PRIMARY KEY,
    meme_id BIGINT NOT NULL,
    situation VARCHAR(255) NOT NULL,
    dialogue_example TEXT,
    source_url VARCHAR(500),
    example_type VARCHAR(20),
    note TEXT,
    tone VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_meme_example
        FOREIGN KEY (meme_id)
        REFERENCES memes(meme_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_meme_examples_meme_id ON meme_examples(meme_id);
CREATE INDEX idx_meme_examples_type ON meme_examples(example_type);

-- 2-3. company_characters
CREATE TABLE company_characters (
    character_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    character_name VARCHAR(255) NOT NULL,
    character_mood VARCHAR(255) NOT NULL,
    character_style VARCHAR(255) NOT NULL,
    voice_tone VARCHAR(255) NOT NULL,
    image_url TEXT NOT NULL,
    voice_url TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    approval_status VARCHAR(20) DEFAULT 'approved' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_company_char
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_company_characters_company ON company_characters(company_id);
CREATE INDEX idx_company_characters_active ON company_characters(is_active);
CREATE INDEX idx_company_characters_approval ON company_characters(approval_status);

-- 2-4. video_projects
CREATE TABLE video_projects (
    project_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    user_id INT NOT NULL,
    character_id INT,
    
    -- 제품 정보
    item_name VARCHAR(255) NOT NULL,
    item_category VARCHAR(100),
    item_highlight TEXT,
    item_url VARCHAR(500),
    item_images TEXT[] DEFAULT '{}',
    
    -- 캐릭터 입력값 (새로 생성할 때)
    character_mood VARCHAR(255),
    character_style VARCHAR(255),
    voice_tone VARCHAR(255),
    voice_description TEXT,
    
    -- 밈 정보
    meme_id INT,
    
    -- 최종 결과물
    final_video_url TEXT,
    
    -- 상태 및 관리
    status VARCHAR(50) DEFAULT 'draft',
    reference_notes TEXT,
    
    -- 비용 및 시간
    cost_estimate NUMERIC(10, 4) DEFAULT 0,
    processing_time INT,
    
    -- 시간 정보
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT fk_project_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project_user
        FOREIGN KEY (user_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project_character
        FOREIGN KEY (character_id)
        REFERENCES company_characters(character_id)
        ON DELETE SET NULL,
    
    CONSTRAINT fk_project_meme
        FOREIGN KEY (meme_id)
        REFERENCES memes(meme_id)
        ON DELETE SET NULL,
    
    CONSTRAINT chk_item_images_count
        CHECK (cardinality(item_images) <= 3),
    
    -- 캐릭터는 기존 것을 선택하거나 새로 만들기 위한 정보가 있어야 함
    CONSTRAINT chk_character_source CHECK (
        (character_id IS NOT NULL) OR 
        (character_mood IS NOT NULL AND character_style IS NOT NULL AND voice_tone IS NOT NULL)
    )
);

CREATE INDEX idx_video_projects_company ON video_projects(company_id);
CREATE INDEX idx_video_projects_user ON video_projects(user_id);
CREATE INDEX idx_video_projects_character ON video_projects(character_id);
CREATE INDEX idx_video_projects_status ON video_projects(status);
CREATE INDEX idx_video_projects_created ON video_projects(created_at DESC);

-- ============================================
-- 3. 생성/결과물
-- ============================================

-- 3-1. prompt_versions (scenario_scripts보다 먼저 생성)
CREATE TABLE prompt_versions (
    version_id SERIAL PRIMARY KEY,
    prompt_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    model_config JSONB,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_prompt_name_version UNIQUE(prompt_name, version)
);

CREATE UNIQUE INDEX idx_prompt_versions_active
    ON prompt_versions(prompt_name)
    WHERE is_active = TRUE;

CREATE INDEX idx_prompt_versions_name ON prompt_versions(prompt_name);

-- 3-2. scenario_scripts
CREATE TABLE scenario_scripts (
    script_id SERIAL PRIMARY KEY,
    
    -- 연결 정보
    project_id INT NOT NULL,
    meme_id BIGINT NOT NULL,
    
    -- 시나리오 메타데이터
    title VARCHAR(255) NOT NULL,
    description TEXT,
    hashtags TEXT[],
    
    -- 3단 구조 시나리오
    scenes JSONB NOT NULL,
    total_duration FLOAT CHECK (total_duration > 0 AND total_duration BETWEEN 15 AND 20),
    
    -- AI 생성 정보
    prompt_version_id INT,
    used_model VARCHAR(50),
    generation_cost NUMERIC(10, 4),
    processing_time_seconds INT,
    
    -- 품질 검증
    quality_check_passed BOOLEAN DEFAULT FALSE,
    quality_issues TEXT[],
    
    -- 고객 승인
    approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected', 'auto_approved')),
    approval_requested_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by_account_id INT,
    
    -- 상태 관리
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'approved', 'rejected')),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_project
        FOREIGN KEY (project_id)
        REFERENCES video_projects(project_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_meme
        FOREIGN KEY (meme_id)
        REFERENCES memes(meme_id)
        ON DELETE RESTRICT,
    
    CONSTRAINT fk_prompt_version
        FOREIGN KEY (prompt_version_id)
        REFERENCES prompt_versions(version_id)
        ON DELETE SET NULL,
    
    CONSTRAINT fk_approved_by
        FOREIGN KEY (approved_by_account_id)
        REFERENCES accounts(account_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_scenario_scripts_project ON scenario_scripts(project_id);
CREATE INDEX idx_scenario_scripts_meme ON scenario_scripts(meme_id);
CREATE INDEX idx_scenario_scripts_approval ON scenario_scripts(approval_status);
CREATE INDEX idx_scenario_scripts_scenes_gin ON scenario_scripts USING GIN (scenes);
CREATE INDEX idx_scenario_scripts_pending_approval
    ON scenario_scripts(approval_requested_at)
    WHERE approval_status = 'pending';

-- 3-3. scene_assets
CREATE TABLE scene_assets (
    asset_id SERIAL PRIMARY KEY,
    script_id INT NOT NULL,
    scene_key VARCHAR(50) NOT NULL,
    
    -- 음성 파일
    audio_url TEXT,
    audio_duration_seconds FLOAT,
    audio_storage_path VARCHAR(500),
    
    -- 캐릭터 이미지
    character_image_url TEXT,
    character_image_storage_path VARCHAR(500),
    
    -- 씬 영상
    scene_video_url TEXT,
    scene_video_storage_path VARCHAR(500),
    scene_video_duration FLOAT,
    
    -- 캐릭터 일관성 점수
    character_similarity_score FLOAT,
    
    -- 생성 정보
    generation_model VARCHAR(50),
    generation_cost NUMERIC(10, 4),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_script
        FOREIGN KEY (script_id)
        REFERENCES scenario_scripts(script_id)
        ON DELETE CASCADE,
    
    UNIQUE(script_id, scene_key)
);

CREATE INDEX idx_scene_assets_script ON scene_assets(script_id);

-- 3-4. videos
CREATE TABLE videos (
    video_id SERIAL PRIMARY KEY,
    
    -- 연결 및 소유권
    project_id INT,
    company_id INT NOT NULL,
    account_id INT,
    
    -- 메타데이터
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- 파일 접근 정보 (S3 기반)
    s3_url TEXT NOT NULL,
    thumbnail_url TEXT,
    presigned_url TEXT,
    presigned_expires_at TIMESTAMP,
    
    -- 파일 상세 정보
    file_size_bytes BIGINT,
    duration_seconds INT,
    resolution VARCHAR(20),
    format VARCHAR(20),
    download_count INT DEFAULT 0,
    
    -- 상태 및 로그
    status VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    error_message TEXT,
    
    -- 시간 정보
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_video_project
        FOREIGN KEY (project_id)
        REFERENCES video_projects(project_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_videos_company ON videos(company_id);
CREATE INDEX idx_videos_project ON videos(project_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created ON videos(created_at DESC);

-- 3-5. admin_video_posts
CREATE TABLE admin_video_posts (
    post_id SERIAL PRIMARY KEY,
    video_id INT NOT NULL,
    channel_id INT NOT NULL,
    
    -- 유튜브 게시 정보
    yt_video_id VARCHAR(255) UNIQUE,
    yt_title VARCHAR(255),
    yt_description TEXT,
    
    -- 게시 상태
    post_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- 시간 정보
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- 에러 핸들링
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    CONSTRAINT fk_video
        FOREIGN KEY (video_id)
        REFERENCES videos(video_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_channel
        FOREIGN KEY (channel_id)
        REFERENCES admin_youtube_channels(channel_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_video ON admin_video_posts(video_id);
CREATE INDEX idx_channel_status ON admin_video_posts(channel_id, post_status);
CREATE INDEX idx_scheduled ON admin_video_posts(scheduled_at) WHERE post_status = 'pending';

-- ============================================
-- 4. 성과 분석
-- ============================================

-- 4-1. performance_metrics
CREATE TABLE performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    
    -- 영상 연결
    video_id INT,
    post_id INT,
    
    -- 데이터 수집 정보
    captured_at TIMESTAMP NOT NULL,
    snapshot_type VARCHAR(20) NOT NULL CHECK (snapshot_type IN ('realtime', 'daily', 'monthly')),
    
    -- 기본 성과 지표
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    dislikes INT DEFAULT 0,
    comments INT DEFAULT 0,
    shares INT DEFAULT 0,
    
    -- 시청 패턴
    watch_time_seconds BIGINT DEFAULT 0,
    average_view_duration FLOAT,
    audience_retention_rate FLOAT,
    
    -- 참여도 지표
    engagement_rate FLOAT,
    
    -- 구독 전환
    subscribers_gained INT DEFAULT 0,
    
    -- 트래픽 소스
    traffic_sources JSONB,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_video
        FOREIGN KEY (video_id)
        REFERENCES videos(video_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_post
        FOREIGN KEY (post_id)
        REFERENCES admin_video_posts(post_id)
        ON DELETE CASCADE,
    
    CONSTRAINT chk_video_or_post CHECK (
        (video_id IS NOT NULL AND post_id IS NULL) OR
        (video_id IS NULL AND post_id IS NOT NULL)
    )
);

CREATE INDEX idx_performance_metrics_video ON performance_metrics(video_id);
CREATE INDEX idx_performance_metrics_post ON performance_metrics(post_id);
CREATE INDEX idx_performance_metrics_captured ON performance_metrics(captured_at DESC);
CREATE INDEX idx_performance_metrics_snapshot ON performance_metrics(snapshot_type);
CREATE UNIQUE INDEX idx_performance_metrics_daily_unique
    ON performance_metrics(video_id, post_id, DATE(captured_at))
    WHERE snapshot_type = 'daily';

-- ============================================
-- 5. 운영/자동화
-- ============================================

-- 5-1. workflow_execution
CREATE TABLE workflow_execution (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id INT NOT NULL,
    company_id INT NOT NULL,
    account_id INT NOT NULL,
    meme_id INT,
    
    workflow_type VARCHAR(50) DEFAULT 'video' NOT NULL,
    status VARCHAR(50) DEFAULT 'created' NOT NULL CHECK (status IN (
        'created', 'generating_character', 'pending_approval',
        'approved', 'rejected', 'processing', 'completed', 'failed', 'cancelled'
    )),
    current_stage VARCHAR(100),
    progress_percentage INT DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    approval_status VARCHAR(50),
    
    total_cost_usd NUMERIC(10, 4) DEFAULT 0,
    retry_count INT DEFAULT 0 CHECK (retry_count BETWEEN 0 AND 10),
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    CONSTRAINT fk_workflow_project
        FOREIGN KEY (project_id)
        REFERENCES video_projects(project_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_workflow_company
        FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_workflow_account
        FOREIGN KEY (account_id)
        REFERENCES accounts(account_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_workflow_meme
        FOREIGN KEY (meme_id)
        REFERENCES memes(meme_id)
        ON DELETE SET NULL
);

CREATE INDEX idx_workflow_project_id ON workflow_execution(project_id);
CREATE INDEX idx_workflow_status ON workflow_execution(status);
CREATE INDEX idx_workflow_created ON workflow_execution(created_at DESC);

-- 5-2. workflow_stages
CREATE TABLE workflow_stages (
    stage_id SERIAL PRIMARY KEY,
    execution_id UUID NOT NULL,
    
    -- 단계 정보
    stage_name VARCHAR(100) NOT NULL,
    stage_order INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    
    -- 시간 정보
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    
    -- 에러
    error_message TEXT,
    
    CONSTRAINT fk_execution
        FOREIGN KEY (execution_id)
        REFERENCES workflow_execution(execution_id)
        ON DELETE CASCADE,
    
    CONSTRAINT uq_execution_stage UNIQUE (execution_id, stage_order)
);

CREATE INDEX idx_workflow_stages_execution ON workflow_stages(execution_id);

-- 5-3. retry_queue
CREATE TABLE retry_queue (
    queue_id SERIAL PRIMARY KEY,
    meme_name VARCHAR(255) NOT NULL,
    
    -- 실패 정보
    failed_stage VARCHAR(50),
    error_message TEXT,
    attempt_count INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    
    -- 재시도 정보
    next_retry_at TIMESTAMP,
    last_attempted_at TIMESTAMP,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_retry_queue_status ON retry_queue(status);
CREATE INDEX idx_retry_queue_next_retry ON retry_queue(next_retry_at) WHERE status = 'pending';

-- ============================================
-- 6. 품질관리
-- ============================================

-- 6-1. prompt_usage_logs
CREATE TABLE prompt_usage_logs (
    log_id SERIAL PRIMARY KEY,
    version_id INT NOT NULL,
    
    -- 실행 연결
    project_id INT,
    script_id INT,
    
    -- 성능 정보
    latency_ms INT,
    token_usage JSONB,
    quality_score NUMERIC(3,2),
    
    -- 상태
    success BOOLEAN NOT NULL,
    error_log TEXT,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_prompt_version
        FOREIGN KEY (version_id)
        REFERENCES prompt_versions(version_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_project
        FOREIGN KEY (project_id)
        REFERENCES video_projects(project_id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_script
        FOREIGN KEY (script_id)
        REFERENCES scenario_scripts(script_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_prompt_usage_logs_version ON prompt_usage_logs(version_id);
CREATE INDEX idx_prompt_usage_logs_project ON prompt_usage_logs(project_id);
CREATE INDEX idx_prompt_usage_logs_created ON prompt_usage_logs(created_at DESC);

-- ============================================
-- 트리거 및 함수
-- ============================================

-- client 삽입 시 account_type 자동 검증
CREATE OR REPLACE FUNCTION check_client_account_type()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT account_type FROM accounts WHERE account_id = NEW.account_id) != 'client' THEN
        RAISE EXCEPTION 'Account must be of type "client"';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_client_account_type
BEFORE INSERT OR UPDATE ON clients
FOR EACH ROW EXECUTE FUNCTION check_client_account_type();

-- admin 삽입 시 account_type 자동 검증
CREATE OR REPLACE FUNCTION check_admin_account_type()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT account_type FROM accounts WHERE account_id = NEW.account_id) != 'admin' THEN
        RAISE EXCEPTION 'Account must be of type "admin"';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_admin_account_type
BEFORE INSERT OR UPDATE ON admins
FOR EACH ROW EXECUTE FUNCTION check_admin_account_type();

-- company_members 삽입 시 client 계정만 가능하도록 검증
CREATE OR REPLACE FUNCTION check_company_member_client_only()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT account_type FROM accounts WHERE account_id = NEW.account_id) != 'client' THEN
        RAISE EXCEPTION 'Only client accounts can be company members';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_company_member_client_only
BEFORE INSERT OR UPDATE ON company_members
FOR EACH ROW EXECUTE FUNCTION check_company_member_client_only();
