# TTS 텍스트 프롬프트 오디오 태그 가이드

- 작업 기간: 2026.01.21
- 작업자: 김진
- 관련 이슈 / PR: #17

---

## 모델
### TTS(Text-to-Speech) 모델
모델 ID	| 설명
|----|----
eleven_v3 | 인간과 유사하고 표현력이 풍부한 음성 생성
eleven_multilingual_v2 | 풍부한 감정 표현을 지닌 가장 실감나는 모델

### TTV(Text-to-Voice) 모델
모델 ID	| 설명
|----|----
eleven_ttv_v3 | 인간과 유사하고 표현력이 풍부한 음성 디자인 모델
eleven_multilingual_ttv_v2 | 풍부한 감정 표현을 지닌 가장 실감나는 음성 디자인 모델

## **오디오 태그 종류**
**Eleven v3 (알파) 모델만 사용 가능**

### **음성 관련**

이 태그들은 음성 전달과 감정 표현을 제어합니다.

- **`[laughs][laughs harder][starts laughing][wheezing]`**
- **`[whispers]`**
- **`[sighs][exhales`**
- **`[sarcastic][curious][excited][crying][snorts][mischievously]`**

**예**

```
[whispers] 이렇게 될 줄은 몰랐지만, 우리가 여기 있어서 정말 다행이야.
```

### **음향 효과**

환경음 및 효과음을 추가하세요:

- **`[gunshot][applause][clapping][explosion]`**
- **`[swallows][gulps]`**

**예**

```
[clapping] 오늘 밤 와주셔서 감사합니다! [gunshot] 저게 뭐지?
```

### **독특하고 특별한**

창의적인 활용을 위한 실험적인 태그:

- **`[strong French accent]`**
    
    (X를 원하는 악센트 기호로 바꾸세요)
    
- **`[sings][woo][fart]`**

**예**

```
[강한 프랑스어 억양] "인생이란 그런 거야, 친구. 모든 걸 통제할 순 없잖아."
```

### **구두**

구두점은 v3의 전달 방식에 상당한 영향을 미칩니다.

- **말줄임표(…)는**
    
    쉼표와 무게감을 더합니다.
    
- **대문자 사용은**
    
    강조를 더합니다.
    
- **표준적인 구두점은**
    
    자연스러운 말의 리듬을 제공합니다.


## 참고 문서
- 모델:

    https://elevenlabs.io/docs/overview/models

- 텍스트 오디오 태그:

    https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices