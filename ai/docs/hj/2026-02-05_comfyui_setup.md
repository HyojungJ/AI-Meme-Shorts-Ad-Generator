# ComfyUI 커스텀 노드 의존성 설치 가이드

## 문제
ComfyUI에서 LTX-2 워크플로우 실행 시 커스텀 노드들이 로드되지 않는 문제 발생

## 원인
- VideoHelperSuite: `cv2`, `imageio-ffmpeg` 등 누락
- KJNodes: `cv2`, `scikit-image` 등 누락
- Impact Pack: `cv2` 등 누락
- Manager: `gitpython` 누락
- LTXVideo: `torchaudio` 버전 불일치

## 해결 방법 (RunPod 또는 ComfyUI 환경)

### 1. 기본 의존성 설치
```bash
pip install opencv-python opencv-python-headless imageio-ffmpeg scikit-image gitpython piexif
```

### 2. PyTorch 및 torchaudio 재설치 (버전 일치)
```bash
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### 3. 각 커스텀 노드 requirements 설치 (선택사항)
```bash
cd /workspace/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite
pip install -r requirements.txt

cd /workspace/ComfyUI/custom_nodes/ComfyUI-KJNodes
pip install -r requirements.txt

cd /workspace/ComfyUI/custom_nodes/ComfyUI-Impact-Pack
pip install -r requirements.txt

cd /workspace/ComfyUI/custom_nodes/ComfyUI-Manager
pip install -r requirements.txt

cd /workspace/ComfyUI/custom_nodes/ComfyUI-LTXVideo
pip install -r requirements.txt
```

### 4. ComfyUI 재시작
```bash
# 실행 중인 ComfyUI 프로세스 종료
pkill -f "python.*main.py"

# ComfyUI 재시작
cd /workspace/ComfyUI
python main.py
```

## 한 번에 실행하는 스크립트

```bash
#!/bin/bash

echo "=== ComfyUI 커스텀 노드 의존성 설치 시작 ==="

# 1. 기본 의존성 설치
echo "1. 기본 의존성 설치 중..."
pip install opencv-python opencv-python-headless imageio-ffmpeg scikit-image gitpython piexif

# 2. PyTorch 재설치
echo "2. PyTorch 및 torchaudio 재설치 중..."
pip uninstall -y torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 3. 커스텀 노드 requirements 설치
echo "3. 커스텀 노드 requirements 설치 중..."
cd /workspace/ComfyUI/custom_nodes

for node_dir in ComfyUI-VideoHelperSuite ComfyUI-KJNodes ComfyUI-Impact-Pack ComfyUI-Manager ComfyUI-LTXVideo; do
    if [ -d "$node_dir" ] && [ -f "$node_dir/requirements.txt" ]; then
        echo "   - $node_dir 설치 중..."
        cd "$node_dir"
        pip install -r requirements.txt
        cd ..
    fi
done

echo "=== 설치 완료 ==="
echo "ComfyUI를 재시작하세요: cd /workspace/ComfyUI && python main.py"
```

## 설치 확인

ComfyUI 시작 로그에서 다음 메시지 확인:
```
0.3 seconds: /workspace/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite
0.3 seconds: /workspace/ComfyUI/custom_nodes/ComfyUI-KJNodes
0.5 seconds: /workspace/ComfyUI/custom_nodes/ComfyUI-Impact-Pack
0.7 seconds: /workspace/ComfyUI/custom_nodes/ComfyUI-Manager
0.X seconds: /workspace/ComfyUI/custom_nodes/ComfyUI-LTXVideo
```

`(IMPORT FAILED)` 메시지가 없어야 정상입니다.

## 필요한 노드들
- `VHS_LoadAudioUpload` (VideoHelperSuite)
- `ImageResizeKJv2` (KJNodes)
- `LTXAVTextEncoderLoader` (LTXVideo)
- `CreateVideo` (VideoHelperSuite)
- `SaveVideo` (VideoHelperSuite)

## 날짜
2026-02-05
