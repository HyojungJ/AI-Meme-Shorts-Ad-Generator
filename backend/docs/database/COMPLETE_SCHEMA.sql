-- public.accounts definition
-- Drop table
-- DROP TABLE public.accounts;

CREATE TABLE public.accounts (
	account_id serial4 NOT NULL,
	email varchar(255) NOT NULL,
	account_type varchar(20) NOT NULL,
	is_active bool DEFAULT true NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT accounts_account_type_check CHECK (((account_type)::text = ANY ((ARRAY['client'::character varying, 'admin'::character varying])::text[]))),
	CONSTRAINT accounts_email_key UNIQUE (email),
	CONSTRAINT accounts_pkey PRIMARY KEY (account_id)
);

-- public.companies definition
-- Drop table
-- DROP TABLE public.companies;

CREATE TABLE public.companies (
	company_id serial4 NOT NULL,
	company_name varchar(100) NOT NULL,
	is_active bool DEFAULT true NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT companies_pkey PRIMARY KEY (company_id)
);

-- public.memes definition
-- Drop table
-- DROP TABLE public.memes;

CREATE TABLE public.memes (
	meme_id bigserial NOT NULL,
	meme_name varchar(255) NOT NULL,
	definition text NULL,
	origin jsonb NULL,
	key_phrase text NULL,
	sources jsonb DEFAULT '[]'::jsonb NULL,
	risk_info varchar(20) NULL,
	meme_type varchar(50) NULL,
	status varchar(50) DEFAULT 'READY'::character varying NULL,
	source_video jsonb DEFAULT '{}'::jsonb NULL,
	video_analysis jsonb DEFAULT '{}'::jsonb NULL,
	confidence float8 NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT memes_meme_name_key UNIQUE (meme_name),
	CONSTRAINT memes_meme_type_check CHECK (((meme_type)::text = ANY ((ARRAY['quotable'::character varying, 'performable'::character varying, 'hybrid'::character varying])::text[]))),
	CONSTRAINT memes_pkey PRIMARY KEY (meme_id),
	CONSTRAINT memes_status_check CHECK (((status)::text = ANY ((ARRAY['READY'::character varying, 'PROCESSING'::character varying, 'PROCESSED'::character varying, 'COMPLETED'::character varying, 'FAILED'::character varying])::text[])))
);
CREATE INDEX idx_memes_name ON public.memes USING btree (meme_name);
CREATE INDEX idx_memes_origin_gin ON public.memes USING gin (origin);
CREATE INDEX idx_memes_status ON public.memes USING btree (status);

-- public.prompt_versions definition
-- Drop table
-- DROP TABLE public.prompt_versions;

CREATE TABLE public.prompt_versions (
	version_id serial4 NOT NULL,
	prompt_name varchar(100) NOT NULL,
	"version" varchar(20) NOT NULL,
	"content" text NOT NULL,
	variables jsonb DEFAULT '[]'::jsonb NULL,
	model_config jsonb NULL,
	is_active bool DEFAULT false NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT prompt_versions_pkey PRIMARY KEY (version_id),
	CONSTRAINT uq_prompt_name_version UNIQUE (prompt_name, version)
);
CREATE UNIQUE INDEX idx_prompt_versions_active ON public.prompt_versions USING btree (prompt_name) WHERE (is_active = true);
CREATE INDEX idx_prompt_versions_name ON public.prompt_versions USING btree (prompt_name);

-- public.retry_queue definition
-- Drop table
-- DROP TABLE public.retry_queue;

CREATE TABLE public.retry_queue (
	queue_id serial4 NOT NULL,
	meme_name varchar(255) NOT NULL,
	failed_stage varchar(50) NULL,
	error_message text NULL,
	attempt_count int4 DEFAULT 0 NULL,
	max_attempts int4 DEFAULT 3 NULL,
	next_retry_at timestamp NULL,
	last_attempted_at timestamp NULL,
	status varchar(20) DEFAULT 'pending'::character varying NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT retry_queue_pkey PRIMARY KEY (queue_id),
	CONSTRAINT retry_queue_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying])::text[])))
);
CREATE INDEX idx_retry_queue_next_retry ON public.retry_queue USING btree (next_retry_at) WHERE ((status)::text = 'pending'::text);
CREATE INDEX idx_retry_queue_status ON public.retry_queue USING btree (status);

