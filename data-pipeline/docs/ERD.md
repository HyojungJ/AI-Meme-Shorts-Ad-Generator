# ERD 문서

- 작업 기간: 2026.01.05
- 관련 이슈: #17

## 1. 개요

* 밈의 정의·기원·상태를 구조적으로 관리
* 밈이 사용된 정적 게시물 및 유튜브 영상 수집
* 유튜브 영상 단위로 영상 분석과 음성 분석을 분리

---

## 2. ERD 구조

```
[meme]
    ├── static_post
    └── youtube
        ├── video
        └── audio
```
* `meme (1) : static_post (N)`
* `meme (1) : youtube (N)`
* `youtube (1) : video (N)`
* `youtube (1) : audio (1)`



---

## 3. 스키마 정보
- Database: postgres
- Schema: memedb
- DBMS: PostgreSQL (표준 문법 사용)

---

## 4. 테이블 상세 정의

### meme 테이블

- 밈의 기본 정보와 처리 상태를 저장하는 핵심 테이블이다.
- 모든 분석 데이터는 이 테이블을 기준으로 연결된다.

| 컬럼명             | 타입           | 설명       |
| --------------- | ------------ | -------- |
| meme_id         | BIGINT (PK)  | 밈 고유 ID  |
| meme_name       | VARCHAR(255) | 밈 이름     |
| meme_definition | TEXT         | 밈의 의미·정의 |
| meme_origin     | TEXT         | 밈의 기원    |
| created_at      | TIMESTAMP    | 생성 시각    |
| is_processed_v  | BOOLEAN      | 영상 분석 여부 |
| is_processed_a  | BOOLEAN      | 음성 분석 여부 |

---

### static_post 테이블

- 웹 검색을 통해 **정적 게시물**에서 밈이 사용된 사례를 저장한다.

| 컬럼명        | 타입           | 설명      |
| ---------- | ------------ | ------- |
| post_id    | BIGINT (PK)  | 게시물 ID  |
| meme_id    | BIGINT (FK)  | 참조 밈 ID |
| post_title | VARCHAR(255) | 게시물 제목  |
| post_url   | TEXT         | 게시물 URL |
| meme_usage | TEXT         | 밈 사용 맥락 |

---

### youtube 테이블

- 밈이 사용된 **유튜브 영상의 기본 메타데이터**를 저장한다.

| 컬럼명         | 타입               | 설명        |
| ----------- | ---------------- | --------- |
| video_id    | VARCHAR(20) (PK) | 유튜브 영상 ID |
| meme_id     | BIGINT (FK)      | 참조 밈 ID   |
| video_title | VARCHAR(255)     | 영상 제목     |
| youtube_url | VARCHAR(50)     | 유튜브 URL   |

---

### video 테이블

- 유튜브 영상에 대한 **영상 분석 결과** 메타데이터를 저장한다.

| 컬럼명               | 타입                   | 설명        |
| ----------------- | -------------------- | --------- |
| video_id          | VARCHAR(20) (PK, FK) | 유튜브 영상 ID |
| time_stamp        | VARCHAR(50)          | 주요 장면 시점  |
| video_description | TEXT                 | 영상 분석 설명  |

---

### audio 테이블

- 유튜브 영상의 **음성 분석 결과**를 저장한다.

| 컬럼명        | 타입                   | 설명             |
| ---------- | -------------------- | -------------- |
| video_id   | VARCHAR(20) (PK, FK) | 유튜브 영상 ID      |
| audio_json | JSONB                | 음성 분석 결과(JSON) |

---

## 5. DB Design Decisions

- YouTube video_id는 외부 식별자이므로 VARCHAR 사용
- 음성 파일은 DB에 저장하지 않고 S3에 저장
- 분석 결과는 JSONB 타입으로 저장

---

## 6. 무결성 및 제약 조건

* 모든 FK는 `ON DELETE CASCADE` 적용
* 상위 데이터 삭제 시 하위 분석 데이터 자동 정리