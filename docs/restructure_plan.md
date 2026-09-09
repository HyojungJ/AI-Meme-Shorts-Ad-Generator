# 완전 재구조화 방안

## 현재 문제점

### 1. 중복된 라우터 구조
```
video.router (/api/v1/videos)
├── POST /generate - 영상 생성 요청
├── GET /characters - 캐릭터 목록
├── POST /characters/generate - 캐릭터 생성
├── POST /characters/{id}/voice/generate - 음성 생성
└── GET /{ad_id} - 광고 조회

content_pipeline.router (/api/v1/video)
├── POST /{ad_id}/character/generate - 캐릭터 생성
├── POST /{ad_id}/voice/generate - 음성 생성
├── POST /{ad_id}/scenario/generate - 시나리오 생성
├── POST /{ad_id}/video/generate - 영상 생성
└── POST /{ad_id}/content/generate - 통합 생성

final.router (/api/v1/videos)
├── GET /{video_id}/download - 영상 다운로드
├── POST /{video_id}/approve - 영상 승인
└── POST /{video_id}/reject - 영상 거부

scenario.router (/api/v1/videos)
├── GET /{job_id}/scenarios - 시나리오 조회
└── POST /{job_id}/scenarios/{script_id}/approve - 시나리오 승인
```

**문제:**
- 같은 기능이 여러 곳에 분산
- URL 패턴 충돌 (`{ad_id}`, `{video_id}`, `{job_id}` 구분 불가)
- 프론트엔드에서 어느 API를 써야 할지 혼란

---

## 재구조화 방안

### 핵심 아이디어
**리소스 중심 설계**: 광고 요청(AdRequest)을 중심으로 모든 하위 리소스 구조화

```
AdRequest (광고 요청)
├── Character (캐릭터)
├── Voice (음성)
├── Scenario (시나리오)
└── Video (최종 영상)
```

---

## 새로운 API 구조

### 1. `/api/v1/ads` - 광고 요청 관리
```
POST   /api/v1/ads                    # 광고 요청 생성
GET    /api/v1/ads                    # 내 광고 목록
GET    /api/v1/ads/{ad_id}            # 광고 상세
DELETE /api/v1/ads/{ad_id}            # 광고 삭제
GET    /api/v1/ads/{ad_id}/status     # 진행 상태
```

### 2. `/api/v1/ads/{ad_id}/character` - 캐릭터
```
POST   /api/v1/ads/{ad_id}/character/generate  # 캐릭터 생성
GET    /api/v1/ads/{ad_id}/character/preview   # 캐릭터 미리보기
POST   /api/v1/ads/{ad_id}/character/approve   # 캐릭터 승인
POST   /api/v1/ads/{ad_id}/character/revise    # 캐릭터 재생성
```

### 3. `/api/v1/ads/{ad_id}/voice` - 음성
```
POST   /api/v1/ads/{ad_id}/voice/generate      # 음성 생성
GET    /api/v1/ads/{ad_id}/voice/preview       # 음성 미리보기
POST   /api/v1/ads/{ad_id}/voice/approve       # 음성 승인
POST   /api/v1/ads/{ad_id}/voice/revise        # 음성 재생성
```

### 4. `/api/v1/ads/{ad_id}/scenario` - 시나리오
```
POST   /api/v1/ads/{ad_id}/scenario/generate   # 시나리오 생성
GET    /api/v1/ads/{ad_id}/scenario             # 시나리오 조회
POST   /api/v1/ads/{ad_id}/scenario/approve    # 시나리오 승인
POST   /api/v1/ads/{ad_id}/scenario/revise     # 시나리오 수정
```

### 5. `/api/v1/ads/{ad_id}/video` - 최종 영상
```
POST   /api/v1/ads/{ad_id}/video/generate      # 영상 생성
GET    /api/v1/ads/{ad_id}/video/preview       # 영상 미리보기
GET    /api/v1/ads/{ad_id}/video/download      # 영상 다운로드
POST   /api/v1/ads/{ad_id}/video/approve       # 영상 승인
POST   /api/v1/ads/{ad_id}/video/reject        # 영상 거부
POST   /api/v1/ads/{ad_id}/video/revise        # 영상 재생성
```

