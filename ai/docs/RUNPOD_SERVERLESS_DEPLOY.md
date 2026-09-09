# RunPod Serverless vLLM 배포 매뉴얼

SKT A.X 3.1 Light (7B) + DoRA LoRA 어댑터를 RunPod Serverless에 배포하는 가이드.

## 모델 정보

| 항목 | 값 |
|------|-----|
| 베이스 모델 | `skt/A.X-3.1-Light` (7B, LlamaForCausalLM) |
| 어댑터 | DoRA LoRA (r=16, alpha=32) |
| 어댑터 크기 | 169MB (`lora_adapter/` 폴더) |
| 베이스 모델 크기 | ~14GB (FP16) |
| 필요 GPU VRAM | ~16GB (FP16, 양자화 불필요) |
| max_seq_length | 4096 |

## 로컬 파일 위치

```
AI-finetune/finetune/outputs/A.X-3.1-Light_20260201_095908/
├── lora_adapter/              ← 배포에 필요한 폴더 (이것만 업로드)
│   ├── adapter_config.json
│   ├── adapter_model.safetensors  (157MB)
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   ├── vocab.json
│   ├── merges.txt
│   ├── special_tokens_map.json
│   └── chat_template.jinja
├── checkpoint-738/            ← 최종 체크포인트 (학습 메타 포함)
└── training_info.json
```

---

## Step 1: RunPod 계정 설정

1. https://www.runpod.io 접속 → 회원가입/로그인
2. **Settings** → **API Keys** → **Create API Key**
3. 생성된 API Key 복사해두기 (나중에 `.env`에 사용)

---

## Step 2: Network Volume 생성

베이스 모델(14GB) + LoRA 어댑터(169MB)를 저장할 영구 스토리지.

1. RunPod 콘솔 → 좌측 **Storage** → **Network Volumes**
2. **+ Network Volume** 클릭
3. 설정:
   - **Name**: `meme-fluencer-models`
   - **Region**: `EU-RO-1` (GPU 가용성 높음)
   - **Size**: `30 GB`
4. **Create** 클릭

> **주의**: Network Volume의 리전을 기억해두기. 이후 Pod과 Serverless Endpoint 모두 **같은 리전**이어야 함.

---

## Step 3: 임시 GPU Pod으로 모델 업로드

Network Volume에 모델 파일을 넣기 위해 임시 Pod을 띄운다.

### 3-1. Pod 생성

1. RunPod 콘솔 → **Pods** → **+ GPU Pod**
2. GPU 선택: 아무거나 싼 거 (`RTX 4090` 등)
   - **반드시 Network Volume과 같은 리전의 GPU를 선택** (다른 리전이면 Volume이 안 보임)
3. Template 선택: `RunPod Pytorch 2.1` (또는 아무 Linux 템플릿)
4. **Customize Deployment** 클릭하여 상세 설정 펼치기
5. Volume 섹션에서:
   - **Network Volume** 드롭다운 → `meme-fluencer-models` 선택
   - 선택하면 자동으로 `/runpod-volume`에 마운트됨
   - (드롭다운이 비어있으면 리전 불일치 → 다른 리전 GPU 선택)
6. **Deploy** 클릭
7. Pod이 Running 상태가 되면 **Connect** → **SSH** 정보 확인

### 3-2. Pod에 SSH 접속

```bash
ssh root@<POD_IP> -p <PORT> -i ~/.ssh/id_ed25519
```

### 3-3. 베이스 모델 다운로드

Pod 안에서 실행:

```bash
pip install huggingface_hub

# huggingface-cli가 안 되는 경우 Python으로 직접 다운로드
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='skt/A.X-3.1-Light',
    local_dir='/runpod-volume/models/base',
    local_dir_use_symlinks=False
)
print('Download complete')
"
```

> 약 14GB 다운로드

### 3-4. LoRA 어댑터 업로드

**로컬 터미널**에서 (Pod 아님) 실행:

```bash
POD_IP=<POD_IP>
POD_PORT=<PORT>

scp -P $POD_PORT -i ~/.ssh/id_ed25519 -r \
  ~/Desktop/meme-fluencer/AI-finetune/finetune/outputs/A.X-3.1-Light_20260201_095908/lora_adapter \
  root@$POD_IP:/runpod-volume/models/lora_adapter
```

### 3-5. 업로드 확인

Pod에서 실행:

