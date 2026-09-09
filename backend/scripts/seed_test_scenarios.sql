-- ============================================
-- 테스트 시나리오별 데이터 생성
-- ============================================
-- 기존 계정 사용: manager@test.com (company_id=11, account_id=13)
-- 기존 밈 사용: meme_id는 실제 DB에서 조회

-- 변수 설정 (실제 값으로 대체 필요)
-- company_id: 11 (테스트기업)
-- account_id: 13 (manager@test.com)
-- meme_id: 실제 밈 ID 사용

-- ============================================
-- 1. 캐릭터 3개 생성 (각 시나리오용)
-- ============================================
INSERT INTO company_characters (company_id, character_name, character_mood, character_style, voice_tone, image_url, is_active)
VALUES 
(11, '밝은 토끼', '밝고 활기찬', '귀여운 3D 스타일', '경쾌한 여성 목소리', 'https://example.com/characters/rabbit.png', true),
(11, '차분한 곰', '차분하고 신뢰감 있는', '사실적인 3D 스타일', '중저음 남성 목소리', 'https://example.com/characters/bear.png', true),
(11, '장난꾸러기 고양이', '장난스럽고 재치있는', '만화 스타일', '톡톡 튀는 여성 목소리', 'https://example.com/characters/cat.png', true)
ON CONFLICT DO NOTHING;

-- ============================================
-- 2. 시나리오 1: 시나리오 검수 대기
-- ============================================
-- 광고 요청
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_keymessage, status, character_id, meme_id, item_images)
SELECT 11, 13, '프리미엄 무선 이어폰', '전자제품', '완벽한 음질, 완벽한 자유', 'pending_approval',
       (SELECT character_id FROM company_characters WHERE character_name='밝은 토끼' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       ARRAY['https://example.com/products/earphone.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='프리미엄 무선 이어폰' AND company_id=11);

-- 워크플로우
INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 무선 이어폰' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       'pending_approval', 'scenario_review', 40
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 무선 이어폰' AND company_id=11)
);

-- 시나리오 스크립트 (검수 대기)
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 무선 이어폰' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
    '프리미엄 무선 이어폰 - 밈 시나리오',
    '완벽한 음질을 강조하는 재미있는 밈 영상',
    '{"intro": {"text": "음질이 이렇게 좋다고?", "duration": 3.0}, "main": {"text": "완벽한 음질, 완벽한 자유", "duration": 10.0}, "outro": {"text": "지금 바로 구매하세요!", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 무선 이어폰' AND company_id=11)
);

-- ============================================
-- 3. 시나리오 2: 이미지 생성 중
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_keymessage, status, character_id, meme_id, item_images)
SELECT 11, 13, '유기농 그린 스무디', '식음료', '매일 아침 건강한 시작', 'processing',
       (SELECT character_id FROM company_characters WHERE character_name='차분한 곰' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       ARRAY['https://example.com/products/smoothie.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       'processing', 'image_generation', 30
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11)
);

-- 시나리오 스크립트 (이미지 생성용)
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
    '유기농 그린 스무디 - 밈 시나리오',
    '건강한 아침을 강조하는 재미있는 밈 영상',
    '{"intro": {"text": "아침이 달라진다!", "duration": 3.0}, "main": {"text": "매일 아침 건강한 시작", "duration": 10.0}, "outro": {"text": "지금 바로 시작하세요!", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11)
);

-- 이미지 생성 (검수 대기)
INSERT INTO image_generations (character_id, script_id, prompt, model, image_url, metadata_json)
SELECT 
    (SELECT character_id FROM company_characters WHERE character_name='차분한 곰' AND company_id=11 LIMIT 1),
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11)),
    '차분하고 신뢰감 있는 곰 캐릭터, 사실적인 3D 스타일',
    'dall-e-3',
    'https://example.com/generated/bear_image.png',
    '{"size": "1024x1024", "status": "pending_review"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM image_generations WHERE script_id = (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='유기농 그린 스무디' AND company_id=11))
);

