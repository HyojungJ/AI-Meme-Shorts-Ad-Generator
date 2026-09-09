# 씬 병합 영상 생성 파이프라인 구성 (자동화 미적용)

- 작업 기간: 2026.01.25 (02-03 업데이트)
- 작업자: kj
- 관련 이슈 / PR: #20

---

## 개요
### 작업 내용
- 씬별 영상을 **FFmpeg 기반**으로 합치는 표준 흐름을 정리
- **마지막 프레임 추출 → 다음 씬 레퍼런스 → 크로스페이드 합치기** 절차 정의
- 자동화 파이프라인에 적용 가능한 최소 입력/출력 스펙과 명령어 레시피 제공

### 주요 기능
1. 로컬 `content_pipeline`이 ComfyUI 서버로 씬 생성 요청 전송
2. ComfyUI 서버가 씬별 mp4 생성 후 서버 디스크에 저장
3. 서버에서 마지막 프레임 추출(FFmpeg) → 다음 씬 레퍼런스로 사용
4. 씬별 영상 규격 정규화(해상도/FPS/코덱)
5. 씬 목록(scenes.txt) 생성 후 FFmpeg로 병합(서버에서 실행)
6. 크로스페이드 + 오디오 L-컷 합치기

---

## 데이터 입출력
### 입력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| scene_videos | list[path] | 씬별 영상 목록 | `["scene_01.mp4", "scene_02.mp4"]` |
| scenes_jsonl | path | 씬 생성 배치 입력(JSONL) | `scenes.jsonl` |
| audio_path | path | 로컬 오디오 경로(자동 업로드) | `data/audio/scene_01.mp3` |
| reference_image_path | path | 로컬 레퍼런스 이미지 경로(자동 업로드) | `data/images/scene_01.png` |
| output_fps | int | 최종 출력 FPS | `24` |
| output_resolution | str | 최종 출력 해상도 | `1280x720` |
| crossfade_seconds | float | 비디오/오디오 크로스페이드 길이 | `0.3` |


### 출력 데이터

| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| last_frame_image | path | 다음 씬 레퍼런스로 사용할 마지막 프레임 | `scene_01_last.png` |
| scenes_result_jsonl | path | 씬 생성 결과(JSONL) | `results.jsonl` |
| merged_video | path | 최종 합쳐진 영상 | `merged.mp4` |

---

## 코드 구성
### 기능/모듈명
- 추가/수정 파일:
- `docs/kj/2026-01-24_scene_merge.md`
- `scripts/video_merge.py`
- `content_pipeline/video/client.py`

- **마지막 프레임 지원 (로컬):**
- `content_pipeline/pipeline.py`
  - COMFY_REMOTE_INPUT_DIR + COMFY_SSH_HOST 설정이 없으면 extract_last_frame() 호출
- `content_pipeline/video/service.py`
  - extract_last_frame()에서 로컬 ffmpeg/ffprobe로 추출
- `content_pipeline/video/nodes.py`
  - service.extract_last_frame(...) 호출 (로컬 방식만 사용)
- `scripts/video_generate_batch.py`
  - _extract_last_frame()로 로컬 ffmpeg 추출

- **마지막 프레임 지원 (원격):**
- `AI/content_pipeline/pipeline.py`
  - COMFY_REMOTE_INPUT_DIR + COMFY_SSH_HOST 설정 시 extract_last_frame_remote() 호출
- `AI/content_pipeline/video/service.py`
  - extract_last_frame_remote()에서 SSH+ffmpeg로 원격 추출
  - S3/HTTP 경로 다운로드 후 병합 처리
- `AI/content_pipeline/video/client.py`
  - 원격 입력 디렉터리로 S3/HTTP 파일 다운로드 (_download_remote_input)
  - payload 로그 출력 추가
- `AI/scripts/video_merge.py`
  - 병합 시 last-frame 추출 옵션 추가

---

## 프로젝트 구조
- 변경 사항: O
```bash
content_pipeline/
├─ video/client.py                    # /upload/audio 405일 때 파일명만 쓰는 fallback 추가
├─ scripts/
|   ├─ video_generate_batch.py        # 여러 씬을 일괄 생성
|   └─ video_merge.py                 # 생성된 씬들을 병합/정규화
├─ data/
|   └─ scenes/scenes.jsonl            # 씬별 입력 메타데이터 리스트
└─ docs/kj/2026-01-24_scene_merge.md
```

