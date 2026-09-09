import json
import logging
import os
import posixpath
import shlex
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from content_pipeline.video.config import VideoConfig

logger = logging.getLogger(__name__)


# --- 1. 유틸리티 함수 ---
def _write_metadata(metadata_path: Path, metadata: dict) -> None:
    """메타데이터를 JSON 파일로 저장"""
    # 디렉토리 생성
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    # JSON 파일로 저장
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")


def _download_remote_input(
    url: str,
    *,
    remote_dir: str,
    prefix: str,
    default_suffix: str,
    host: str,
    user: str,
    key_path: str,
    port: str,
) -> str:
    """S3/URL을 ComfyUI 원격 입력 디렉터리로 다운로드하고 파일명 반환"""
    # s3:// URI만 허용 (presigned HTTPS URL로 변환)
    if not url.startswith("s3://"):
        raise ValueError("remote input only supports s3:// URLs")
    from content_pipeline.db import _maybe_presign_s3_url
    url = _maybe_presign_s3_url(url)

    if not (host and user and key_path and remote_dir):
        raise RuntimeError("COMFY_SSH_HOST/USER/KEY/REMOTE_INPUT_DIR are required for remote download")

    parsed = urlparse(url)
    # presigned URL이 이중 인코딩되면 path에 %3F 등이 포함됨 → unquote 후 ? 앞만 사용
    clean_path = unquote(parsed.path).split("?")[0]
    suffix = Path(clean_path).suffix or default_suffix
    filename = Path(clean_path).name or f"{prefix}_{int(time.time())}{suffix}"
    remote_path = f"{remote_dir.rstrip('/')}/{filename}"

    # 원격 호스트에서 직접 다운로드하여 로컬 임시 파일 생성을 방지
    cmd = [
        "ssh",
        "-i",
        key_path,
        "-p",
        port,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
        f"{user}@{host}",
        f"mkdir -p {shlex.quote(remote_dir)} && curl -L --max-time 60 -o {shlex.quote(remote_path)} {shlex.quote(url)}",
    ]
    subprocess.run(cmd, check=True)
    return filename


def _infer_output_dir(input_dir: str, *, kind: str = "output") -> str:
    # input 디렉터리를 기준으로 output/temp 경로를 추론
    if not input_dir:
        return ""
    normalized = input_dir.replace("\\", "/").rstrip("/")
    if normalized.endswith("/input"):
        base = normalized[:-6]
        return f"{base}/{kind}"
    return ""