```bash
echo "=== 베이스 모델 ==="
ls /runpod-volume/models/base/*.safetensors | head -5
du -sh /runpod-volume/models/base/

echo "=== LoRA 어댑터 ==="
ls /runpod-volume/models/lora_adapter/
du -sh /runpod-volume/models/lora_adapter/
```

예상 결과:
```
=== 베이스 모델 ===
/runpod-volume/models/base/model-00001-of-00004.safetensors
...
14G     /runpod-volume/models/base/

=== LoRA 어댑터 ===
adapter_config.json  adapter_model.safetensors  tokenizer.json  ...
169M    /runpod-volume/models/lora_adapter/
```

### 3-6. 임시 Pod 종료

확인 끝나면 Pod 즉시 종료 (과금 멈춤):

1. RunPod 콘솔 → Pods → 해당 Pod → **Stop** → **Terminate**

> Network Volume은 Pod과 독립적이라 Pod 종료해도 데이터 유지됨

---

## Step 4: Serverless Endpoint 생성

### 4-1. 기본 Endpoint 생성 (베이스 모델 + LoRA 지원)

1. RunPod 콘솔 → 좌측 **Serverless** → **+ New Endpoint**

2. **Select a Template** 화면에서:
   - **vLLM** 카드 선택 (RunPod 공식 vLLM Worker)
   - 또는 검색에서 `vllm` 입력

3. **Worker Configuration**:
   - **Endpoint Name**: `scenario-vllm`
   - **GPU**: `48GB` (A40 또는 L40)
     - 7B FP16 모델 + LoRA = ~16GB, 48GB면 넉넉
     - 24GB GPU도 가능하나 여유가 적음
   - **Network Volume**: `meme-fluencer-models` 선택
     - 같은 리전이어야 드롭다운에 표시됨

4. **Scaling**:
   - **Min Workers**: `0` (요청 없으면 자동 꺼짐, 비용 절감)
   - **Max Workers**: `1` (테스트용)
   - **Idle Timeout**: `5초`
   - **Execution Timeout**: `300초`

5. **Environment Variables** (하나씩 추가):

   | Key | Value | 설명 |
   |-----|-------|------|
   | `MODEL_NAME` | `/runpod-volume/models/base` | 베이스 모델 경로 |
   | `TOKENIZER_NAME` | `/runpod-volume/models/base` | 토크나이저 경로 |
   | `GPU_MEMORY_UTILIZATION` | `0.9` | GPU 메모리 90% 사용 (**1.0 금지 — 크래시 발생**) |
   | `MAX_MODEL_LEN` | `4096` | 최대 시퀀스 길이 |
   | `TRUST_REMOTE_CODE` | `1` | 커스텀 모델 코드 허용 |
   | `DISABLE_LOG_STATS` | `1` | 로그 줄이기 |
   | `ENABLE_LORA` | `1` | LoRA 기능 활성화 |
   | `MAX_LORA_RANK` | `64` | 최대 LoRA rank (우리는 16이지만 여유있게) |
   | `LORA_MODULES` | (아래 참조) | LoRA 어댑터 경로 |

6. **Create Endpoint** 클릭

7. Endpoint가 생성되면 **Endpoint ID** 복사 (대시보드에 표시됨)

---

### 4-2. LORA_MODULES 설정 (핵심)

`LORA_MODULES` 환경변수는 JSON 배열 형식이어야 한다. RunPod vLLM Worker 코드가 이렇게 파싱:

```python
adapters = json.loads(os.getenv("LORA_MODULES", '[]'))
for adapter in adapters:
    LoRAModulePath(**adapter)  # name, path 필수
```

**올바른 값:**

```
[{"name":"scenario-lora","path":"/runpod-volume/models/lora_adapter"}]
```

- `name`: 추론 요청에서 모델 이름으로 사용할 이름
- `path`: Network Volume 내 LoRA 어댑터 경로

**RunPod UI에 입력할 때:**
- Key: `LORA_MODULES`
- Value: `[{"name":"scenario-lora","path":"/runpod-volume/models/lora_adapter"}]`
- 그대로 복사해서 붙여넣기

