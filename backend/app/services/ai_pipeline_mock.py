"""
AI 파이프라인 Mock 클라이언트
실제 AI 서비스 없이 테스트용
"""
from typing import Optional, Dict, Any
from datetime import datetime
import random

from app.services.ai_pipeline_base import AIPipelineBase


class AIPipelineMockClient(AIPipelineBase):
    """AI 파이프라인 Mock 클라이언트 (테스트용)"""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or "http://mock-ai-pipeline")
    
    async def generate_character_image(
        self,
        character_prompt: str,
        character_name: str,
        company_id: int,
        aspect_ratio: str = "9:16",
        product_name: Optional[str] = None,
        product_category: Optional[str] = None,
        product_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        캐릭터 이미지 생성 Mock
        """
        image_prompt = character_prompt or ""
        voice_design_prompt = "A warm, friendly voice."
        if product_name or product_category or product_description:
            safe_name = product_name or "product"
            if not image_prompt:
                image_prompt = (
                    f"A friendly mascot character for {safe_name}, cheerful mood, clean illustration style, "
                    "full body shot, soft lighting."
                )
            voice_design_prompt = "A warm, friendly voice with an upbeat and approachable tone."

        return {
            "image_url": f"https://s3.amazonaws.com/admeme-media-dev/mock/character_{company_id}_{random.randint(1000, 9999)}.png",
            "image_path": f"mock/character_{company_id}.png",
            "model": "imagen-3.0-mock",
            "voice_design_prompt": voice_design_prompt,
            "image_prompt": image_prompt,
        }

    async def generate_scene_image(
        self,
        product_image_url: str,
        character_image_url: str,
        scenario_prompt: str,
        scene_key: str,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """
        씬 이미지 생성 Mock
        """
        return {
            "image_url": f"https://s3.amazonaws.com/admeme-media-dev/mock/scene_{scene_key}_{random.randint(1000, 9999)}.png",
            "image_path": f"mock/scene_{scene_key}.png",
        }
    
    async def generate_scenario(
        self,
        product_name: str,
        product_category: str,
        product_highlight: str,
        meme_id: Optional[int] = None,
        ad_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        시나리오 생성 Mock
        """
        return {
            "title": f"{product_name} 광고 시나리오",
            "scenes": [
                {
                    "content": "안녕하세요! 오늘은 특별한 제품을 소개합니다",
                    "visual_description": "캐릭터가 카메라를 향해 밝게 인사하는 장면",
                    "duration": 5.0,
                    "timestamp": "0:00",
                },
                {
                    "content": f"{product_highlight}",
                    "visual_description": "제품을 클로즈업하며 특징을 보여주는 장면",
                    "duration": 10.0,
                    "timestamp": "0:05",
                },
                {
                    "content": "지금 바로 만나보세요!",
                    "visual_description": "캐릭터가 제품을 들고 마무리 인사하는 장면",
                    "duration": 5.0,
                    "timestamp": "0:15",
                },
            ],
            "script_id": random.randint(1, 9999),
        }
    
    async def generate_voice(
        self,
        text: str,
        voice_description: str,
        character_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        """
        음성 생성 Mock
        """
        # 텍스트 길이 기반으로 duration 계산 (대략 1초당 3글자)
        duration = len(text) / 3.0
        
        return {
            "voice_url": f"https://s3.amazonaws.com/admeme-media-dev/mock/voice_{character_id}_{random.randint(1000, 9999)}.mp3",
            "voice_id": f"mock_voice_{character_id}",
            "duration_seconds": round(duration, 2),
            "size_bytes": random.randint(50000, 200000),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "text": text,
                "voice_description": voice_description,
                "model": "elevenlabs-mock"
            }
        }
    
    async def regenerate_video(
        self,
        video_id: int,
        ad_id: int,
        revision_notes: str,
        feedback: Optional[str],
        company_id: int
    ) -> Dict[str, Any]:
        """
        영상 재생성 Mock
        """
        return {
            "video_id": video_id,
            "status": "processing",
            "message": "영상 재생성이 시작되었습니다 (Mock)",
            "estimated_time_seconds": 180,
            "metadata": {
                "revision_notes": revision_notes,
                "feedback": feedback
            }
        }

    async def generate_video(
        self,
        ad_id: int,
        script_id: int,
        company_id: int,
        character_id: int = None,
        scenes: list = None,
        character_image_url: str = None,
        voice_id: str = None,
        title: str = None,
        product_image_url: str = None,
        voice_description: str = None,
        clone_prompt_url: str = None,
        character_description: str = None,
    ) -> Dict[str, Any]:
        """
        영상 생성 Mock
        """
        return {
            "video_id": random.randint(1, 9999),
            "video_url": f"https://s3.amazonaws.com/admeme-media-dev/mock/video_{ad_id}_{random.randint(1000, 9999)}.mp4",
            "status": "completed",
            "estimated_duration": random.randint(60, 180),
            "created_at": datetime.utcnow().isoformat()
        }

    async def regenerate_character_image(
        self,
        character_id: int,
        original_image_url: str,
        revision_notes: str,
        character_prompt: str,
        company_id: int,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """캐릭터 이미지 재생성 Mock (AI 검수 포함)"""
        return {
            "image_url": f"https://s3.amazonaws.com/admeme-media-dev/mock/character_regen_{company_id}_{random.randint(1000, 9999)}.png",
            "image_path": f"mock/character_regen_{company_id}.png",
            "model": "nanobanana-mock",
            "verification_score": 0.85,
            "verification_decision": "approved",
            "retry_count": 0,
        }

    async def revise_scenario(
        self,
        script_id: int,
        scene_revisions: list,
        company_id: int,
        ad_id: int = None
    ) -> Dict[str, Any]:
        """
        시나리오 씬별 수정 Mock
        """
        revised_scenes = []
        for i, rev in enumerate(scene_revisions):
            revised_scenes.append({
                "scene_number": rev.get("scene_number", i + 1),
                "content": f"수정된 씬 {rev.get('scene_number', i + 1)}: {rev.get('scenario_notes', '')}",
                "timestamp": f"0:{(i * 5):02d}"
            })

        return {
            "script_id": script_id,
            "scenes": revised_scenes,
            "title": f"수정된 시나리오 (script {script_id})",
            "status": "revised",
        }

    async def revise_video(
        self,
        video_id: int,
        scene_revisions: list,
        company_id: int
    ) -> Dict[str, Any]:
        """
        영상 씬별 수정 Mock
        """
        return {
            "video_id": video_id,
            "status": "processing",
            "estimated_duration": random.randint(60, 180),
            "message": "영상 수정이 시작되었습니다 (Mock)",
            "created_at": datetime.utcnow().isoformat()
        }
