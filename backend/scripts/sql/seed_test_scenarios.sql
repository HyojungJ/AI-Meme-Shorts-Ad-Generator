-- ============================================
-- ?ŒìŠ¤???œë‚˜ë¦¬ì˜¤ë³??°ì´???ì„±
-- ============================================
-- ê¸°ì¡´ ê³„ì • ?¬ìš©: manager@test.com (company_id=11, account_id=13)
-- ê¸°ì¡´ ë°??¬ìš©: meme_id???¤ì œ DB?ì„œ ì¡°íšŒ

-- ë³€???¤ì • (?¤ì œ ê°’ìœ¼ë¡??€ì²??„ìš”)
-- company_id: 11 (?ŒìŠ¤?¸ê¸°??
-- account_id: 13 (manager@test.com)
-- meme_id: ?¤ì œ ë°?ID ?¬ìš©

-- ============================================
-- 1. ìºë¦­??3ê°??ì„± (ê°??œë‚˜ë¦¬ì˜¤??
-- ============================================
INSERT INTO company_characters (company_id, character_name, character_mood, character_style, voice_tone, image_url, is_active)
VALUES 
(11, 'ë°ì? ? ë¼', 'ë°ê³  ?œê¸°ì°?, 'ê·€?¬ìš´ 3D ?¤í???, 'ê²½ì¾Œ???¬ì„± ëª©ì†Œë¦?, 'https://example.com/characters/rabbit.png', true),
(11, 'ì°¨ë¶„??ê³?, 'ì°¨ë¶„?˜ê³  ? ë¢°ê°??ˆëŠ”', '?¬ì‹¤?ì¸ 3D ?¤í???, 'ì¤‘ì????¨ì„± ëª©ì†Œë¦?, 'https://example.com/characters/bear.png', true),
(11, '?¥ë‚œê¾¸ëŸ¬ê¸?ê³ ì–‘??, '?¥ë‚œ?¤ëŸ½ê³??¬ì¹˜?ˆëŠ”', 'ë§Œí™” ?¤í???, '?¡í†¡ ?€???¬ì„± ëª©ì†Œë¦?, 'https://example.com/characters/cat.png', true)
ON CONFLICT DO NOTHING;

-- ============================================
-- 2. ?œë‚˜ë¦¬ì˜¤ 1: ?œë‚˜ë¦¬ì˜¤ ê²€???€ê¸?
-- ============================================
-- ê´‘ê³  ?”ì²­
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_description, status, character_id, meme_id, item_images)
SELECT 11, 13, '?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´??, '?„ì?œí’ˆ', '?„ë²½???Œì§ˆ, ?„ë²½???ìœ ', 'pending_approval',
       (SELECT character_id FROM company_characters WHERE character_name='ë°ì? ? ë¼' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       ARRAY['https://example.com/products/earphone.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´?? AND company_id=11);

-- ?Œí¬?Œë¡œ??
INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´?? AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       'pending_approval', 'scenario_review', 40
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´?? AND company_id=11)
);

-- ?œë‚˜ë¦¬ì˜¤ ?¤í¬ë¦½íŠ¸ (ê²€???€ê¸?
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´?? AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
    '?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´??- ë°??œë‚˜ë¦¬ì˜¤',
    '?„ë²½???Œì§ˆ??ê°•ì¡°?˜ëŠ” ?¬ë??ˆëŠ” ë°??ìƒ',
    '{"intro": {"text": "?Œì§ˆ???´ë ‡ê²?ì¢‹ë‹¤ê³?", "duration": 3.0}, "main": {"text": "?„ë²½???Œì§ˆ, ?„ë²½???ìœ ", "duration": 10.0}, "outro": {"text": "ì§€ê¸?ë°”ë¡œ êµ¬ë§¤?˜ì„¸??", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´?? AND company_id=11)
);

-- ============================================
-- 3. ?œë‚˜ë¦¬ì˜¤ 2: ?´ë?ì§€ ?ì„± ì¤?
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_description, status, character_id, meme_id, item_images)
SELECT 11, 13, '? ê¸°??ê·¸ë¦° ?¤ë¬´??, '?ìŒë£?, 'ë§¤ì¼ ?„ì¹¨ ê±´ê°•???œì‘', 'processing',
       (SELECT character_id FROM company_characters WHERE character_name='ì°¨ë¶„??ê³? AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       ARRAY['https://example.com/products/smoothie.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       'processing', 'image_generation', 30
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11)
);

-- ?œë‚˜ë¦¬ì˜¤ ?¤í¬ë¦½íŠ¸ (?´ë?ì§€ ?ì„±??
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
    '? ê¸°??ê·¸ë¦° ?¤ë¬´??- ë°??œë‚˜ë¦¬ì˜¤',
    'ê±´ê°•???„ì¹¨??ê°•ì¡°?˜ëŠ” ?¬ë??ˆëŠ” ë°??ìƒ',
    '{"intro": {"text": "?„ì¹¨???¬ë¼ì§„ë‹¤!", "duration": 3.0}, "main": {"text": "ë§¤ì¼ ?„ì¹¨ ê±´ê°•???œì‘", "duration": 10.0}, "outro": {"text": "ì§€ê¸?ë°”ë¡œ ?œì‘?˜ì„¸??", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11)
);

-- ?´ë?ì§€ ?ì„± (ê²€???€ê¸?
INSERT INTO image_generations (character_id, script_id, prompt, model, image_url, metadata_json)
SELECT 
    (SELECT character_id FROM company_characters WHERE character_name='ì°¨ë¶„??ê³? AND company_id=11 LIMIT 1),
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11)),
    'ì°¨ë¶„?˜ê³  ? ë¢°ê°??ˆëŠ” ê³?ìºë¦­?? ?¬ì‹¤?ì¸ 3D ?¤í???,
    'dall-e-3',
    'https://example.com/generated/bear_image.png',
    '{"size": "1024x1024", "status": "pending_review"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM image_generations WHERE script_id = (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='? ê¸°??ê·¸ë¦° ?¤ë¬´?? AND company_id=11))
);

