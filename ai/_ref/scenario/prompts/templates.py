import json


def get_skeleton_prompt(meme_data: dict, characters: list) -> str:
    meme_type = meme_data.get("meme_type", "quotable")
    key_phrase = meme_data.get("key_phrase", "")
    definition = meme_data.get("definition", "")
    meme_name = meme_data.get("meme_name", "")

    video = meme_data.get("video", {}) or {}
    audio = meme_data.get("audio", {}) or {}
    audio_json = audio.get("audio_json", {}) or {}

    motion_prompt_hint = video.get("motion_prompt_hint", "")
    detected_text = audio_json.get("detected_text", "")

    character_desc = "\n".join([
        f"- {c['name']}: {c['description']} (말투: {c['style']})"
        for c in characters
    ])

    meme_key = key_phrase or detected_text or meme_name

    return f"""숏폼 코미디 시나리오를 작성하세요.

# 밈 정보
- 이름: {meme_name}
- 정의: {definition}
- 유형: {meme_type}
- 핵심 대사/동작: {meme_key}
{f"- 동작 힌트: {motion_prompt_hint}" if motion_prompt_hint else ""}

# 캐릭터
{character_desc}

# 컨셉
"밈에 진심인 부장 vs 당황하는 사원"의 회사 일상 코미디

---

# Beat 타입 정의 (중요!)

## dialogue (대사)
- 캐릭터가 **말을 하는** 모든 경우
- text 필드에 실제 대사 작성
- 예: "부장님, 보고서 가져왔습니다", "네? 그게 뭔데요?"

## action (동작)
- 캐릭터가 **말 없이** 동작만 하는 경우
- text 필드에 동작 설명 (나래이션 아님, 영상 생성용)
- motion_prompt에 영어로 상세 동작 설명
- 예: 부장이 자리에서 일어나 밈 동작을 시전한다

## reaction (무언 리액션)
- 캐릭터가 **말 없이** 표정/감정만 보여주는 경우
- emotion 필드에 감정 작성
- text 필드 비워두기 (또는 null)
- 예: 사원이 충격받은 표정으로 굳는다

⚠️ **핵심**: 캐릭터가 입을 열어 말하면 무조건 dialogue!
- "네?" → dialogue (짧아도 대사임)
- "뭐요...?" → dialogue
- "하..." → dialogue (탄식도 대사)
- (말 없이 당황한 표정) → reaction

---

# 시나리오 구조

## 업무 상황으로 시작 (필수)
밈이 갑자기 나오면 안 됨. 회사 업무 맥락에서 시작:
- 보고서 제출, 회의 전후, 점심시간, 퇴근 직전 등

## 3씬 구조 (8 beats, 총 15초)

⚠️ **비용 절감**: Sora 호출 = 씬 개수. 반드시 3개 씬만 생성!

**Duration 배분**: Intro 5초 → Meme 6초 → Outro 4초

### Scene 1: intro (3 beats, 5초) - 대화 중심
- beat 1: 사원 dialogue (1.5초) - 업무 관련 말 걸기
- beat 2: 부장 dialogue (2초) - 밈 화제 전환
- beat 3: 사원 dialogue (1.5초) - 당황한 반응

### Scene 2: meme (3 beats, 6초) ⭐핵심⭐
- beat 4: 부장 dialogue (1.5초) - 시전 예고
- beat 5: 부장 action (3초) - 밈 시전
  - text: "{meme_key}" (밈 대사 - TTS 생성됨)
  - motion_prompt: 50+ words 영어 상세 동작
- beat 6: 사원 dialogue (1.5초) - 짧은 리액션

### Scene 3: outro (2 beats, 4초) - 마무리
- beat 7: 사원 dialogue (2초) - 당황/체념 대사
- beat 8: 부장 dialogue (2초) - 만족스러운 마무리

---

# 대사 규칙
- 사원 dialogue: 4개 (beat 1, 3, 6, 7)
- 부장 dialogue: 3개 (beat 2, 4, 8) + meme text
- 대사는 짧게! 한 문장 8-12자 이내
- 리듬감 있게 주고받기

---

# scene_motion_prompt (필수)
모든 씬에 영어로 30-50 words. 캐릭터 동작 시점 명시:
- "0-1.5s: employee speaks. 1.5-3.5s: boss speaks. 3.5-5s: employee reacts."

---

# 출력 규칙
- dialogue beat의 text는 [PLACEHOLDER: 상황설명] 형태
- action beat의 text는 밈 대사 (한국어)
- **총 duration: 15초 (엄수!)**
- **씬 개수: 3개 (엄수!)**"""


