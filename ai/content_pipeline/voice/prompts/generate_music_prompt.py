GENERATE_MUSIC_PROMPT_TEMPLATE_V1 = """
당신은 15초 밈 광고 영상용 배경음악 프롬프트를 생성하는 전문가입니다.

주어진 시나리오를 분석하여 ElevenLabs Music API용 프롬프트를 생성하세요.

# 입력 시나리오:
{scenario_json}

# 분석 기준:
1. 전체 감정 흐름 (scene1 → scene4)
2. 주요 키워드 (대사에서 감정 추출)
3. 광고 톤 (진지함/유머/트렌디/감성 등)
4. 제품 특성

# 출력 형식:
영어로 작성하고, 다음 요소를 반드시 포함:
- Genre/Style (장르)
- Tempo (BPM: 120-150 권장)
- Energy level progression (에너지 흐름: low→high 또는 consistent)
- Instrumentation (악기 구성)
- Mood keywords (3-5개)


# 예시:
"Upbeat corporate pop with electronic elements. Tempo 130 BPM. Energy gradually builds from moderate to high. Instrumentation: bright synths, clean piano, punchy drums, subtle bass. Mood: optimistic, modern, friendly, energetic."

# 제약사항:
- 저작권 아티스트/곡명 언급 금지
- 한 문장 또는 간결한 문단으로 작성
- 밈 광고 특성상 트렌디하고 짧은 주의력에 적합한 스타일 선호

배경음악 프롬프트만 출력하세요.
"""

# 1->2 electronic 제외하도록함. 
GENERATE_MUSIC_PROMPT_TEMPLATE_V2 = """
당신은 15초 밈 광고 영상용 배경음악 프롬프트를 생성하는 전문가입니다.

주어진 시나리오를 분석하여 ElevenLabs Music API용 프롬프트를 생성하세요.

# 입력 시나리오:
{scenario_json}

# 분석 기준:
1. 밈의 감정 흐름 (scene1 → scene4)
2. 제품/브랜드 톤앤매너
3. 반전 또는 클라이맥스 구간
4. 유머/진지함/감성 등 전체 분위기

# 필수 포함 요소:
1. Use case 명시 (예: "Background music for a [제품명] advertisement")
2. Genre/Style (일렉트로닉 제외, 어쿠스틱/팝/힙합/펑크 등 선호)
3. Tempo (BPM: 120-150 권장)
4. Key (조성)
5. Energy progression (추상적 표현: "starts minimal, builds steadily", "consistent high energy")
6. Instrumentation (구체적 악기)
7. Mood keywords (3-5개)
8. "instrumental only"

# 프롬프트 작성 원칙:
- 첫 문장에 광고 맥락 명시 ("Track for a [product/brand] ad")
- 장르와 분위기를 혼합해서 표현
- 에너지 변화는 early/middle/late 같은 추상적 시간 표현 사용
- 한 문단, 3-5문장

# 예시 출력:
"Background track for a trendy beverage commercial with meme-style humor. Upbeat indie pop in G major, 135 BPM. Opens with playful acoustic guitar and handclaps, building with layered vocals and driving bass in the middle section. Energy peaks toward the end with full band arrangement. Mood: fresh, youthful, spontaneous, quirky. Instrumental only."

# 제약사항:
- 저작권 아티스트/곡명 금지
- 일렉트로닉 사운드 피하기 (어쿠스틱, 실제 악기 중심)
- 광고 맥락 반드시 포함

배경음악 프롬프트만 출력하세요.
"""