-- ============================================
-- 4. ?œë‚˜ë¦¬ì˜¤ 3: ?Œì„± ?ì„± ì¤?
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_description, status, character_id, meme_id, item_images)
SELECT 11, 13, '?¤ë§ˆ????ì¡°ëª…', 'ê°€?„ì œ??, '?¹ì‹ ??ê³µê°„?????¤ë§ˆ?¸í•˜ê²?, 'processing',
       (SELECT character_id FROM company_characters WHERE character_name='?¥ë‚œê¾¸ëŸ¬ê¸?ê³ ì–‘?? AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
       ARRAY['https://example.com/products/light.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
       'processing', 'voice_generation', 50
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11)
);

-- ?œë‚˜ë¦¬ì˜¤ ?¤í¬ë¦½íŠ¸ (?Œì„± ?ì„±??
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 2 LIMIT 1),
    '?¤ë§ˆ????ì¡°ëª… - ë°??œë‚˜ë¦¬ì˜¤',
    '?¤ë§ˆ?¸í•œ ?í™œ??ê°•ì¡°?˜ëŠ” ?¬ë??ˆëŠ” ë°??ìƒ',
    '{"intro": {"text": "?´ì œ ì¡°ëª…???¤ë§ˆ?¸í•˜ê²?", "duration": 3.0}, "main": {"text": "?¹ì‹ ??ê³µê°„?????¤ë§ˆ?¸í•˜ê²?, "duration": 10.0}, "outro": {"text": "ì§€ê¸?ë°”ë¡œ ê²½í—˜?˜ì„¸??", "duration": 2.0}}'::jsonb,
    15.0,
    'pending',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11)
);

-- ?Œì„± ?ì„± (ê²€???€ê¸?
INSERT INTO voice_generations (character_id, script_id, scene_key, text_content, audio_url, duration_seconds, settings_json)
SELECT 
    (SELECT character_id FROM company_characters WHERE character_name='?¥ë‚œê¾¸ëŸ¬ê¸?ê³ ì–‘?? AND company_id=11 LIMIT 1),
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11)),
    'intro',
    '?´ì œ ì¡°ëª…???¤ë§ˆ?¸í•˜ê²?',
    'https://example.com/generated/cat_voice.mp3',
    3.0,
    '{"model": "elevenlabs", "voice_id": "test123", "status": "pending_review"}'::jsonb
