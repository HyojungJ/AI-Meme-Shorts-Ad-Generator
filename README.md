# OpenCV 생성물 검증

이미지·비디오 생성물에 대한 OpenCV 기반 1차 품질 검증을 추가했습니다.
LLM/VLM(GPT-4o Vision, Gemini) 검증 **앞단**에서 돌아가는, 모델 호출 없는 결정적 게이트입니다.

## 모듈

`ai/content_pipeline/validation/opencv_checks.py`

- `verify_image_opencv(source)` / `verify_video_opencv(source)` → `OpenCVCheckResult(passed, issues, metrics)`
- 입력은 로컬 경로와 S3/HTTP URL 모두 지원 (URL은 presign 후 임시 파일로 다운로드해 검사)

## 검사 항목

**이미지**: 디코드 가능 여부, 최소 해상도, 9:16 종횡비, 블러(라플라시안 분산), 노출(평균 밝기), 단색/깨진 프레임(표준편차)

**비디오**: 디코드/열기, 프레임 수, 길이, 해상도, 검은 프레임 비율, 샘플 프레임 평균 블러

## 파이프라인 연동

- 이미지: `verify_image_opencv_node` → 생성 직후·VLM 검증 전에 실행
- 비디오: `verify_video_opencv_node` → 그래프를 `generate → merge → verify_opencv → verify`로 구성
- OpenCV 검증 실패 + 재시도 여력이 있으면 비싼 모델 호출을 건너뛰고 바로 재생성
- 검증기 자체 오류 시에는 게이트를 막지 않고 기존 VLM/Gemini 검증으로 넘김

## 설정

모든 임계값은 `OPENCV_*` 환경변수로 조정할 수 있습니다 (예: `OPENCV_IMAGE_MIN_WIDTH`, `OPENCV_VIDEO_MAX_BLACK_FRAME_RATIO`).