def _remote_delete_files(
    *,
    host: str,
    user: str,
    key_path: str,
    port: str,
    remote_dir: str,
    rel_paths: list[str],
) -> None:
    # 원격 디렉터리에서 상대 경로 파일들을 안전하게 삭제
    if not (host and user and key_path and remote_dir and rel_paths):
        return
    targets = []
    for rel in rel_paths:
        cleaned = rel.replace("\\", "/").lstrip("/")
        targets.append(posixpath.join(remote_dir.rstrip("/"), cleaned))
    try:
        cmd = [
            "ssh",
            "-i",
            key_path,
            "-p",
            port,
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=10",
            f"{user}@{host}",
            "rm",
            "-f",
            "--",
            *targets,
        ]
        subprocess.run(cmd, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("Remote cleanup failed for %s: %s", remote_dir, exc)
        return


def _write_mock_video(output_path: Path, duration_seconds: float | None) -> None:
    """테스트용 가짜(Mock) 비디오 파일을 생성 (OpenCV 사용)"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        with open(output_path, "wb") as handle:
            handle.write(b"MOCKVIDEO")
        return

    fps = 24
    duration = max(float(duration_seconds or 2.0), 1.0)
    frame_count = int(fps * duration)
    width, height = 640, 360
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        with open(output_path, "wb") as handle:
            handle.write(b"MOCKVIDEO")
        return

    for idx in range(frame_count):
        intensity = int(255 * (idx / max(frame_count - 1, 1)))
        frame = np.full((height, width, 3), (intensity, 30, 120), dtype=np.uint8)
        cv2.putText(
            frame,
            f"mock scene {idx+1}",
            (20, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)
    writer.release()


# --- 2. ComfyUI 영상 생성 클라이언트 클래스 ---
class VideoClient:
    """내부 관리 및 통신 메서드"""
    def __init__(self, config: VideoConfig):
        self.config = config

    def _load_workflow(self) -> dict:
        """ComfyUI JSON 워크플로우 파일을 로드"""
        path = self.config.comfyui_workflow_path

        if not path:
            raise FileNotFoundError("COMFY_WORKFLOW_PATH is not set")

        if not path.is_absolute():
            candidates: list[Path] = []
            base_env = os.getenv("COMFY_WORKFLOW_BASE", "").strip()
            if base_env:
                candidates.append(Path(base_env))
            # AI package root (AI/)
            candidates.append(Path(__file__).resolve().parents[2])
            # CWD fallback
            candidates.append(Path.cwd())

            resolved = None
            for base in candidates:
                candidate = (base / path).resolve()
                if candidate.exists():
                    resolved = candidate
                    break
            path = resolved or (Path.cwd() / path).resolve()

        if not path.exists():
            raise FileNotFoundError(
                f"COMFY_WORKFLOW_PATH is not set or file does not exist: {path}"
            )
        
        # 파일 읽기
        raw = path.read_text(encoding="utf-8")
        # JSON 파싱
        payload = json.loads(raw)
        # prompt를 찾아 반환 
        # - payload가 dict 형태라면 내부에 prompt가 있는지 확인
        if isinstance(payload, dict):
            extra = payload.get("extra")
            if isinstance(extra, dict) and isinstance(extra.get("prompt"), dict):
                return extra["prompt"]
            if isinstance(payload.get("prompt"), dict):
                return payload["prompt"]
        return payload

    def _render_workflow(
        self,
        workflow: dict,
        *,
        prompt: str,
        reference_image_name: str | None,
        reference_audio_name: str | None,
        audio_url: str | None,
        duration_seconds: float | None,
    ) -> dict:
        """워크플로우 내의 플레이스홀더({{prompt}} 등)를 실제 값으로 치환"""
        # 워크플로우 내의 FPS 설정을 찾아 초 단위 길이를 프레임 수로 계산
        def is_negative_prompt(text: str) -> bool:
            lowered = text.lower()
            return any(
                token in lowered
                for token in (
                    "blurry",
                    "out of focus",
                    "low quality",
                    "deformed",
                    "extra limbs",
                    "artifacts",
                    "noise",
                )
            )

        negative_terms = [
            "extra characters",
            "multiple people",
            "crowd",
            "background people",
            "extra faces",
            "photorealistic",
            "real human",
            "live action",
            "text",
            "subtitles",
            "captions",
            "watermark",
            "letters",
            "words",
            "title card",
            "text overlay",
        ]

        def append_negative_terms(text: str) -> str:
            # 네거티브 프롬프트에 필수 금지 키워드를 누락 없이 보강
            lowered = text.lower()
            extras = [term for term in negative_terms if term.lower() not in lowered]
            if not extras:
                return text
            sep = ", " if text.strip() else ""
            return f"{text}{sep}{', '.join(extras)}"

        def find_frame_rate(nodes: dict) -> float:
            """
            workflow 노드에서 frame_rate 값을 찾아 반환

            - frame_rate가 직접 숫자로 입력된 경우
            - frame_rate가 다른 노드의 출력값을 참조하는 경우
            - 노드가 FloatConstant / PrimitiveFloat 타입이며 제목이 "Frame Rate"인 경우
            - 위 경우 모두 해당되지 않으면 기본값 24.0 반환
            """
            # 1) 모든 노드를 순회하며 frame_rate 입력값을 찾음
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                inputs = node.get("inputs", {})
                if "frame_rate" not in inputs:
                    continue
                frame_rate = inputs.get("frame_rate")

                # 1-1) frame_rate가 숫자라면 바로 반환
                if isinstance(frame_rate, (int, float)):
                    return float(frame_rate)
                
                # 1-2) frame_rate가 [src_id, ...] 형태로 참조되는 경우 처리
                if isinstance(frame_rate, list) and frame_rate:
                    src_id = str(frame_rate[0])
                    src = nodes.get(src_id)

                    # 참조된 노드가 존재하고, 그 노드의 value가 숫자라면 반환
                    if isinstance(src, dict):
                        value = src.get("inputs", {}).get("value")
                        if isinstance(value, (int, float)):
                            return float(value)
                        
            # 2) frame_rate가 직접 입력으로 없을 경우
            # FloatConstant / PrimitiveFloat 노드를 찾아서 "Frame Rate" 메타정보가 있는지 확인
            for node in nodes.values():
                if not isinstance(node, dict):
                    continue
                if node.get("class_type") in ("FloatConstant", "PrimitiveFloat"):
                    meta = node.get("_meta", {})
                    
                    # meta.title에 "Frame Rate"가 포함되어 있으면 해당 노드의 value를 사용
                    if "Frame Rate" in (meta.get("title") or ""):
                        value = node.get("inputs", {}).get("value")
                        if isinstance(value, (int, float)):
                            return float(value)
                        
            # 3) 위에서 찾지 못하면 기본값 24fps 반환
            return 24.0

        fps = find_frame_rate(workflow)

        duration_frames = None
        if duration_seconds:
            duration_frames = max(1, round(float(duration_seconds) * float(fps)))

        def replace_value(value):
            """재귀적으로 딕셔너리/리스트를 탐색하며 문자열 치환"""
            if isinstance(value, str):
                if value.strip() == "{{duration_seconds}}":
                    return duration_frames if duration_frames is not None else value
                return (
                    value.replace("{{prompt}}", prompt)
                    .replace("{{reference_image}}", reference_image_name or "")
                    .replace("{{audio}}", reference_audio_name or "")
                    .replace("{{audio_url}}", audio_url or "")
                    .replace("{{duration_seconds}}", str(duration_seconds or ""))
                )
            if isinstance(value, list):
                return [replace_value(v) for v in value]
            if isinstance(value, dict):
                return {k: replace_value(v) for k, v in value.items()}
            return value

        rendered = {}

        # 워크플로 입력값을 실제 값으로 덮어쓰는 로직
        # - ComfyUI 워크플로우의 노드들에서 prompt, 이미지/오디오 파일명, duration_frames를 주입하는 로직
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            rendered[node_id] = {
                "class_type": node.get("class_type"),
                "_meta": node.get("_meta"),
                "inputs": replace_value(node.get("inputs", {})),
            }

            class_type = rendered[node_id]["class_type"]
            inputs = rendered[node_id]["inputs"]

            # 1) 텍스트 프롬프트 주입 (CLIPTextEncode 노드)
            if class_type == "CLIPTextEncode" and isinstance(inputs.get("text"), str):
                if is_negative_prompt(inputs["text"]):
                    inputs["text"] = append_negative_terms(inputs["text"])
                else:
                    inputs["text"] = prompt
            # 2) 이미지 파일명 주입 (LoadImage 노드)
            if class_type == "LoadImage" and reference_image_name and "image" in inputs:
                inputs["image"] = reference_image_name
            # 3) 오디오 파일명 주입 (LoadAudio 또는 VHS_LoadAudioUpload 노드)
            if class_type in ("LoadAudio", "VHS_LoadAudioUpload") and reference_audio_name and "audio" in inputs:
                inputs["audio"] = reference_audio_name
            # 4) 오디오 URL 주입이 가능한 경우 (audio_url 입력이 있는 노드)
            if "audio_url" in inputs:
                if audio_url:
                    inputs["audio_url"] = audio_url
                elif reference_audio_name:
                    inputs["audio_url"] = reference_audio_name

        # 5) duration_frames가 주어졌을 때 프레임 관련 입력값을 모두 갱신
        if duration_frames is not None:
            frame_inputs = {"length", "frames_number", "num_frames", "frames"}
            for node_id, node in rendered.items():
                inputs = node.get("inputs", {})
                for input_name, input_value in list(inputs.items()):
                    if input_name not in frame_inputs:
                        continue
                    # 5-1) 숫자 형태로 직접 입력된 경우
                    if isinstance(input_value, (int, float)):
                        inputs[input_name] = int(duration_frames)
                        # 5-2) 다른 노드의 출력값을 참조하는 경우
                    elif isinstance(input_value, list) and input_value:
                        src_id = str(input_value[0])
                        src = rendered.get(src_id)
                        if src and "inputs" in src and "value" in src["inputs"]:
                            src["inputs"]["value"] = int(duration_frames)
        return rendered

    def _upload_reference_image(self, path: Path) -> str:
        """ComfyUI 서버에 참조 이미지를 업로드"""
        # 이미지 파일을 ComfyUI에 업로드하고 서버가 반환한 이름을 사용
        if not self.config.comfyui_base_url:
            raise ValueError("COMFY_COMFYUI_BASE_URL is required for ComfyUI mode")
        url = f"{self.config.comfyui_base_url.rstrip('/')}/upload/image"
        # 멀티파트 업로드로 이미지 전송
        with path.open("rb") as handle:
            files = {"image": (path.name, handle)}
            resp = requests.post(url, files=files, timeout=self.config.request_timeout)
        resp.raise_for_status()
        payload = resp.json()
        # 서버가 파일명을 반환하지 않으면 로컬 이름 사용
        return payload.get("name", path.name)

    def _submit_prompt(self, workflow: dict) -> str:
        """ComfyUI 서버에 프롬프트를 업로드"""
        # 렌더된 워크플로우를 /prompt에 제출하고 prompt_id를 수령
        url = f"{self.config.comfyui_base_url.rstrip('/')}/prompt"
        resp = requests.post(url, json={"prompt": workflow}, timeout=self.config.request_timeout)
        if not resp.ok:
            raise RuntimeError(f"ComfyUI /prompt failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        prompt_id = payload.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"Missing prompt_id in ComfyUI response: {payload}")
        # 추후 /history 조회에 필요한 prompt_id 반환
        return prompt_id

    def _upload_reference_audio(self, path: Path) -> str:
        """ComfyUI 서버에 오디오 업로드"""
        # /upload/audio가 막혀 있으면 SSH/SCP로 원격 input에 업로드
        if not self.config.comfyui_base_url:
            raise ValueError("COMFY_COMFYUI_BASE_URL is required for ComfyUI mode")
        url = f"{self.config.comfyui_base_url.rstrip('/')}/upload/audio"
        # 멀티파트 업로드로 오디오 전송
        with path.open("rb") as handle:
            files = {"audio": (path.name, handle)}
            resp = requests.post(url, files=files, timeout=self.config.request_timeout)
        if resp.status_code == 405:
            # 서버가 오디오 업로드를 막는 경우, 원격 input 디렉터리에 직접 업로드
            host = self.config.comfy_ssh_host.strip()
            user = self.config.comfy_ssh_user.strip()
            key_path = os.path.expanduser(self.config.comfy_ssh_key or "")
            port = (self.config.comfy_ssh_port or "22").strip()
            remote_input = self.config.comfy_remote_input_dir.strip()
            if not (host and user and key_path and remote_input):
                raise RuntimeError("/upload/audio not supported and COMFY_SSH_HOST/USER/KEY/REMOTE_INPUT_DIR are not set")
            remote_target = f"{user}@{host}:{remote_input.rstrip('/')}/{path.name}"
            # scp로 원격 업로드 수행
            cmd = ["scp", "-i", key_path, "-P", port, "-o", "StrictHostKeyChecking=no", str(path), remote_target]
            subprocess.run(cmd, check=True)
            # 원격 업로드된 파일명 반환
            return path.name
        resp.raise_for_status()
        payload = resp.json()
        # 서버가 파일명을 반환하지 않으면 로컬 이름 사용
        return payload.get("name", path.name)


    def _poll_history(self, prompt_id: str) -> dict:
        """작업 완료 여부를 확인하기 위해 History API를 폴링(대기)"""
        url = f"{self.config.comfyui_base_url.rstrip('/')}/history/{prompt_id}"
        deadline = time.time() + self.config.comfyui_max_wait
        while time.time() < deadline:
            resp = requests.get(url, timeout=self.config.request_timeout)
            resp.raise_for_status()
            payload = resp.json()
            if payload and prompt_id in payload:
                entry = payload[prompt_id]
                outputs = entry.get("outputs", {})
                # progress 값만 있는 경우 (예: {'139': {'value': [79.0]}}) 는 미완료
                # 실제 미디어 출력 (videos/images key)이 있을 때만 완료로 판단
                if outputs and self._select_video_output(outputs):
                    return entry
            time.sleep(self.config.comfyui_poll_interval)
        raise TimeoutError("ComfyUI history polling timed out")

    def _download_output(self, output_info: dict, output_path: Path) -> None:
        url = f"{self.config.comfyui_base_url.rstrip('/')}/view"
        params = {
            "filename": output_info.get("filename"),
            "subfolder": output_info.get("subfolder", ""),
            "type": output_info.get("type", "output"),
        }
        resp = requests.get(url, params=params, timeout=self.config.request_timeout)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)

    def _select_video_output(self, outputs: dict) -> dict | None:
        for _, node in outputs.items():
            videos = node.get("videos") if isinstance(node, dict) else None
            if videos:
                return videos[0]
            images = node.get("images") if isinstance(node, dict) else None
            if images:
                return images[0]
        return None

    # --- RunPod Serverless 전용 메서드 ---

    def _encode_file_base64_serverless(self, path: Path) -> str:
        """파일을 base64 문자열로 인코딩"""
        import base64
        return base64.b64encode(path.read_bytes()).decode("utf-8")

    def _upload_reference_image_serverless(self, path: Path) -> str:
        """참조 이미지를 base64로 인코딩해서 반환 (서버리스용)"""
        return self._encode_file_base64_serverless(path)

    def _upload_reference_audio_serverless(self, path: Path) -> str:
        """참조 오디오를 base64로 인코딩해서 반환 (서버리스용)"""
        return self._encode_file_base64_serverless(path)

    def _submit_prompt_serverless(
        self,
        workflow: dict,
        *,
        image_b64: str | None = None,
        image_name: str | None = None,
        audio_b64: str | None = None,
        audio_name: str | None = None,
    ) -> str:
        """RunPod Serverless /run 엔드포인트에 작업 제출, job_id 반환"""
        api_key = self.config.runpod_comfy_api_key
        endpoint_id = self.config.runpod_comfy_endpoint_id
        if not api_key or not endpoint_id:
            raise ValueError("COMFY_RUNPOD_API_KEY and COMFY_RUNPOD_ENDPOINT_ID are required for serverless mode")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        # input 구성: workflow + 파일 데이터(base64)
        # RunPod ComfyUI 워커 핸들러는 "workflow" 키를 기대함 (ComfyUI 내부 /prompt 키와 다름)
        # 이미지/오디오 모두 "images" 배열에 {"name": ..., "image": ...} 형식으로 포함
        # → 워커 핸들러가 images 배열 전체를 /comfyui/input/ 에 저장함
        payload_input: dict = {"workflow": workflow}
        files: list[dict] = []
        if image_b64 and image_name:
            files.append({"name": image_name, "image": image_b64})
        if audio_b64 and audio_name:
            files.append({"name": audio_name, "image": audio_b64})
        if files:
            payload_input["images"] = files

        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        resp = requests.post(url, headers=headers, json={"input": payload_input}, timeout=self.config.request_timeout)
        if not resp.ok:
            raise RuntimeError(f"RunPod /run failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        job_id = payload.get("id")
        if not job_id:
            raise RuntimeError(f"Missing job id in RunPod response: {payload}")
        return job_id

    def _poll_status_serverless(self, job_id: str) -> dict:
        """RunPod Serverless 작업 완료 여부를 폴링, 완료된 output dict 반환"""
        api_key = self.config.runpod_comfy_api_key
        endpoint_id = self.config.runpod_comfy_endpoint_id
        headers = {"Authorization": f"Bearer {api_key}"}
        url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        deadline = time.time() + self.config.comfyui_max_wait
        while time.time() < deadline:
            resp = requests.get(url, headers=headers, timeout=self.config.request_timeout)
            resp.raise_for_status()
            payload = resp.json()
            status = payload.get("status", "")
            if status == "COMPLETED":
                return payload.get("output", {})
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"RunPod job {job_id} ended with status: {status}, error: {payload.get('error')}")
            time.sleep(self.config.comfyui_poll_interval)
        raise TimeoutError(f"RunPod serverless polling timed out for job {job_id}")

    def _download_output_serverless(self, output: dict, output_path: Path) -> None:
        """RunPod output에서 비디오를 추출해 로컬에 저장 (base64 또는 URL)"""
        import base64

        # 실제 응답: {"images": [{"data": "<base64>", "filename": "...", "type": "base64"}]}
        # fallback: {"video": ...} 또는 {"videos": [...]}
        item = None
        images = output.get("images") or []
        if images:
            item = images[0]
        if not item:
            item = output.get("video") or (output.get("videos") or [None])[0]
        if not item:
            raise RuntimeError(f"No video found in RunPod output: {output}")

        # {"data": base64, "type": "base64"} 형태
        if isinstance(item, dict):
            if item.get("type") == "base64":
                raw = item.get("data") or item.get("image") or ""
                if "," in raw:
                    raw = raw.split(",", 1)[1]
                output_path.write_bytes(base64.b64decode(raw))
                return
            url = item.get("url")
            if url:
                resp = requests.get(url, timeout=self.config.request_timeout)
                resp.raise_for_status()
                output_path.write_bytes(resp.content)
                return

        # 평문 base64 문자열
        if isinstance(item, str):
            if "," in item:
                item = item.split(",", 1)[1]
            output_path.write_bytes(base64.b64decode(item))
            return

        raise RuntimeError(f"Unrecognized video output format from RunPod: {type(item)}")

    def generate_video(
        self,
        *,
        prompt: str,
        audio_path: str | None = None,
        audio_url: str | None = None,
        reference_image_path: str | None = None,
        reference_image_url: str | None = None,
        output_path: str | None = None,
        duration_seconds: float | None = None,
        model_name: str = "ltx2",                         # ltx2 | wan2.6
        mock_sample_path: str | None = None,
    ) -> dict:
        """
        전체 프로세스 조율
        1. 유효성 검사 및 경로 설정
        2. 이미지 준비 (URL일 경우 다운로드)
        3. 실행 모드 분기 (Mock 모드 vs ComfyUI 모드)
        """
        if not prompt.strip():
            raise ValueError("prompt is required")

        temp_paths: list[Path] = []

        if not output_path:
            filename = f"scene_{int(time.time())}.mp4"
            output_path = str(self.config.output_dir / filename)
        output_path = str(Path(output_path))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 가짜 영상 생성 로직 실행
        if self.config.mode == "mock":
            if mock_sample_path:
                sample_path = Path(mock_sample_path)
                if not sample_path.exists():
                    raise FileNotFoundError(f"mock_sample_path not found: {mock_sample_path}")
                Path(output_path).write_bytes(sample_path.read_bytes())
            else:
                _write_mock_video(Path(output_path), duration_seconds)
        # 진짜 영상 생성 로직 실행
        elif self.config.mode == "comfyui":
            remote_input_dir = self.config.comfy_remote_input_dir.strip()
            host = self.config.comfy_ssh_host.strip()
            user = self.config.comfy_ssh_user.strip()
            key_path = os.path.expanduser(self.config.comfy_ssh_key or "")
            port = (self.config.comfy_ssh_port or "22").strip()
            remote_ready = bool(host and user and key_path)
            use_remote_input = bool(remote_input_dir and remote_ready)
            remote_cleanup_names: list[str] = []

            # (1) 워크플로우 로드
            if not self.config.comfyui_base_url:
                raise ValueError(
                    "COMFY_COMFYUI_BASE_URL is required for ComfyUI mode"
                )
            workflow = self._load_workflow()

            # (2) 이미지 업로드
            reference_image_name = None
            reference_audio_name = None
            if reference_image_path:
                reference_image_name = self._upload_reference_image(Path(reference_image_path))
            elif reference_image_url:
                if not use_remote_input:
                    raise ValueError("reference_image_url requires remote input (s3:// only)")
                reference_image_name = _download_remote_input(
                    reference_image_url,
                    remote_dir=remote_input_dir,
                    prefix="image",
                    default_suffix=".png",
                    host=host,
                    user=user,
                    key_path=key_path,
                    port=port,
                )
            if reference_image_name:
                remote_cleanup_names.append(reference_image_name)

            # (3) 음성 업로드
            if audio_path:
                audio_path_obj = Path(audio_path)
                reference_audio_name = self._upload_reference_audio(audio_path_obj)
            elif audio_url:
                if not use_remote_input:
                    raise ValueError("audio_url requires remote input (s3:// only)")
                reference_audio_name = _download_remote_input(
                    audio_url,
                    remote_dir=remote_input_dir,
                    prefix="audio",
                    default_suffix=".wav",
                    host=host,
                    user=user,
                    key_path=key_path,
                    port=port,
                )
            if reference_audio_name:
                remote_cleanup_names.append(reference_audio_name)

            # (4) 프롬프트 치환 및 API 제출
            workflow = self._render_workflow(
                workflow,
                prompt=prompt,
                reference_image_name=reference_image_name,
                reference_audio_name=reference_audio_name,
                audio_url=audio_url,
                duration_seconds=duration_seconds,
            )

            prompt_id = self._submit_prompt(workflow)
            history = self._poll_history(prompt_id)            
            output_info = self._select_video_output(history.get("outputs", {}))

            # (5) 완료 대기(Polling) 및 결과물 다운로드
            if not output_info:
                raise RuntimeError(f"No video outputs found in history: {history.get('outputs')}")
            self._download_output(output_info, Path(output_path))

            # (6) ComfyUI 입력/출력 정리 (항상 실행)
            clean_input = True
            clean_output = True
            host = self.config.comfy_ssh_host.strip()
            user = self.config.comfy_ssh_user.strip()
            key_path = os.path.expanduser(self.config.comfy_ssh_key or "")
            port = (self.config.comfy_ssh_port or "22").strip()
            remote_ready = bool(host and user and key_path)

            if clean_input and remote_cleanup_names:
                # 업로드/다운로드된 입력 파일 정리
                names = [n for n in remote_cleanup_names if n]
                if names:
                    if remote_ready and remote_input_dir:
                        _remote_delete_files(
                            host=host,
                            user=user,
                            key_path=key_path,
                            port=port,
                            remote_dir=remote_input_dir,
                            rel_paths=names,
                        )

            if clean_output and output_info:
                # 생성된 출력 파일 정리 (output/temp 유형 모두 처리)
                filename = output_info.get("filename")
                subfolder = output_info.get("subfolder") or ""
                output_type = (output_info.get("type") or "output").lower()
                if output_type not in ("output", "temp"):
                    output_type = "output"
                if filename:
                    rel_output = posixpath.join(subfolder, filename) if subfolder else filename
                    if remote_ready:
                        remote_output_dir = self.config.comfy_remote_output_dir.strip()
                        if not remote_output_dir:
                            # output/temp 폴더 구조를 input 경로에서 추론
                            remote_output_dir = _infer_output_dir(remote_input_dir, kind=output_type)
                        if remote_output_dir:
                            base_name = os.path.basename(remote_output_dir.rstrip("/")).lower()
                            rel_norm = rel_output.replace("\\", "/").lstrip("/")
                            if base_name and rel_norm.lower().startswith(f"{base_name}/"):
                                # remote_output_dir 내부에서 상대 경로로 정규화
                                rel_norm = rel_norm[len(base_name) + 1 :]
                            _remote_delete_files(
                                host=host,
                                user=user,
                                key_path=key_path,
                                port=port,
                                remote_dir=remote_output_dir,
                                rel_paths=[rel_norm],
                            )

        # RunPod Serverless 영상 생성 로직
        elif self.config.mode == "serverless":
            # (1) 워크플로우 로드
            workflow = self._load_workflow()

            # (2) 이미지 base64 인코딩
            reference_image_name = None
            image_b64 = None
            if reference_image_path:
                img_path = Path(reference_image_path)
                reference_image_name = img_path.name
                image_b64 = self._upload_reference_image_serverless(img_path)
            elif reference_image_url:
                # S3/presigned URL → 로컬 임시 파일로 다운로드 후 base64 인코딩
                from content_pipeline.db import _maybe_presign_s3_url
                dl_url = _maybe_presign_s3_url(reference_image_url)
                parsed_name = unquote(Path(urlparse(dl_url).path).name) or f"ref_image_{int(time.time())}.png"
                tmp_img = Path(tempfile.mkdtemp()) / parsed_name
                temp_paths.append(tmp_img)
                dl_resp = requests.get(dl_url, timeout=self.config.request_timeout)
                dl_resp.raise_for_status()
                tmp_img.write_bytes(dl_resp.content)
                reference_image_name = tmp_img.name
                image_b64 = self._upload_reference_image_serverless(tmp_img)

            # (3) 오디오 base64 인코딩
            reference_audio_name = None
            audio_b64 = None
            if audio_path:
                aud_path = Path(audio_path)
                reference_audio_name = aud_path.name
                audio_b64 = self._upload_reference_audio_serverless(aud_path)
            elif audio_url:
                # S3/presigned URL → 로컬 임시 파일로 다운로드 후 base64 인코딩
                from content_pipeline.db import _maybe_presign_s3_url
                dl_url = _maybe_presign_s3_url(audio_url)
                parsed_name = unquote(Path(urlparse(dl_url).path).name) or f"ref_audio_{int(time.time())}.wav"
                tmp_aud = Path(tempfile.mkdtemp()) / parsed_name
                temp_paths.append(tmp_aud)
                dl_resp = requests.get(dl_url, timeout=self.config.request_timeout)
                dl_resp.raise_for_status()
                tmp_aud.write_bytes(dl_resp.content)
                reference_audio_name = tmp_aud.name
                audio_b64 = self._upload_reference_audio_serverless(tmp_aud)

            # (4) 프롬프트 치환
            workflow = self._render_workflow(
                workflow,
                prompt=prompt,
                reference_image_name=reference_image_name,
                reference_audio_name=reference_audio_name,
                audio_url=None,
                duration_seconds=duration_seconds,
            )

            # (5) 작업 제출 및 완료 대기
            job_id = self._submit_prompt_serverless(
                workflow,
                image_b64=image_b64,
                image_name=reference_image_name,
                audio_b64=audio_b64,
                audio_name=reference_audio_name,
            )
            output = self._poll_status_serverless(job_id)

            # (6) 결과물 다운로드
            self._download_output_serverless(output, Path(output_path))

        else:
            raise NotImplementedError("ComfyUI integration is not implemented yet.")

        # 4. 메타데이터(.json) 파일 작성
        size_bytes = Path(output_path).stat().st_size
        created_at = datetime.now(timezone.utc).isoformat()
        metadata_path = str(Path(output_path).with_suffix(".json"))
        metadata = {
            "model": model_name,
            "prompt": prompt,
            "reference_image_path": reference_image_path,
            "reference_image_url": reference_image_url,
            "audio_path": audio_path,
            "audio_url": audio_url,
            "duration_seconds": duration_seconds,
            "output_path": output_path,
            "size_bytes": size_bytes,
            "created_at": created_at,
        }
        _write_metadata(Path(metadata_path), metadata)

        for temp_path in temp_paths:
            if temp_path.exists():
                temp_path.unlink()

        # 5. 임시 파일 삭제 및 결과 정보 반환
        return {
            "output_path": output_path,
            "metadata_path": metadata_path,
            "size_bytes": size_bytes,
            "created_at": created_at,
            "model": model_name,
            "duration_seconds": duration_seconds,
        }
