# RunPod 파인튜닝 가이드

시나리오 생성 모델 파인튜닝을 위한 RunPod 환경 설정 및 학습 실행 가이드.

## 목차

1. [사전 준비](#1-사전-준비)
2. [RunPod Pod 생성](#2-runpod-pod-생성)
3. [환경 설정](#3-환경-설정)
4. [데이터 업로드](#4-데이터-업로드)
5. [학습 실행](#5-학습-실행)
6. [모델 저장 및 다운로드](#6-모델-저장-및-다운로드)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 사전 준비

### 필요한 계정

| 서비스 | 용도 | 링크 |
|--------|------|------|
| RunPod | GPU 서버 | https://runpod.io |
| HuggingFace | 모델 다운로드 | https://huggingface.co |
| W&B (선택) | 학습 모니터링 | https://wandb.ai |

### HuggingFace 토큰 발급

1. https://huggingface.co/settings/tokens 접속
2. **New token** → `Read` 권한으로 생성
3. 토큰 복사 (나중에 사용)

### 학습 데이터 확인

```
finetune/data/splits/
├── train.jsonl  (1,962개)
├── val.jsonl    (238개)
└── test.jsonl   (322개)
```

---

## 2. RunPod Pod 생성

### 2.1 GPU 선택

| 모델 | 파라미터 | 권장 GPU | 예상 VRAM | 시간당 비용 |
|------|----------|----------|-----------|-------------|
| SKT A.X 3.1 Light | 7B | A100 40GB | ~16GB | ~$1.5 |
| Kakao Kanana 8B | 8B | A100 40GB | ~18GB | ~$1.5 |
| Mi:dm 2.0 Mini | 2.3B | RTX 4090 | ~8GB | ~$0.7 |

### 2.2 Pod 생성 단계

1. [RunPod Console](https://runpod.io/console/pods) 접속
2. **+ Deploy** 클릭
3. GPU 선택: **A100 40GB** (또는 상위)
4. Template 선택: **RunPod PyTorch 2.8.0**
5. 설정 수정:
   - **Container Disk**: `100 GB`
   - **Volume Disk**: `50 GB` (모델 저장용)
6. Environment Variables 추가:
   ```
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```
7. **Deploy** 클릭

### 2.3 Pod 접속

- **Web Terminal**: Pod 카드에서 **Connect** → **Start Web Terminal**
- **SSH**: `ssh root@{pod-ip} -p {port} -i ~/.ssh/id_rsa`

---

## 3. 환경 설정

### 3.1 기본 환경 확인

```bash
# GPU 확인
nvidia-smi

# Python 버전 확인
python --version  # 3.10+ 필요
```

### 3.2 Unsloth 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# Unsloth 설치 (권장 방법)
pip install unsloth

# 의존성 설치 (버전 충돌 방지)
pip install --no-deps trl peft accelerate bitsandbytes

# 추가 패키지
pip install wandb datasets pyyaml
```

### 3.3 설치 확인

```bash
python -c "from unsloth import FastLanguageModel; print('Unsloth OK')"
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### 3.4 HuggingFace 로그인

```bash
huggingface-cli login
# 프롬프트에 HF_TOKEN 입력
```

### 3.5 W&B 로그인 (선택)

```bash
wandb login
# 프롬프트에 API 키 입력
```

---

## 4. 데이터 업로드

### 방법 1: Git Clone (권장)

```bash
cd /workspace
git clone https://github.com/SKN19-Final-4team/meme-fluencer-AI-finetune.git
cd meme-fluencer-AI-finetune
```

### 방법 2: SCP 직접 업로드

```bash
# 로컬에서 실행
scp -P {port} -r finetune/data/splits root@{pod-ip}:/workspace/data/
scp -P {port} -r finetune/training root@{pod-ip}:/workspace/training/
```

### 방법 3: S3/GCS 사용

```bash
# RunPod에서 실행
pip install awscli
aws s3 cp s3://your-bucket/finetune-data/ /workspace/data/ --recursive
```

### 데이터 구조 확인

```bash
ls -la /workspace/meme-fluencer-AI-finetune/finetune/data/splits/
# train.jsonl, val.jsonl, test.jsonl 확인
```

---

## 5. 학습 실행

### 5.1 Config 확인

```bash
cat finetune/training/configs/skt_ax.yaml
```

주요 설정:
```yaml
model_name: "skt/A.X-3.1-Light"
max_seq_length: 4096
lora_r: 16
lora_alpha: 32
lora_dropout: 0.1
use_dora: true
batch_size: 2
grad_accum: 4
learning_rate: 0.0002
epochs: 3
use_neftune: true
neftune_noise_alpha: 5
use_wandb: true
```

### 5.2 학습 시작

```bash
cd /workspace/meme-fluencer-AI-finetune

# SKT A.X 모델
python finetune/training/train.py --config finetune/training/configs/skt_ax.yaml

# Kakao Kanana 모델
python finetune/training/train.py --config finetune/training/configs/kanana_8b.yaml

# Mi:dm Mini 모델
python finetune/training/train.py --config finetune/training/configs/midm_mini.yaml
```

### 5.3 백그라운드 실행 (SSH 끊김 방지)

```bash
# tmux 사용
tmux new -s training
python finetune/training/train.py --config finetune/training/configs/skt_ax.yaml

# 세션 분리: Ctrl+B, D
# 재접속: tmux attach -t training
```

또는:

```bash
nohup python finetune/training/train.py --config finetune/training/configs/skt_ax.yaml > training.log 2>&1 &
tail -f training.log
```

### 5.4 학습 모니터링

- **W&B**: https://wandb.ai 에서 실시간 확인
- **로컬 로그**: `tail -f training.log`
- **GPU 사용량**: `watch -n 1 nvidia-smi`

### 5.5 예상 학습 시간

| 모델 | 데이터 | GPU | 예상 시간 |
|------|--------|-----|-----------|
| SKT A.X 7B | 2,000개 | A100 40GB | ~2-3시간 |
| Kanana 8B | 2,000개 | A100 40GB | ~3시간 |
| Mi:dm 2.3B | 2,000개 | RTX 4090 | ~1시간 |

---

## 6. 모델 저장 및 다운로드

### 6.1 학습 완료 후 파일 위치

```
finetune/outputs/{model_name}_{timestamp}/
├── lora_adapter/
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   └── tokenizer files...
└── training_info.json
```

### 6.2 HuggingFace Hub 업로드

```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_folder(
    folder_path="finetune/outputs/{model_name}_{timestamp}/lora_adapter",
    repo_id="your-username/scenario-lora-adapter",
    repo_type="model",
)
```

### 6.3 로컬로 다운로드

```bash
# 로컬에서 실행
scp -P {port} -r root@{pod-ip}:/workspace/finetune/outputs/ ./outputs/
```

### 6.4 GGUF 변환 (선택)

```bash
# Ollama/llama.cpp용 변환
python -m unsloth.save_gguf \
    --model_path finetune/outputs/{model}/lora_adapter \
    --output_path finetune/outputs/{model}/gguf \
    --quantization q4_k_m
```

---

## 7. 트러블슈팅

### CUDA Out of Memory

```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**해결:**
1. `batch_size` 줄이기 (2 → 1)
2. `grad_accum` 늘리기 (4 → 8)
3. `max_seq_length` 줄이기 (4096 → 2048)

### Unsloth 설치 오류

```
ERROR: Could not find a version that satisfies the requirement unsloth
```

**해결:**
```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```

### 모델 다운로드 실패

```
OSError: We couldn't connect to 'https://huggingface.co'
```

**해결:**
```bash
# HF 토큰 재설정
huggingface-cli login --token $HF_TOKEN

# 또는 환경변수로
export HF_TOKEN=hf_xxxxxxxxxxxx
```

### W&B 연결 오류

```
wandb: ERROR Run initialization has timed out
```

**해결:**
```bash
# 오프라인 모드
wandb offline

# 또는 W&B 비활성화
# config에서 use_wandb: false
```

### SSH 연결 끊김

**해결:**
- `tmux` 또는 `screen` 사용
- `nohup` 으로 백그라운드 실행

---

## 부록: 빠른 시작 스크립트

```bash
#!/bin/bash
# quick_start.sh

set -e

echo "=== 1. 환경 설정 ==="
pip install --upgrade pip
pip install unsloth wandb datasets pyyaml
pip install --no-deps trl peft accelerate bitsandbytes

echo "=== 2. HuggingFace 로그인 ==="
huggingface-cli login --token $HF_TOKEN

echo "=== 3. 데이터 확인 ==="
ls -la finetune/data/splits/

echo "=== 4. 학습 시작 ==="
python finetune/training/train.py --config finetune/training/configs/skt_ax.yaml

echo "=== 완료 ==="
```

실행:
```bash
chmod +x quick_start.sh
./quick_start.sh
```

---

## 참고 자료

- [RunPod Documentation](https://docs.runpod.io)
- [Unsloth Documentation](https://docs.unsloth.ai)
- [HuggingFace PEFT](https://huggingface.co/docs/peft)
- [W&B Documentation](https://docs.wandb.ai)
