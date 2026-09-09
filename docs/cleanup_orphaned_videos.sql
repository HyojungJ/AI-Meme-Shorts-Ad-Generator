-- script_id=2606이 videos 테이블에 남아있는지 확인
SELECT video_id, script_id, ad_id, s3_url, created_at 
FROM videos 
WHERE script_id = 2606;

-- ad_id=3000과 관련된 videos 레코드 확인
SELECT v.video_id, v.script_id, v.ad_id, v.s3_url 
FROM videos v
LEFT JOIN scenario_scripts ss ON v.script_id = ss.script_id
WHERE ss.script_id IS NULL OR ss.ad_id = 3000;

-- 고아 레코드 삭제 (scenario_scripts에 없는 videos)
-- 실행 전 위 SELECT로 확인 후 실행하세요
BEGIN;

DELETE FROM videos 
WHERE script_id IN (
    SELECT v.script_id 
    FROM videos v
    LEFT JOIN scenario_scripts ss ON v.script_id = ss.script_id
    WHERE ss.script_id IS NULL
);

-- 또는 script_id=2606만 삭제
DELETE FROM videos WHERE script_id = 2606;

COMMIT;