-- public.admins definition
-- Drop table
-- DROP TABLE public.admins;

CREATE TABLE public.admins (
	admin_id serial4 NOT NULL,
	account_id int4 NOT NULL,
	hashed_password varchar(255) NOT NULL,
	refresh_token text NULL,
	rt_expires_at timestamp NULL,
	last_login_at timestamp NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT admins_account_id_key UNIQUE (account_id),
	CONSTRAINT admins_pkey PRIMARY KEY (admin_id),
	CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE
);

-- Table Triggers
create trigger trigger_check_admin_account_type before
insert
    or
update
    on
    public.admins for each row execute function check_admin_account_type();

-- public.clients definition
-- Drop table
-- DROP TABLE public.clients;

CREATE TABLE public.clients (
	client_id serial4 NOT NULL,
	account_id int4 NOT NULL,
	hashed_password varchar(255) NOT NULL,
	refresh_token text NULL,
	rt_expires_at timestamp NULL,
	reset_token text NULL,
	reset_expires_at timestamp NULL,
	last_login_at timestamp NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT clients_account_id_key UNIQUE (account_id),
	CONSTRAINT clients_pkey PRIMARY KEY (client_id),
	CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE
);

-- Table Triggers
create trigger trigger_check_client_account_type before
insert
    or
update
    on
    public.clients for each row execute function check_client_account_type();

-- public.company_characters definition
-- Drop table
-- DROP TABLE public.company_characters;

CREATE TABLE public.company_characters (
	character_id serial4 NOT NULL,
	company_id int4 NOT NULL,
	character_name varchar(255) NOT NULL,
	character_mood varchar(255) NOT NULL,
	character_style varchar(255) NOT NULL,
	voice_tone varchar(255) NOT NULL,
	image_url text NOT NULL,
	is_active bool DEFAULT true NOT NULL,
	created_at timestamptz DEFAULT now() NOT NULL,
	updated_at timestamptz DEFAULT now() NOT NULL,
	image_prompt text NULL,
	image_model varchar(50) NULL,
	elevenlabs_voice_id text NULL,
	voice_design_prompt text NULL,
	generation_metadata jsonb DEFAULT '{}'::jsonb NULL,
	CONSTRAINT company_characters_pkey PRIMARY KEY (character_id),
	CONSTRAINT fk_company_char FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE CASCADE
);
CREATE INDEX idx_company_characters_active ON public.company_characters USING btree (is_active);
CREATE INDEX idx_company_characters_company ON public.company_characters USING btree (company_id);

-- public.company_members definition
-- Drop table
-- DROP TABLE public.company_members;

CREATE TABLE public.company_members (
	member_id serial4 NOT NULL,
	company_id int4 NOT NULL,
	account_id int4 NOT NULL,
	"role" varchar(20) NOT NULL,
	member_name varchar(100) NOT NULL,
	department varchar(100) NULL,
	is_primary bool DEFAULT false NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT company_members_pkey PRIMARY KEY (member_id),
	CONSTRAINT company_members_role_check CHECK (((role)::text = ANY ((ARRAY['manager'::character varying, 'member'::character varying])::text[]))),
	CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE,
	CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE CASCADE
);
CREATE INDEX idx_company_members_account ON public.company_members USING btree (account_id);
CREATE INDEX idx_company_members_company ON public.company_members USING btree (company_id);
CREATE UNIQUE INDEX idx_company_members_primary_unique ON public.company_members USING btree (company_id) WHERE (is_primary = true);

-- Table Triggers
create trigger trigger_check_company_member_client_only before
insert
    or
update
    on
    public.company_members for each row execute function check_company_member_client_only();

-- public.meme_examples definition
-- Drop table
-- DROP TABLE public.meme_examples;

