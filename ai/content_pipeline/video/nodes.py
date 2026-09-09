import json
import logging
from functools import lru_cache
import time
import os
from pathlib import Path
from openai import OpenAI
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

from content_pipeline.video.config import load_video_config
from content_pipeline.video.service import VideoService
from content_pipeline.video.state import VideoState
from content_pipeline.db import insert_final_video, save_verification_result, upsert_scene_video
from content_pipeline.video.utils import build_scene_inputs_from_db


@lru_cache(maxsize=1)
def _get_service() -> VideoService:
    config = load_video_config()
    return VideoService(config)


def _build_scene_prompt(state: VideoState, scene_index: int) -> str:
    """
    시나리오 기반 프롬프트 생성 로직
    - 시나리오의 제목, 설명, 씬별 세부 내용을 조합하여 최종 생성용 텍스트 프롬프트 구축
    """
    scenario = state.get("scenario")
    if not scenario or not scenario.scenes:
        return ""
    scene = scenario.scenes[scene_index]
    parts = [scenario.title]                # 기초 프롬프트에 제목 추가
    if scenario.description:
        parts.append(scenario.description)  # 시나리오 전체 설명 추가

    # 씬 고유 정보(순서, 목적, 모션, 코미디 요소, 세부 비트) 조합
    scene_bits = [f"scene {scene.scene_number}"]
    if getattr(scene, "purpose", None):
        scene_bits.append(scene.purpose)
    if getattr(scene, "comedy_beat", None):
        scene_bits.append(scene.comedy_beat)
    for beat in getattr(scene, "beats", []) or []:
        if getattr(beat, "text", None):
            scene_bits.append(beat.text)

    # 비트 단위 정보는 ' - '로 연결하고, 전체 문맥은 줄바꿈으로 구분
    parts.append(" - ".join(filter(None, scene_bits)))
    return "\n".join(parts).strip()


def convert_video_prompt_node(prompt: str, modification_request: str = "") -> str:
    """
    LTX 입력 프롬프트 가공 노드
    - 한글 시나리오 → LTX용 영문 I2V 프롬프트로 변환하는 어댑터
    """
    text = (prompt or "").strip()
    if not text:
        return ""

    service = _get_service()
    config = service.config
    client = OpenAI(api_key=config.openai_api_key)

    modification_section = ""
    if modification_request:
        modification_section = f"""
### Modification Request ###
The user wants these changes applied to the regenerated video:
{modification_request}
Incorporate these changes into the prompt while keeping the scene structure intact.
"""

    system_prompt = f"""You convert a structured scene JSON into a concise video-generation prompt for LTX-2.

### LTX-2 Prompting Rules ###
1. Output a single continuous paragraph. No bullet points, no line breaks.
2. Start EVERY prompt with the character's full appearance: hair color/style, skin tone, outfit details, accessories. This MUST be identical across all scenes.
3. After the character description, state the shot type and environment.
4. Describe the character's starting pose concretely.
5. Use temporal connectors (as, while, then, simultaneously) to link actions.
6. Use active present-tense verbs. Describe "how" movement happens.
7. Replace emotion labels with visible cues (e.g., "wide grin" instead of "happy").
8. Specify camera movement (slow push-in, static, tracking shot, etc.).

### Character Identity (HIGHEST PRIORITY) ###
- If a "character_appearance" field exists, it defines THE ONLY character.
- Translate it to ENGLISH. Then expand into a detailed visual description: fur/skin color, clothing, body proportions, distinctive features (ears, tail, eyes, etc.).
- IGNORE and DISCARD any person/human/animal descriptions in "visual_description" or "action" that conflict with "character_appearance". Replace them with the character from "character_appearance".
- Example: if character_appearance="토끼 콘셉트의 캐릭터" → "A cheerful anthropomorphic rabbit with large upright ears, soft white fur, round eyes, wearing a colorful vest" (expand with plausible visual details).
- If "character_appearance" is absent, extract the character's appearance from "visual_description".
- The character's outfit, hair, body type, and colors must NEVER change between scenes.

### STRICT PROHIBITIONS ###
- NEVER include dialogue or spoken words in the prompt. The "dialogue" field is for audio only — ignore it completely.
- NEVER describe text, logos, titles, subtitles, captions, or any written words appearing on screen.
- NEVER mention other characters, friends, bystanders, patrons, or crowds. The scene has ONLY the main character.
- Express the character's communication through body language (gestures, facial expressions, posture) instead of speech.

### Constraints ###
- Style: Stylized 3D animation, non-photorealistic. No real humans.
- Only ONE character in the entire scene. No other people, animals, or characters visible.
- No text, subtitles, captions, logos, or watermarks on screen.
- Language: Translate Korean input into fluent English.
- If a "context" field exists, reflect the product/meme theme in the environment and props, NOT as on-screen text.
{modification_section}
### Input JSON ###
{text}
"""

    response = client.chat.completions.create(
        model=config.openai_model_id,
        messages=[
            {"role": "system", "content": "You are a professional cinematic prompt engineer for video generation models."},
            {"role": "user", "content": system_prompt},
        ],
        temperature=0.3,
        max_tokens=600,
    )

    # 모델 출력 정규화 (None 대비)
    response_text = (response.choices[0].message.content or "").strip()

    def _looks_like_template(value: str) -> bool:
        # 모델이 실제 답 대신 템플릿을 그대로 되돌린 경우 감지
        lowered = value.lower()
        return "input json" in lowered

    def _fallback_prompt(raw: str) -> str:
        # 출력이 비어 있거나 템플릿이면 안전한 기본 프롬프트 생성
        raw = (raw or "").strip()
        if not raw:
            return "A medium shot in a bright, stylized 3D setting with soft ambient lighting."
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                visual = payload.get("visual_description") or payload.get("visual") or ""
                action = payload.get("action") or ""
                scene_type = payload.get("scene_type") or ""
                parts = ["A medium shot in a stylized 3D setting"]
                if scene_type:
                    parts.append(f"during a {scene_type} moment")
                if visual:
                    parts.append(visual)
                if action:
                    parts.append(action)
                return ". ".join(p for p in parts if p)
        except Exception:
            pass
        return raw

    # 사용 불가 출력은 구조화된 fallback으로 대체
    if not response_text or _looks_like_template(response_text):
        response_text = _fallback_prompt(text)

    # 생성 드리프트 방지를 위해 스타일/연속성 가드 추가
    style_guard = "Style: stylized 3D animation, non-photorealistic, no real humans."
    continuity_guard = (
        "Continuity: the character's appearance (face, hair, outfit, colors, body proportions) "
        "must be IDENTICAL to the reference image. Do not alter, add, or remove any clothing or accessories. "
        "Do not add any other people or background characters."
    )
    return f"{response_text}\n{style_guard}\n{continuity_guard}"


