# 시나리오 재생성 템플릿

REGENERATE_SCENARIO_TEMPLATE_V1 = """
# 역할
당신은 밈을 활용한 짧은 광고 영상 시나리오를 수정하는 마케팅 크리에이터입니다.

# 기존 시나리오
{original_scenario}

# 피드백
{feedback}

# Context: 상품 정보
---
* 회사: {company_name}
* 상품: {item_name}
* 제품 설명: {item_description}
* 캐릭터 말투: {voice_design_prompt}

# 밈 정보 (재확인)
- 밈 이름: {meme_name}
- 밈 정의: {definition}
- 핵심 문구: {key_phrase}
- 밈 활용 예시:
{usage_examples}

# 지시 사항
위 피드백을 **모두 반영**하여 시나리오를 재생성하세요.

## 주의사항
1. 피드백의 모든 요구사항을 반드시 반영
2. 밈의 맥락을 정확히 이해하고 활용
3. 상품의 핵심 가치를 명확히 전달
4. 대사는 반드시 한국어로 작성 (15~30자)
5. 총 길이 15~20초 준수

# 출력 형식
JSON 형식으로 출력하세요:
```json
{
  "title": "시나리오 제목",
  "description": "시나리오 설명",
  "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"],
  "scenes": {
    "scene1": {
      "dialogue": "캐릭터 대사 (한국어, 15~30자)",
      "visual_description": "Visual description in English",
      "scene_motion_prompt": "Motion prompt in English",
      "purpose": "씬의 목적"
    },
    "scene2": { ... },
    "scene3": { ... },
    "scene4": { ... }
  }
}
```
"""


REGENERATE_SCENARIO_TEMPLATE_V2 = """
# 역할
당신은 밈을 활용한 짧은 광고 영상 시나리오를 수정하는 마케팅 크리에이터입니다.

# 기존 시나리오
{original_scenario}

# 피드백
{feedback}

# Context: 상품 정보 (재확인)
---
* 회사: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 제품 설명: {item_description}
* 캐릭터 말투: {voice_design_prompt}
---

# 밈 정보 (재확인)
---
* 밈 이름: {meme_name}
* 밈 정의: {definition}
* 핵심 문구: {key_phrase}
* 밈 활용 예시:
{usage_examples}
---

# 지시 사항
위 피드백을 **모두 반영**하여 시나리오를 재생성하세요.

## 피드백 반영 우선순위
1. 브랜드 안전성 관련 피드백 (최우선)
2. 밈 활용 방식 개선
3. 상품 메시지 전달 개선
4. 대사 및 표현 개선

## 주의사항
1. **피드백 완전 반영**: 모든 피드백 요구사항을 반드시 반영
2. **밈 활용**: 밈의 맥락을 정확히 이해하고 자연스럽게 활용
3. **상품 전달**: 상품의 핵심 가치를 명확히 전달
4. **형식 준수**:
   - 대사는 반드시 한국어 (15~30자)
   - 총 길이 15~20초
   - JSON 형식 정확히 지키기

# 출력 형식
JSON 형식으로 출력하세요:
```json
{
  "title": "시나리오 제목 (10자 이내)",
  "description": "시나리오 설명 (1-2문장, 50자 이내)",
  "hashtags": ["#해시태그1", "#해시태그2", "#해시태그3"],
  "scenes": {
    "scene1": {
      "dialogue": "캐릭터 대사 (한국어, 15~30자)",
      "visual_description": "Visual description in English (1-2 sentences)",
      "scene_motion_prompt": "Motion prompt in English",
      "purpose": "씬의 목적 (한 문장)"
    },
    "scene2": { ... },
    "scene3": { ... },
    "scene4": { ... }
  }
}
```
"""


REGENERATE_SCENARIO_TEMPLATE_V3 = """
# 역할
당신은 밈을 활용한 짧은 광고 영상 시나리오를 수정하는 마케팅 크리에이터입니다.

# 기존 시나리오
{original_scenario}

# 피드백
{feedback}

# Context: 상품 정보 (재확인)
---
* 회사: {company_name}
* 상품/서비스명: {item_name}
* 카테고리: {item_category}
* 제품 설명: {item_description}
* 캐릭터 음성 설계 프롬프트: {voice_design_prompt}
---

# 밈 정보 (재확인)
---
* 밈 이름: {meme_name}
* 밈 정의: {definition}
* 핵심 문구: {key_phrase}
* 밈 활용 예시:
{usage_examples}
---

# 지시 사항
위 피드백을 **모두 반영**하여 시나리오를 재생성하세요.

## 피드백 반영 우선순위
1. 브랜드 안전성 관련 피드백 (최우선)
2. 밈 활용 방식 개선
3. 상품 메시지 전달 개선
4. 대사 및 표현 개선

## 시나리오 구조
- scene1 (Hook): 밈으로 즉각적 주의 흡착
- scene2, scene3 (Body): 밈과 상품의 연결을 스토리로 전개
- scene4 (Close): 명확한 행동 유도 (CTA)

## 대사 작성 규칙
- 반드시 **(감정) 대사** 형태로 작성
- 대사 중 감정이 전환되는 경우 그 부분마다 감정 표기
- **대사 길이: 반드시 15~25자(공백 미포함, 감정 표기 제외)**
- 예시:
  - (신나게) 야 이거 진짜 대박이에요! 완전 좋아, 미쳤어요!  # 19자
  - (웃으며) 뭐 뭐야 이게 진짜에요? (신나게) 완전 말도 안 되게 좋은데요!  # 20자

## visual_description 작성 규칙 (상세하게!)
각 씬의 visual_description은 **영상 제작자가 바로 촬영/제작할 수 있도록** 다음 요소를 모두 포함하여 2-3문장으로 상세히 작성:
1. **배경/장소**: 구체적인 공간
2. **카메라 앵글/구도**: 촬영 방식
3. **캐릭터 위치/포즈**: 화면 내 위치와 자세
4. **상품/소품 배치**: 상품이 어떻게 보이는지
5. **분위기/조명**: 전체적인 톤

## 주의사항
1. **피드백 완전 반영**: 모든 피드백 요구사항을 반드시 반영
2. **밈 활용**: 밈의 맥락을 정확히 이해하고 자연스럽게 활용
3. **상품 전달**: 상품의 핵심 가치를 명확히 전달
4. **모든 필드는 반드시 한국어로 작성** (영어나 다른 언어 절대 사용 금지)
5. **Bad 예시로 분류된 활용 방식 회피**
6. aggressive 또는 지나치게 sarcastic한 톤은 피하고, voice_design_prompt와 조화를 이룰 것

# 출력 형식
scene1, scene2, scene3, scene4 키로 씬들을 구성하세요.
- scene1의 scene_type은 "hook"
- scene2, scene3의 scene_type은 "body"
- scene4의 scene_type은 "close"

각 씬은 다음 필드를 포함:
- dialogue: (감정) 대사 형태 (한국어, 15~25자)
- emotion: 감정 상태 (한국어)
- action: 행동/표정 (한국어)
- visual_description: 시각 정보 (한국어, 2-3문장, 상세하게)
- scene_type: "hook", "body", "close" 중 하나

메타데이터:
- title: 15자 이내의 임팩트 있는 제목 (한국어)
- description: 50자 이내의 시나리오 요약 (한국어)
- hashtags: 3-5개의 해시태그 (# 기호 제외)
"""
