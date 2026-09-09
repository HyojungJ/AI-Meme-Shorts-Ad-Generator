"""
Content Pipeline - helper functions, constants, schemas.
"""
import base64
import logging
import os
import sys
import tempfile
import time

logger = logging.getLogger(__name__)
from pathlib import Path
from langchain_openai import ChatOpenAI

from pydantic import BaseModel, Field

# 팀원 시나리오 코드 import (상대 import 해결)
_scenario_path = Path(__file__).parent / "scenario"
if str(_scenario_path) not in sys.path:
    sys.path.insert(0, str(_scenario_path))

from content_pipeline.voice.nodes import design_voice_node, generate_voice_node, _get_service as get_voice_service
from content_pipeline.voice.state import get_initial_state as get_voice_state
from content_pipeline.voice.config import load_voice_config
from content_pipeline.image.nodes import generate_character_image_node, generate_scene_image_node
from content_pipeline.video.config import load_video_config
from content_pipeline.video.nodes import generate_video_node, merge_video_node
from content_pipeline.schema import Scene, ScenarioOutput
from content_pipeline.scenario.prompts.generate_scenario_templates import GENERATE_SCENARIO_TEMPLATE_V4
from content_pipeline.scenario.prompts.review_scenario_templates import REVIEW_SCENARIO_TEMPLATE_V3
from content_pipeline.scenario.prompts.regenerate_scenario_templates import REGENERATE_SCENARIO_TEMPLATE_V3
from content_pipeline.scenario.prompts.meme_example_templates import MEME_EXAMPLE_TEMPLATE_V1


# Voice Design용 샘플 텍스트 (ElevenLabs 요구사항: 100자 이상)
# -> 이걸 사용자에게 들려줘서 검수받음.
VOICE_DESIGN_SAMPLE_TEXT = """안녕하세요, 저는 활기차고 밝은 캐릭터입니다. 오늘도 좋은 하루 보내세요!
여러분과 함께하는 이 시간이 정말 즐겁습니다. 매일매일 새로운 이야기를 들려드릴게요.
앞으로도 많은 응원 부탁드립니다. 감사합니다!"""


def _build_product_context(company_data: dict, meme_data: dict) -> str:
    parts = []
    if company_data.get("item_name"):
        parts.append(f"Product: {company_data['item_name']}")
    if company_data.get("item_category"):
        parts.append(f"Category: {company_data['item_category']}")
    if meme_data.get("meme_name"):
        parts.append(f"Meme: {meme_data['meme_name']}")
    phrase = meme_data.get("key_phrase", "")
    if phrase and phrase != "핵심 문구 없음":
        parts.append(f"Key phrase: {phrase}")
    return " | ".join(parts) if parts else ""


# === 상품(제품) 정보 기반 캐릭터 이미지용/음성용 분리를 위한 스키마 ===


class CharacterStyleSplit(BaseModel):
    """상품(제품) 정보 기반 캐릭터 이미지용/음성용 프롬프트로 분리 생성 결과."""
    character_prompt: str = Field(
        description="Gemini 이미지 생성용 서술형 프롬프트 (영어, 스타일/조명/분위기 포함)"
    )
    voice_description: str = Field(
        description="ElevenLabs 음성 생성용 프롬프트 (영어, 나이/음색/속도/감정 포함)"
    )


