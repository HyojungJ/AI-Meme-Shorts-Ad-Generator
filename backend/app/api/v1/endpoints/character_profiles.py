"""
캐릭터 프로필 API 엔드포인트
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class CharacterProfile(BaseModel):
    """캐릭터 프로필 응답 모델"""
    id: str
    name: str
    subtitle: str
    emoji: str
    appearance: str
    voice: str
    full_description: str
    image_url: str
    audio_url: str


@router.get("", response_model=List[CharacterProfile])
def get_character_profiles():
    """
    캐릭터 프로필 목록 조회
    
    사용자가 선택할 수 있는 캐릭터 프로필 샘플을 반환합니다.
    각 프로필에는 이미지와 음성 샘플이 포함되어 있습니다.
    """
    profiles = [
        {
            "id": "friendly-20s-female",
            "name": "친근한 20대 여성",
            "subtitle": "밝고 친근한 분위기",
            "emoji": "😊",
            "appearance": "20대 초반 여성, 밝은 미소, 자연스러운 메이크업, 캐주얼한 스타일",
            "voice": "밝고 친근한 톤, 귀여운 말투, 부드럽고 경쾌한 목소리",
            "full_description": "20대 초반 여성, 밝은 미소, 자연스러운 메이크업, 캐주얼한 스타일. 밝고 친근한 톤, 귀여운 말투, 부드럽고 경쾌한 목소리.",
            "image_url": "/static/character-profiles/sample1.png",
            "audio_url": "/static/character-profiles/sample1.mp3"
        },
        {
            "id": "professional-30s-male",
            "name": "전문적인 30대 남성",
            "subtitle": "신뢰감 있는 전문가",
            "emoji": "👔",
            "appearance": "30대 중반 남성, 단정한 헤어스타일, 깔끔한 정장 스타일",
            "voice": "신뢰감 있는 차분한 목소리, 명확한 발음, 안정적인 톤",
            "full_description": "30대 중반 남성, 단정한 헤어스타일, 깔끔한 정장 스타일. 신뢰감 있는 차분한 목소리, 명확한 발음, 안정적인 톤.",
            "image_url": "/static/character-profiles/sample2.png",
            "audio_url": "/static/character-profiles/sample2.mp3"
        },
        {
            "id": "energetic-rabbit",
            "name": "발랄한 토끼 캐릭터",
            "subtitle": "귀엽고 생기 넘치는",
            "emoji": "🐰",
            "appearance": "토끼 콘셉트의 캐릭터, 밝고 친근한 인상, 사람과 유사한 제스처와 행동",
            "voice": "활기차고 에너지 넘치는 목소리, 빠른 템포, 밝은 톤",
            "full_description": "토끼 콘셉트의 캐릭터, 밝고 친근한 인상, 사람과 유사한 제스처와 행동. 활기차고 에너지 넘치는 목소리, 빠른 템포, 밝은 톤.",
            "image_url": "/static/character-profiles/sample3.png",
            "audio_url": "/static/character-profiles/sample3.mp3"
        }
    ]
    
    return profiles
