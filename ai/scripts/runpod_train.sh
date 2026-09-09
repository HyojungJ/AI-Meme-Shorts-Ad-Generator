#!/bin/bash
# RunPod 원클릭 학습 스크립트
# 사용법: curl -sSL https://raw.githubusercontent.com/SKN19-Final-4team/AI/feature/46-scenario-finetuning/scripts/runpod_train.sh | bash

set -e

echo "=============================================="
echo "  시나리오 파인튜닝 - RunPod 자동 설정"
echo "=============================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
REPO_URL="https://github.com/SKN19-Final-4team/AI.git"
BRANCH="feature/46-scenario-finetuning"
WORK_DIR="/workspace/meme-fluencer-finetune"
CONFIG="${CONFIG:-skt_ax.yaml}"  # 환경변수로 변경 가능
# WANDB_API_KEY: 환경변수로 설정

# 함수: 단계 출력
step() {
    echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1"
}

# 함수: 경고 출력
warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 함수: 에러 출력
error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 1. 환경 확인
step "1/8 환경 확인..."
if ! command -v nvidia-smi &> /dev/null; then
    error "NVIDIA GPU를 찾을 수 없습니다. RunPod GPU 인스턴스에서 실행하세요."
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo ""

# 2. HuggingFace 토큰 확인
step "2/8 HuggingFace 토큰 확인..."
if [ -z "$HF_TOKEN" ]; then
    warn "HF_TOKEN 환경변수가 설정되지 않았습니다."
    echo "    다음 중 하나를 실행하세요:"
    echo "    1) export HF_TOKEN=hf_xxxxx"
    echo "    2) huggingface-cli login"
    echo ""
    read -p "계속하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "    HF_TOKEN 설정됨 ✓"
fi

# 3. 패키지 설치
step "3/8 패키지 설치..."
pip install --upgrade pip -q
pip install unsloth -q
pip install --no-deps trl peft accelerate bitsandbytes -q
pip install wandb datasets pyyaml -q
echo "    패키지 설치 완료 ✓"

# 4. 저장소 클론
step "4/8 저장소 클론..."
if [ -d "$WORK_DIR" ]; then
    warn "기존 디렉토리 발견. 업데이트 중..."
    cd "$WORK_DIR"
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    git clone -b "$BRANCH" "$REPO_URL" "$WORK_DIR"
    cd "$WORK_DIR"
fi
echo "    저장소 준비 완료 ✓"

# 5. 데이터 확인
step "5/8 데이터 확인..."
TRAIN_FILE="$WORK_DIR/finetune/data/splits/train.jsonl"
if [ ! -f "$TRAIN_FILE" ]; then
    error "학습 데이터를 찾을 수 없습니다: $TRAIN_FILE"
fi
TRAIN_COUNT=$(wc -l < "$TRAIN_FILE")
echo "    Train 데이터: ${TRAIN_COUNT}개 ✓"

# 6. HuggingFace 로그인
step "6/8 HuggingFace 로그인..."
if [ -n "$HF_TOKEN" ]; then
    huggingface-cli login --token "$HF_TOKEN" --add-to-git-credential
    echo "    로그인 완료 ✓"
else
    if ! huggingface-cli whoami &> /dev/null; then
        warn "HuggingFace 로그인이 필요합니다."
        huggingface-cli login
    else
        echo "    이미 로그인됨 ✓"
    fi
fi

# 7. W&B 로그인 (선택)
step "7/8 W&B 설정..."
if [ -n "$WANDB_API_KEY" ]; then
    wandb login "$WANDB_API_KEY"
    echo "    W&B 로그인 완료 ✓"
else
    warn "WANDB_API_KEY 미설정 - 오프라인 모드로 실행"
    wandb offline
fi

# 8. 학습 시작
step "8/8 학습 시작..."
echo ""
echo "=============================================="
echo "  Config: $CONFIG"
echo "  데이터: ${TRAIN_COUNT}개"
echo "=============================================="
echo ""

cd "$WORK_DIR"
python finetune/training/train.py --config "finetune/training/configs/$CONFIG"

echo ""
echo "=============================================="
echo -e "${GREEN}  학습 완료!${NC}"
echo "=============================================="
echo ""
echo "결과물 위치:"
echo "  $WORK_DIR/finetune/outputs/"
echo ""
echo "모델 업로드:"
echo "  huggingface-cli upload your-username/model-name finetune/outputs/*/lora_adapter"
