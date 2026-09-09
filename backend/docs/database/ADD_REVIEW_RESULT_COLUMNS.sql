-- ============================================
-- 콘텐츠 검수 피드백 저장을 위한 컬럼 추가
-- ============================================
-- 작성일: 2026-01-27
-- 목적: videos, company_characters 테이블에 review_result JSONB 컬럼 추가
-- 
-- 이 컬럼은 사용자의 검수 피드백 및 수정 요청 내역을 저장합니다.
-- ============================================

-- 1. videos 테이블에 review_result 컬럼 추가
ALTER TABLE public.videos 
ADD COLUMN review_result jsonb NULL;

COMMENT ON COLUMN public.videos.review_result IS '영상 검수 피드백 및 수정 요청 내역 (JSONB)';

-- 2. company_characters 테이블에 review_result 컬럼 추가
ALTER TABLE public.company_characters 
ADD COLUMN review_result jsonb NULL;

COMMENT ON COLUMN public.company_characters.review_result IS '캐릭터 이미지/음성 검수 피드백 및 수정 요청 내역 (JSONB)';

-- ============================================
-- 확인 쿼리
-- ============================================

-- 컬럼 추가 확인
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('videos', 'company_characters')
  AND column_name = 'review_result';

-- ============================================
-- 롤백 (필요시)
-- ============================================

-- ALTER TABLE public.videos DROP COLUMN review_result;
-- ALTER TABLE public.company_characters DROP COLUMN review_result;

-- ============================================
-- review_result 데이터 구조 예시
-- ============================================

/*
{
  "latest": {
    "revision_notes": "배경음악을 더 밝게, 자막 크기를 키워주세요",
    "feedback": "전체적으로 좋은데 세부 조정이 필요해요",
    "requested_by": 13,
    "requested_at": "2026-01-27T10:30:00"
  },
  "history": [
    {
      "revision_notes": "첫 번째 수정 요청",
      "feedback": "목소리가 너무 작아요",
      "requested_by": 13,
      "requested_at": "2026-01-27T10:00:00"
    },
    {
      "revision_notes": "두 번째 수정 요청",
      "feedback": "이번엔 목소리가 너무 커요",
      "requested_by": 13,
      "requested_at": "2026-01-27T10:30:00"
    }
  ]
}
*/

-- ============================================
-- 사용 예시
-- ============================================

-- 영상 피드백 조회
SELECT 
    video_id,
    title,
    status,
    review_result->'latest'->>'revision_notes' as latest_feedback,
    jsonb_array_length(review_result->'history') as feedback_count
FROM public.videos
WHERE review_result IS NOT NULL;

-- 캐릭터 피드백 조회
SELECT 
    character_id,
    character_name,
    is_active,
    review_result->'latest'->>'revision_notes' as latest_feedback,
    jsonb_array_length(review_result->'history') as feedback_count
FROM public.company_characters
WHERE review_result IS NOT NULL;
