"""파인튜닝 모델용 프롬프트 템플릿

학습 데이터(instruction_variants.py)와 동일한 형식.
학습-추론 프롬프트 정렬을 위해 추론 시에도 동일 구조 사용.
"""

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


USER_PROMPT_TEMPLATES = [
    # 변형 1: 프로덕션과 동일한 형식
    """# Context: 상품 정보
---
* 회사명: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 핵심 메시지: {item_description}
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
- 메시지: {item_description}
- 캐릭터: {voice_design_prompt}""",

    # 변형 3: 구조화된 형식
    """[상품 정보]
회사명: {company_name}
상품/서비스: {item_name}
카테고리: {item_category}
핵심 메시지: {item_description}
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