def get_dialogue_prompt(character: dict, scene_context: str, beat_info: dict, meme_data: dict = None) -> str:
    style_tags = ", ".join(character.get("style_tags", []))

    # 밈 대사 정보 (quotable인 경우)
    meme_phrase_hint = ""
    if meme_data:
        key_phrase = meme_data.get("key_phrase", "")
        audio = meme_data.get("audio", {})
        audio_json = audio.get("audio_json", {}) if audio else {}
        detected_text = audio_json.get("detected_text", "") if audio_json else ""

        if key_phrase or detected_text:
            meme_phrase_hint = f"""
## 밈 핵심 대사
원본: "{key_phrase or detected_text}"
meme 씬에서 부장이 이 대사를 시전한다면, 원본 그대로 또는 자연스럽게 변형하세요.
"""

    # 캐릭터별 상세 가이드
    char_guide = CHARACTER_GUIDES.get(character['name'], "")

    return f"""당신은 캐릭터 대사 작가입니다.

## 캐릭터 정보
- 이름: {character['name']}
- 설명: {character['description']}
- 말투 스타일: {character['style']}
- 스타일 태그: {style_tags}
{char_guide}
{meme_phrase_hint}

## 씬 맥락
{scene_context}

## 생성할 대사 정보
- 비트 ID: {beat_info['beat_id']}
- 상황: {beat_info.get('placeholder', '')}
- 코미디 비트: {beat_info.get('comedy_beat', '')}

## 요청
위 캐릭터의 페르소나에 맞는 자연스럽고 재미있는 대사를 생성하세요.

## 규칙
- {character['name']}의 말투 특성을 살리세요
- 10-30자 내외의 짧은 대사
- 코미디 타이밍을 고려하세요
- 상황에 맞는 감정을 담으세요

대사만 출력하세요 (따옴표 없이)."""


def get_finalizer_prompt(skeleton: dict, dialogues: dict, meme_data: dict = None) -> str:
    video_hint = ""
    if meme_data:
        video = meme_data.get("video", {}) or {}
        motion_prompt_hint = video.get("motion_prompt_hint", "")
        if motion_prompt_hint:
            video_hint = f"\n# 밈 동작 참고\n{motion_prompt_hint}\n"

    return f"""시나리오를 완성하세요.

# 골격
```json
{json.dumps(skeleton, ensure_ascii=False, indent=2)}
```

# 대사
```json
{json.dumps(dialogues, ensure_ascii=False, indent=2)}
```
{video_hint}
# 작업
1. [PLACEHOLDER]를 대사로 교체
2. TTS 대상: dialogue + meme 씬 action (밈 대사)
3. 모든 씬에 scene_motion_prompt 추가 (30-50 words, 영어, 타이밍 명시)
4. meme 씬 motion_prompt 상세화 (50+ words, 영어)

# 검증
- **3개 씬, 8 beats (엄수!)**
- 사원 dialogue: 4개
- 부장 dialogue: 3개 + meme text
- **총 duration: 15초 (엄수!)**"""


# 캐릭터별 상세 가이드
CHARACTER_GUIDES = {
    "부장": """
### 부장 캐릭터 심화 가이드
- 50대 중년 남성, 밈에 진심으로 빠삭함
- 밈 시전 시 100% 자신감 (틀려도 당당)
- 사원에게 자랑하고 인정받고 싶어함

**말투 특성:**
- 반말 사용, 친근하지만 상사다운 톤
- 밈을 설명할 때 신나고 자신감 넘침
- 시전 후 뿌듯해하며 칭찬을 기대함
- 문장 끝에 "~지", "~야" 자주 사용

⚠️ 매번 다른 표현을 사용하세요. 같은 대사 반복 금지!
""",

    "사원": """
### 사원 캐릭터 심화 가이드
- 20대 후반, 밈에 관심 없거나 이미 질림
- 부장의 갑작스러운 행동에 당황
- 어색하게 호응하거나 만류하는 역할

**말투 특성:**
- 존댓말 사용, 조심스러운 톤
- 당황하면 말끝을 흐림 ("...요?", "...ㅎㅎ")
- 속마음과 겉말이 다름 (겉으론 호응, 속으론 당황)
- 짧은 반응이 많음

⚠️ 매번 다른 표현을 사용하세요. 같은 대사 반복 금지!
"""
}
