# 밈 목록 조회 API 문서

## 개요

영상 생성 시 사용할 밈을 선택하기 위한 밈 목록 조회 API입니다.

**작업일**: 2026-01-27

---

## 배경

영상 생성 요청 시 `meme_id`를 입력받지만, 프론트엔드에서 실제 DB에 있는 밈 목록을 불러올 수 있는 엔드포인트가 없었습니다. 사용자가 선택 가능한 밈 목록을 제공하기 위해 API를 추가했습니다.

---

## API 엔드포인트

### 1. 밈 목록 조회

```http
GET /api/v1/memes
```

**설명**: 영상 생성 시 선택할 수 있는 밈 목록을 조회합니다.

**인증**: Bearer Token 필요

**쿼리 파라미터**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| status | string | 선택 | - | 밈 상태 필터 (READY, PROCESSING, COMPLETED, FAILED) |
| meme_type | string | 선택 | - | 밈 타입 필터 (quotable, performable, hybrid) |
| search | string | 선택 | - | 밈 이름 검색 (부분 일치) |
| offset | integer | 선택 | 0 | 페이지네이션 오프셋 |
| limit | integer | 선택 | 50 | 페이지 크기 (최대 200) |

**응답 예시**:
```json
{
  "total_count": 10,
  "memes": [
    {
      "meme_id": 1,
      "meme_name": "무야호",
      "definition": "기쁨이나 흥분을 표현하는 밈",
      "meme_type": "quotable",
      "key_phrase": "무야호~",
      "status": "READY"
    },
    {
      "meme_id": 2,
      "meme_name": "어쩔티비",
      "definition": "상대방의 말에 무관심하거나 반박할 때 사용",
      "meme_type": "performable",
      "key_phrase": "어쩔티비 저쩔티비",
      "status": "READY"
    }
  ]
}
```

**사용 예시**:
```javascript
// 사용 가능한 밈 목록 조회 (READY 상태만)
GET /api/v1/memes?status=READY&limit=100

// 밈 이름으로 검색
GET /api/v1/memes?search=무야호

// quotable 타입 밈만 조회
GET /api/v1/memes?meme_type=quotable
```

---

### 2. 밈 상세 정보 조회

```http
GET /api/v1/memes/{meme_id}
```

**설명**: 특정 밈의 상세 정보를 조회합니다.

**인증**: Bearer Token 필요

**경로 파라미터**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| meme_id | integer | 필수 | 밈 ID |

**응답 예시**:
```json
{
  "meme_id": 1,
  "meme_name": "무야호",
  "definition": "기쁨이나 흥분을 표현하는 밈",
  "origin": {
    "source": "유튜브",
    "creator": "크리에이터명",
    "year": 2020
  },
  "key_phrase": "무야호~",
  "sources": [
    "https://youtube.com/...",
    "https://naver.com/..."
  ],
  "risk_info": "low",
  "meme_type": "quotable",
  "status": "READY",
  "confidence": 0.95,
  "created_at": "2026-01-27T10:00:00"
}
```

**에러 응답**:
```json
{
  "detail": "밈을 찾을 수 없습니다"
}
```

---

## 밈 데이터 구조

### Meme 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| meme_id | bigint | 밈 ID (PK) |
| meme_name | varchar(255) | 밈 이름 (고유) |
| definition | text | 밈 정의/설명 |
| origin | jsonb | 밈 출처 정보 |
| key_phrase | text | 핵심 문구 |
| sources | jsonb | 참고 자료 URL 목록 |
| risk_info | varchar(20) | 위험도 정보 |
| meme_type | varchar(50) | 밈 타입 (quotable, performable, hybrid) |
| status | varchar(50) | 상태 (READY, PROCESSING, PROCESSED, COMPLETED, FAILED) |
| source_video | jsonb | 원본 영상 정보 |
| video_analysis | jsonb | 영상 분석 결과 |
| confidence | float | 신뢰도 점수 |
| created_at | timestamp | 생성일시 |
| updated_at | timestamp | 수정일시 |

### 밈 타입 (meme_type)

- **quotable**: 대사/문구 중심 밈 (예: "무야호", "어쩔티비")
- **performable**: 동작/행동 중심 밈 (예: 춤, 제스처)
- **hybrid**: 대사 + 동작 복합 밈

### 밈 상태 (status)

- **READY**: 사용 가능
- **PROCESSING**: 처리 중
- **PROCESSED**: 처리 완료
- **COMPLETED**: 완전히 준비됨
- **FAILED**: 처리 실패

---

## 프론트엔드 연동 가이드

### 1. 영상 생성 페이지 로드 시

```javascript
// 사용 가능한 밈 목록 조회
const response = await fetch('/api/v1/memes?status=READY&limit=100', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const data = await response.json();
// data.memes를 드롭다운에 표시
```

### 2. 밈 선택 UI

```jsx
<select name="meme_id">
  <option value="">밈 선택 (선택사항)</option>
  {data.memes.map(meme => (
    <option key={meme.meme_id} value={meme.meme_id}>
      {meme.meme_name} - {meme.key_phrase}
    </option>
  ))}
</select>
```

### 3. 영상 생성 요청 시

```javascript
const formData = new FormData();
formData.append('product_name', '상품명');
formData.append('product_category', '카테고리');
formData.append('product_highlight', '핵심 메시지');
formData.append('meme_id', selectedMemeId); // 선택한 밈 ID
// ... 기타 필드

await fetch('/api/v1/videos/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

---

## 구현 파일

- `app/api/v1/endpoints/memes.py` - 밈 API 엔드포인트
- `app/models/meme.py` - 밈 모델 정의
- `app/main.py` - 라우터 등록

---

## 권한

- 모든 엔드포인트는 **로그인한 사용자**만 접근 가능
- Client, Admin 모두 조회 가능
- 회사 구분 없이 전체 밈 목록 조회 가능

---

## 향후 개선 사항

- [ ] 밈 추천 기능 (상품 카테고리 기반)
- [ ] 밈 인기도 순 정렬
- [ ] 밈 미리보기 이미지/영상
- [ ] 밈 사용 통계 (어떤 밈이 가장 많이 사용되는지)
- [ ] Admin 전용 밈 관리 API (생성, 수정, 삭제)

---

## 테스트

### Swagger UI에서 테스트

1. `/docs` 접속
2. 로그인하여 Bearer Token 획득
3. `GET /api/v1/memes` 엔드포인트 테스트
4. 다양한 필터 옵션 시도

### cURL 예시

```bash
# 밈 목록 조회
curl -X GET "http://localhost:8000/api/v1/memes?status=READY" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 밈 상세 조회
curl -X GET "http://localhost:8000/api/v1/memes/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 에러 처리

| 상태 코드 | 설명 |
|----------|------|
| 200 | 성공 |
| 401 | 인증 실패 (토큰 없음 또는 만료) |
| 404 | 밈을 찾을 수 없음 (상세 조회 시) |
| 500 | 서버 오류 |