- 서버 경로
```bash
ComfyUI/
├─ merge_video/             
|   ├─ scenes.txt           # 병합할 mp4 파일 경로
|   └─ video_merge.py
├─ input/                   # 입력(오디오/이미지)
├─ output/                  # 출력(씬별 mp4)
└─ data/video/merged.mp4    # 병합 결과(최종 mp4)
```
---

## 실행/테스트 방법
### 역할 분리
- 로컬: 오케스트레이션(요청, 상태 관리, 메타데이터 수집)
- 서버: 실제 생성(ComfyUI) + 병합(FFmpeg) + 대용량 I/O

### 1) Scene1 생성 (로컬)
```bash
uv run python -m scripts.video_generate_test `
  --prompt "A young woman sits on a sunlit park bench. She speaks naturally, then brings a regular cola bottle to her lips and drinks through her mouth, swallowing normally. Do not distort, deform, or change the shape of the cola bottle. Keep the bottle realistic and unchanged." `
  --reference-image-path "data/images/scene_01.png" `
  --audio-path "data/audio/scene_01.mp3" `
  --output-path "data/video/scene_01.mp4"
```

### 2) Scene1 결과 mp4에서 마지막 프레임 추출 (서버)
```bash
ffmpeg -y -sseof -0.1 -i "/workspace/ComfyUI/output/LTX-2 Image Audio 2 Video  _00020_.mp4" -frames:v 1 /workspace/ComfyUI/input/scene_01_last.png
```

### 3) 마지막 프레임 로컬로 복사 (로컬)
```bash
scp -P 39443 root@103.196.86.144:/workspace/ComfyUI/input/scene_01_last.png data/images/
```

### 4) scene_01_last.png를 레퍼런스로 Scene2 생성 (로컬)
```bash
uv run python -m scripts.video_generate_test `
  --prompt "She gently turns the bottle, looks at the label, and smiles. The frame transitions smoothly from her to a wide shot of children running and laughing across the park. Same lighting and color grading as the previous scene, warm daylight, consistent exposure, same camera angle and background tone." `
  --reference-image-path "data/images/scene_01_last.png" `
  --audio-path "data/audio/scene_02.mp3" `
  --output-path "data/video/scene_02.mp4"
```

### 5) 병합할 mp4 파일 경로 scenes.txt에 저장 (서버)
```bash
printf "/workspace/ComfyUI/output/<scene1>.mp4\n/workspace/ComfyUI/output/<scene2>.mp4\n" > /workspace/ComfyUI/merge_video/scenes.txt
```

### 6) 병합 (서버) 
```bash
python merge_video/video_merge.py --scenes merge_video/scenes.txt --output data/video/merged.mp4 --crossfade 0.3
```

### 7) 재인코딩해서 호환성 높이기 (서버)
```bash
ffmpeg -y -i /workspace/ComfyUI/data/video/merged.mp4 `
  -c:v libx264 -profile:v baseline -level 3.1 -pix_fmt yuv420p `
  -c:a aac -ar 48000 -ac 2 `
  /workspace/ComfyUI/data/video/merged_compat.mp4
```

### 8) 내려받기 (로컬)
```bash
scp -P 39443 root@103.196.86.144:/workspace/ComfyUI/data/video/merged_compat.mp4 data/video/
```
---

## 트러블 슈팅

1. last frame 추출 실패 (Output file is empty)
- 원인: `-sseof -0.01`이 너무 촘촘하거나 입력 파일이 정상적이지 않음
- 해결: `-sseof -0.1`로 완화하고 `ffprobe`로 duration 확인 후 재시도

2. 병합 결과가 로컬에서 재생되지 않음
- 원인: 플레이어/코덱 호환 문제 또는 moov atom 위치 문제
- 해결: baseline 재인코딩 후 다운로드

3. 원격 병합 대응 부족
- 원인: 마지막 프레임 추출/병합을 로컬에서만 수행해 원격 환경에서 씬 연결이 불안정
- 해결: 마지막 프레임 추출을 로컬/원격 모두 지원하도록 확장하고, 원격 병합 스크립트에 마지막 프레임 추출 옵션을 추가