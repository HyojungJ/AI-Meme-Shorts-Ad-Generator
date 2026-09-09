"""
AI 파이프라인 클라이언트 ABC 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class AIPipelineBase(ABC):
    """AI 파이프라인 클라이언트 공통 인터페이스"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url

    @abstractmethod
    async def generate_character_image(
        self,
        character_prompt: str,
        character_name: str,
        company_id: int,
        aspect_ratio: str = "9:16",
        product_name: Optional[str] = None,
        product_category: Optional[str] = None,
        product_description: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def generate_scene_image(
        self,
        product_image_url: str,
        character_image_url: str,
        scenario_prompt: str,
        scene_key: str,
        aspect_ratio: str = "9:16",
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def generate_scenario(
        self,
        product_name: str,
        product_category: str,
        product_highlight: str,
        meme_id: Optional[int] = None,
        ad_id: Optional[int] = None,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def generate_voice(
        self,
        text: str,
        voice_description: str,
        character_id: int,
        company_id: int,
    ) -> Dict[str, Any]: ...

    @abstractmethod
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
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def regenerate_video(
        self,
        video_id: int,
        ad_id: int,
        revision_notes: str,
        feedback: Optional[str],
        company_id: int,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def regenerate_character_image(
        self,
        character_id: int,
        original_image_url: str,
        revision_notes: str,
        character_prompt: str,
        company_id: int,
        aspect_ratio: str = "9:16",
        **kwargs,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def revise_scenario(
        self,
        script_id: int,
        scene_revisions: list,
        company_id: int,
        ad_id: int = None,
    ) -> Dict[str, Any]: ...

    @abstractmethod
    async def revise_video(
        self,
        video_id: int,
        scene_revisions: list,
        company_id: int,
    ) -> Dict[str, Any]: ...