### 6. `/api/v1/ads/{ad_id}/content` - 통합 생성 (선택적)
```
POST   /api/v1/ads/{ad_id}/content/generate    # 전체 컨텐츠 자동 생성
POST   /api/v1/ads/{ad_id}/content/approve     # 전체 승인
POST   /api/v1/ads/{ad_id}/content/revise      # 전체 재생성
```

---

## 파일 구조 변경

### Before (현재)
```
backend/app/api/v1/endpoints/
├── video.py          # 캐릭터, 음성, 광고 요청 혼재
├── content_pipeline.py  # 전체 파이프라인
├── final.py          # 최종 영상
├── scenario.py       # 시나리오
└── status.py         # 상태 조회
```

### After (재구조화)
```
backend/app/api/v1/endpoints/
├── ads.py            # 광고 요청 CRUD + 상태
├── character.py      # 캐릭터 생성/승인
├── voice.py          # 음성 생성/승인
├── scenario.py       # 시나리오 생성/승인
├── video.py          # 최종 영상 생성/승인/다운로드
└── content.py        # 통합 생성 (선택적)
```

---

## 장점

### 1. 명확한 리소스 계층
```
Ad → Character → Voice → Scenario → Video
```
각 단계가 명확하게 분리되고 순서가 보임

### 2. URL 충돌 제거
```
/api/v1/ads/123/character  # 캐릭터
/api/v1/ads/123/video      # 영상
```
더 이상 `{ad_id}`와 `{video_id}` 혼동 없음

### 3. RESTful 설계
```
GET    /ads/{id}           # 조회
POST   /ads/{id}/character # 하위 리소스 생성
DELETE /ads/{id}           # 삭제
```
표준 REST 패턴 준수

### 4. 프론트엔드 코드 단순화
```typescript
// Before
await videoApi.generateCharacter(...)
await contentPipelineApi.generateCharacter(...)  // 어느 걸 써야 하지?

// After
await adsApi.character.generate(adId, ...)  // 명확함
```

### 5. 확장성
```
/api/v1/ads/{ad_id}/analytics  # 광고별 분석
/api/v1/ads/{ad_id}/comments   # 광고별 댓글
/api/v1/ads/{ad_id}/versions   # 버전 관리
```
새 기능 추가가 쉬움

---

## 단점 및 고려사항

### 1. 대규모 수정 필요
- 모든 엔드포인트 파일 재작성
- 프론트엔드 API 클라이언트 전체 수정
- 테스트 코드 수정

### 2. 마이그레이션 기간
- 기존 API와 새 API 병행 운영 필요
- 점진적 마이그레이션 전략 필요

### 3. 작업 시간
- 예상 소요 시간: 2-3일
- 테스트 및 검증: 1-2일

---

## 마이그레이션 전략

### Phase 1: 새 API 추가 (기존 유지)
```python
# main.py
app.include_router(ads.router, prefix="/api/v1/ads", tags=["광고 (신규)"])
app.include_router(video.router, prefix="/api/v1/videos", tags=["영상 (구버전)"])
```

### Phase 2: 프론트엔드 점진적 전환
```typescript
// 새 API로 하나씩 전환
const response = await adsApi.character.generate(adId, data)
```

### Phase 3: 구버전 API 제거
```python
# 구버전 라우터 제거
# app.include_router(video.router, ...)  # 삭제
```

---

## 즉시 적용 가능한 최소 수정안

시간이 부족하다면 이것만이라도:

```python
# main.py
app.include_router(video.router, prefix="/api/v1/requests", tags=["광고 요청"])
app.include_router(content_pipeline.router, prefix="/api/v1/pipeline", tags=["파이프라인"])
app.include_router(final.router, prefix="/api/v1/finals", tags=["최종 영상"])
app.include_router(scenario.router, prefix="/api/v1/scenarios", tags=["시나리오"])
```

이렇게만 해도 URL 충돌은 해결됨!
