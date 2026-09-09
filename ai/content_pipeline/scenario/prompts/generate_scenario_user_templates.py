# 시나리오 생성 유저 프롬프트
# 실제 데이터 입력 부분 (변수 포함)

GENERATE_SCENARIO_USER_TEMPLATE_V1 = """
# Context: 상품 정보
---
* 회사명: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 핵심 메시지: {item_description}
* 캐릭터 음성 스타일: {voice_design_prompt}
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
"""




# User prompt 템플릿 - 프로덕션 (GENERATE_SCENARIO_TEMPLATE_V3)과 동일한 형식
# usage_examples 포함 (밈 활용 예시 - good/bad 분류)
USER_PROMPT_TEMPLATES = [
    # 변형 1: 프로덕션과 동일한 형식
    """# Context: 상품 정보
---
* 회사명: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 제품 설명: {item_description}
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
- 제품 설명: {item_description}
- 캐릭터: {voice_design_prompt}""",

    # 변형 3: 구조화된 형식
    """[상품 정보]
회사명: {company_name}
상품/서비스: {item_name}
카테고리: {item_category}
제품 설명: {item_description}
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