-- ============================================
-- 4. 시나리오 3: 음성 생성 중
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_keymessage, status, character_id, meme_id, item_images)
SELECT 11, 13, '스마트 홈 조명', '가전제품', '당신의 공간을 더 스마트하게', 'processing',
       (SELECT character_id FROM company_characters WHERE character_name='장난꾸러기 고양이' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
       ARRAY['https://example.com/products/light.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
       'processing', 'voice_generation', 50
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11)
);

-- 시나리오 스크립트 (음성 생성용)
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
    '스마트 홈 조명 - 밈 시나리오',
    '스마트한 생활을 강조하는 재미있는 밈 영상',
    '{"intro": {"text": "이제 조명도 스마트하게!", "duration": 3.0}, "main": {"text": "당신의 공간을 더 스마트하게", "duration": 10.0}, "outro": {"text": "지금 바로 경험하세요!", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11)
);

-- 음성 생성 (검수 대기)
INSERT INTO voice_generations (character_id, script_id, scene_key, text_content, audio_url, duration_seconds, settings_json)
SELECT 
    (SELECT character_id FROM company_characters WHERE character_name='장난꾸러기 고양이' AND company_id=11 LIMIT 1),
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11)),
    'intro',
    '이제 조명도 스마트하게!',
    'https://example.com/generated/cat_voice.mp3',
    3.0,
    '{"model": "elevenlabs", "voice_id": "test123", "status": "pending_review"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM voice_generations WHERE script_id = (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='스마트 홈 조명' AND company_id=11))
);

-- ============================================
-- 5. 시나리오 4: 완료된 영상 (다운로드 가능)
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_keymessage, status, character_id, meme_id, item_images)
SELECT 11, 13, '친환경 대나무 칫솔', '생활용품', '지구를 생각하는 작은 실천', 'completed',
       (SELECT character_id FROM company_characters WHERE character_name='밝은 토끼' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       ARRAY['https://example.com/products/toothbrush.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       'completed', 'completed', 100
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11)
);

-- 시나리오 (승인됨)
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
    '친환경 대나무 칫솔 - 밈 시나리오',
    '환경 보호를 강조하는 재미있는 밈 영상',
    '{"intro": {"text": "플라스틱은 이제 그만!", "duration": 3.0}, "main": {"text": "지구를 생각하는 작은 실천", "duration": 10.0}, "outro": {"text": "오늘부터 시작하세요!", "duration": 2.0}}'::jsonb,
    15.0,
    'approved',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11)
);

-- 영상 (완료됨)
INSERT INTO videos (ad_id, company_id, account_id, script_id, title, description, s3_url, thumbnail_url, duration_seconds, file_size_bytes, resolution, status)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11),
    11,
    13,
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11)),
    '친환경 대나무 칫솔',
    '지구를 생각하는 작은 실천',
    'https://example.com/videos/toothbrush_final.mp4',
    'https://example.com/thumbnails/toothbrush_thumb.jpg',
    15,
    5242880,
    '1920x1080',
    'client_approved'
WHERE NOT EXISTS (
    SELECT 1 FROM videos WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='친환경 대나무 칫솔' AND company_id=11)
);

-- ============================================
-- 6. 시나리오 5: 게시된 영상 (성과 데이터 있음)
-- ============================================
-- YouTube 채널 먼저 생성 (admin_id는 seed_data.py에서 생성된 관리자 사용)
INSERT INTO admin_youtube_channels (admin_id, yt_channel_id, channel_name, channel_handle, access_token, refresh_token, token_expires_at, is_active)
SELECT 
    (SELECT admin_id FROM admins WHERE account_id = (SELECT account_id FROM accounts WHERE email='admin@meme-fluencer.com' LIMIT 1)),
    'UC_test_channel_001',
    '밈플루언서 공식 채널',
    '@meme-fluencer',
    'test_access_token',
    'test_refresh_token',
    NOW() + INTERVAL '30 days',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM admin_youtube_channels WHERE yt_channel_id='UC_test_channel_001'
);

INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_keymessage, status, character_id, meme_id, item_images)
SELECT 11, 13, '프리미엄 요가 매트', '스포츠용품', '완벽한 그립감, 완벽한 균형', 'completed',
       (SELECT character_id FROM company_characters WHERE character_name='차분한 곰' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       ARRAY['https://example.com/products/yoga_mat.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       'completed', 'completed', 100
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11)
);

INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
    '프리미엄 요가 매트 - 밈 시나리오',
    '완벽한 균형을 강조하는 재미있는 밈 영상',
    '{"intro": {"text": "균형이 중요해!", "duration": 3.0}, "main": {"text": "완벽한 그립감, 완벽한 균형", "duration": 10.0}, "outro": {"text": "지금 바로 시작하세요!", "duration": 2.0}}'::jsonb,
    15.0,
    'approved',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11)
);

INSERT INTO videos (ad_id, company_id, account_id, script_id, title, description, s3_url, thumbnail_url, duration_seconds, file_size_bytes, resolution, status)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11),
    11,
    13,
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11)),
    '프리미엄 요가 매트',
    '완벽한 그립감, 완벽한 균형',
    'https://example.com/videos/yoga_mat_final.mp4',
    'https://example.com/thumbnails/yoga_mat_thumb.jpg',
    15,
    6291456,
    '1920x1080',
    'client_approved'
WHERE NOT EXISTS (
    SELECT 1 FROM videos WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='프리미엄 요가 매트' AND company_id=11)
);

-- YouTube 게시
INSERT INTO admin_video_posts (video_id, channel_id, yt_video_id, yt_title, yt_description, post_status, published_at)
SELECT 
    (SELECT video_id FROM videos WHERE title='프리미엄 요가 매트' AND company_id=11),
    (SELECT channel_id FROM admin_youtube_channels WHERE yt_channel_id='UC_test_channel_001'),
    'YT_' || (SELECT video_id FROM videos WHERE title='프리미엄 요가 매트' AND company_id=11)::text,
    '프리미엄 요가 매트',
    '완벽한 그립감, 완벽한 균형',
    'published',
    NOW() - INTERVAL '30 days'
WHERE NOT EXISTS (
    SELECT 1 FROM admin_video_posts WHERE video_id = (SELECT video_id FROM videos WHERE title='프리미엄 요가 매트' AND company_id=11)
);

-- 성과 데이터 (최근 30일, 일별)
INSERT INTO performance_metrics (video_id, captured_at, snapshot_type, views, likes, dislikes, comments, shares, watch_time_seconds, average_view_duration, audience_retention_rate, engagement_rate, subscribers_gained)
SELECT 
    (SELECT video_id FROM videos WHERE title='프리미엄 요가 매트' AND company_id=11),
    NOW() - (i || ' days')::interval,
    'daily',
    10000 + (i * 500) + (random() * 1000)::int,
    (300 + (i * 15) + (random() * 50)::int),
    (10 + (random() * 5)::int),
    (50 + (i * 2) + (random() * 10)::int),
    (20 + (i * 1) + (random() * 5)::int),
    (10000 + (i * 500)) * 12,
    12.0 + (random() * 2),
    75.0 + (random() * 10),
    4.5 + (random() * 1.5),
    (5 + (random() * 3)::int)
FROM generate_series(0, 29) AS i
WHERE NOT EXISTS (
    SELECT 1 FROM performance_metrics 
    WHERE video_id = (SELECT video_id FROM videos WHERE title='프리미엄 요가 매트' AND company_id=11)
    AND DATE(captured_at) = DATE(NOW() - (i || ' days')::interval)
);

-- ============================================
-- 완료!
-- ============================================
-- 생성된 테스트 시나리오:
-- 1. 시나리오 검수 대기: 프리미엄 무선 이어폰 (pending_approval, 40%)
-- 2. 이미지 생성 중: 유기농 그린 스무디 (processing, 30%)
-- 3. 음성 생성 중: 스마트 홈 조명 (processing, 50%)
-- 4. 영상 다운로드 가능: 친환경 대나무 칫솔 (completed, 100%)
-- 5. 성과 데이터 있음: 프리미엄 요가 매트 (completed + published, 100%)
