# 보이스 디자인(Voice Design) 가이드  

- 작업 기간: 2026.01.21
- 작업자: 김진
- 관련 이슈 / PR: #24

---

ElevenLabs의 **Voice Design eleven_ttv_v3** 모델은 단순한 키워드 나열보다  
**구체적인 상황(Context)과 명확한 페르소나(Persona)** 를 묘사할 때 더 높은 품질의 음성을 생성

---

## 1. 핵심 파라미터 상세 전략

| 카테고리 | 설명 | 추천 키워드 (영문 권장) |
|--------|------|-----------------------------|
| **나이 (Age)** | 목소리의 두께와 성숙도를 결정 | Young child, Teenager, Middle-aged, Elderly / Senior |
| **억양 (Accent)** | 브랜드의 글로벌·문화적 컨텍스트를 결정 | Neutral American, Soft British, Professional Korean |
| **성별 (Gender)** | 음성의 기본 공명대(Resonance) 설정 | Male, Female, Non-binary / Gender-neutral |
| **어조 (Tone)** | 광고의 무드를 결정하는 핵심 요소 | Trustworthy, Authoritative, Friendly, Sarcastic |
| **속도 (Speed)** | 영상 길이·대사 밀도 조절 | Fast-paced, Calm / Measured, Slow and languid |
| **지침 척도 (Scale)** | 창의성 ↔ 정확도 균형 | 8~12: 정확한 구현 / 3~5: 창의적 탐색 |

---

## 2. 고퀄리티 음성을 위한 프롬프팅 팁 

### 1) 페르소나 설정 (Persona)
단순한 속성 나열보다 **직업·역할 기반 묘사**가 효과적

- *Like a documentary narrator*
- *Late-night radio host*
- *Experienced commercial voice actor*

### 2) 질감 묘사 (Texture)
음성의 물리적 질감을 명시하면 캐릭터성이 강화

- Gravelly (거친)
- Smooth (매끄러운)
- Breathy (숨소리가 섞인)
- Raspy (쇳소리가 나는)

### 3) 마이크·공간 설정 (Environment)
녹음 환경을 지정하면 공간감과 몰입도가 향상됩니다.

- Studio quality
- Over the phone
- In a large hall
- Close-mic recording

---

## 3. 실전 광고용 프롬프트 조합 예시

| 광고 컨셉 | 추천 프롬프트 (Voice Description) |
|---------|----------------------------------|
| **럭셔리 브랜드** | A sophisticated, middle-aged female voice with a posh British accent. The tone is calm and elegant, with a silky smooth texture. |
| **IT / 하이테크** | A young adult, gender-neutral voice with a neutral American accent. The tone is precise, intelligent, and energetic, sounding like a futuristic AI. |
| **식품 / 가정용품** | A warm, friendly male voice in his 30s. Sounds trustworthy and approachable, like a kind neighbor speaking at a natural, steady pace. |
| **게임 / 영화 트레일러** | A deep, booming elderly male voice. Gravelly and authoritative, with a sense of ancient wisdom and a slow, dramatic pace. |

---

## 활용 팁
- **카테고리·전략·예시를 명확히 분리**해 가독성 확보
- 프롬프트 예시는 코드 블록 또는 테이블로 정리
- `Voice ID + Prompt Template` 구조로 관리 추천

## 참조 문서
[ElevenLabs Voice Design v3: Create Custom AI Voices](https://elevenlabs.io/blog/voice-design-v3#prompting-power-tips)
[Voice design | ElevenLabs Documentation](https://elevenlabs.io/docs/creative-platform/voices/voice-design)