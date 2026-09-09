import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


def score_video(
    video_path: str,
    criteria: str,
    model: str | None = None,
) -> str:
    if not video_path:
        raise ValueError("video_path is required")
    if not criteria:
        raise ValueError("criteria is required")

    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video path not found: {video_path}")

    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("NANO_BANANA_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY, GEMINI_API_KEY, or NANO_BANANA_API_KEY is required in .env")

    client = genai.Client(api_key=api_key)
    model = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-pro"

    uploaded = client.files.upload(
        file=path,
    )

    # 파일이 ACTIVE 상태가 될 때까지 대기
    import time
    max_wait = 60  # 최대 60초 대기
    wait_interval = 2  # 2초마다 확인
    elapsed = 0
    
    while uploaded.state.name != "ACTIVE":
        if elapsed >= max_wait:
            raise TimeoutError(f"File upload timeout after {max_wait}s. State: {uploaded.state.name}")
        time.sleep(wait_interval)
        elapsed += wait_interval
        uploaded = client.files.get(name=uploaded.name)

    prompt = f"""
당신은 AI 생성 영상의 **모든 종류의 오류**를 검증하는 전문 검수자입니다.

**임무**: 이 이미지에서 현실에서 불가능하거나 부자연스러운 모든 요소를 찾으세요.

## 검증 체크리스트 (모든 항목 확인)

### 🧍 1. 인체 해부학
- 손가락/발가락 개수 (정상: 각 5개)
- 눈/귀/코/입 개수와 위치
- 팔/다리 개수 (정상: 각 2개)
- 관절 방향 (팔꿈치, 손목, 무릎, 발목)
- 신체 비율 (머리:몸통:팔:다리)
- 얼굴 특징 배치 (눈 위 → 코 중간 → 입 아래)

### 🤝 2. 물체 상호작용
- 손이 물체를 실제로 잡고 있는가? (접촉하고 있는가?)
- 물체 사용 방식이 올바른가?
  - 컵/병 → 입
  - 포크/숟가락 → 입
  - 칫솔 → 치아
  - 펜 → 손으로 올바르게 잡음
- 물체가 손/신체를 통과하는가?
- 물체와 신체의 상대적 크기가 자연스러운가?

### ⚡ 3. 물리 법칙
- **중력**: 물체가 지지 없이 공중에 떠있는가?
- **충돌**: 물체가 벽/바닥/다른 물체를 통과하는가?
- **관통**: 사람이 벽/문/물체를 통과하는가?
- **액체**: 물/음료가 위로 흐르거나 중력 무시하는가?
- **그림자**: 그림자 방향이 광원과 일치하는가?
- **반사**: 거울/유리 반사가 자연스러운가?

### 🎨 4. 시각적 일관성
- **색상 변화**: 동일 물체/사람의 색이 갑자기 변하는가?
- **물체 변형**: 물체가 갑자기 다른 것으로 바뀌는가?
- **텍스처 왜곡**: 옷/벽/바닥 패턴이 뒤틀리거나 깨지는가?
- **조명 일관성**: 조명이 갑자기 변하거나 불일치하는가?
- **크기 변화**: 물체/사람 크기가 일관성 없이 변하는가?

### 🔄 5. 시공간 연속성
- **순간이동**: 물체/사람이 갑자기 다른 위치에 나타나는가?
- **복제**: 동일 물체가 여러 개로 복제되는가?
- **소멸/생성**: 물체/신체 부위가 갑자기 사라지거나 나타나는가?
- **시간 역행**: 동작이 거꾸로 재생되는 것처럼 보이는가?

### 🏠 6. 환경 및 배경
- **원근법**: 배경 원근감이 왜곡되는가?
- **건축 구조**: 벽/천장/바닥 각도가 불가능한가?
- **물체 배치**: 물체가 불가능한 위치/각도에 있는가?
- **환경 일관성**: 실내/실외가 혼재되거나 모순되는가?

### 👕 7. 의복 및 액세서리
- **부착**: 옷이 몸에 제대로 붙어있는가, 떠있는가?
- **중력**: 옷/머리카락이 중력을 무시하는가?
- **레이어링**: 옷 겹침이 자연스러운가?
- **변형**: 옷이 갑자기 변하거나 사라지는가?

## 채점 기준 (엄격하게 적용)

**0-20점 (치명적 오류 - 즉시 명백):**
- 손가락 7개 이상 / 3개 이하
- 팔/다리/눈 개수 비정상
- 음료를 코/눈으로 마심
- 사람이 벽을 통과함
- 관절이 180도 반대로 꺾임
- 물체가 명백히 공중 부양
- 같은 사람이 동시에 2명 존재

**21-40점 (심각한 오류 - 명백히 발견):**
- 손가락 6개 또는 4개
- 손이 물체에 안 닿는데 잡고 있음
- 물체가 손/벽 관통
- 색상이 급격히 변함
- 물체가 갑자기 바뀜
- 그림자 방향 완전 불일치

**41-60점 (명확한 부자연스러움):**
- 손가락 일부 융합
- 관절 각도 불가능
- 물체 크기 불일치
- 텍스처 심하게 왜곡
- 조명 일관성 깨짐
- 신체 비율 이상

**61-80점 (미세한 이상):**
- 손 위치 약간 어색
- 미세한 색상 변화
- 경미한 텍스처 깨짐
- 약간의 원근법 오류

**81-100점 (거의 완벽):**
- 매우 미미한 결함만 있거나
- 완전히 오류 없음

## 분석 절차

**1단계**: 전체 관찰 - 첫인상에서 이상한 점
**2단계**: 신체 검증 - 손가락 세기, 관절 확인, 얼굴 특징
**3단계**: 물체 검증 - 접촉점, 사용 방식, 물리 법칙
**4단계**: 환경 검증 - 배경, 조명, 그림자, 원근법
**5단계**: 연속성 검증 - 색상, 크기, 위치 일관성
**6단계**: 종합 판단 - 모든 오류 취합 및 점수 산정

## 주의사항

✅ **평가 대상**:
- 해부학적 정확성
- 물리 법칙 준수
- 시각적 일관성
- 시공간 연속성
- 환경 현실성

❌ **평가 제외**:
- 영상 품질 (해상도, 압축)
- 미적 감각 (예쁜지 아닌지)
- 창의성 (독특한 구도)

## 응답 형식 (JSON만)

{{
  "score": 0-100 정수,
  "errors_found": [
    {{
      "category": "인체해부학 / 물체상호작용 / 물리법칙 / 시각적일관성 / 시공간연속성 / 환경배경 / 의복",
      "severity": "치명적 / 심각 / 명확 / 미세",
      "description": "구체적인 오류 설명"
    }}
  ],
  "summary": "발견된 모든 오류를 간결하게 요약. 오류 없으면 '오류 없음'"
}}

**예시 (오류 있음)**:
{{
  "score": 15,
  "errors_found": [
    {{"category": "물체상호작용", "severity": "치명적", "description": "컵을 코로 가져가 마시는 장면"}},
    {{"category": "인체해부학", "severity": "심각", "description": "왼손 손가락 6개"}},
    {{"category": "물리법칙", "severity": "심각", "description": "사람이 벽을 통과함"}},
    {{"category": "시각적일관성", "severity": "명확", "description": "셔츠 색이 파란색에서 빨간색으로 갑자기 변함"}}
  ],
  "summary": "컵을 코로 마시는 치명적 오류, 왼손 손가락 6개, 벽 관통, 셔츠 색상 급변"
}}

**예시 (오류 없음)**:
{{
  "score": 95,
  "errors_found": [],
  "summary": "오류 없음. 모든 요소가 해부학적으로 정확하고 물리 법칙을 준수하며 시각적으로 일관됨"
}}

평가 기준:
{criteria}

지금 이 이미지를 철저히 분석하세요.
"""

    response = client.models.generate_content(
        model=model,
        contents=[
            uploaded,
            prompt,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    return response.text or ""


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")
    test_video_path = repo_root / "tests" / "VLM" / "sample_video" / "sample3.mp4"
    test_criteria = """
요가 매트 위에 서 있는 곰
"""
    output_text = score_video(str(test_video_path), test_criteria)
    print(output_text)
