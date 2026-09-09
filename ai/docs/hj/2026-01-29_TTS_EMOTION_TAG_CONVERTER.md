# TTS 감정 태그 변환 시스템

## 개요

시나리오 생성 모델의 출력 형식 `(감정) 대사`를 ElevenLabs TTS API가 인식할 수 있는 `[태그] 대사` 형식으로 자동 변환하는 시스템

## 문제 정의

- **입력**: 시나리오 모델 출력 - `(기쁨) 오늘 날씨가 정말 좋네!`
- **필요**: ElevenLabs TTS 입력 - `[excited] 오늘 날씨가 정말 좋네!`
- **과제**: 한국어 감정 레이블 → 영어 오디오 태그 자동 변환

## 구현 방식

### 1단계: 파인튜닝 시도 (실패)

#### 학습 데이터 생성
- OpenAI API를 활용한 5,000개 학습 데이터 자동 생성
- 대사 길이 분포: 짧은(20%), 중간(50%), 긴(30%)
- 중복 제거 및 품질 검증 완료

#### 모델 파인튜닝
- **베이스 모델**: `kakaocorp/kanana-nano-2.1b-instruct`
- **방법**: LoRA 파인튜닝 (r=16, alpha=32, 4-bit 양자화)
- **학습**: 3 에폭 (4,500개 학습 / 500개 검증)
- **결과 모델**: [HyojungJ/kanana-tts-ko-admeme](https://huggingface.co/HyojungJ/kanana-tts-ko-admeme)

#### 실패 원인
1. **모델 크기 한계**: 2.1B 파라미터는 복잡한 instruction following에 부족
2. **출력 불안정**: 
   - 대사 내용 임의 변경: `(기쁨) 오늘 날씨가 정말 좋네!` → `(기쁨) 와, 날씨가 정말 좋네!`
   - 긴 설명문 생성: 태그 대신 설명 텍스트 출력
   - 감정 레이블 유지: `(기쁨)` 형식 그대로 출력
3. **System 프롬프트 문제**: 2000자 이상의 긴 프롬프트를 소형 모델이 학습하기 어려움

### 2단계: GPT-4o-mini 적용 (현재)

#### 구현 위치
`content_pipeline/voice/nodes.py` - `convert_to_tts_node()` 함수

#### 코드
```python
def convert_to_tts_node(dialogue: str) -> str:
    """
    (감정) 대사 → [tag] 대사 변환
    
    Example:
        >>> convert_to_tts_node("(기쁨) 오늘 날씨가 정말 좋네!")
        "[excited] 오늘 날씨가 정말 좋네!"
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""다음 대사를 ElevenLabs v3 형식으로 변환하세요.

규칙:
- (감정) 제거하고 영어 태그로 변환
- 대사 내용은 절대 변경 금지
- 한 줄로만 출력

예시:
입력: (기쁨) 오늘 날씨가 정말 좋네!
출력: [excited] 오늘 날씨가 정말 좋네!

입력: (슬픔) 이제 정말 끝인가봐...
출력: [sad] 이제 정말 끝인가봐...

입력: {dialogue}
출력:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=200
    )
    
    return response.choices[0].message.content.strip().split('\n')[0]
```

#### 장점
- ✅ 안정적인 출력: 대사 내용 변경 없음
- ✅ 높은 정확도: 감정 → 태그 매핑 정확
- ✅ 간단한 구현: API 호출만으로 완성
- ✅ 유지보수 용이: 프롬프트 수정으로 개선 가능

#### 단점
- ❌ API 비용 발생 (대사당 ~$0.0001)
- ❌ 네트워크 의존성
- ❌ 응답 지연 (~500ms)

## 감정 태그 매핑 가이드

### 긍정적 감정
- 기쁨, 즐거움, 행복 → `[excited]` 또는 `[lighthearted]`
- 흥분, 신남, 들뜸 → `[excited]`
- 호기심, 궁금함 → `[curious]`
- 놀람, 깜짝 → `[surprised]`
- 안도, 안심 → `[relieved]`
- 감탄, 경외 → `[awe]`

### 부정적 감정
- 화남, 분노 → `[angry]`
- 짜증, 불쾌 → `[annoyed]`
- 좌절, 답답함 → `[frustrated]`
- 슬픔, 우울 → `[sad]`
- 울음, 흐느낌 → `[crying]` 또는 `[sobbing]`
- 실망 → `[disappointed]`
- 지루함 → `[bored]`
- 긴장, 불안 → `[nervous]`
- 혼란, 당황 → `[confused]`

### 중립/특수
- 피곤함, 지침 → `[sighs]` 또는 `[exhales]`
- 무덤덤, 무감정 → `[flatly]` 또는 `[matter-of-fact]`
- 비꼼, 냉소 → `[sarcastic]`
- 장난, 장난스럽게 → `[mischievously]`
- 그리움, 아쉬움 → `[wistful]`
- 체념, 포기 → `[resigned]`
- 회상, 회고 → `[reflective]`
- 극적, 드라마틱 → `[dramatic tone]`

### 발화 방식
- 속삭임, 속삭이듯 → `[whispers]`
- 웃음, 웃으며 → `[laughs]` 또는 `[giggles]`
- 한숨, 한숨 쉬며 → `[sighs]`
- 소리지름, 소리지르듯 → `[shouts]` 또는 `[screams]`
- 망설임, 망설이며 → `[hesitates]`
- 더듬음, 더듬거리며 → `[stammers]`

## 사용 예시

### Voice Pipeline 통합
```python
from content_pipeline.voice.nodes import convert_to_tts_node

# 시나리오 모델 출력
scenario_output = "(기쁨) 오늘 날씨가 정말 좋네!"

# TTS 태그로 변환
tts_prompt = convert_to_tts_node(scenario_output)
# → "[excited] 오늘 날씨가 정말 좋네!"

# ElevenLabs API에 전달
audio = elevenlabs_client.generate(
    text=tts_prompt,
    voice="..."
)
```

## 향후 계획

### 파인튜닝 재시도
1. **프롬프트 간소화**: System 프롬프트 제거, Few-shot 예시만 사용
2. **더 큰 모델**: 7B 이상 모델로 재시도
3. **학습 데이터 개선**: 
   - 대사 내용 변경 방지 강조
   - 더 다양한 감정 표현 추가
   - 엣지 케이스 보강

### 하이브리드 접근
- 일반적인 케이스: 파인튜닝 모델 (빠름, 저렴)
- 복잡한 케이스: GPT-4o-mini (정확함)
- Fallback 체인 구성

## 참고 자료

- **파인튜닝 모델**: https://huggingface.co/HyojungJ/kanana-tts-ko-admeme
- **베이스 모델**: https://huggingface.co/kakaocorp/kanana-nano-2.1b-instruct
- **ElevenLabs v3 태그**: https://elevenlabs.io/docs/speech-synthesis/prompting
