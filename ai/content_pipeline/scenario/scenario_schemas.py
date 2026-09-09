"""
시나리오 생성을 위한 Pydantic 스키마
LLM structured output 형식 정의
"""
from pydantic import BaseModel, Field
from typing import List, Dict
from enum import Enum


class StructureType(str, Enum):
    """시나리오 구조 타입"""
    HOOK = "hook"  # 3-5초, 시선 포착
    BODY = "body"  # 7-9초, 밈 활용 스토리
    CLOSE = "close"  # 3-5초, CTA


class Scene(BaseModel):
    """개별 씬 정보"""
    scene_type: StructureType = Field(..., description="씬 타입 (hook/body/close)")
    
    # TTS용 데이터
    dialogue: str = Field(
        ..., 
        description="(감정) 대사 형태로 작성. 예: (진지하게) 지금 바로 시작해 보시는 거 어때요? (활기차게) 진심으로 강력 추천합니다!"
    )
    
    # 영상 생성용 데이터
    action: str = Field(..., description="캐릭터의 행동/표정 설명")
    visual_description: str = Field(..., description="배경, 소품, 화면 구성")


class Scenario(BaseModel):
    """전체 시나리오 (3단 구조)"""
    scene1: Scene = Field(..., description="Hook 씬")
    scene2: Scene = Field(..., description="Body 씬 1")
    scene3: Scene = Field(..., description="Body 씬 2")
    scene4: Scene = Field(..., description="Close 씬")
    
    # 메타 정보
    title: str = Field(..., max_length=50, description="시나리오 제목 (15자 이내 권장)")
    description: str = Field(..., max_length=200, description="시나리오 요약 설명 (50자 이내 권장)")
    hashtags: List[str] = Field(..., min_length=3, max_length=5, description="해시태그 3-5개 (밈, 상품 관련)")

class FeedbackCategory(str, Enum):
    """피드백 카테고리"""
    BRAND_SAFETY = "brand_safety"
    MESSAGE_DELIVERY = "message_delivery"
    CHARACTER_CONSISTENCY = "character_consistency"
    MEME_USAGE = "meme_usage"
    COMPLETENESS = "completeness"


class FeedbackItem(BaseModel):
    """개별 피드백"""
    category: FeedbackCategory = Field(..., description="피드백 카테고리")
    description: str = Field(..., description="구체적 개선 사항")


class SceneReview(BaseModel):
    """씬별 평가 결과"""
    scene_key: str = Field(..., pattern="^scene[1-4]$")
    brand_safety_score: float = Field(..., ge=0, le=10)
    message_delivery_score: float = Field(..., ge=0, le=10)
    character_consistency_score: float = Field(..., ge=0, le=10)
    meme_usage_score: float = Field(..., ge=0, le=10)
    completeness_score: float = Field(..., ge=0, le=10)
    feedback_items: List[FeedbackItem] = Field(default_factory=list, description="이 씬의 개선사항 리스트")


class ReviewResult(BaseModel):
    """전체 시나리오 검수 결과"""
    scene_reviews: List[SceneReview] = Field(..., min_length=4, max_length=4, description="씬별 평가 (4개)")
    total_score: float = Field(..., ge=0, le=200, description="전체 점수 합산")
    approved: bool = Field(..., description="승인 여부")