CREATE TABLE public.meme_examples (
	example_id serial4 NOT NULL,
	meme_id int8 NOT NULL,
	situation varchar(255) NOT NULL,
	dialogue_example text NULL,
	source_url varchar(500) NULL,
	example_type varchar(20) NULL,
	note text NULL,
	tone varchar(20) NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT meme_examples_pkey PRIMARY KEY (example_id),
	CONSTRAINT fk_meme_example FOREIGN KEY (meme_id) REFERENCES public.memes(meme_id) ON DELETE CASCADE
);
CREATE INDEX idx_meme_examples_meme_id ON public.meme_examples USING btree (meme_id);
CREATE INDEX idx_meme_examples_type ON public.meme_examples USING btree (example_type);

-- public.ad_requests definition
-- Drop table
-- DROP TABLE public.ad_requests;

CREATE TABLE public.ad_requests (
	ad_id int4 DEFAULT nextval('video_projects_project_id_seq'::regclass) NOT NULL,
	company_id int4 NOT NULL,
	account_id int4 NOT NULL,
	character_id int4 NULL,
	item_name varchar(255) NOT NULL,
	item_category varchar(20) NULL,
	item_url varchar(500) NULL,
	item_images _text DEFAULT '{}'::text[] NULL,
	voice_description text NULL,
	meme_id int4 NULL,
	status varchar(50) DEFAULT 'draft'::character varying NULL,
	created_at timestamptz DEFAULT now() NOT NULL,
	updated_at timestamptz DEFAULT now() NOT NULL,
	item_description text NULL,
	character_style_raw text NULL,
	notes text NULL,
	CONSTRAINT ad_requests_pk PRIMARY KEY (ad_id),
	CONSTRAINT chk_ad_request_images_count CHECK ((cardinality(item_images) <= 1)),
	CONSTRAINT fk_ad_request_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE,
	CONSTRAINT fk_ad_request_character FOREIGN KEY (character_id) REFERENCES public.company_characters(character_id) ON DELETE SET NULL,
	CONSTRAINT fk_ad_request_company FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE CASCADE,
	CONSTRAINT fk_ad_request_meme FOREIGN KEY (meme_id) REFERENCES public.memes(meme_id) ON DELETE SET NULL
);
CREATE INDEX idx_ad_requests_account ON public.ad_requests USING btree (account_id);
CREATE INDEX idx_ad_requests_company ON public.ad_requests USING btree (company_id);
CREATE INDEX idx_ad_requests_status ON public.ad_requests USING btree (status);
CREATE INDEX idx_video_projects_character ON public.ad_requests USING btree (character_id);
CREATE INDEX idx_video_projects_created ON public.ad_requests USING btree (created_at DESC);
CREATE INDEX idx_video_projects_user ON public.ad_requests USING btree (account_id);

-- public.admin_youtube_channels definition
-- Drop table
-- DROP TABLE public.admin_youtube_channels;

CREATE TABLE public.admin_youtube_channels (
	channel_id serial4 NOT NULL,
	admin_id int4 NOT NULL,
	yt_channel_id varchar(255) NOT NULL,
	channel_name varchar(255) NOT NULL,
	channel_handle varchar(255) NULL,
	access_token text NOT NULL,
	refresh_token text NOT NULL,
	token_expires_at timestamp NOT NULL,
	is_active bool DEFAULT true NOT NULL,
	last_synced_at timestamp NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT admin_youtube_channels_admin_id_key UNIQUE (admin_id),
	CONSTRAINT admin_youtube_channels_pkey PRIMARY KEY (channel_id),
	CONSTRAINT admin_youtube_channels_yt_channel_id_key UNIQUE (yt_channel_id),
	CONSTRAINT fk_admin_profile FOREIGN KEY (admin_id) REFERENCES public.admins(admin_id) ON DELETE CASCADE
);

-- public.scenario_scripts definition
-- Drop table
-- DROP TABLE public.scenario_scripts;

