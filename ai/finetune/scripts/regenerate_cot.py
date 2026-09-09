"""seeds_final.jsonl의 수정된 시나리오에 맞게 CoT를 GPT-4o로 역생성.

사용법:
    uv run python finetune/scripts/regenerate_cot.py

입력: finetune/data/seeds/seeds_final.jsonl
출력: finetune/data/seeds/seeds_final_cot.jsonl
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

INPUT_PATH = Path("finetune/data/seeds/seeds_final.jsonl")
OUTPUT_PATH = Path("finetune/data/seeds/seeds_final_cot.jsonl")

COT_REGEN_PROMPT = """아래는 밈 광고 시나리오의 최종 JSON입니다. 이 시나리오가 만들어지기까지의 사고 과정(thinking)을 작성해주세요.

## 반드시 포함할 체크리스트

### 1. 밈 분석
- 이 밈이 원래 쓰이는 상황/감정: [구체적으로 서술]
- 핵심 문구 또는 행동: [밈의 핵심 요소 그대로 인용]

### 2. 상품 × 밈 시나리오 설계
- 상품을 사용하다가 밈의 감정이 터지는 구체적 상황: [설계]
- 밈 핵심 요소가 등장하는 씬: scene[N], 이유: [왜 여기인지]
- 밈이 여러 씬에 걸쳐 스토리를 이끌어가는 방식: [설계]

### 3. 교체 테스트 (필수!)
- 밈 대사/행동을 "와 이거 진짜 좋다"로 바꿔도 광고가 작동하는가?
  → [예: 재설계 필요 / 아니오: 통과, 이유 설명]

### 4. 대사 초안 (반드시 "(감정) 대사" 형태) + 글자수
글자수 세는 법: (감정) 태그를 완전히 제거한 후 남은 텍스트의 글자수를 셈 (공백, 구두점 포함)

- scene1: (감정) "[대사]" → 감정 태그 제외 후 N자
- scene2: (감정) "[대사]" → 감정 태그 제외 후 N자
- scene3: (감정) "[대사]" → 감정 태그 제외 후 N자
- scene4: (감정) "[대사]" → 감정 태그 제외 후 N자
- 모든 대사에 (감정) 태그가 있는지 확인

### 5. 장소 확인
- 촬영 장소: [상품이 실제 사용되는 구체적 장소 1곳]
- 4씬 모두 이 장소에서 진행: [확인]

## 규칙
- thinking 내용만 출력 (태그 없이, 본문만)
- 아래 시나리오 JSON과 정확히 일치하는 대사/행동/장소를 사용
- 글자수는 실제로 정확히 세서 작성
- 등장인물 1명 기준
- 한국어로 작성

---

## 밈 정보
- 밈 이름: {meme_name}
- 회사: {company_name}
- 캐릭터 톤: {voice_design_prompt}

## 시나리오 JSON
```json
{scenario_json}
```"""


def extract_scenario(assistant_content: str) -> dict | None:
    """assistant 메시지에서 JSON 시나리오 추출."""
    # thinking 이후 부분에서 추출
    thinking_end = assistant_content.find("</thinking>")
    text = assistant_content[thinking_end:] if thinking_end != -1 else assistant_content

    code_block = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, c in enumerate(text[start:], start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def regenerate_cot(client: OpenAI, seed: dict) -> str:
    """GPT-4o로 시나리오에 맞는 CoT 역생성."""
    meta = seed["metadata"]
    assistant_content = seed["messages"][2]["content"]
    scenario = extract_scenario(assistant_content)

    if not scenario:
        raise ValueError(f"JSON 추출 실패: {meta.get('meme_name')}")

    scenario_json = json.dumps(scenario, ensure_ascii=False, indent=2)

    prompt = COT_REGEN_PROMPT.format(
        meme_name=meta.get("meme_name", "?"),
        company_name=meta.get("company_name", "?"),
        voice_design_prompt=meta.get("voice_design_prompt", "?"),
        scenario_json=scenario_json,
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "시나리오에 맞는 사고 과정(thinking)을 체크리스트 형식으로 작성하는 전문가입니다. thinking 본문만 출력하세요.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    return response.choices[0].message.content.strip()


def rebuild_assistant(seed: dict, new_thinking: str) -> str:
    """새 CoT + 기존 시나리오 JSON으로 assistant 메시지 재구성."""
    assistant_content = seed["messages"][2]["content"]
    scenario = extract_scenario(assistant_content)
    scenario_json = json.dumps(scenario, ensure_ascii=False, indent=2)

    return f"<thinking>\n{new_thinking}\n</thinking>\n\n```json\n{scenario_json}\n```"


def main():
    client = OpenAI()

    seeds = []
    with open(INPUT_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                seeds.append(json.loads(line))

    print(f"총 {len(seeds)}개 seed 처리")

    results = []
    for i, seed in enumerate(seeds):
        meta = seed["metadata"]
        label = f"{meta.get('meme_name', '?')} x {meta.get('company_name', '?')}"
        print(f"[{i+1}/{len(seeds)}] {label} ... ", end="", flush=True)

        try:
            new_thinking = regenerate_cot(client, seed)
            new_assistant = rebuild_assistant(seed, new_thinking)

            updated = {
                "messages": [
                    seed["messages"][0],  # system
                    seed["messages"][1],  # user
                    {"role": "assistant", "content": new_assistant},
                ],
                "metadata": seed["metadata"],
            }
            results.append(updated)
            print(f"OK ({len(new_thinking)}자)")

        except Exception as e:
            print(f"FAIL: {e}")
            results.append(seed)  # 실패 시 원본 유지

        # rate limit
        if i < len(seeds) - 1:
            time.sleep(0.5)

    with open(OUTPUT_PATH, "w") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n완료: {OUTPUT_PATH} ({len(results)}개)")


if __name__ == "__main__":
    main()
