"""프롬프트 A/B 테스트 스크립트

여러 프롬프트 변형을 다양한 밈/상품 조합으로 테스트하고 결과를 비교.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from content_pipeline.scenario.finetuned_client import generate_with_finetuned
from content_pipeline.scenario.scenario_database import load_company_data, load_meme_data
from content_pipeline.scenario.prompts.meme_example_templates import MEME_EXAMPLE_TEMPLATE_V1
from content_pipeline.scenario.finetuned_prompts import INSTRUCTION_VARIANTS, USER_PROMPT_TEMPLATES

# ── 테스트 케이스 ──
TEST_CASES = [
    {"ad_id": 3154, "label": "MacBook Pro + 테크놀로지아"},
    {"ad_id": 3152, "label": "스팸 + 운동많이된다"},
    {"ad_id": 3156, "label": "시원스쿨 + 핵심을찔렀어"},
]

# ── 프롬프트 변형 ──

# v3: 현재 버전 (예시 과다)
PROMPT_V3_BLOATED = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 핵심 원칙: Setup → Punchline
밈은 scene3에서 "터지는 한 순간"에 집중하세요. scene1-2는 그 순간을 위한 빌드업입니다.
밈을 여러 씬에 반복하지 마세요. scene3에서 한 번만 강렬하게 터뜨리세요.

## 4씬 구조

### scene1 (hook): 공감되는 상황 제시
- 시청자가 "아 나도 그래" 할 수 있는 일상 속 문제나 욕구
- 밈은 아직 등장하지 않음. 상황만 깔기
- 감정: 답답, 고민, 귀찮음 등 부정적 감정으로 시작

### scene2 (body): 전환점 + 상품 등장
- scene1의 문제를 해결하거나 반전시키는 계기
- 상품이 자연스럽게 등장하며 기대감/반신반의 형성
- 감정: 궁금, 기대, 반신반의 (scene1과 다른 감정)

### scene3 (body): 밈이 터지는 클라이맥스
- 상품 체험의 감정이 극에 달해 밈이 자연스럽게 튀어나오는 순간
- 밈의 원래 감정/맥락과 상품 체험이 겹치는 지점
- 감정: 놀람, 감탄, 흥분 (scene1-2와 확연히 다른 폭발적 감정)

### scene4 (close): CTA
- 상품명을 반드시 언급 + 구체적 행동 유도
- 밈의 여운을 살린 마무리

## 제약
- 등장인물 1명 (혼자 카메라 보며 말하는 형식)
- 한 장소에서 촬영 (앵글만 변경)
- 한국어

## 대사 규칙 (dialogue) ★중요★
- 반드시 "(감정) 대사" 형태. 감정 전환 시 각 부분마다 감정 표기
- 모든 씬의 대사가 15~25자 (공백 미포함, 감정 표기 제외). 15자 미만 절대 불가
- 셋업 씬(scene1-2)도 반드시 15자 이상. 짧은 감탄/질문으로 때우지 말 것
  - 나쁜 예: "(답답) 왜 이렇게 느려?" → 8자, 위반
  - 좋은 예: "(답답) 아 이거 로딩만 벌써 삼십분째인데 진짜" → 18자
  - 나쁜 예: "(궁금) 이게 가능해?" → 6자, 위반
  - 좋은 예: "(반신반의) 이게 진짜 된다고? 한번 써보기나 하자" → 19자
- 밈 문구가 짧으면 대사 안에 자연스럽게 녹여서 15자 이상으로 만들 것
  - 나쁜 예: "(감탄) 테크놀로지아!" → 6자, 위반
  - 좋은 예: "(놀라며) 이 속도 실화야? 완전 테크놀로지아잖아!" → 20자
- 광고 카피가 아닌 실제 사람이 할 법한 자연스러운 구어체
- dialogue 필드에는 대사만 작성 (visual_description, emotion 등 다른 정보 포함 금지)

## visual_description 규칙
각 씬의 visual_description은 다음 5요소를 모두 포함하여 2-3문장으로 상세히 작성:
1. 배경/장소 (구체적 공간, 4씬 모두 같은 장소)
2. 카메라 앵글/구도 (클로즈업, 전신 샷, 45도 측면 등)
3. 캐릭터 위치/포즈
4. 상품/소품 배치
5. 분위기/조명

## thinking (시나리오 작성 전 필수)
1. 밈의 원래 감정과 사용 상황
2. 이 감정이 상품 체험 중 자연스럽게 발생하는 구체적 상황 설계
3. scene1→2→3 감정 변화 설계 (예: 답답→반신반의→폭발)
4. scene3 대사 초안: 밈 문구를 15자 이상 자연스러운 문장으로 녹인 대사
5. 교체 테스트: scene3에서 밈을 "와 좋다"로 바꿔도 임팩트가 유지되면 → 재설계"""