CREATE TABLE public.scenario_scripts (
	script_id serial4 NOT NULL,
	ad_id int4 NOT NULL,
	meme_id int8 NOT NULL,
	title varchar(255) NOT NULL,
	description text NULL,
	hashtags _text NULL,
	scenes jsonb NOT NULL,
	total_duration float8 NULL,
	prompt_version_id int4 NULL,
	used_model varchar(50) NULL,
	generation_cost numeric(10, 4) NULL,
	processing_time_seconds int4 NULL,
	quality_check_passed bool DEFAULT false NULL,
	quality_issues _text NULL,
	approval_status varchar(20) DEFAULT 'pending'::character varying NULL,
	approval_requested_at timestamp NULL,
	approved_at timestamp NULL,
	approved_by_account_id int4 NULL,
	status varchar(50) DEFAULT 'draft'::character varying NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT scenario_scripts_approval_status_check CHECK (((approval_status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying, 'auto_approved'::character varying])::text[]))),
	CONSTRAINT scenario_scripts_pkey PRIMARY KEY (script_id),
	CONSTRAINT scenario_scripts_status_check CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'validated'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[]))),
	CONSTRAINT scenario_scripts_total_duration_check CHECK (((total_duration > (0)::double precision) AND ((total_duration >= (15)::double precision) AND (total_duration <= (20)::double precision)))),
	CONSTRAINT fk_approved_by FOREIGN KEY (approved_by_account_id) REFERENCES public.accounts(account_id) ON DELETE SET NULL,
	CONSTRAINT fk_meme FOREIGN KEY (meme_id) REFERENCES public.memes(meme_id) ON DELETE RESTRICT,
	CONSTRAINT fk_prompt_version FOREIGN KEY (prompt_version_id) REFERENCES public.prompt_versions(version_id) ON DELETE SET NULL,
	CONSTRAINT fk_scenario_ad FOREIGN KEY (ad_id) REFERENCES public.ad_requests(ad_id) ON DELETE CASCADE
);
CREATE INDEX idx_scenario_scripts_approval ON public.scenario_scripts USING btree (approval_status);
CREATE INDEX idx_scenario_scripts_meme ON public.scenario_scripts USING btree (meme_id);
CREATE INDEX idx_scenario_scripts_pending_approval ON public.scenario_scripts USING btree (approval_requested_at) WHERE ((approval_status)::text = 'pending'::text);
CREATE INDEX idx_scenario_scripts_project ON public.scenario_scripts USING btree (ad_id);
CREATE INDEX idx_scenario_scripts_scenes_gin ON public.scenario_scripts USING gin (scenes);

-- public.scene_assets definition
-- Drop table
-- DROP TABLE public.scene_assets;

CREATE TABLE public.scene_assets (
	asset_id serial4 NOT NULL,
	script_id int4 NOT NULL,
	scene_key varchar(50) NOT NULL,
	audio_url text NULL,
	audio_duration_seconds float8 NULL,
	audio_storage_path varchar(500) NULL,
	character_image_url text NULL,
	character_image_storage_path varchar(500) NULL,
	scene_video_url text NULL,
	scene_video_storage_path varchar(500) NULL,
	scene_video_duration float8 NULL,
	character_similarity_score float8 NULL,
	generation_model varchar(50) NULL,
	generation_cost numeric(10, 4) NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT scene_assets_pkey PRIMARY KEY (asset_id),
	CONSTRAINT scene_assets_script_id_scene_key_key UNIQUE (script_id, scene_key),
	CONSTRAINT fk_script FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id) ON DELETE CASCADE
);
CREATE INDEX idx_scene_assets_script ON public.scene_assets USING btree (script_id);

-- public.videos definition
-- Drop table
-- DROP TABLE public.videos;