> **주의**: RunPod UI가 JSON의 따옴표를 제거하는 버그가 있을 수 있음. Worker 로그에 `LoRAModulePath() argument after ** must be a mapping, not str` 에러가 나면 [4-3. LORA_MODULES 문제 해결](#4-3-lora_modules-ui-문제-해결) 참조.

---

### 4-3. LORA_MODULES UI 문제 해결

RunPod UI에서 JSON 환경변수 값이 깨지는 경우, 아래 3가지 방법 중 하나를 사용.

#### 방법 A: RunPod API로 Endpoint 수정 (권장)

UI를 우회하고 API로 직접 환경변수를 설정. JSON이 정확히 보존됨.

```bash
RUNPOD_API_KEY=<API Key>
ENDPOINT_ID=<Step 4에서 생성한 Endpoint ID>

# 기존 Endpoint에 LORA_MODULES 환경변수 추가
curl -s -X PATCH "https://rest.runpod.io/v1/endpoints/${ENDPOINT_ID}" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "env": {
      "MODEL_NAME": "/runpod-volume/models/base",
      "TOKENIZER_NAME": "/runpod-volume/models/base",
      "GPU_MEMORY_UTILIZATION": "0.9",
      "MAX_MODEL_LEN": "4096",
      "TRUST_REMOTE_CODE": "1",
      "DISABLE_LOG_STATS": "1",
      "ENABLE_LORA": "1",
      "MAX_LORA_RANK": "64",
      "LORA_MODULES": "[{\"name\":\"scenario-lora\",\"path\":\"/runpod-volume/models/lora_adapter\"}]"
    }
  }'
```

> `LORA_MODULES` 값의 따옴표가 `\"` 로 이스케이프된 것에 주의. 이것은 JSON 안에 JSON 문자열을 넣는 것이라 이중 이스케이프 필요.

#### 방법 B: Custom Template에 ENV 하드코딩

1. RunPod 콘솔 → **Serverless** → **Custom Template**
2. **Container Image**: `runpod/worker-v1-vllm:stable-cuda12.1.0`
3. **Docker Arguments** 또는 **Container Start Command**에 환경변수를 직접 설정하기 어려우므로, 대신 Custom Docker Image를 만든다:

```dockerfile
FROM runpod/worker-v1-vllm:stable-cuda12.1.0
ENV LORA_MODULES='[{"name":"scenario-lora","path":"/runpod-volume/models/lora_adapter"}]'
```

Docker Hub에 push 후 해당 이미지로 Endpoint 생성.

#### 방법 C: LoRA 없이 배포 + 런타임 로딩 (가장 안정적)

`LORA_MODULES` 없이 배포하고, 첫 요청 전에 런타임으로 LoRA를 동적 로딩.

**Endpoint 환경변수** (LORA_MODULES 제외):

| Key | Value |
|-----|-------|
| `MODEL_NAME` | `/runpod-volume/models/base` |
| `TOKENIZER_NAME` | `/runpod-volume/models/base` |
| `GPU_MEMORY_UTILIZATION` | `0.9` |
| `MAX_MODEL_LEN` | `4096` |
| `TRUST_REMOTE_CODE` | `1` |
| `DISABLE_LOG_STATS` | `1` |
| `ENABLE_LORA` | `1` |
| `MAX_LORA_RANK` | `64` |
| `VLLM_ALLOW_RUNTIME_LORA_UPDATING` | `True` |

**배포 후, 추론 전에 LoRA 로딩 요청 전송:**

```bash
ENDPOINT_ID=<Endpoint ID>
API_KEY=<API Key>

# 1. LoRA 어댑터 런타임 로딩
curl -s -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "openai_route": "/v1/load_lora_adapter",
      "openai_input": {
        "lora_name": "scenario-lora",
        "lora_path": "/runpod-volume/models/lora_adapter"
      }
    }
  }'
```

로딩 성공 확인 후 추론 요청 가능. Cold start 시마다 다시 로딩해야 함.

> **한계**: Min Workers=0이면 매번 cold start할 때마다 LoRA를 다시 로딩해야 함.
> `finetuned_client.py`에 자동 로딩 로직을 추가하면 해결 가능.

---

## Step 5: AI 프로젝트 .env 설정

`AI/.env` 파일에 추가:

```env
RUNPOD_ENDPOINT_ID=<Step 4에서 복사한 Endpoint ID>
RUNPOD_API_KEY=<Step 1에서 복사한 API Key>
LORA_ADAPTER_NAME=scenario-lora
USE_FINETUNED_SCENARIO=true
```

> `LORA_ADAPTER_NAME`은 `LORA_MODULES`에서 설정한 `name` 값과 일치해야 함.
> `finetuned_client.py`가 이 이름을 `model` 필드에 사용하여 LoRA 어댑터 추론 요청.

---

## Step 6: 테스트

### 6-1. Worker 상태 확인

Endpoint 생성 직후 Worker가 Initializing → Ready 되는지 확인:

1. RunPod 콘솔 → **Serverless** → 해당 Endpoint 클릭
2. **Workers** 탭에서 상태 확인
3. **Logs** 탭에서 에러 확인

정상 로그 예시:
```
INFO:     vLLM version: 2.x.x
INFO:     Loading model from /runpod-volume/models/base
INFO:     Model loaded successfully
INFO:     Initialized adapter: {'name': 'scenario-lora', 'path': '/runpod-volume/models/lora_adapter'}
```

에러가 있으면 [트러블슈팅](#트러블슈팅) 참조.

### 6-2. 베이스 모델 테스트 (LoRA 없이)

먼저 베이스 모델이 정상 작동하는지 확인:

```bash
ENDPOINT_ID=<Endpoint ID>
API_KEY=<API Key>

curl -s -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "openai_route": "/v1/chat/completions",
      "openai_input": {
        "model": "/runpod-volume/models/base",
        "messages": [
          {"role": "user", "content": "안녕하세요, 간단한 인사 부탁드립니다."}
        ],
        "max_tokens": 100,
        "temperature": 0.7
      }
    }
  }' | python3 -m json.tool
```

> 첫 요청은 Cold Start로 `IN_QUEUE` 상태가 반환될 수 있음. 1~3분 후 재요청.

정상 응답:
```json
{
  "status": "COMPLETED",
  "output": {
    "choices": [{
      "message": {
        "content": "안녕하세요! ..."
      }
    }]
  }
}
```

> **모델 이름 참고**: vLLM이 모델을 로드하면 소문자로 정규화됨. `/runpod-volume/models/base` 또는 `skt/a.x-3.1-light` 둘 다 사용 가능.

### 6-3. LoRA 어댑터 테스트

베이스 모델 정상 확인 후, LoRA 어댑터로 테스트:

```bash
curl -s -X POST "https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "openai_route": "/v1/chat/completions",
      "openai_input": {
        "model": "scenario-lora",
        "messages": [
          {
            "role": "user",
            "content": "밈 이름: 무야호\n톤: 유쾌\n배경: 사무실\n상품명: 핫식스\n상품 설명: 에너지 음료\n시나리오를 JSON으로 생성해주세요."
          }
        ],
        "max_tokens": 2000,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["<|im_end|>"]
      }
    }
  }' | python3 -m json.tool
```

> `"model": "scenario-lora"` — `LORA_MODULES`에서 설정한 `name` 값을 사용.
> 베이스 모델 경로(`/runpod-volume/models/lora_adapter`)가 아닌 **이름**을 사용해야 함.

### 6-4. 파이프라인에서 테스트

```bash
cd AI
uv run python -c "
from content_pipeline.scenario.finetuned_client import generate_with_finetuned
result = generate_with_finetuned(
    system_prompt='',
    user_prompt='밈 이름: 무야호\n톤: 유쾌\n배경: 사무실\n상품명: 핫식스\n상품 설명: 에너지 음료'
)
print(result)
"
```

### 6-5. 예상 응답 구조

```json
{
  "status": "COMPLETED",
  "output": {
    "choices": [{
      "message": {
        "content": "<thinking>...</thinking>\n```json\n{\"title\": \"...\", \"scene1\": {...}, ...}\n```"
      }
    }]
  }
}
```

---

## finetuned_client.py 수정 필요사항

현재 `finetuned_client.py`에서 `model` 필드에 경로(`/runpod-volume/models/lora_adapter`)를 사용하고 있다. LoRA 어댑터는 **이름**으로 참조해야 하므로 수정 필요:

```python
# 변경 전 (현재 코드)
lora_path = os.getenv("LORA_ADAPTER_PATH", "/runpod-volume/models/lora_adapter")
# payload에서: "model": lora_path

