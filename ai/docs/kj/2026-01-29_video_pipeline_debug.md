# 영상 파이프라인 정리/디버그 기록

- 작업 기간: 2026.01.29
- 작업자: 김진
- 관련 이슈 / PR: #75

---

## 개요
- ComfyUI 원격 입력(SSH+curl) 기반으로 전환 및 문제 원인 파악
- 비디오 생성 파이프라인의 프롬프트 입력 흐름 정리
- DB에서 씬 정보를 가져와 LTX용 프롬프트로 변환하는 어댑터 노드를 추가
- ElevenLabs 커스텀 보이스 슬롯이 최대치에 도달하면 슬롯 자동 정리

---

## 변경 요약
    
### 1) DB → 비디오 프롬프트 전달 방식 변경
- `scenario_scripts.scenes`의 **씬 단일 객체(JSON)** 를 그대로 프롬프트로 전달
- 기존 action/visual 조합 방식은 **씬 객체가 없을 때만 fallback**
- 관련 파일
  - `content_pipeline/video/utils.py`

### 2) LTX 프롬프트 어댑터 노드 추가
- `convert_video_prompt_node`에서 **씬 JSON → LTX용 영문 시네마틱 프롬프트** 변환
- `generate_video_node`에서 변환된 프롬프트를 사용해 영상 생성
- 관련 파일
  - `content_pipeline/video/nodes.py`

### 3) 불필요한 DB 호출 최소화
- 씬 JSON이 있는 경우 `load_scenario_prompts()` 호출 제거
- fallback 시에만 호출하도록 변경
- 관련 파일
  - `content_pipeline/video/utils.py`

### 4) 보이스 슬롯 자동 정리
- ElevenLabs 커스텀 보이스 슬롯이 최대치에 도달하면, 가장 오래된 보이스부터 삭제하고 신규 보이스를 생성하도록 처리
- `voice_type=non-default` / `created_at_unix` 기준 오름차순 정렬 후 초과분 삭제
- 관련 환경 변수
  - `ELEVENLABS_MAX_CUSTOM_VOICES` : 커스텀 보이스 최대 개수 (기본 25)
- 관련 파일
  - `content_pipeline/voice/client.py`
  - `content_pipeline/voice/config.py`
  - `content_pipeline/voice/service.py`
  - `.env.example`


---

## 테스트/검증
- 수동 검증: `scene_inputs`에 씬 JSON이 그대로 들어가는지 확인
- 변환 검증: `convert_video_prompt_node` 출력이 LTX용 프롬프트로 생성되는지 확인

---

## 참고
- 씬 객체가 없을 경우에만 action/visual 조합 fallback 사용
- 프롬프트 품질 편차를 줄이기 위해 어댑터 노드 기반으로 입력 정규화