WHERE NOT EXISTS (
    SELECT 1 FROM voice_generations WHERE script_id = (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?¤ë§ˆ????ì¡°ëª…' AND company_id=11))
);

-- ============================================
-- 5. ?œë‚˜ë¦¬ì˜¤ 4: ?„ë£Œ???ìƒ (?¤ìš´ë¡œë“œ ê°€??
-- ============================================
INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_description, status, character_id, meme_id, item_images)
SELECT 11, 13, 'ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”', '?í™œ?©í’ˆ', 'ì§€êµ¬ë? ?ê°?˜ëŠ” ?‘ì? ?¤ì²œ', 'completed',
       (SELECT character_id FROM company_characters WHERE character_name='ë°ì? ? ë¼' AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       ARRAY['https://example.com/products/toothbrush.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
       'completed', 'completed', 100
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11)
);

-- ?œë‚˜ë¦¬ì˜¤ (?¹ì¸??
INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' LIMIT 1),
    'ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†” - ë°??œë‚˜ë¦¬ì˜¤',
    '?˜ê²½ ë³´í˜¸ë¥?ê°•ì¡°?˜ëŠ” ?¬ë??ˆëŠ” ë°??ìƒ',
    '{"intro": {"text": "?Œë¼?¤í‹±?€ ?´ì œ ê·¸ë§Œ!", "duration": 3.0}, "main": {"text": "ì§€êµ¬ë? ?ê°?˜ëŠ” ?‘ì? ?¤ì²œ", "duration": 10.0}, "outro": {"text": "?¤ëŠ˜ë¶€???œì‘?˜ì„¸??", "duration": 2.0}}'::jsonb,
    15.0,
    'approved',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11)
);

-- ?ìƒ (?„ë£Œ??
INSERT INTO videos (ad_id, company_id, account_id, script_id, title, description, s3_url, thumbnail_url, duration_seconds, file_size_bytes, resolution, status)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11),
    11,
    13,
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11)),
    'ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”',
    'ì§€êµ¬ë? ?ê°?˜ëŠ” ?‘ì? ?¤ì²œ',
    'https://example.com/videos/toothbrush_final.mp4',
    'https://example.com/thumbnails/toothbrush_thumb.jpg',
    15,
    5242880,
    '1920x1080',
    'client_approved'
WHERE NOT EXISTS (
    SELECT 1 FROM videos WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†”' AND company_id=11)
);

-- ============================================
-- 6. ?œë‚˜ë¦¬ì˜¤ 5: ê²Œì‹œ???ìƒ (?±ê³¼ ?°ì´???ˆìŒ)
-- ============================================
-- YouTube ì±„ë„ ë¨¼ì? ?ì„± (admin_id??seed_data.py?ì„œ ?ì„±??ê´€ë¦¬ì ?¬ìš©)
INSERT INTO admin_youtube_channels (admin_id, yt_channel_id, channel_name, channel_handle, access_token, refresh_token, token_expires_at, is_active)
SELECT 
    (SELECT admin_id FROM admins WHERE account_id = (SELECT account_id FROM accounts WHERE email='admin@meme-fluencer.com' LIMIT 1)),
    'UC_test_channel_001',
    'ë°ˆí”Œë£¨ì–¸??ê³µì‹ ì±„ë„',
    '@meme-fluencer',
    'test_access_token',
    'test_refresh_token',
    NOW() + INTERVAL '30 days',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM admin_youtube_channels WHERE yt_channel_id='UC_test_channel_001'
);

INSERT INTO ad_requests (company_id, account_id, item_name, item_category, item_description, status, character_id, meme_id, item_images)
SELECT 11, 13, '?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸', '?¤í¬ì¸ ìš©??, '?„ë²½??ê·¸ë¦½ê°? ?„ë²½??ê· í˜•', 'completed',
       (SELECT character_id FROM company_characters WHERE character_name='ì°¨ë¶„??ê³? AND company_id=11 LIMIT 1),
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       ARRAY['https://example.com/products/yoga_mat.jpg']
WHERE NOT EXISTS (SELECT 1 FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11);

INSERT INTO workflow_execution (execution_id, ad_id, company_id, account_id, meme_id, status, current_stage, progress_percentage)
SELECT gen_random_uuid(),
       (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11),
       11, 13,
       (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
       'completed', 'completed', 100
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_execution WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)
);

