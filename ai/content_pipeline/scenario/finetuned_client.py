"""파인튜닝 모델 (RunPod vLLM Worker) 클라이언트

RunPod Serverless에 서빙되는 vLLM Worker에 시나리오 생성 요청을 보내고,
응답에서 JSON을 파싱하여 Scenario 객체로 변환.

RunPod vLLM Worker는 OpenAI-compatible API를 제공.
"""

import json
import os
import re
import time

import requests

from dataclasses import dataclass

from content_pipeline.scenario.scenario_schemas import Scenario


@dataclass
class FinetunedResult:
    """파인튜닝 모델 생성 결과"""
    scenario: Scenario
    thinking: str
    full_response: str
    system_prompt: str
    user_prompt: str

FINETUNED_SYSTEM_PROMPT = """당신은 밈 광고 시나리오 작가입니다. 15초 숏폼, 4씬 구성.

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


def _get_runpod_config():
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "")
    api_key = os.getenv("RUNPOD_API_KEY", "")
    base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    model_name = os.getenv("RUNPOD_MODEL_NAME", "/runpod-volume/models/merged")
    return endpoint_id, api_key, base_url, model_name


def extract_json_from_response(text: str) -> dict | None:
    """모델 응답에서 JSON 추출. <thinking> 태그 이후의 JSON을 파싱."""
    # ```json 코드 블록에서 추출
    code_block = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1))
        except json.JSONDecodeError:
            pass

    # 중괄호 매칭으로 추출
    start_idx = text.find("{")
    if start_idx == -1:
        return None

    depth = 0
    for i, char in enumerate(text[start_idx:], start_idx):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start_idx : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _poll_runpod(job_id: str, timeout: int = 120) -> dict:
    """RunPod 비동기 작업 완료 대기."""
    _, api_key, base_url, _ = _get_runpod_config()
    headers = {"Authorization": f"Bearer {api_key}"}
    status_url = f"{base_url}/status/{job_id}"

    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(status_url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        if status == "COMPLETED":
            return data["output"]
        if status == "FAILED":
            raise RuntimeError(f"RunPod 작업 실패: {data.get('error', 'unknown')}")

        time.sleep(2)

    raise TimeoutError(f"RunPod 작업 타임아웃 ({timeout}초)")


def _call_runpod(base_url, headers, payload) -> str:
    """RunPod에 요청 보내고 output 반환."""
    response = requests.post(
        f"{base_url}/runsync",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()

    status = result.get("status")
    if status in ("IN_QUEUE", "IN_PROGRESS"):
        output = _poll_runpod(result["id"])
    elif status == "COMPLETED":
        output = result["output"]
    elif status == "FAILED":
        raise RuntimeError(f"RunPod 작업 실패: {result.get('error', 'unknown')}")
    else:
        output = result.get("output", result)

    if isinstance(output, list):
        output = output[0]

    choices = output.get("choices", [])
    if not choices:
        raise RuntimeError(f"모델 응답 없음: {output}")

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        content = choices[0].get("text", "")
    return content


SCENARIO_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "thinking": {"type": "string"},
        "scenario": {
            "type": "object",
            "properties": {
                "scene1": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string", "enum": ["hook", "body", "close"]},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene2": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string", "enum": ["hook", "body", "close"]},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene3": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string", "enum": ["hook", "body", "close"]},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "scene4": {
                    "type": "object",
                    "properties": {
                        "scene_type": {"type": "string", "enum": ["hook", "body", "close"]},
                        "dialogue": {"type": "string"},
                        "action": {"type": "string"},
                        "visual_description": {"type": "string"},
                    },
                    "required": ["scene_type", "dialogue", "action", "visual_description"],
                },
                "title": {"type": "string", "maxLength": 50},
                "description": {"type": "string", "maxLength": 200},
                "hashtags": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 5},
            },
            "required": ["scene1", "scene2", "scene3", "scene4", "title", "description", "hashtags"],
        },
    },
    "required": ["thinking", "scenario"],
}


def generate_with_finetuned(system_prompt: str, user_prompt: str) -> FinetunedResult:
    """파인튜닝 모델로 시나리오 생성.

    vLLM guided JSON으로 스키마 강제. 학습 데이터와 동일한 {thinking, scenario} 구조.

    Returns:
        FinetunedResult: scenario, thinking, full_response, system_prompt, user_prompt 포함
    """
    _, api_key, base_url, model_name = _get_runpod_config()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    effective_system = system_prompt if system_prompt else FINETUNED_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": effective_system},
        {"role": "user", "content": user_prompt},
    ]

    temperature = float(os.getenv("FINETUNED_TEMPERATURE", "0.7"))

    # vLLM guided JSON: 학습 데이터와 동일한 스키마 강제
    payload = {
        "input": {
            "openai_route": "/v1/chat/completions",
            "openai_input": {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "top_p": 0.9,
                "max_tokens": 2500,  # 모델 컨텍스트 4096 - 최대 입력 1500 여유분
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "scenario_output",
                        "schema": SCENARIO_OUTPUT_SCHEMA,
                    },
                },
            },
        }
    }

    content = _call_runpod(base_url, headers, payload)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"JSON 파싱 실패: {e}\nRaw: {content[:500]}"
        ) from e

    # {thinking, scenario} 구조에서 분리
    thinking = parsed.get("thinking", "")
    scenario_dict = parsed.get("scenario", parsed)

    # scene_type이 enum 값이 아닌 경우 씬 번호 기반으로 보정
    _scene_type_map = {"scene1": "hook", "scene2": "body", "scene3": "body", "scene4": "close"}
    for key, expected_type in _scene_type_map.items():
        scene = scenario_dict.get(key)
        if isinstance(scene, dict) and scene.get("scene_type") not in ("hook", "body", "close"):
            scene["scene_type"] = expected_type

    # description 200자 초과 시 자르기
    if isinstance(scenario_dict.get("description"), str) and len(scenario_dict["description"]) > 200:
        scenario_dict["description"] = scenario_dict["description"][:197] + "..."

    # hashtags 3개 미만이면 기본 태그로 보충
    tags = scenario_dict.get("hashtags") or []
    if len(tags) < 3:
        defaults = ["#밈", "#숏폼", "#광고"]
        for d in defaults:
            if len(tags) >= 3:
                break
            if d not in tags:
                tags.append(d)
        scenario_dict["hashtags"] = tags

    return FinetunedResult(
        scenario=Scenario(**scenario_dict),
        thinking=thinking,
        full_response=content,
        system_prompt=effective_system,
        user_prompt=user_prompt,
    )
