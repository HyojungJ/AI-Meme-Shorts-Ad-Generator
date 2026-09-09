# 씬 병합 자동화 파이프라인

- 작업 기간: 2026.01.25
- 작업자: kj
- 관련 이슈 / PR: #20

---

## 개요
### 작업 내용
- 씬 생성 후 병합까지 이어지는 자동 합성 노드를 추가
- 병합 파라미터(크로스페이드/출력 경로) 상태 전달
- 병합은 ffmpeg가 있는 환경에서 실행됨 (로컬/서버 중 선택)

### 주요 기능
1. scenes.jsonl 읽어 임시 '영상 생성 입력용 스키마' 구성
2. scene_inputs에 씬별 prompt/오디오/이미지/출력 경로를 넣음
3. generate -> merge -> postprocess 일괄 실행
2. 병합 노드 실행
   - scene_inputs의 순서대로 생성된 영상이 자동으로 병합 대상
   - `crossfade_seconds` 사용 (기본 0.3)
   - `merged_output_path` 사용 (미지정 시 기본 경로)
3. 병합 결과 URL/경로 반환
4. 차후 스토리지 업로드(LOCAL/S3)가 가능하도록 변경 (미구현)


---

## 입력/출력 규칙
### 입력(상태)
| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| crossfade_seconds | float | 크로스페이드 길이(초), 미지정 시 0.3 | `0.3` |
| merged_output_path | str | 병합 결과 출력 경로 | `data/video/merged.mp4` |

### 출력(상태)
| **항목** | **타입** | **설명** | **예시** |
| --- | --- | --- | --- |
| merged_video_url | str | 병합 결과 업로드 URL | `https://.../merged.mp4` |
| merged_storage_path | str | 병합 결과 스토리지 경로 | `s3://bucket/merged.mp4` |
| merged_output_path | str | 병합 결과 로컬 경로 | `data/video/merged.mp4` |

---

## 코드 구성
### 기능/모듈명
- 추가/수정 파일:
- `video/nodes.py` 
  - `merge_video_node` 추가
- `video/graph.py` 
  - `generate -> merge -> END` 연결
- `video/state.py` 
  - `crossfade_seconds`, `merged_output_path` 상태 필드
  - `merged_video_url`, `merged_storage_path` 결과 필드


## 프로젝트 구조
- 변경 사항: O
```bash
content_pipeline/
├─ video/
|   ├─ nodes.py                       # 영상 병합 노드 추가
|   ├─ graph.py                       
|   └─ state.py
├─ scripts/
|   └─ video_graph_from_scenes.py     # 씬 생성부터 병합까지 graph 실행
├─ data/
|   └─ scenes/scenes.jsonl            # 씬별 입력 메타데이터 리스트
└─ docs/kj/2026-01-24_scene_merge.md
```

---
## 실행/테스트 방법 (자동화)
### 역할 분리
- 로컬: 오케스트레이션(요청, 상태 관리, 메타데이터 수집) + 병합(FFmpeg)
- 서버: 실제 생성(ComfyUI)

### 서버
#### 1) 의존성 설치
```bash
cd ComfyUI
pip install -r requirements.txt

# 기본 도구
apt update
apt install -y git ffmpeg python3-pip

# 파이썬 의존성
pip install opencv-python imageio-ffmpeg
pip install scikit-image
```

#### 2) ComfyUI 실행
```powershell
python main.py --listen 127.0.0.1 --port 8188 --reserve-vram 1
```

### 로컬
#### 0) 전제
- 병합을 실행하는 환경에 ffmpeg가 설치된 상태에서 실행
- `scene_outputs[*].storage_path`는 병합을 실행하는 환경의 로컬 경로
```bash
$bin = "C:\Users\user\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
$env:Path = "$bin;$env:Path"
ffmpeg -version
```

#### 1) 로컬 터미널에서 SSH 터널 생성
```bash
ssh -N -L 8189:localhost:8188 root@<RUNPOD_PUBLIC_IP>
```

#### 2) 스크립트 기반 실행
`scenes.jsonl`을 기반으로 video graph 실행

```bash
uv run python -m scripts.video_graph_from_scenes `
  --scenes data/scenes/scenes.jsonl `
  --crossfade 0.3 `
  --merged-output-path data/video/merged.mp4
```