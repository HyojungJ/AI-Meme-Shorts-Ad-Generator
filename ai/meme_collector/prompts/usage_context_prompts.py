USAGE_CONTEXT_PROMPT_V1 = """You are analyzing a Korean meme video.

## Task
1. Determine if this video actually shows the meme being used
2. If relevant, extract how the meme is used and classify as good/bad example

## Rules
- is_relevant: Set to false if video just happens to share similar words but isn't about this meme
- context: 구체적인 상황 (예: "친구가 황당한 말을 했을 때")
- usage: **반드시 밈 대사를 따옴표('')로 인용** (예: "'무야호~!' 하며 팔을 들어올린다")
- If not relevant, leave context and usage empty

## example_type 판단 기준
- **good**: 밈의 원래 맥락을 이해하고 재치있게 활용한 경우
  - 적절한 상황에서 유머로 사용
  - 브랜드/제품 홍보에 센스있게 활용
  - 원본의 뉘앙스를 살린 패러디

- **bad**: 밈을 잘못 활용한 경우
  - 맥락 무시하고 강제로 끼워넣음
  - 불쾌감/거부감 유발
  - 세대 비하, 조롱 목적
  - "아재 감성", "억지 밈" 등의 반응을 받은 경우
"""


# V1->V2
# 국가인권위원회 '혐오표현 판단기준에 관한 토론회' 참고함.
USAGE_CONTEXT_PROMPT_V2 = """You are analyzing a Korean meme video.

## Task
1. Determine if this video actually shows the meme being used
2. If relevant, extract how the meme is used and classify as good/bad example

## Rules
- is_relevant: Set to false if video just happens to share similar words but isn't about this meme
- context: 구체적인 상황 (예: "친구가 황당한 말을 했을 때")
- usage: **반드시 밈 대사를 따옴표('')로 인용** (예: "'무야호~!' 하며 팔을 들어올린다")
- If not relevant, leave context and usage empty

## example_type 판단 기준

### good (적절한 활용)
밈을 원래 의미와 맥락에 맞게 자연스럽게 사용한 경우:
- 원본과 유사한 상황/감정에서 자연스럽게 사용
- 밈의 핵심 대사/표현을 올바른 타이밍에 사용
- 다른 사용자들이 이해하고 공감할 수 있는 맥락
- 원본의 유머/뉘앙스를 잘 살려서 활용
- 상황에 맞는 자연스러운 변형 (패러디)

### bad (부적절한 활용)
밈을 잘못 이해하거나 맥락 없이 사용한 경우:

**맥락 무시:**
- 밈과 전혀 관련 없는 상황에 억지로 사용
- 밈의 원래 의미와 정반대 상황에서 사용
- "그냥 유행이니까" 식으로 무분별하게 삽입

**이해 부족:**
- 밈의 뜻을 잘못 이해하고 사용
- 세대/문화 차이로 맥락을 못 읽고 어색하게 사용
- 밈을 몰라도 너무 모르는 사용 (완전히 엉뚱한 활용)

**차별/혐오 표현 (위험 카테고리):**

1. **age_bias (세대 갈등):**
   - 꼰대, 틀딱, 노인 비하
   - MZ 비하, 요즘 애들
   - 영포티(조롱 맥락), 세대 갈등 조장

2. **gender_conflict (성별 갈등):**
   - 한남, 한녀, 페미
   - 남혐/여혐 표현
   - 성별 기반 일반화/비하

3. **regional_bias (지역 비하):**
   - 특정 지역 비하/멸칭
   - 지역 갈등 조장
   - 지역 기반 차별 표현

4. **mockery (일반 조롱/비하):**
   - 특정 집단/개인 조롱
   - 비꼼, 비아냥 목적 사용
   - 원본 왜곡하여 부정적 의미 부여

5. **profanity (욕설/비속어):**
   - ~충, ~놈, ~년
   - 직접적 욕설, 비속어
   - 공격적 언어

6. **political (정치 논란):**
   - 정치 진영 갈등 조장
   - 정치인/정당 비하
   - 정치적 논란 유발

7. **discrimination (차별 표현):**
   - 외모 비하 (못생김, 뚱뚱함 등)
   - 장애인 조롱, 능력 비하
   - 인종/국적 차별
   - 직업 비하 (알바, 특정 직종 등)
   - 학력 차별
   - 비용/짐 프레임 (특정 집단을 사회적 비용이나 부담으로 묘사) 
   - 능력주의적 비하 (구조적 문제를 개인의 의지 부족/게으름으로 치부) 
   - 특정 집단 행동의 일반화 (개인의 잘못을 집단 전체의 특성으로 매도)

8. **sexual (성적 대상화):**
   - 성희롱성 표현
   - 성적 대상화
   - 불쾌감 유발하는 성적 표현

9. **incident_exploitation (사건/사고 악용):**
   - 비극적 사건을 밈으로 소비
   - 타인의 불행 희화화
   - 사회적 참사 조롱

10. **community_hate (혐오 커뮤니티 용어):**
    - 일베 등 혐오 커뮤니티 전용 용어
    - 특정 집단 비하 목적 신조어
    - 혐오 문화 확산 표현

11. **insensitive_metaphor (무감각한 비유):**
    - ~린이 (아동 비하)
    - 마약~ (중독 희화화)
    - ~노예 (역사적 비극 소비)
    - ~병/~장애 (질병 희화화)
    - 자살/죽음 농담
    - 전쟁/학살 비유
    - 결정장애 (우유부단함 희화화)
    - 꿀먹은 벙어리/벙어리 냉가슴 (답답한 상황 비유)
    - 절름발이 행정/정책 (불완전함 비유)
    - 눈먼 돈/장님 코끼리 (맹목성/무지 비유)
    - 정신 나갔다/미쳤다 (비상식적 상황 비유)

12. **social_exclusion (사회적 배제/부정):**
    - 존재 부정 ("내 눈에 띄지 마라", "보고 싶지 않다")
    - 격리/분리 조장 ("음지에서만 해라", "어디 가둬야 한다")

**판단 우선순위:**
1. 밈의 사용이 다른 사람에게 불편하지 않은가? (차별/혐오 표현 체크)
2. 사용된 맥락이 밈의 원래 의미와 맞는가?
3. 자연스러운 사용인가? 억지스러운가?

**의심스러우면 good으로 판단** (확실한 bad 신호가 없으면 good)
"""