# v4: 간결 원칙 (예시 최소화)
PROMPT_V4_CONCISE = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 구조: Setup → Punchline
밈은 scene3 클라이맥스에서 딱 한 번만 터뜨리세요. scene1-2는 빌드업입니다.

- scene1 (hook): 시청자가 공감할 일상 속 문제. 밈은 아직 등장하지 않음.
- scene2 (body): 상품이 등장하며 전환. 기대감 형성.
- scene3 (body): 상품 체험 감정이 극에 달해 밈이 자연스럽게 터지는 순간.
- scene4 (close): 상품명 + CTA.

씬별로 감정이 확실히 달라야 합니다 (예: 답답 → 반신반의 → 폭발 → 여유).

## 대사 규칙
- "(감정) 대사" 형태. 모든 씬 15~25자 (감정 태그 제외, 공백 미포함). 15자 미만 절대 불가.
- 밈 문구가 짧으면 자연스러운 문장 안에 녹일 것. 밈만 단독으로 외치지 마세요.
- 실제 사람이 할 법한 구어체. 광고 카피 금지.

## 제약
- 1명, 한 장소, 앵글만 변경
- 한국어
- dialogue 필드에는 대사만 (다른 정보 섞지 말 것)

## visual_description
2-3문장. 배경/장소, 앵글, 캐릭터 포즈, 상품 배치, 분위기/조명 포함.

## thinking
시나리오 전에 반드시: 밈 감정 분석 → 상품 체험과 겹치는 상황 설계 → 감정 아크 설계 → scene3 대사 초안 → 교체 테스트"""


# v5: 미니멀 (원칙만, 모델에 자율성)
PROMPT_V5_MINIMAL = """밈 광고 시나리오 작가. 15초 숏폼, 4씬.

구조: 공감(scene1) → 전환(scene2) → 밈 폭발(scene3) → CTA(scene4)

scene1-2에서 일상 문제를 깔고, scene3에서 상품 체험의 감정이 극에 달해 밈이 자연스럽게 터지게 하세요.
밈은 scene3에서 한 번만. 반복 금지.

규칙:
- "(감정) 대사" 형태, 씬당 15~25자 (감정 태그 제외). 밈 문구가 짧으면 문장 안에 녹일 것.
- 1명, 한 장소, 한국어
- 씬별 감정이 확연히 다를 것
- dialogue에는 대사만

thinking: 밈 감정 → 상품 체험과 겹치는 상황 → 감정 아크 → scene3 대사 초안 → 교체 테스트"""


# v6: 구조 + 원칙만 (예시 제거, 규칙 명확)
PROMPT_V6_RULES_ONLY = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 구조: Setup → Punchline
밈은 scene3에서 딱 한 번만 터뜨리세요. scene1-2는 빌드업, scene4는 CTA입니다.
밈을 여러 씬에 반복하면 안 됩니다.

### scene1 (hook): 공감
시청자가 공감할 일상 속 문제나 욕구를 구체적으로 묘사. 밈은 등장하지 않음.
상품과 관련된 구체적 불편함이나 상황을 대사로 표현.

### scene2 (body): 전환
상품이 등장하며 scene1의 문제를 해결할 기대감 형성.
scene1과 확연히 다른 감정으로 전환.

### scene3 (body): 밈 클라이맥스
상품 체험의 감정이 극에 달해 밈이 자연스럽게 터지는 순간.
밈 문구를 자연스러운 구어체 문장 안에 녹여서 사용.
밈만 단독으로 외치지 말고, 상품 체험 반응과 함께 한 문장으로 연결.

### scene4 (close): CTA
상품명을 포함한 구체적 추천 문장. 검색, 구매 등 행동 유도.

## 대사 규칙
- "(감정) 대사" 형태. 감정 전환 시 각 부분마다 감정 표기.
- 모든 씬(scene1~4) 대사 15~25자 (감정 태그 제외, 공백 미포함). 15자 미만 절대 불가.
- 밈 문구가 짧아도 주변 문맥과 함께 15자 이상 문장으로 구성.
- 실제 사람이 카메라 앞에서 할 법한 자연스러운 구어체.
- dialogue 필드에는 대사 텍스트만 작성.

## 제약
- 1명, 한 장소(앵글만 변경), 한국어
- 씬별 감정이 서로 달라야 함 (같은 감정 반복 금지)

## visual_description
2-3문장. 배경/장소(4씬 동일), 앵글, 캐릭터 포즈, 상품 배치, 분위기/조명 포함.

## thinking (필수)
1. 밈의 원래 감정과 상황
2. 상품 체험 중 이 감정이 자연스럽게 발생하는 구체적 상황
3. 감정 아크: scene1(부정) → scene2(전환) → scene3(폭발) → scene4(여유)
4. 각 씬 대사 초안과 글자수 확인 (15자 미만이면 문장을 구체적으로 늘리기)
5. 교체 테스트: scene3 밈을 "와 좋다"로 바꿔도 임팩트가 유지되면 → 재설계"""


# v7: 규칙 + thinking 자기교정 강화
PROMPT_V7_SELFCHECK = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 구조: Setup → Punchline
밈은 scene3에서 딱 한 번만 터뜨리세요. scene1-2는 빌드업, scene4는 CTA입니다.

### scene1 (hook): 공감
상품과 관련된 일상 속 불편함이나 욕구를 구체적으로 묘사. 밈 등장하지 않음.

### scene2 (body): 전환
상품이 등장하며 기대감 형성. scene1과 다른 감정.

### scene3 (body): 밈 클라이맥스
상품 체험의 감정이 극에 달해 밈이 터지는 순간.
밈 문구를 구어체 문장 안에 녹여서 사용. 밈만 단독으로 외치지 말 것.

### scene4 (close): CTA
상품명을 포함하여 구체적 추천 이유와 함께 행동 유도. "검색해봐", "한번 써봐" 등.

## 대사 규칙
- "(감정) 대사" 형태. 모든 씬 15~25자 (감정 태그 제외, 공백 미포함).
- 15자 = "이거써보니까진짜완전다르더라" 정도의 길이. 이보다 짧으면 안 됩니다.
- 상황, 감정, 행동을 구체적으로 묘사하면 자연스럽게 15자 이상이 됩니다.
- dialogue 필드에는 대사 텍스트만 작성.

## 제약
- 1명, 한 장소(앵글만 변경), 한국어
- 씬별 감정이 서로 달라야 함

## visual_description
2-3문장. 배경(4씬 동일), 앵글, 포즈, 상품 배치, 조명 포함.

## thinking (필수 — 반드시 아래 순서대로)
1. 밈 감정 분석: 이 밈이 원래 어떤 상황/감정에서 쓰이는가
2. 상황 설계: 상품 체험 중 이 감정이 자연스럽게 발생하는 구체적 상황
3. 감정 아크: scene1→2→3→4 각각 어떤 감정인지 (서로 달라야 함)
4. 대사 초안 + 글자수 세기:
   - scene1: "[초안]" → N자. 15자 미만이면 → 상황을 더 구체적으로 묘사하여 수정 → "[수정]" → N자
   - scene2: "[초안]" → N자. 15자 미만이면 → 수정
   - scene3: "[초안]" → N자. 밈이 문장에 녹아있는지 확인
   - scene4: "[초안]" → N자. 상품명이 포함되어 있는지 확인. 15자 미만이면 → 수정