def convert_video_prompts_batch(prompts: list[str], modification_request: str = "") -> list[str]:
    """
    모든 씬 프롬프트를 한 번의 GPT 호출로 변환 — 캐릭터 묘사 동일성 보장.
    단일 씬이면 기존 함수를 사용하고, 다수 씬이면 일괄 변환한다.
    """
    if not prompts:
        return []
    if len(prompts) == 1:
        return [convert_video_prompt_node(prompts[0], modification_request)]

    service = _get_service()
    config = service.config
    client = OpenAI(api_key=config.openai_api_key)

    modification_section = ""
    if modification_request:
        modification_section = (
            "\n### Modification Request ###\n"
            f"Apply these changes to all scenes:\n{modification_request}\n"
        )

    numbered = "\n\n".join(f"--- Scene {i+1} ---\n{p}" for i, p in enumerate(prompts))

    system_msg = (
        "You convert structured scene data into concise video-generation prompts for LTX-2.\n\n"
        "### ABSOLUTE RULE ###\n"
        "The character's full appearance description at the START of every prompt "
        "MUST be EXACTLY identical, word-for-word, across ALL scenes. "
        "Write it once for Scene 1, then copy-paste it verbatim for every subsequent scene.\n\n"
        "### LTX-2 Prompting Rules ###\n"
        "1. Each scene = one continuous paragraph. No bullet points, no line breaks.\n"
        "2. Start EVERY prompt with the character's full appearance: "
        "hair color/style, skin tone, outfit details, accessories.\n"
        "3. After the character description, state the shot type and environment.\n"
        "4. Describe the character's starting pose concretely.\n"
        "5. Use temporal connectors (as, while, then, simultaneously) to link actions.\n"
        "6. Use active present-tense verbs.\n"
        "7. Replace emotion labels with visible cues (e.g., 'wide grin' not 'happy').\n"
        "8. Specify camera movement.\n\n"
        "### Character Identity (HIGHEST PRIORITY) ###\n"
        "- If 'character_appearance' exists, it defines THE ONLY character in ALL scenes.\n"
        "- Translate it to ENGLISH. Then expand it into a detailed visual description: "
        "fur/skin color, clothing, body proportions, distinctive features (ears, tail, eyes, etc.).\n"
        "- IGNORE and DISCARD any person/human/animal descriptions in 'visual_description' or 'action'.\n"
        "- Replace them with the character from 'character_appearance'.\n"
        "- Example: if character_appearance='토끼 콘셉트의 캐릭터, 밝은 인상' → "
        "'A cheerful anthropomorphic rabbit character with large upright ears, soft white fur, "
        "round expressive eyes, wearing a colorful vest' (adapt details from the reference image context).\n"
        "- If 'character_appearance' is absent, extract from 'visual_description' of Scene 1.\n\n"
        "### Constraints ###\n"
        "- Style: Stylized 3D animation, non-photorealistic. No real humans.\n"
        "- Only ONE character. Never add extra people.\n"
        "- No text, subtitles, captions, or watermarks on screen.\n"
        "- Translate Korean to fluent English.\n"
        "- Reflect 'context' field in environment/interaction if present.\n\n"
        "### Output ###\n"
        'Return a JSON object: {"prompts": ["scene1 prompt", "scene2 prompt", ...]}'
    )

    user_msg = f"{modification_section}Convert these {len(prompts)} scenes:\n\n{numbered}"

    try:
        response = client.chat.completions.create(
            model=config.openai_model_id,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.0,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        text = (response.choices[0].message.content or "").strip()
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            result = parsed.get("prompts") or parsed.get("scenes") or list(parsed.values())[0]
        elif isinstance(parsed, list):
            result = parsed
        else:
            raise ValueError("unexpected format")

        if not isinstance(result, list) or len(result) != len(prompts):
            raise ValueError(f"expected {len(prompts)} prompts, got {len(result) if isinstance(result, list) else 'non-list'}")

    except Exception as exc:
        logger.warning("Batch prompt conversion failed (%s), falling back to per-scene", exc)
        return [convert_video_prompt_node(p, modification_request) for p in prompts]

    style_guard = "Style: stylized 3D animation, non-photorealistic, no real humans."
    continuity_guard = (
        "Continuity: the character's appearance (face, hair, outfit, colors, body proportions) "
        "must be IDENTICAL to the reference image. Do not alter, add, or remove any clothing or accessories. "
        "Do not add any other people or background characters."
    )
    return [f"{p}\n{style_guard}\n{continuity_guard}" for p in result]


def generate_video_node(state: VideoState) -> dict:
    """
    실제 비디오 생성 실행 노드
    - 씬 단위로 반복 생성
    - state["max_retries"]로 씬별 재시도 횟수 설정 (기본 0)
    """
    scenario = state.get("scenario")
    if not scenario:
        return {"status": "failed", "error": "scenario is required", "output": None}
    if not scenario.scenes:
        return {"status": "failed", "error": "scenario.scenes is empty", "output": None}

    scene_count = len(scenario.scenes)
    outputs: list[dict] = []
    service = _get_service()
    config = service.config
    remote_ready = bool(
        config.comfy_ssh_host
        and config.comfy_ssh_user
        and config.comfy_ssh_key
        and config.comfy_remote_input_dir
    )
    modification_request = (state.get("modification_request") or "").strip()
    max_retries = state.get("max_retries", 0)
    scene_inputs = state.get("scene_inputs") or []
    if not scene_inputs and scenario.script_id:
        scene_inputs = build_scene_inputs_from_db(
            script_id=scenario.script_id,
            output_dir=service.config.output_dir,
            scene_key_map=state.get("scene_key_map"),
            product_context=state.get("product_context"),
        )

    # 프롬프트 일괄 변환 (한 번의 GPT 호출로 캐릭터 묘사 동일성 보장)
    raw_prompts = []
    for idx in range(scene_count):
        prompt = _build_scene_prompt(state, idx)
        if idx < len(scene_inputs) and isinstance(scene_inputs[idx], dict):
            prompt = scene_inputs[idx].get("prompt") or prompt
        if not prompt:
            return {"status": "failed", "error": f"scene {idx} prompt is empty", "output": None}
        raw_prompts.append(prompt)
    converted_prompts = convert_video_prompts_batch(raw_prompts, modification_request)

    for idx in range(scene_count):
        prompt = converted_prompts[idx]
        audio_path = state.get("audio_path")
        audio_url = state.get("audio_url")
        if idx < len(scene_inputs) and isinstance(scene_inputs[idx], dict):
            audio_path = scene_inputs[idx].get("audio_path") or audio_path
            audio_url = scene_inputs[idx].get("audio_url") or audio_url
        if not audio_path and not audio_url:
            return {"status": "failed", "error": "audio_path or audio_url is required", "output": None}
        reference_image_path = None
        reference_image_url = None
        duration_seconds = None
        output_path = None
        scene_key = None
        voice_gen_id = None
        image_id = None
        if idx < len(scene_inputs) and isinstance(scene_inputs[idx], dict):
            reference_image_path = scene_inputs[idx].get("reference_image_path")
            reference_image_url = scene_inputs[idx].get("reference_image_url")
            duration_seconds = scene_inputs[idx].get("duration_seconds")
            output_path = scene_inputs[idx].get("output_path")
            scene_key = scene_inputs[idx].get("scene_key")
            voice_gen_id = scene_inputs[idx].get("voice_gen_id")
            image_id = scene_inputs[idx].get("image_id")
        if remote_ready and not output_path:
            output_path = str(service.config.output_dir / f"scene_{idx + 1:02d}.mp4")
        # 씬별 재시도 루프
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = service.generate_video(
                    prompt=prompt,
                    audio_path=audio_path,
                    audio_url=audio_url,
                    reference_image_path=reference_image_path,
                    reference_image_url=reference_image_url,
                    duration_seconds=duration_seconds,
                    output_path=output_path,
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < max_retries:
                    time.sleep(3)
        if last_error:
            return {
                "status": "failed",
                "error": f"scene {idx} generation failed: {last_error}",
                "scene_outputs": outputs,
                "output": None,
            }

        outputs.append(
            {
                "scene_number": scenario.scenes[idx].scene_number,
                "video_url": result.video_url,
                "duration_seconds": result.duration_seconds or 0.0,
                "storage_path": result.storage_path,
                "model": result.model,
                "local_path": output_path,
            }
        )
        try:
            script_id = scenario.script_id
            if not script_id:
                outputs[-1]["db_error"] = "missing required field: script_id"
                continue
            if not scene_key:
                scene_key = f"{scenario.scenes[idx].scene_type}_{scenario.scenes[idx].scene_number:02d}"
            scene_video_id = upsert_scene_video(
                script_id=script_id,
                scene_key=scene_key,
                voice_gen_id=voice_gen_id,
                image_id=image_id,
                video_url=result.video_url,
                duration_seconds=result.duration_seconds,
                size_bytes=result.size_bytes,
                generation_model=result.model,
                generation_metadata={
                    "prompt": prompt,
                    "reference_image_path": reference_image_path,
                    "reference_image_url": reference_image_url,
                    "audio_path": audio_path,
                    "audio_url": audio_url,
                },
            )
            outputs[-1]["db_scene_video_id"] = scene_video_id
        except Exception as exc:
            outputs[-1]["db_error"] = str(exc)

    return {"status": "ok", "scene_outputs": outputs, "output": None}


def merge_video_node(state: VideoState) -> dict:
    """
    씬 영상을 병합하는 최종 합성 노드
    - 크로스페이드 적용
    """
    scene_outputs = state.get("scene_outputs") or []
    if not scene_outputs:
        return {"status": "failed", "error": "scene_outputs is empty", "output": None}

    service = _get_service()
    output_path = state.get("merged_output_path")

    merge_result = service.merge_videos(
        scene_outputs=scene_outputs,
        output_path=output_path,
    )
    output_path = merge_result["merged_output_path"]
    upload_url = merge_result["merged_video_url"]
    storage_path = merge_result["merged_storage_path"]

    response = {
        "status": "ok",
        "merged_output_path": str(output_path),
        "merged_video_url": upload_url,
        "merged_storage_path": storage_path,
        "output": None,
    }
    try:
        # Insert merged video metadata into videos table when required keys exist.
        company_id = state.get("company_id")
        title = state.get("title") or (state.get("scenario").title if state.get("scenario") else None)
        if not company_id or not title:
            missing = []
            if not company_id:
                missing.append("company_id")
            if not title:
                missing.append("title")
            response["db_error"] = f"missing required fields: {', '.join(missing)}"
            return response
        total_duration = sum(s.get("duration_seconds", 0) for s in scene_outputs)
        video_id = insert_final_video(
            ad_id=state.get("ad_id"),
            company_id=company_id,
            account_id=state.get("account_id"),
            title=title,
            description=state.get("description"),
            s3_url=upload_url,
            file_size_bytes=merge_result["size_bytes"],
            duration_seconds=total_duration if total_duration else None,
            resolution=None,
            fmt=None,
            status="completed",
            script_id=state.get("scenario").script_id if state.get("scenario") else None,
        )
        response["db_video_id"] = video_id
    except Exception as exc:
        response["db_error"] = str(exc)
    return response



def verify_video_node(state: VideoState) -> dict:
    """
    영상 물리 법칙 검증 노드 - Gemini 2.5 Pro 사용
    - 생성된 영상의 물리적/해부학적 오류를 자동 검증
    - 검증 대상: 해부학적 오류, 물리 법칙 위반, 불가능한 동작, 부자연스러운 움직임
    - 점수 기준: ≥60점(사용자 제시), <60점(재생성, 최대 3회)
    - 사용자 피드백 무관, 생성 직후 자동 실행
    """
    video_url = (state.get("merged_video_url") or "").strip()
    retry_count = state.get("retry_count", 0)

    # 필수 입력값 확인
    if not video_url:
        return {"status": "failed", "error": "merged_video_url is required"}

    try:
        config = _get_service().config
        api_key = config.google_api_key
        if not api_key:
            return {"status": "failed", "error": "GOOGLE_API_KEY, GEMINI_API_KEY, or NANO_BANANA_API_KEY is required"}
        
        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-pro"

        # 비디오 파일 업로드
        uploaded = client.files.upload(file=video_url)
        
        # 파일이 ACTIVE 상태가 될 때까지 대기
        max_wait = 60
        wait_interval = 2
        elapsed = 0
        
        while uploaded.state.name != "ACTIVE":
            if elapsed >= max_wait:
                return {"status": "failed", "error": f"File upload timeout after {max_wait}s"}
            time.sleep(wait_interval)
            elapsed += wait_interval
            uploaded = client.files.get(name=uploaded.name)

        prompt = """다음 영상에서 **물리적/해부학적 오류**를 찾아주세요.

중요: 영상의 품질(해상도, 프레임 수)이 아니라 **내용의 오류**만 평가하세요!

검증 대상 (오류만 찾기):
1. 해부학적 오류: 손가락 6개, 팔 3개, 관절이 이상한 방향으로 꺾임 등
2. 물리 법칙 위반: 음료를 코로 마심, 물체가 공중에 떠있음, 중력 무시 등
3. 불가능한 동작: 사람이 할 수 없는 자세나 움직임
4. 부자연스러운 상호작용: 물체를 잡지 않고 들고 있는 것처럼 보임 등

채점 기준 및 예시:
- 0-20점: 심각한 오류 (예: 음료를 코로 마심, 손가락 7개, 팔이 3개)
- 21-40점: 명확한 오류 (예: 물체가 손에 닿지 않는데 들고 있음, 관절이 반대로 꺾임)
- 41-60점: 눈에 띄는 부자연스러움 (예: 움직임이 매우 어색함, 물리 법칙 약간 위반)
- 61-80점: 약간의 이상함 (예: 손 위치가 약간 어색함)
- 81-100점: 거의 완벽하거나 완벽함

주의사항:
- 영상이 정지 이미지로 구성되어 있거나 프레임이 적은 것은 감점 대상이 아닙니다!
- 영상 품질, 해상도, 부드러움은 평가하지 마세요!
- 오직 **내용의 물리적/해부학적 오류**만 찾으세요!

영상을 프레임별로 자세히 분석하여 오류를 찾아주세요.

응답 형식 (JSON):
{"score": 0-100 정수, "analysis": "발견된 구체적인 오류 설명 (오류가 없으면 '오류 없음')"}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=[
                uploaded,
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        # JSON 응답 파싱
        result_text = response.text or "{}"
        verification_result = json.loads(result_text)
        score = verification_result.get("score", 0)
        analysis = verification_result.get("analysis", "")

        # 점수 기준에 따른 결정
        if score >= 60:
            decision = "present_to_user"
            message = f"AI 분석 점수: {score}점. 확인해주세요."
        else:
            if retry_count >= 3:
                decision = "present_to_user"
                message = f"재생성 한도 초과. AI 분석 점수: {score}점. 이대로 진행하시겠습니까?"
            else:
                decision = "auto_retry"
                message = f"물리적 오류 발견 (점수: {score}점). 자동으로 재생성합니다."

        return {
            "status": "ok",
            "verification_result": verification_result,
            "decision": decision,
            "message": message,
            "score": score,
            "analysis": analysis,
            "retry_count": retry_count,
        }

    except Exception as exc:
        return {"status": "failed", "error": str(exc)}