PRODUCT_CHARACTER_PROMPT_TEMPLATE = """
당신은 AI로 광고용 캐릭터를 생성하는 크리에이티브 디렉터다.
아래의 제품 정보를 바탕으로, 해당 제품에 어울리는 캐릭터 이미지 생성용 프롬프트와 음성 생성용 프롬프트를 작성해라.

[입력]
- 제품명: {item_name}
- 제품종류: {item_category}
- 제품설명: {item_description}

[캐릭터 설계 규칙]
- 캐릭터는 광고에서 제품을 직접 소개하고 말하는 역할이다

[character_prompt (Gemini 이미지 생성용)]
**형식:** 서술형 문장 (키워드 나열 금지)
**필수 포함 요소:**
- 외형 정보: (나이대 / 성별 / 주요 특징)
- 캐릭터 형태: (동물형 / 인간형 / 의인화된 오브젝트)
- 비주얼 스타일: (예: illustration, 3D, cartoon 등 / 실사 제외)
- 조명(lighting): 조명 방향과 분위기
- 구도: 프레이밍 (full body shot 고정)
- 분위기: 전체적인 무드

**예시 1:**
입력:
- 제품명: 스마트 워치
- 제품종류: 웨어러블 디바이스
- 제품설명: 건강 관리와 일상 알림을 동시에 제공하는 라이프스타일 스마트 워치
출력: "20대 후반의 인간형 캐릭터로, 단정하면서도 활동적인 인상을 주는 외형. 깔끔하고 현대적인 3D 일러스트 스타일로 표현된다. 부드러운 전면 조명이 캐릭터를 비추는 full body shot 구도로, 밝고 신뢰감 있는 분위기의 라이프스타일 테크 광고에 어울리는 무드를 연출한다."

**예시 2:**
입력:
- 제품명: 과일 탄산음료
- 제품종류: 음료
- 제품설명: 상큼한 과일 향과 청량한 탄산이 특징인 가볍게 즐기는 탄산음료
출력: "귀여운 과일 모양의 캐릭터로, 둥글고 말랑한 실루엣에 밝은 표정이 특징이며, 과일의 신선함을 떠올리게 하는 컬러를 사용한 카툰 스타일 일러스트로 표현된다. 위에서 부드럽게 내려오는 조명이 캐릭터를 비추는 full body shot 구도로, 발랄하고 경쾌한 분위기의 음료 광고에 어울리는 밝은 무드를 전달한다."

[voice_description (Qwen3 음성 디자인용)]
**형식:** 자연어 서술 (1~2문장)
**필수 포함 요소:**
- 나이대: "20대", "30대" 등
- 성별 (또는 음색 특성)
- 음색(timbre): warm, smooth, gravelly, crisp 등
- 말하는 속도(pacing): speaks slowly, conversational pace 등
- 감정 톤(emotion): energetic, calm, professional 등

**예시 1:**
입력:
- 제품명: 스마트 워치
- 제품종류: 웨어러블 디바이스
- 제품설명: 건강 관리와 일상 알림을 동시에 제공하는 라이프스타일 스마트 워치
출력: "20대 후반 연령대의 중성적인 음색을 가진 목소리로, 부드럽고 또렷한 음색에 약간의 에너지가 느껴지며, 일상 대화에 가까운 속도로 말한다. 친근하면서도 자신감 있는 감정 톤으로 제품을 자연스럽게 설명하는 광고용 음성이다."

[주의사항]
- 입력에 없는 정보는 자연스럽게 추론하여 채워주세요
- 둘 다 비어있으면 안 됨
"""


def suggest_character_prompts_from_product(
    item_name: str,
    item_category: str | None = None,
    item_description: str | None = None,
) -> dict:
    """
    상품(제품) 정보 기반 캐릭터 이미지/음성 프롬프트 추천 (LLM 사용).

    Returns:
        {
            "character_prompt": "A cheerful young man in his early 20s with bright eyes...",
            "voice_description": "A young man in his early 20s with an energetic, warm voice..."
        }
    """
    if not (item_name or item_category or item_description):
        return {
            "character_prompt": "A friendly young adult with bright eyes and a warm, welcoming smile. The lighting is soft and even, creating a cheerful atmosphere. Photorealistic style with natural features.",
            "voice_description": "A young adult with a bright, friendly voice. They speak at a natural conversational pace with a warm, welcoming tone. Their voice has a smooth, clear timbre.",
        }

    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    structured_llm = llm.with_structured_output(CharacterStyleSplit)

    prompt = PRODUCT_CHARACTER_PROMPT_TEMPLATE.format(
        item_name=item_name or "",
        item_category=item_category or "",
        item_description=item_description or "",
    )
    result = structured_llm.invoke(prompt)

    return {
        "character_prompt": result.character_prompt,
        "voice_description": result.voice_description,
    }


def _save_voice_sample(audio_base64: str, voice_name: str) -> str:
    """
    Base64 인코딩된 샘플 음성을 디코딩하여 storage에 저장.

    Args:
        audio_base64: Base64 인코딩된 오디오 데이터
        voice_name: 보이스 이름 (파일명에 사용)

    Returns:
        저장된 샘플 음성의 URL
    """
    config = load_voice_config()
    service = get_voice_service()

    audio_bytes = base64.b64decode(audio_base64)

    config.temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=config.temp_dir, suffix=".mp3", delete=False
    ) as tmp:
        tmp.write(audio_bytes)
        temp_path = Path(tmp.name)

    try:
        timestamp = int(time.time())
        key = f"voice_samples/{voice_name}_{timestamp}.mp3"

        result = service.storage.upload_file(
            temp_path,
            key=key,
            metadata={"voice_name": voice_name, "type": "sample"},
        )
        return result.url
    finally:
        if temp_path.exists():
            temp_path.unlink()


def convert_to_scenes(scenario) -> list[dict]:
    """
    팀원 Scenario (scene1~scene4 구조) → scenes[] 리스트로 변환.

    Args:
        scenario: Scenario Pydantic 모델 (scene1, scene2, scene3, scene4)

    Returns:
        scenes: 4개 씬 딕셔너리 리스트
    """
    scenes = []

    # scene1 (hook), scene2 (body), scene3 (body), scene4 (close)
    scene_attrs = ["scene1", "scene2", "scene3", "scene4"]

    for i, attr in enumerate(scene_attrs, start=1):
        scene = getattr(scenario, attr)
        scenes.append({
            "scene_key": f"scene_{i:02d}",
            "scene_number": i,
            "structure_type": scene.scene_type.value if hasattr(scene.scene_type, 'value') else scene.scene_type,
            "dialogue": scene.dialogue,
            "scenario_prompt": scene.visual_description,
            "duration": getattr(scene, "duration_seconds", 5.0),
            "action": scene.action,
        })

    return scenes