CREATE TABLE public.videos (
	video_id serial4 NOT NULL,
	ad_id int4 NULL,
	company_id int4 NOT NULL,
	account_id int4 NULL,
	title varchar(255) NOT NULL,
	description text NULL,
	s3_url text NOT NULL,
	thumbnail_url text NULL,
	presigned_url text NULL,
	presigned_expires_at timestamp NULL,
	file_size_bytes int8 NULL,
	duration_seconds int4 NULL,
	resolution varchar(20) NULL,
	format varchar(20) NULL,
	status varchar(20) DEFAULT 'processing'::character varying NOT NULL,
	error_message text NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	completed_at timestamp NULL,
	rejection_reason text NULL,
	rejected_at timestamp NULL,
	rejected_by_account_id int4 NULL,
	script_id int4 NULL,
	CONSTRAINT videos_pkey PRIMARY KEY (video_id),
	CONSTRAINT videos_status_check CHECK (((status)::text = ANY ((ARRAY['processing'::character varying, 'completed'::character varying, 'client_approved'::character varying, 'client_rejected'::character varying, 'admin_approved'::character varying, 'admin_rejected'::character varying, 'published'::character varying, 'failed'::character varying])::text[]))),
	CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE SET NULL,
	CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE CASCADE,
	CONSTRAINT fk_video_ad FOREIGN KEY (ad_id) REFERENCES public.ad_requests(ad_id) ON DELETE CASCADE,
	CONSTRAINT videos_rejected_by_account_id_fkey FOREIGN KEY (rejected_by_account_id) REFERENCES public.accounts(account_id),
	CONSTRAINT videos_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id)
);
CREATE INDEX idx_videos_company ON public.videos USING btree (company_id);
CREATE INDEX idx_videos_created ON public.videos USING btree (created_at DESC);
CREATE INDEX idx_videos_project ON public.videos USING btree (ad_id);
CREATE UNIQUE INDEX idx_videos_script ON public.videos USING btree (script_id) WHERE (script_id IS NOT NULL);
CREATE INDEX idx_videos_status ON public.videos USING btree (status);

-- public.voice_generations definition
-- Drop table
-- DROP TABLE public.voice_generations;

CREATE TABLE public.voice_generations (
	voice_gen_id serial4 NOT NULL,
	character_id int4 NOT NULL,
	script_id int4 NULL,
	scene_key varchar(50) NOT NULL,
	text_content text NOT NULL,
	text_hash varchar(64) NULL,
	audio_url text NULL,
	duration_seconds float8 NULL,
	size_bytes int8 NULL,
	settings_json jsonb DEFAULT '{}'::jsonb NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT voice_generations_character_id_text_hash_key UNIQUE (character_id, text_hash),
	CONSTRAINT voice_generations_pkey PRIMARY KEY (voice_gen_id),
	CONSTRAINT voice_generations_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.company_characters(character_id),
	CONSTRAINT voice_generations_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id)
);
CREATE INDEX idx_voice_gen_character ON public.voice_generations USING btree (character_id);
CREATE INDEX idx_voice_gen_script ON public.voice_generations USING btree (script_id);

-- public.workflow_execution definition
-- Drop table
-- DROP TABLE public.workflow_execution;

CREATE TABLE public.workflow_execution (
	execution_id uuid DEFAULT gen_random_uuid() NOT NULL,
	ad_id int4 NOT NULL,
	company_id int4 NOT NULL,
	account_id int4 NOT NULL,
	meme_id int4 NULL,
	status varchar(50) DEFAULT 'created'::character varying NOT NULL,
	current_stage varchar(100) NULL,
	progress_percentage int4 DEFAULT 0 NULL,
	approval_status varchar(50) NULL,
	total_cost_usd numeric(10, 4) DEFAULT 0 NULL,
	retry_count int4 DEFAULT 0 NULL,
	error_message text NULL,
	created_at timestamptz DEFAULT now() NULL,
	completed_at timestamptz NULL,
	CONSTRAINT workflow_execution_pkey PRIMARY KEY (execution_id),
	CONSTRAINT workflow_execution_progress_percentage_check CHECK (((progress_percentage >= 0) AND (progress_percentage <= 100))),
	CONSTRAINT workflow_execution_retry_count_check CHECK (((retry_count >= 0) AND (retry_count <= 10))),
	CONSTRAINT workflow_execution_status_check CHECK (((status)::text = ANY ((ARRAY['created'::character varying, 'generating_character'::character varying, 'generating_scenario'::character varying, 'generating_video'::character varying, 'pending_approval'::character varying, 'approved'::character varying, 'rejected'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'cancelled'::character varying])::text[]))),
	CONSTRAINT fk_workflow_account FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE CASCADE,
	CONSTRAINT fk_workflow_ad FOREIGN KEY (ad_id) REFERENCES public.ad_requests(ad_id) ON DELETE CASCADE,
	CONSTRAINT fk_workflow_company FOREIGN KEY (company_id) REFERENCES public.companies(company_id) ON DELETE CASCADE,
	CONSTRAINT fk_workflow_meme FOREIGN KEY (meme_id) REFERENCES public.memes(meme_id) ON DELETE SET NULL
);
CREATE INDEX idx_workflow_created ON public.workflow_execution USING btree (created_at DESC);
CREATE INDEX idx_workflow_project_id ON public.workflow_execution USING btree (ad_id);
CREATE INDEX idx_workflow_status ON public.workflow_execution USING btree (status);

