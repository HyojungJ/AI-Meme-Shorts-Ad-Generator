"""
AI 파이프라인 클라이언트
팀원이 운영하는 별도 AI 서비스와 통신
"""
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.services.ai_pipeline_base import AIPipelineBase


class AIPipelineClient(AIPipelineBase):
    """AI 파이프라인 HTTP 클라이언트"""

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url or getattr(settings, 'AI_PIPELINE_URL', 'http://localhost:8001'))
        self.timeout = 300.0
    
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
        캐릭터 이미지 생성 요청
        
        Args:
            character_prompt: 캐릭터 생성 프롬프트
            character_name: 캐릭터 이름
            company_id: 회사 ID
            aspect_ratio: 이미지 비율
        
        Returns:
            AI 파이프라인 응답 (image_url, metadata 등)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "character_prompt": character_prompt,
                "character_name": character_name,
                "company_id": company_id,
                "aspect_ratio": aspect_ratio,
            }
            if product_name or product_category or product_description:
                payload.update({
                    "product_name": product_name,
                    "product_category": product_category,
                    "product_description": product_description,
                })
            response = await client.post(
                f"{self.base_url}/generate-character",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def suggest_character_prompts_from_product(
        self,
        item_name: str,
        item_category: Optional[str] = None,
        item_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """제품 정보 기반 캐릭터 프롬프트 추천"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "item_name": item_name,
                "item_category": item_category,
                "item_description": item_description,
            }
            response = await client.post(
                f"{self.base_url}/suggest-character-prompts",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            if "character_image_prompt" not in data and "character_prompt" in data:
                data["character_image_prompt"] = data["character_prompt"]
            if "character_voice_prompt" not in data and "voice_description" in data:
                data["character_voice_prompt"] = data["voice_description"]
            return data
    
    async def generate_scene_image(
        self,
        product_image_url: str,
        character_image_url: str,
        scenario_prompt: str,
        scene_key: str,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """
        씬 이미지 생성 요청
        
        Args:
            product_image_url: 상품 이미지 URL
            character_image_url: 캐릭터 이미지 URL
            scenario_prompt: 시나리오 프롬프트
            scene_key: 씬 키 (intro, main, outro 등)
            aspect_ratio: 이미지 비율
        
        Returns:
            AI 파이프라인 응답
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/generate-scene",
                json={
                    "product_image_url": product_image_url,
                    "character_image_url": character_image_url,
                    "scenario_prompt": scenario_prompt,
                    "scene_key": scene_key,
                    "aspect_ratio": aspect_ratio
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def generate_scenario(
        self,
        product_name: str,
        product_category: str,
        product_highlight: str,
        meme_id: Optional[int] = None,
        ad_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        시나리오 생성 요청

        Args:
            product_name: 상품명
            product_category: 상품 카테고리
            product_highlight: 상품 하이라이트
            meme_id: 밈 ID
            ad_id: 광고 요청 ID

        Returns:
            AI 파이프라인 응답 (시나리오 2개)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/generate-scenario",
                json={
                    "product_name": product_name,
                    "product_category": product_category,
                    "product_highlight": product_highlight,
                    "meme_id": meme_id,
                    "ad_id": ad_id,
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def generate_voice(
        self,
        text: str,
        voice_description: str,
        character_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        """
        음성 생성 요청
        
        Args:
            text: 음성으로 변환할 텍스트
            voice_description: 음성 설명/스타일
            character_id: 캐릭터 ID
            company_id: 회사 ID
        
        Returns:
            AI 파이프라인 응답 (voice_url, voice_id 등)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/generate-voice",
                json={
                    "text": text,
                    "voice_description": voice_description,
                    "character_id": character_id,
                    "company_id": company_id
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def regenerate_video(
        self,
        video_id: int,
        ad_id: int,
        revision_notes: str,
        feedback: Optional[str],
        company_id: int
    ) -> Dict[str, Any]:
        """
        영상 재생성 요청

        Args:
            video_id: 영상 ID
            ad_id: 광고 요청 ID
            revision_notes: 수정 요청 내용
            feedback: 추가 피드백
            company_id: 회사 ID

        Returns:
            AI 파이프라인 응답
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/regenerate-video",
                json={
                    "video_id": video_id,
                    "ad_id": ad_id,
                    "revision_notes": revision_notes,
                    "feedback": feedback,
                    "company_id": company_id
                }
            )
            response.raise_for_status()
            return response.json()

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
        영상 생성 요청

        Args:
            ad_id: 광고 요청 ID
            script_id: 시나리오 스크립트 ID
            company_id: 회사 ID
            character_id: 캐릭터 ID (TTS DB 저장용)
            scenes: 시나리오 씬 목록
            character_image_url: 캐릭터 이미지 URL
            voice_id: ElevenLabs 보이스 ID
            title: 영상 제목
            product_image_url: 제품 이미지 URL (씬 이미지 합성용)
            voice_description: Qwen TTS instruct용 음성 설명
            clone_prompt_url: Qwen clone prompt S3 URL

        Returns:
            AI 파이프라인 응답 (video_url, estimated_duration 등)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "ad_id": ad_id,
                "script_id": script_id,
                "company_id": company_id,
                "character_id": character_id,
                "scenes": scenes,
                "character_image_url": character_image_url,
                "voice_id": voice_id,
                "title": title,
                "product_image_url": product_image_url,
            }
            if voice_description:
                payload["voice_description"] = voice_description
            if clone_prompt_url:
                payload["clone_prompt_url"] = clone_prompt_url
            if character_description:
                payload["character_description"] = character_description
            response = await client.post(
                f"{self.base_url}/generate-video",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def regenerate_character_image(
        self,
        character_id: int,
        original_image_url: str,
        revision_notes: str,
        character_prompt: str,
        company_id: int,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """캐릭터 이미지 재생성 요청 (AI 검수 포함)"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/regenerate-character-image",
                json={
                    "character_id": character_id,
                    "original_image_url": original_image_url,
                    "revision_notes": revision_notes,
                    "character_prompt": character_prompt,
                    "company_id": company_id,
                    "aspect_ratio": aspect_ratio,
                }
            )
            response.raise_for_status()
            return response.json()

    async def revise_scenario(
        self,
        script_id: int,
        scene_revisions: list,
        company_id: int,
        ad_id: int = None
    ) -> Dict[str, Any]:
        """
        시나리오 씬별 수정 요청

        Args:
            script_id: 시나리오 스크립트 ID
            scene_revisions: 씬별 수정 요청 목록
            company_id: 회사 ID

        Returns:
            AI 파이프라인 응답 (수정된 시나리오)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/revise-scenario",
                json={
                    "script_id": script_id,
                    "scene_revisions": scene_revisions,
                    "company_id": company_id,
                    "ad_id": ad_id
                }
            )
            response.raise_for_status()
            return response.json()

    async def revise_video(
        self,
        video_id: int,
        scene_revisions: list,
        company_id: int
    ) -> Dict[str, Any]:
        """
        영상 씬별 수정 요청

        Args:
            video_id: 영상 ID
            scene_revisions: 씬별 수정 요청 목록
            company_id: 회사 ID

        Returns:
            AI 파이프라인 응답
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/revise-video",
                json={
                    "video_id": video_id,
                    "scene_revisions": scene_revisions,
                    "company_id": company_id
                }
            )
            response.raise_for_status()
            return response.json()
