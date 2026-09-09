# 영상 파이프라인 정리/디버그 기록

- 작업 기간: 2026.01.29
- 작업자: 김진
- 관련 이슈 / PR: #75

---

## 개요
- 영상 생성 파이프라인의 메타데이터 저장 정책 정리
- ComfyUI 원격 입력(SSH+curl) 기반으로 전환 및 문제 원인 파악

---

## 변경 요약

### 1) 메타데이터 정책
- **이미지 메타데이터 JSON 파일의 S3 업로드 제거**
  - DB(`image_generations.metadata_json`)에만 저장
  - 관련 변경: `content_pipeline/image/service.py`
- **영상 메타데이터 JSON 파일의 S3 업로드 제거**
  - DB(`scene_videos.generation_metadata`)에만 저장
  - 관련 변경: `content_pipeline/video/service.py`
- **S3 업로드 시 메타데이터 헤더 미전송**
  - 한글(비 ASCII) 메타데이터로 인한 S3 에러 방지
  - 관련 변경:
    - `content_pipeline/video/storage.py`
    - `content_pipeline/image/storage.py`
    - `content_pipeline/voice/storage.py`

### 2) ComfyUI 입력 전달 방식
- URL 입력을 로컬 임시파일 다운로드 대신 **원격 서버에서 직접 다운로드(SSH+curl)** 처리
  - 함수: `content_pipeline/video/client.py::_download_remote_input`

### 3) 캐릭터 제한(영상 생성)
- 영상 생성 프롬프트에 "참조 이미지의 캐릭터만 사용" 문구 강제 추가
  - `content_pipeline/video/service.py`

---

## 실행/테스트 방법

### 패스프레이즈 없는 키 사용
1. 새 키 생성
   ```
   ssh-keygen -t ed25519 -f C:\Users\user\.ssh\id_ed25519_nopass -N ""
   ```
2. 공개키 서버 등록
   ```
   type C:\Users\user\.ssh\id_ed25519_nopass.pub | ssh -p 30417 root@103.196.86.55 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
   ```
3. `.env` 수정
   ```
   COMFY_SSH_KEY=C:\Users\user\.ssh\id_ed25519_nopass
   ```

### 실행
```
uv run --python-preference=system python scripts\video_graph_from_scenes.py --ad-id 1724 --company-id 45
```

---

## 참고
- `content_pipeline/video/config.py`에서 `load_dotenv(override=True)` 사용 중
- `uv run` 실행 시 환경변수 로딩 방식에 주의

---

## 트러블 슈팅

1. ComfyUI 원격 입력 다운로드 단계에서 SSH 실패 발생 (DB 조회는 정상 동작)
- 문제: 스크립트 실행 시 SSH 오류: `Permission denied (publickey,password)`
- 원인: 비대화 모드에서 키 인증 실패로 `ssh-agent` 서비스 시작 불가
- 해결: 
    - video/client.py `ssh -o BatchMode=yes ...` (78-79 line) 삭제
    - 패스프레이즈 없는 키 사용