-- public.workflow_stages definition
-- Drop table
-- DROP TABLE public.workflow_stages;

CREATE TABLE public.workflow_stages (
	stage_id serial4 NOT NULL,
	execution_id uuid NOT NULL,
	stage_name varchar(100) NOT NULL,
	stage_order int4 NOT NULL,
	status varchar(50) DEFAULT 'pending'::character varying NOT NULL,
	started_at timestamptz NULL,
	completed_at timestamptz NULL,
	duration_seconds int4 NULL,
	error_message text NULL,
	CONSTRAINT uq_execution_stage UNIQUE (execution_id, stage_order),
	CONSTRAINT workflow_stages_pkey PRIMARY KEY (stage_id),
	CONSTRAINT workflow_stages_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying, 'skipped'::character varying])::text[]))),
	CONSTRAINT fk_execution FOREIGN KEY (execution_id) REFERENCES public.workflow_execution(execution_id) ON DELETE CASCADE
);
CREATE INDEX idx_workflow_stages_execution ON public.workflow_stages USING btree (execution_id);

-- public.admin_video_posts definition
-- Drop table
-- DROP TABLE public.admin_video_posts;

CREATE TABLE public.admin_video_posts (
	post_id serial4 NOT NULL,
	video_id int4 NOT NULL,
	channel_id int4 NOT NULL,
	yt_video_id varchar(255) NULL,
	yt_title varchar(255) NULL,
	yt_description text NULL,
	post_status varchar(20) DEFAULT 'pending'::character varying NOT NULL,
	scheduled_at timestamp NULL,
	published_at timestamp NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	error_message text NULL,
	retry_count int4 DEFAULT 0 NULL,
	CONSTRAINT admin_video_posts_pkey PRIMARY KEY (post_id),
	CONSTRAINT admin_video_posts_yt_video_id_key UNIQUE (yt_video_id),
	CONSTRAINT fk_channel FOREIGN KEY (channel_id) REFERENCES public.admin_youtube_channels(channel_id) ON DELETE CASCADE,
	CONSTRAINT fk_video FOREIGN KEY (video_id) REFERENCES public.videos(video_id) ON DELETE CASCADE
);
CREATE INDEX idx_channel_status ON public.admin_video_posts USING btree (channel_id, post_status);
CREATE INDEX idx_scheduled ON public.admin_video_posts USING btree (scheduled_at) WHERE ((post_status)::text = 'pending'::text);
CREATE INDEX idx_video ON public.admin_video_posts USING btree (video_id);

-- public.image_generations definition
-- Drop table
-- DROP TABLE public.image_generations;

CREATE TABLE public.image_generations (
	image_id serial4 NOT NULL,
	character_id int4 NOT NULL,
	script_id int4 NOT NULL,
	prompt text NULL,
	model varchar(50) NULL,
	image_url text NULL,
	size_bytes int8 NULL,
	metadata_json jsonb DEFAULT '{}'::jsonb NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT image_generations_pkey PRIMARY KEY (image_id),
	CONSTRAINT image_generations_script_id_key UNIQUE (script_id),
	CONSTRAINT image_generations_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.company_characters(character_id),
	CONSTRAINT image_generations_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id)
);
CREATE INDEX idx_image_gen_character ON public.image_generations USING btree (character_id);

-- public.performance_metrics definition
-- Drop table
-- DROP TABLE public.performance_metrics;

