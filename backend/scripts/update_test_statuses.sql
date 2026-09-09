-- 기존 테스트 데이터의 상태 업데이트

-- 유기농 그린 스무디 -> 이미지 검수 대기 (processing 사용)
UPDATE ad_requests 
SET status = 'processing'
WHERE item_name = '유기농 그린 스무디' AND company_id = 11;

UPDATE workflow_execution 
SET status = 'processing', 
    current_stage = 'image_generation', 
    progress_percentage = 30
WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name = '유기농 그린 스무디' AND company_id = 11);

-- 스마트 홈 조명 -> 음성 검수 대기 (processing 사용)
UPDATE ad_requests 
SET status = 'processing'
WHERE item_name = '스마트 홈 조명' AND company_id = 11;

UPDATE workflow_execution 
SET status = 'processing', 
    current_stage = 'voice_generation', 
    progress_percentage = 50
WHERE ad_id = (SELECT ad_id FROM ad_requests WHERE item_name = '스마트 홈 조명' AND company_id = 11);
