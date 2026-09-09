"""Instruction 다양화 - 오버피팅 방지용 지시문 변형

v3 설계 원칙:
- System prompt: 최소화 — 밈 통합 1개 핵심 규칙 + 하드 제약 (1인/1장소)
- 포맷/길이 규칙 제거: structured output 스키마 + validation이 강제
- Instruction variants: 한 줄 태스크 설명만 (system prompt와 중복 없음)
"""

import random


# System prompt - 밈 통합을 최우선 규칙으로 단순화 (v3)
# 설계: 포맷/길이는 structured output + validation이 잡음 → 창작 품질에 집중
SYSTEM_PROMPT = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 최우선 규칙: 밈이 스토리의 뼈대
밈의 핵심 요소(문구, 행동, 감정)가 최소 2개 씬에 걸쳐 스토리를 이끌어야 합니다.
밈을 빼면 광고가 성립하지 않아야 합니다. 밈 대사를 "와 좋다"로 바꿔도 작동하면 실패입니다.

## 제약
- 등장인물 1명 (혼자 카메라 보며 말하는 형식)
- 한 장소에서 촬영 (앵글만 변경)
- 대사: "(감정) 대사" 형태, 짧은 구어체
- scene4: 상품명 + CTA
- 한국어

## thinking (시나리오 작성 전 필수)
1. 밈의 원래 사용 상황과 감정
2. 밈 핵심 요소가 등장하는 씬 번호들과 이유
3. 교체 테스트: 밈을 "와 좋다"로 바꿔도 광고가 성립하면 → 재설계"""


# Instruction 변형 (오버피팅 방지 - 동일한 의미, 다른 표현)
# System prompt가 품질 규칙을 담당하므로, instruction은 태스크 설명 + 리마인더만
INSTRUCTION_VARIANTS = [
    # 변형 1: 기본
    "위 밈과 상품으로 4씬 광고 시나리오를 작성하세요.",

    # 변형 2: 밈 강조
    "이 밈을 중심으로 상품 광고 시나리오(4씬)를 만들어 주세요.",

    # 변형 3: 상황 유도
    "이 밈이 자연스럽게 터지는 상품 광고 상황을 4씬으로 설계하세요.",

    # 변형 4: 결과물 중심
    "밈 × 상품 광고 시나리오를 JSON으로 작성하세요.",

    # 변형 5: 간결
    "밈을 활용한 15초 광고 시나리오를 작성하세요.",
]


# User prompt 템플릿 - 프로덕션 (GENERATE_SCENARIO_TEMPLATE_V3)과 동일한 형식
# usage_examples 포함 (밈 활용 예시 - good/bad 분류)
USER_PROMPT_TEMPLATES = [
    # 변형 1: 프로덕션과 동일한 형식
    """# Context: 상품 정보
---
* 회사명: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 제품 설명: {item_keymessage}
* 캐릭터 말투: {voice_design_prompt}
---

# Data: 활용할 밈
---
* 밈 이름: {meme_name}
* 밈 정의: {definition}
* 밈 핵심 문구: {key_phrase}

* 밈 활용 예시 종류
- 사용 맥락
- 사용 예시
- 예시 분류: good, bad
- 예시 분류가 bad일 경우 사유
- 예시 톤: playful, sarcastic, aggressive, friendly, neutral
{usage_examples}
---

# 지시 사항
{instruction}""",

    # 변형 2: 간결한 형식
    """{instruction}

---
## 밈
- 이름: {meme_name}
- 정의: {definition}
- 핵심 문구: {key_phrase}
{usage_examples}

## 기업
- 회사: {company_name}
- 상품: {item_name} ({item_category})
- 제품 설명: {item_keymessage}
- 캐릭터: {voice_design_prompt}""",

    # 변형 3: 구조화된 형식
    """[상품 정보]
회사명: {company_name}
상품/서비스: {item_name}
카테고리: {item_category}
제품 설명: {item_keymessage}
캐릭터 톤: {voice_design_prompt}

[밈 정보]
밈 이름: {meme_name}
밈 정의: {definition}
핵심 문구: {key_phrase}

[밈 활용 예시]
{usage_examples}

[작업 지시]
{instruction}""",
]


def get_random_instruction() -> str:
    """랜덤 instruction 변형 반환"""
    return random.choice(INSTRUCTION_VARIANTS)


def get_random_user_prompt_template() -> str:
    """랜덤 user prompt 템플릿 반환"""
    return random.choice(USER_PROMPT_TEMPLATES)


def format_user_prompt(
    meme_name: str,
    definition: str,
    key_phrase: str,
    company_name: str,
    item_name: str,
    item_category: str,
    item_keymessage: str,
    voice_design_prompt: str,
    usage_examples: str = "",
) -> str:
    """랜덤 템플릿으로 user prompt 생성"""
    template = get_random_user_prompt_template()
    instruction = get_random_instruction()

    return template.format(
        meme_name=meme_name,
        definition=definition or "정보 없음",
        key_phrase=key_phrase or meme_name,
        company_name=company_name,
        item_name=item_name,
        item_category=item_category,
        item_keymessage=item_keymessage,
        voice_design_prompt=voice_design_prompt,
        usage_examples=usage_examples or "예시 없음",
        instruction=instruction,
    )