5. 교체 테스트: scene3 밈을 "와 좋다"로 바꿔도 임팩트 유지되면 → 재설계"""


# v8: 글자수 대신 "2문장 이상" 규칙
PROMPT_V8_TWO_SENTENCES = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

## 구조: Setup → Punchline
밈은 scene3에서 딱 한 번만 터뜨리세요. scene1-2는 빌드업, scene4는 CTA입니다.

### scene1 (hook): 공감
상품과 관련된 일상 속 불편함이나 욕구를 구체적으로 묘사. 밈 등장하지 않음.

### scene2 (body): 전환
상품이 등장하며 기대감 형성. scene1과 다른 감정.

### scene3 (body): 밈 클라이맥스
상품 체험의 감정이 극에 달해 밈이 터지는 순간.
밈 문구를 구어체 문장 안에 녹여서 사용. 밈만 단독으로 외치지 말 것.

### scene4 (close): CTA
상품명을 포함하여 추천 이유와 행동 유도.

## 대사 규칙 (가장 중요)
- "(감정) 대사" 형태.
- 각 대사는 반드시 2문장 이상으로 구성. 한 문장짜리 대사는 금지.
  올바른 대사: "(답답) 아 이 작업 왜 이렇게 안 끝나지? 벌써 한 시간째야"
  올바른 대사: "(놀라며) 헐 이게 진짜 된다고? 와 완전 달라졌잖아"
- 실제 사람이 카메라 앞에서 할 법한 자연스러운 구어체.
- dialogue 필드에는 대사 텍스트만 작성.

## 제약
- 1명, 한 장소(앵글만 변경), 한국어
- 씬별 감정이 서로 달라야 함

## visual_description
2-3문장. 배경(4씬 동일), 앵글, 포즈, 상품 배치, 조명 포함.

## thinking (필수)
1. 밈 감정 분석
2. 상품 체험 중 이 감정이 자연스럽게 발생하는 상황
3. 감정 아크: scene1(부정) → scene2(전환) → scene3(폭발) → scene4(여유)
4. 각 씬 대사 초안 (모두 2문장 이상인지 확인)
5. 교체 테스트"""


PROMPTS = {
    "v3_bloated": PROMPT_V3_BLOATED,
    "v4_concise": PROMPT_V4_CONCISE,
    "v5_minimal": PROMPT_V5_MINIMAL,
    "v6_rules_only": PROMPT_V6_RULES_ONLY,
    "v7_selfcheck": PROMPT_V7_SELFCHECK,
    "v8_two_sentences": PROMPT_V8_TWO_SENTENCES,
}


def count_chars(dialogue: str) -> int:
    """감정 태그 제거 후 공백 제외 글자수."""
    clean = re.sub(r"\([^)]*\)\s*", "", dialogue)
    return len(clean.replace(" ", ""))


def has_json_garbage(dialogue: str) -> bool:
    """대사에 JSON 찌꺼기가 섞여있는지."""
    return "visual_description" in dialogue or "emotion" in dialogue or "'," in dialogue


