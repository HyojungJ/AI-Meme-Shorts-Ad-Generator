#!/bin/bash
# RunPod ComfyUI 초기 설정 스크립트

echo "=== RunPod ComfyUI 설정 시작 ==="

# ComfyUI 디렉토리로 이동
cd /workspace/ComfyUI

# 1. ComfyUI-KJNodes 설치
echo "1. ComfyUI-KJNodes 설치 중..."
cd custom_nodes
if [ ! -d "ComfyUI-KJNodes" ]; then
    git clone https://github.com/kijai/ComfyUI-KJNodes.git
    cd ComfyUI-KJNodes
    pip install -r requirements.txt
    cd ..
else
    echo "ComfyUI-KJNodes 이미 설치됨"
fi

# 2. ComfyUI-Custom-Scripts 설치
echo "2. ComfyUI-Custom-Scripts 설치 중..."
if [ ! -d "ComfyUI-Custom-Scripts" ]; then
    git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git
else
    echo "ComfyUI-Custom-Scripts 이미 설치됨"
fi

# 3. ComfyUI-VideoHelperSuite 설치
echo "3. ComfyUI-VideoHelperSuite 설치 중..."
if [ ! -d "ComfyUI-VideoHelperSuite" ]; then
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
    cd ComfyUI-VideoHelperSuite
    pip install -r requirements.txt
    cd ..
else
    echo "ComfyUI-VideoHelperSuite 이미 설치됨"
fi

# 4. ComfyUI-LTXVideo 설치 (LTX 모델용)
echo "4. ComfyUI-LTXVideo 설치 중..."
cd /workspace/ComfyUI/custom_nodes
if [ ! -d "ComfyUI-LTXVideo" ]; then
    git clone https://github.com/Lightricks/ComfyUI-LTXVideo.git
    cd ComfyUI-LTXVideo
    pip install -r requirements.txt
    cd ..
else
    echo "ComfyUI-LTXVideo 이미 설치됨"
fi

echo "=== 설치 완료 ==="
echo ""
echo "ComfyUI 시작 명령어:"
echo "cd /workspace/ComfyUI"
echo "python main.py --listen 0.0.0.0 --port 8189 --reserve-vram 1"