CREATE TABLE public.performance_metrics (
	metric_id serial4 NOT NULL,
	video_id int4 NULL,
	post_id int4 NULL,
	captured_at timestamp NOT NULL,
	snapshot_type varchar(20) NOT NULL,
	"views" int4 DEFAULT 0 NULL,
	likes int4 DEFAULT 0 NULL,
	dislikes int4 DEFAULT 0 NULL,
	"comments" int4 DEFAULT 0 NULL,
	shares int4 DEFAULT 0 NULL,
	watch_time_seconds int8 DEFAULT 0 NULL,
	average_view_duration float8 NULL,
	audience_retention_rate float8 NULL,
	engagement_rate float8 NULL,
	subscribers_gained int4 DEFAULT 0 NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT chk_video_or_post CHECK ((((video_id IS NOT NULL) AND (post_id IS NULL)) OR ((video_id IS NULL) AND (post_id IS NOT NULL)))),
	CONSTRAINT performance_metrics_pkey PRIMARY KEY (metric_id),
	CONSTRAINT performance_metrics_snapshot_type_check CHECK (((snapshot_type)::text = ANY ((ARRAY['realtime'::character varying, 'daily'::character varying, 'monthly'::character varying])::text[]))),
	CONSTRAINT fk_post FOREIGN KEY (post_id) REFERENCES public.admin_video_posts(post_id) ON DELETE CASCADE,
	CONSTRAINT fk_video FOREIGN KEY (video_id) REFERENCES public.videos(video_id) ON DELETE CASCADE
);
CREATE INDEX idx_performance_metrics_captured ON public.performance_metrics USING btree (captured_at DESC);
CREATE UNIQUE INDEX idx_performance_metrics_daily_unique ON public.performance_metrics USING btree (video_id, post_id, date(captured_at)) WHERE ((snapshot_type)::text = 'daily'::text);
CREATE INDEX idx_performance_metrics_post ON public.performance_metrics USING btree (post_id);
CREATE INDEX idx_performance_metrics_snapshot ON public.performance_metrics USING btree (snapshot_type);
CREATE INDEX idx_performance_metrics_video ON public.performance_metrics USING btree (video_id);

-- public.prompt_usage_logs definition
-- Drop table
-- DROP TABLE public.prompt_usage_logs;

CREATE TABLE public.prompt_usage_logs (
	log_id serial4 NOT NULL,
	version_id int4 NOT NULL,
	ad_id int4 NULL,
	script_id int4 NULL,
	latency_ms int4 NULL,
	token_usage jsonb NULL,
	quality_score numeric(3, 2) NULL,
	success bool NOT NULL,
	error_log text NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT prompt_usage_logs_pkey PRIMARY KEY (log_id),
	CONSTRAINT fk_prompt_log_ad FOREIGN KEY (ad_id) REFERENCES public.ad_requests(ad_id) ON DELETE CASCADE,
	CONSTRAINT fk_prompt_version FOREIGN KEY (version_id) REFERENCES public.prompt_versions(version_id) ON DELETE CASCADE,
	CONSTRAINT fk_script FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id) ON DELETE CASCADE
);
CREATE INDEX idx_prompt_usage_logs_created ON public.prompt_usage_logs USING btree (created_at DESC);
CREATE INDEX idx_prompt_usage_logs_project ON public.prompt_usage_logs USING btree (ad_id);
CREATE INDEX idx_prompt_usage_logs_version ON public.prompt_usage_logs USING btree (version_id);

-- public.scene_videos definition
-- Drop table
-- DROP TABLE public.scene_videos;

CREATE TABLE public.scene_videos (
	scene_video_id serial4 NOT NULL,
	script_id int4 NOT NULL,
	scene_key varchar(50) NOT NULL,
	voice_gen_id int4 NULL,
	image_id int4 NULL,
	video_url text NULL,
	duration_seconds float8 NULL,
	size_bytes int8 NULL,
	generation_model varchar(50) NULL,
	generation_cost numeric(10, 4) NULL,
	generation_metadata jsonb DEFAULT '{}'::jsonb NULL,
	created_at timestamptz DEFAULT now() NULL,
	CONSTRAINT scene_videos_pkey PRIMARY KEY (scene_video_id),
	CONSTRAINT scene_videos_script_id_scene_key_key UNIQUE (script_id, scene_key),
	CONSTRAINT scene_videos_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image_generations(image_id),
	CONSTRAINT scene_videos_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scenario_scripts(script_id),
	CONSTRAINT scene_videos_voice_gen_id_fkey FOREIGN KEY (voice_gen_id) REFERENCES public.voice_generations(voice_gen_id)
);
CREATE INDEX idx_scene_videos_script ON public.scene_videos USING btree (script_id);

