import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from content_pipeline.video.client import VideoClient
from content_pipeline.video.config import VideoConfig
from content_pipeline.video.storage import LocalStorageBackend, S3StorageBackend, VideoStorageBackend


@dataclass(frozen=True)
class VideoNodeOutput:
    video_url: str
    storage_path: str
    duration_seconds: float | None
    size_bytes: int
    created_at: str
    model: str


class VideoService:
    """
    영상 생성 및 관리 서비스
    1. 씬별 영상 생성
    2. 통합 관리
    """
    CROSSFADE_SECONDS = 0.3

    def __init__(self, config: VideoConfig):
        self.config = config
        self.client = VideoClient(config)
        self.storage = self._build_storage_backend(config)

    def generate_video(
        self,
        *,
        prompt: str,
        audio_path: str | None = None,
        audio_url: str | None = None,
        reference_image_path: str | None = None,
        reference_image_url: str | None = None,
        duration_seconds: float | None = None,
        output_path: str | None = None,
        mock_sample_path: str | None = None,
    ) -> VideoNodeOutput:
        """
        1. 씬별 영상 생성
        - 씬 이미지+씬 음성+프롬프트를 기반으로 영상을 생성하고 저장
        - 반환값: 생성된 영상과 메타데이터 경로
        """
        # 영상 생성 API 호출
        result = self.client.generate_video(
            prompt=prompt,
            audio_path=audio_path,
            audio_url=audio_url,
            reference_image_path=reference_image_path,
            reference_image_url=reference_image_url,
            output_path=output_path,
            duration_seconds=duration_seconds,
            mock_sample_path=mock_sample_path,
        )
        return self._upload_result(result)

    def _upload_result(self, result: dict) -> VideoNodeOutput:
        """
        2. 통합 관리
        영상 생성 결과를 스토리지에 업로드하고, 업로드된 영상/메타데이터 정보를 반환
        - 로컬에 생성된 영상 및 메타데이터 파일 로드
        - 스토리지 업로드용 key 생성
        - 영상 파일 업로드
        - 메타데이터에 스토리지 정보 및 접근 URL 반영
        - 업데이트된 메타데이터 파일 업로드
        - 최종 결과 반환        
        """
        # 메타데이터 및 파일 경로
        metadata_path = Path(result["metadata_path"])
        video_path = Path(result["output_path"])
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        # output_dir 기준 상대 경로를 스토리지 key로 사용
        # (output_dir 외부에 있을 경우 파일명만 사용)
        try:
            relative_key = video_path.relative_to(self.config.output_dir).as_posix()
        except ValueError:
            relative_key = video_path.name

        # 스토리지 prefix 정리 (앞/뒤 슬래시 제거)
        key = self._build_storage_key(kind="scene", relative_key=relative_key)
        # 파일 업로드
        upload = self.storage.upload_file(video_path, key=key, metadata=metadata)

        # 업로드 결과를 메타데이터에 반영
        metadata.update(
            {
                "storage_backend": self.config.storage.backend,
                "video_url": upload.url,
                "storage_path": upload.storage_path,
            }
        )

        # 로컬 메타데이터 파일 갱신
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")
        # 노드 출력용 결과 객체 반환
        return VideoNodeOutput(
            video_url=upload.url,
            storage_path=upload.storage_path,
            duration_seconds=metadata.get("duration_seconds"),
            size_bytes=upload.size_bytes,
            created_at=upload.created_at,
            model=metadata.get("model", ""),
        )

    def merge_videos(
        self,
        *,
        scene_outputs: list[dict],
        output_path: str | None,
    ) -> dict:
        # 로컬 또는 원격에서 씬을 병합한 뒤 최종 결과물을 업로드
        if not scene_outputs:
            raise ValueError("scene_outputs is empty")

        crossfade_seconds = self.CROSSFADE_SECONDS

        output_path_obj = Path(
            output_path
            or self.config.output_dir / f"merged_{int(time.time())}.mp4"
        )

        if self.config.mode == "serverless":
            local_paths: list[Path] = []
            for item in scene_outputs:
                if not isinstance(item, dict):
                    raise ValueError("scene output is invalid")
                lp = item.get("local_path")
                if not lp or not Path(lp).exists():
                    raise ValueError(f"local_path missing or not found: {lp}")
                local_paths.append(Path(lp))
            self._local_merge_scene_videos(local_paths, output_path_obj, crossfade_seconds)
            source_paths = [str(p) for p in local_paths]
        else:
            scene_urls: list[str] = []
            for item in scene_outputs:
                if not isinstance(item, dict):
                    raise ValueError("scene output is invalid")
                storage_path = item.get("storage_path")
                video_url = item.get("video_url")
                source_url = video_url or storage_path
                if not source_url:
                    raise ValueError("scene output missing video_url")
                source_url = str(source_url)
                if "://" not in source_url:
                    raise ValueError(f"remote merge requires URL sources, got: {source_url}")
                scene_urls.append(source_url)
            self._remote_merge_scene_videos(scene_urls, output_path_obj, crossfade_seconds)
            source_paths = [str(p) for p in scene_urls]

        try:
            relative_key = output_path_obj.relative_to(self.config.output_dir).as_posix()
        except ValueError:
            relative_key = output_path_obj.name
        key = self._build_storage_key(kind="final", relative_key=relative_key)
        metadata = {
            "kind": "merged_video",
            "crossfade_seconds": crossfade_seconds,
            "source_paths": source_paths,
            "created_at": time.time(),
        }
        upload = self.storage.upload_file(output_path_obj, key=key, metadata=metadata)
        return {
            "merged_output_path": output_path_obj,
            "merged_video_url": upload.url,
            "merged_storage_path": upload.storage_path,
            "size_bytes": upload.size_bytes,
        }

    @staticmethod
    def _has_audio_stream(path: Path) -> bool:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True,
        )
        return bool(result.stdout.strip())

    def _local_merge_scene_videos(
        self,
        local_paths: list[Path],
        output_path: Path,
        crossfade_seconds: float,
    ) -> None:
        """로컬 ffmpeg single-pass 병합 (재인코딩 1회, H.264 CRF 18)"""
        if not local_paths:
            raise ValueError("local_paths is empty")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if len(local_paths) == 1:
            shutil.copy2(local_paths[0], output_path)
            return

        # 모든 씬의 duration·오디오 유무 사전 조회
        durations: list[float] = []
        has_audio: list[bool] = []
        for p in local_paths:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                capture_output=True, text=True, check=True,
            )
            durations.append(float(probe.stdout.strip()))
            has_audio.append(self._has_audio_stream(p))

        n = len(local_paths)
        merge_audio = all(has_audio)

        # single-pass xfade 체인 구성
        video_parts: list[str] = []
        audio_parts: list[str] = []
        accumulated = durations[0]
        prev_v = "[0:v]"
        prev_a = "[0:a]"

        for i in range(1, n):
            offset = max(0.0, accumulated - crossfade_seconds)
            v_out = "[vout]" if i == n - 1 else f"[v{i}]"
            video_parts.append(
                f"{prev_v}[{i}:v]xfade=transition=fade"
                f":duration={crossfade_seconds}:offset={offset:.3f}{v_out}"
            )
            if merge_audio:
                a_out = "[aout]" if i == n - 1 else f"[a{i}]"
                audio_parts.append(
                    f"{prev_a}[{i}:a]acrossfade=d={crossfade_seconds}{a_out}"
                )
                prev_a = a_out
            accumulated += durations[i] - crossfade_seconds
            prev_v = v_out

        filter_complex = ";".join(video_parts + audio_parts)

        inputs: list[str] = []
        for p in local_paths:
            inputs += ["-i", str(p)]

        maps = ["-map", "[vout]"]
        if merge_audio:
            maps += ["-map", "[aout]"]

        cmd = [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", filter_complex,
            *maps,
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p",
        ]
        if merge_audio:
            cmd += ["-c:a", "aac", "-b:a", "192k"]
        cmd.append(str(output_path))
        subprocess.run(cmd, check=True)

    def extract_last_frame_local(self, video_path: Path, output_path: Path) -> Path:
        """로컬 ffmpeg로 마지막 프레임 추출 (서버리스용)"""
        if not video_path.exists():
            raise FileNotFoundError(f"video not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-y", "-sseof", "-0.1", "-i", str(video_path),
             "-frames:v", "1", "-update", "1", str(output_path)],
            check=True,
        )
        return output_path

    def extract_last_frame_remote(self, video_path: Path, output_path: Path) -> Path:
        host = self.config.comfy_ssh_host.strip()
        user = self.config.comfy_ssh_user.strip()
        key_path = os.path.expanduser(self.config.comfy_ssh_key or "")
        port = (self.config.comfy_ssh_port or "22").strip()
        remote_dir = self.config.comfy_remote_input_dir.strip().rstrip("/")
        if not (host and user and key_path and remote_dir):
            raise RuntimeError("COMFY_SSH_HOST/USER/KEY/REMOTE_INPUT_DIR are required for remote capture")

        if not video_path.exists():
            raise FileNotFoundError(f"video not found: {video_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        remote_video = f"{remote_dir}/{video_path.name}"
        remote_frame = f"{remote_dir}/{video_path.stem}_last.png"

        scp_opts = [
            "scp",
            "-i",
            key_path,
            "-P",
            port,
            "-o",
            "StrictHostKeyChecking=no",
        ]
        ssh_base = [
            "ssh",
            "-i",
            key_path,
            "-p",
            port,
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "ConnectTimeout=10",
            f"{user}@{host}",
        ]

        subprocess.run([*scp_opts, str(video_path), f"{user}@{host}:{remote_video}"], check=True)
        subprocess.run(
            [
                *ssh_base,
                "ffmpeg",
                "-y",
                "-sseof",
                "-0.1",
                "-i",
                remote_video,
                "-frames:v",
                "1",
                "-update",
                "1",
                remote_frame,
            ],
            check=True,
        )
        subprocess.run([*scp_opts, f"{user}@{host}:{remote_frame}", str(output_path)], check=True)
        return output_path

    def _remote_merge_scene_videos(
        self,
        scene_urls: list[str],
        output_path: Path,
        crossfade_seconds: float,
    ) -> None:
        # ComfyUI 서버에서 SSH를 통한 원격 병합
        if not scene_urls:
            raise ValueError("scene_urls is empty")

        host = self.config.comfy_ssh_host.strip()
        user = self.config.comfy_ssh_user.strip()
        key_path = os.path.expanduser(self.config.comfy_ssh_key or "")
        port = (self.config.comfy_ssh_port or "22").strip()
        remote_dir = self.config.comfy_remote_merge_dir.strip() or self.config.comfy_remote_input_dir.strip()
        if not (host and user and key_path and remote_dir):
            raise RuntimeError("COMFY_SSH_HOST/USER/KEY and COMFY_REMOTE_MERGE_DIR are required for remote merge")

        remote_dir = remote_dir.rstrip("/")
        remote_output = f"{remote_dir}/{output_path.name}"
        remote_script = f"{remote_dir}/merge_script.sh"
        remote_url_list = f"{remote_dir}/merge_urls.txt"

        scp_opts = [
            "scp", "-i", key_path, "-P", port,
            "-o", "StrictHostKeyChecking=no",
        ]
        ssh_base = [
            "ssh", "-i", key_path, "-p", port,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            f"{user}@{host}",
        ]

        input_files = []
        for idx in range(1, len(scene_urls) + 1):
            input_files.append(f"{remote_dir}/scene_{idx:02d}.mp4")

        # single-pass 병합 스크립트 생성
        script_lines = [
            "#!/bin/bash",
            "set -e",
            f'REMOTE_DIR="{remote_dir}"',
            f'URL_LIST="{remote_url_list}"',
            f'OUTPUT="{remote_output}"',
            f"CROSSFADE={crossfade_seconds}",
            "",
            "# 씬 영상 다운로드",
            "idx=1",
            'while IFS= read -r url; do',
            '  outfile="$REMOTE_DIR/scene_$(printf \'%02d\' $idx).mp4"',
            '  curl -L --max-time 120 -o "$outfile" "$url"',
            '  idx=$((idx + 1))',
            'done < "$URL_LIST"',
            "",
        ]
        files_str = " ".join(f'"{f}"' for f in input_files)
        script_lines.append(f"files=({files_str})")
        script_lines += [
            'N=${#files[@]}',
            '',
            'if [ $N -eq 1 ]; then',
            '  cp "${files[0]}" "$OUTPUT"',
            '  rm -f "$URL_LIST" "$0"',
            '  exit 0',
            'fi',
            '',
            '# duration 측정',
            'declare -a durations',
            'for f in "${files[@]}"; do',
            '  dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")',
            '  durations+=("$dur")',
            'done',
            '',
            '# 오디오 유무 확인',
            'all_audio=true',
            'for f in "${files[@]}"; do',
            '  a=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$f")',
            '  if [ -z "$a" ]; then all_audio=false; break; fi',
            'done',
            '',
            '# single-pass xfade 필터 구성',
            'vfilter=""',
            'afilter=""',
            'accumulated="${durations[0]}"',
            'for (( i=1; i<N; i++ )); do',
            '  offset=$(awk -v acc="$accumulated" -v c="$CROSSFADE" \'BEGIN{v=acc-c; if(v<0)v=0; printf "%.3f", v}\')',
            '  if [ $i -eq 1 ]; then vin="[0:v]"; ain="[0:a]"',
            '  else vin="[v$((i-1))]"; ain="[a$((i-1))]"; fi',
            '  if [ $i -eq $((N-1)) ]; then vout="[vout]"; aout="[aout]"',
            '  else vout="[v${i}]"; aout="[a${i}]"; fi',
            '  vfilter="${vfilter}${vin}[${i}:v]xfade=transition=fade:duration=${CROSSFADE}:offset=${offset}${vout};"',
            '  if $all_audio; then',
            '    afilter="${afilter}${ain}[${i}:a]acrossfade=d=${CROSSFADE}${aout};"',
            '  fi',
            '  accumulated=$(awk -v acc="$accumulated" -v d="${durations[$i]}" -v c="$CROSSFADE" \'BEGIN{printf "%.3f", acc+d-c}\')',
            'done',
            '',
            'filter="${vfilter}${afilter}"',
            'filter="${filter%;}"',
            '',
            'ffargs=(-y)',
            'for f in "${files[@]}"; do ffargs+=(-i "$f"); done',
            'ffargs+=(-filter_complex "$filter" -map "[vout]")',
            'if $all_audio; then ffargs+=(-map "[aout]"); fi',
            'ffargs+=(-c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p)',
            'if $all_audio; then ffargs+=(-c:a aac -b:a 192k); fi',
            'ffargs+=("$OUTPUT")',
            'ffmpeg "${ffargs[@]}"',
            '',
            'rm -f "$URL_LIST" "$0"',
        ]

        # 원격 bash 실행 시 LF 줄바꿈을 보장하여 Windows 환경의 CRLF 문제를 방지
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sh",
            delete=False,
            encoding="utf-8",
            newline="\n",
        ) as sf:
            sf.write("\n".join(script_lines) + "\n")
            local_script = sf.name

        # s3:// URI → presigned HTTPS URL 변환 (curl 다운로드용)
        from content_pipeline.db import _maybe_presign_s3_url
        scene_urls = [_maybe_presign_s3_url(u) for u in scene_urls]

        # 원격 셸 파싱을 위해 LF 줄바꿈을 보장
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
            newline="\n",
        ) as uf:
            for url in scene_urls:
                uf.write(url + "\n")
            local_urls = uf.name

        try:
            subprocess.run([*scp_opts, local_urls, f"{user}@{host}:{remote_url_list}"], check=True)
            subprocess.run([*scp_opts, local_script, f"{user}@{host}:{remote_script}"], check=True)
        finally:
            os.unlink(local_script)
            os.unlink(local_urls)

        # 원격 실행
        subprocess.run([*ssh_base, f"bash {remote_script}"], check=True)

        # 결과 다운로드
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [*scp_opts, f"{user}@{host}:{remote_output}", str(output_path)],
            check=True,
        )

        # 원격 입력/출력 파일 누적 방지를 위한 정리 (항상 실행)
        clean_input = True
        clean_output = True
        rm_targets: list[str] = []
        if clean_input:
            # 병합 과정에서 다운로드한 입력 씬 파일들 삭제
            rm_targets.extend(input_files)
        if clean_output:
            # 원격에서 생성된 병합 결과 파일 삭제
            rm_targets.append(remote_output)
        if rm_targets:
            # 삭제 실패해도 병합 결과는 로컬로 내려받았으므로 진행
            subprocess.run(
                [*ssh_base, "rm", "-f", "--", *rm_targets],
                check=False,
            )

    def _build_storage_key(self, *, kind: str, relative_key: str) -> str:
        prefix = self.config.storage.prefix.strip("/")
        if kind == "scene":
            key = f"scene_videos/{Path(relative_key).name}"
        elif kind == "final":
            key = f"videos/{relative_key}"
        else:
            key = relative_key
        return f"{prefix}/{key}" if prefix else key

    def _build_storage_backend(self, config: VideoConfig) -> VideoStorageBackend:
        """저장소 백엔드 생성"""
        backend = config.storage.backend.lower()
        if backend == "s3":
            return S3StorageBackend(
                bucket=config.storage.s3_bucket,
                region=config.storage.s3_region,
                public_base_url=config.storage.public_base_url,
            )
        return LocalStorageBackend(
            base_dir=config.storage.base_dir,
            public_base_url=config.storage.public_base_url,
        )
