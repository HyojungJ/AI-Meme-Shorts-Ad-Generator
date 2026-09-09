# 2026-02-06 변경 사항: 영상 프롬프트 + 병합 + Qwen 음성

- 작업 기간: 2026.02.06
- 작업자: 김진
- 관련 이슈 / PR: #

---


## 개요
1. 영상 프롬프트 보강 (템플릿 방지 + 비실사/단일 캐릭터 강화)
2. 영상 프롬프트/씬 생성, ComfyUI 입력·출력 정리
3. 일관성 유지를 위해 Qwen 음성(voice_design/clone) 사용 방식 변경

---

## 1) 영상 프롬프트 보강 (템플릿 방지 + 비실사/단일 캐릭터 강화)
**목표:** 템플릿 에코 방지, 비실사 스타일 강제, 단일 캐릭터 연속성 강화.

**변경 내용**
1. 영상 프롬프트 변환 어댑터의 템플릿 에코 방지/비실사 강제
2. 실사 인물이 나오지 않도록 프롬프트/워크플로우를 조정
- 템플릿 에코(`Input JSON`) 감지 시 폴백 프롬프트로 대체.
- 예시 및 규칙을 "스타일라이즈드 3D" 중심으로 수정.
- 결과 프롬프트가 항상 `"A cinematic scene begins"`로 시작하도록 보정.
- 결과 프롬프트 끝에 스타일 가드 문구 추가.
- 프롬프트 결과에 연속성 가드 추가 (동일 캐릭터/의상/색상/구도 유지, 다른 사람 금지)
- ComfyUI negative prompt에 인물 추가 방지 키워드 보강

**파일**
- `AI/content_pipeline/video/nodes.py`
- `AI/content_pipeline/video/client.py`

**동작**
- 템플릿 에코 감지 시 최소 폴백 프롬프트로 교체.
- 모든 출력에 실사 방지를 위한 강한 제한 문구 추가:  
  `Style: stylized 3D animation, non-photorealistic, no real humans.`
- LLM 출력에 연속성/단일 캐릭터 지시가 항상 포함됨
- negative prompt가 있으면 인물 추가 관련 키워드가 자동 추가됨

---


## 2) ComfyUI input/output 자동 삭제 보강
**목표:** ComfyUI `input/`, `output/` 파일 자동 삭제 로직 추가

**변경 내용**
- ComfyUI 서버의 input/output 디렉터리 안 파일들 삭제
- `output`/`temp` 타입을 인식해 출력 디렉터리 추론 보강.
- `subfolder`가 `output/`로 시작하는 경우 중복 경로 제거.

**필수 조건**
- 원격 삭제: `COMFY_REMOTE_INPUT_DIR` 필수, 출력 삭제는 `COMFY_REMOTE_OUTPUT_DIR` 권장.

**파일**
- `AI/content_pipeline/video/client.py` (ComfyUI generate_video)
  - input에서 삭제: 업로드한 참조 이미지/오디오 파일
    - 예: image_*.png, audio_*.wav (실제 파일명은 업로드된 이름)
  - output에서 삭제: ComfyUI가 생성한 결과 파일 1개
    - 예: output/ 또는 temp/ 아래의 결과 영상/이미지 파일
- `AI/content_pipeline/video/service.py` (원격 merge)
  - input에서 삭제: 병합용으로 다운로드한 씬 파일들
    - 예: scene_01.mp4, scene_02.mp4 …
  - output에서 삭제: 원격에서 생성된 최종 병합 파일
    - 예: merged_*.mp4

**동작**
- 입력 파일(업로드/다운로드된 이미지·오디오) 자동 삭제.
- 출력 파일(ComfyUI output/temp)의 생성 직후 자동 삭제.


---

## 3) Qwen Voice Design → Clone 경로 적용
**목표:** 
- `voice_design` 모델은 design_voice_node_qwen()에서 샘플 음성 생성 단계에 사용. 이 음성으로 clone prompt를 만들고 S3에 저장.
- `voice_clone` 모델은 generate_voice_node_qwen()에서 clone prompt를 읽어 최종 음성을 생성.
- `voice_id`는 `voice_name`, `voice_description`, `base_model_id`를 기반으로 해시 생성.
- `design_text`(프롬프트)는 `voice_id` 생성에 포함되지 않음.

**변경 내용**
1. legacy(`qwen3:custom`/`qwen3:design`) 경로 제거  
   `AI/content_pipeline/voice/client_qwen.py`, `AI/content_pipeline/voice/nodes.py`에서 레거시 분기 삭제.
2. Voice Design → 샘플 생성 → S3 저장  
   샘플 URL을 `company_characters.voice_sample_url`에 저장.
3. **Voice Cloning 경로 유지**  
   `qwen3:clone:*` voice_id를 사용하고, TTS 단계에서 clone_prompt_url로 합성.
4. 괄호 cue 제거  
   generate 단계에서 `( … )` cue는 제거하고 감정 톤 반영 없이 합성.

**파일**
- `AI/content_pipeline/voice/`
   - client_qwen.py
   - config.py
   - nodes.py
   - service.py
   - state.py

**동작**
- 같은 `voice_description`/`voice_name`/`base_model_id`면 동일한 `voice_id`로 생성.
- 실제 합성은 clone prompt 기반으로 일관성 유지.