# 변경 후
lora_name = os.getenv("LORA_ADAPTER_NAME", "scenario-lora")
# payload에서: "model": lora_name
```

`.env` 파일도 변경:
```env
# 변경 전
LORA_ADAPTER_PATH=/runpod-volume/models/lora_adapter

# 변경 후
LORA_ADAPTER_NAME=scenario-lora
```

---

## 주의사항

### GPU_MEMORY_UTILIZATION 절대 1.0으로 설정 금지

`GPU_MEMORY_UTILIZATION=1.0`으로 설정하면 Worker가 `init_device` 단계에서 크래시.
항상 `0.9` 이하로 설정.

### Cold Start

- **Min Workers=0**이면 첫 요청 시 모델 로딩에 **1~3분** 소요
- 테스트 전에 warm-up 요청 하나 보내놓고 기다리기
- 응답이 `IN_QUEUE` 또는 `IN_PROGRESS`로 오면 정상 (로딩 중)
- `finetuned_client.py`가 자동으로 폴링함

### 비용

- A40 Serverless: ~$0.00039/sec (~$1.4/hr 사용 시간만)
- Min Workers=0: 요청 없으면 과금 없음
- Network Volume: ~$0.07/GB/월 (30GB = ~$2.1/월)

### DoRA 호환성

- vLLM Worker 이미지 `stable-cuda12.1.0`은 vLLM 2.x 기반으로 DoRA LoRA 지원
- `adapter_config.json`에 `"use_dora": true` 설정되어 있으면 vLLM이 자동 인식
- 별도 설정 불필요

### 타임아웃

- `/runsync`: 최대 ~90초 대기 후 응답
- 90초 초과 시 `IN_QUEUE`/`IN_PROGRESS` 상태 반환 → `finetuned_client.py`가 `/status/{job_id}`로 폴링
- Execution Timeout 300초 내에 완료되어야 함

### 리전 일치

- **Network Volume과 Serverless Endpoint는 같은 리전이어야 함**
- Volume 생성 시 선택한 리전 기억해두기
- 다른 리전이면 Endpoint에서 Volume이 보이지 않음

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| Worker `init_device` 크래시 | `GPU_MEMORY_UTILIZATION=1.0` | `0.9`로 변경 |
| `LoRAModulePath() argument after ** must be a mapping, not str` | RunPod UI가 JSON 따옴표 제거 | [방법 A/B/C](#4-3-lora_modules-ui-문제-해결) 사용 |
| `MODEL_NOT_FOUND` | 모델 경로 오타 | Volume 마운트 확인, 경로 정확히 입력 |
| `CUDA out of memory` | GPU VRAM 부족 | 더 큰 GPU 선택 또는 `GPU_MEMORY_UTILIZATION` 낮추기 |
| `LoRA adapter not found` | LoRA 경로/이름 오류 | `adapter_config.json`이 해당 경로에 있는지 확인, 이름 확인 |
| `IN_QUEUE` 오래 지속 | Cold start | 1~3분 대기, 이후 요청은 빠름 |
| `FAILED` | Worker 에러 | RunPod 콘솔 → Endpoint → Logs 확인 |
| Volume 연결 안 됨 | 리전 불일치 | Volume과 Endpoint 리전이 같은지 확인 |
| Worker Initializing 무한루프 | 모델 로딩 실패 | Logs 확인 — 보통 메모리 부족 또는 모델 경로 오류 |
| `distributed_executor_backend` 에러 | Ray 불필요 설정 | 해당 환경변수 제거 (기본값 사용) |
| 추론 시 `model not found` | LoRA 이름 불일치 | `LORA_MODULES`의 `name`과 요청의 `model` 필드 일치시키기 |

---

## 환경변수 전체 레퍼런스 (vLLM Worker)

| Key | 기본값 | 설명 |
|-----|--------|------|
| `MODEL_NAME` | - | 베이스 모델 경로 또는 HuggingFace repo ID |
| `TOKENIZER_NAME` | MODEL_NAME과 동일 | 토크나이저 경로 |
| `GPU_MEMORY_UTILIZATION` | `0.9` | GPU 메모리 사용 비율 (0~0.95) |
| `MAX_MODEL_LEN` | 모델 기본값 | 최대 시퀀스 길이 |
| `TRUST_REMOTE_CODE` | `0` | 커스텀 모델 코드 허용 |
| `DISABLE_LOG_STATS` | `0` | 통계 로그 비활성화 |
| `ENABLE_LORA` | `0` | LoRA 기능 활성화 |
| `MAX_LORA_RANK` | `16` | 최대 LoRA rank |
| `MAX_LORAS` | `1` | 동시 LoRA 배치 수 |
| `LORA_MODULES` | `[]` | JSON 배열: `[{"name":"x","path":"/path"}]` |
| `LORA_EXTRA_VOCAB_SIZE` | `256` | LoRA 추가 어휘 크기 |
| `LORA_DTYPE` | `auto` | LoRA 데이터 타입 |
| `VLLM_ALLOW_RUNTIME_LORA_UPDATING` | `False` | 런타임 LoRA 동적 로딩 허용 |
