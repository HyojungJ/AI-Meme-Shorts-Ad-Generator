# Legacy Scripts (Deprecated)

이 폴더는 레거시 코드입니다. 새로운 구조는 `app/` 폴더를 사용하세요.

## 마이그레이션 완료

- ✅ **인증 (auth)** → `app/api/v1/endpoints/auth.py` + `app/crud/auth.py`
- ✅ **영상 생성 (generation)** → `app/api/v1/endpoints/video.py` + `app/crud/video.py`
- ✅ **상태 추적 (status)** → `app/api/v1/endpoints/status.py`
- ✅ **시나리오 (scenario)** → `app/api/v1/endpoints/scenario.py` + `app/crud/scenario.py`
- ✅ **영상 다운로드 (final)** → `app/api/v1/endpoints/final.py`
- ✅ **Admin 관리 (admin)** → `app/api/v1/endpoints/admin.py` + `app/crud/admin.py`

## 새 구조 사용법

```bash
# 새 구조로 서버 실행
python -m app.main

# 또는
uvicorn app.main:app --reload
```

## 이 폴더의 파일들

참고용으로만 보관됩니다. 실제 운영에는 사용하지 마세요.