INSERT INTO scenario_scripts (ad_id, meme_id, title, description, scenes, total_duration, approval_status, generation_type)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11),
    (SELECT meme_id FROM memes WHERE status='READY' OFFSET 1 LIMIT 1),
    '?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸ - ë°??œë‚˜ë¦¬ì˜¤',
    '?„ë²½??ê· í˜•??ê°•ì¡°?˜ëŠ” ?¬ë??ˆëŠ” ë°??ìƒ',
    '{"intro": {"text": "ê· í˜•??ì¤‘ìš”??", "duration": 3.0}, "main": {"text": "?„ë²½??ê·¸ë¦½ê°? ?„ë²½??ê· í˜•", "duration": 10.0}, "outro": {"text": "ì§€ê¸?ë°”ë¡œ ?œì‘?˜ì„¸??", "duration": 2.0}}'::jsonb,
    15.0,
    'approved',
    'initial'
WHERE NOT EXISTS (
    SELECT 1 FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)
);

INSERT INTO videos (ad_id, company_id, account_id, script_id, title, description, s3_url, thumbnail_url, duration_seconds, file_size_bytes, resolution, status)
SELECT 
    (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11),
    11,
    13,
    (SELECT script_id FROM scenario_scripts WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)),
    '?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸',
    '?„ë²½??ê·¸ë¦½ê°? ?„ë²½??ê· í˜•',
    'https://example.com/videos/yoga_mat_final.mp4',
    'https://example.com/thumbnails/yoga_mat_thumb.jpg',
    15,
    6291456,
    '1920x1080',
    'client_approved'
WHERE NOT EXISTS (
    SELECT 1 FROM videos WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)
);

-- YouTube ê²Œì‹œ
INSERT INTO admin_video_posts (video_id, channel_id, yt_video_id, yt_title, yt_description, post_status, published_at)
SELECT 
    (SELECT video_id FROM videos WHERE title='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11),
    (SELECT channel_id FROM admin_youtube_channels WHERE yt_channel_id='UC_test_channel_001'),
    'YT_' || (SELECT video_id FROM videos WHERE title='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)::text,
    '?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸',
    '?„ë²½??ê·¸ë¦½ê°? ?„ë²½??ê· í˜•',
    'published',
    NOW() - INTERVAL '30 days'
WHERE NOT EXISTS (
    SELECT 1 FROM admin_video_posts WHERE video_id = (SELECT video_id FROM videos WHERE title='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)
);

-- ?±ê³¼ ?°ì´??(ìµœê·¼ 30?? ?¼ë³„)
INSERT INTO performance_metrics (video_id, captured_at, snapshot_type, views, likes, dislikes, comments, shares, watch_time_seconds, average_view_duration, audience_retention_rate, engagement_rate, subscribers_gained)
SELECT 
    (SELECT video_id FROM videos WHERE title='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11),
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
    WHERE video_id = (SELECT video_id FROM videos WHERE title='?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸' AND company_id=11)
    AND DATE(captured_at) = DATE(NOW() - (i || ' days')::interval)
);

-- ============================================
-- ?„ë£Œ!
-- ============================================
-- ?ì„±???ŒìŠ¤???œë‚˜ë¦¬ì˜¤:
-- 1. ?œë‚˜ë¦¬ì˜¤ ê²€???€ê¸? ?„ë¦¬ë¯¸ì—„ ë¬´ì„  ?´ì–´??(pending_approval, 40%)
-- 2. ?´ë?ì§€ ?ì„± ì¤? ? ê¸°??ê·¸ë¦° ?¤ë¬´??(processing, 30%)
-- 3. ?Œì„± ?ì„± ì¤? ?¤ë§ˆ????ì¡°ëª… (processing, 50%)
-- 4. ?ìƒ ?¤ìš´ë¡œë“œ ê°€?? ì¹œí™˜ê²??€?˜ë¬´ ì¹«ì†” (completed, 100%)
-- 5. ?±ê³¼ ?°ì´???ˆìŒ: ?„ë¦¬ë¯¸ì—„ ?”ê? ë§¤íŠ¸ (completed + published, 100%)