def run_test(prompt_name: str, prompt: str, ad_id: int, label: str) -> dict:
    """단일 테스트 실행."""
    company = load_company_data(ad_id)
    meme = load_meme_data(company["meme_id"], MEME_EXAMPLE_TEMPLATE_V1)

    user_prompt = USER_PROMPT_TEMPLATES[0].format(
        company_name=company["company_name"],
        item_name=company["item_name"],
        item_category=company["item_category"],
        item_description=company["item_description"],
        voice_design_prompt=company["voice_design_prompt"],
        meme_name=meme["meme_name"],
        definition=meme["definition"],
        key_phrase=meme["key_phrase"],
        usage_examples=meme["usage_examples"],
        instruction=INSTRUCTION_VARIANTS[0],
    )

    result = generate_with_finetuned(system_prompt=prompt, user_prompt=user_prompt)
    scenario = result.scenario

    scenes = {}
    issues = []
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        scene = getattr(scenario, key)
        chars = count_chars(scene.dialogue)
        garbage = has_json_garbage(scene.dialogue)

        if chars < 15:
            issues.append(f"{key}: {chars}자 (15자 미만)")
        if chars > 25:
            issues.append(f"{key}: {chars}자 (25자 초과)")
        if garbage:
            issues.append(f"{key}: JSON 찌꺼기")

        scenes[key] = {
            "dialogue": scene.dialogue,
            "chars": chars,
            "action": scene.action,
            "garbage": garbage,
        }

    # 밈 반복 체크
    meme_phrase = meme["key_phrase"].strip("'").strip()
    meme_count = sum(
        1 for k, v in scenes.items()
        if meme_phrase and meme_phrase in v["dialogue"]
    )
    if meme_count > 1:
        issues.append(f"밈 반복 {meme_count}회")

    return {
        "prompt": prompt_name,
        "test_case": label,
        "thinking": result.thinking[:200] if result.thinking else "",
        "scenes": scenes,
        "issues": issues,
        "issue_count": len(issues),
        "title": scenario.title,
    }


def print_result(r: dict):
    print(f"\n{'='*60}")
    print(f"[{r['prompt']}] {r['test_case']}")
    print(f"{'='*60}")
    for key in ["scene1", "scene2", "scene3", "scene4"]:
        s = r["scenes"][key]
        flag = " ⚠️" if s["chars"] < 15 or s["garbage"] else " ✓"
        print(f"  {key}: {s['dialogue'][:60]}{'...' if len(s['dialogue'])>60 else ''}")
        print(f"         {s['chars']}자{flag}")
    print(f"  title: {r['title'][:30]}")
    if r["issues"]:
        print(f"  ⚠️ 문제: {', '.join(r['issues'])}")
    else:
        print(f"  ✅ 문제 없음")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", choices=list(PROMPTS.keys()), default=None)
    parser.add_argument("--ad", type=int, default=None)
    args = parser.parse_args()

    results = []

    if args.prompt and args.ad:
        # 단일 테스트
        label = next((t["label"] for t in TEST_CASES if t["ad_id"] == args.ad), f"ad={args.ad}")
        r = run_test(args.prompt, PROMPTS[args.prompt], args.ad, label)
        print_result(r)
        results.append(r)
    else:
        # 전체 테스트
        prompt_list = [args.prompt] if args.prompt else list(PROMPTS.keys())
        ad_list = [args.ad] if args.ad else [t["ad_id"] for t in TEST_CASES]

        for pname in prompt_list:
            for tc in TEST_CASES:
                if tc["ad_id"] not in ad_list:
                    continue
                print(f"\n▶ Testing {pname} × {tc['label']}...")
                try:
                    r = run_test(pname, PROMPTS[pname], tc["ad_id"], tc["label"])
                    print_result(r)
                    results.append(r)
                except Exception as e:
                    print(f"  ❌ 실패: {e}")
                    results.append({"prompt": pname, "test_case": tc["label"], "error": str(e)})

    # 요약
    print(f"\n\n{'='*60}")
    print("📊 요약")
    print(f"{'='*60}")
    for pname in PROMPTS:
        pr = [r for r in results if r.get("prompt") == pname and "error" not in r]
        if not pr:
            continue
        total_issues = sum(r["issue_count"] for r in pr)
        print(f"\n  {pname}: {len(pr)}건 테스트, 총 {total_issues}개 문제")
        for r in pr:
            status = "✅" if r["issue_count"] == 0 else f"⚠️ {r['issue_count']}개"
            print(f"    {r['test_case']}: {status}")
