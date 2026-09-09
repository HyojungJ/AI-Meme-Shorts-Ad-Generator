# 사용자 인증 API 구현 완료 문서

## 프로젝트 개요

Google 로그인을 사용하는 사용자 인증 시스템 구축

---

## 1. DB 테이블 설계 및 생성

### users 테이블 구조

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    google_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    nickname VARCHAR(100) NOT NULL,
    profile_img VARCHAR(500),
    yt_channel_id VARCHAR(100),
    yt_access_token TEXT,
    yt_refresh_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_google_id ON users(google_id);
```

### 주요 필드 설명

- `user_id`: 사용자 고유 번호 (자동 증가)
- `google_id`: Google 사용자 ID (중복 불가)
- `email`: 이메일 (중복 불가)
- `nickname`: 닉네임
- `profile_img`: 프로필 이미지 URL
- `yt_channel_id`: YouTube 채널 ID
- `created_at`: 가입 일시
- `updated_at`: 정보 수정 일시

---

## 2. 구현한 기능

### 2-1. Google 로그인

**파일:** `scripts/user_auth_api.py`

**기능:**
- Google에서 받은 토큰이 진짜인지 확인
- 확인되면 사용자 정보 반환 (Google ID, 이메일, 이름, 프로필 사진)

**함수:** `verify_google_token(token)`

### 2-2. JWT 토큰 발급

**파일:** `scripts/user_auth_api.py`

**기능:**
- 우리 서비스 전용 토큰 생성
- 30분 후 자동 만료
- 사용자 정보를 토큰에 포함

**함수:** `create_access_token(user_data)`

### 2-3. 토큰 검증 미들웨어

**파일:** `scripts/user_auth_api.py`

**기능:**
- API 요청할 때마다 토큰 확인
- 토큰이 없거나 잘못되면 에러 반환
- 토큰이 만료되면 별도 에러 반환

**함수:** `auth_middleware(request)`

### 2-4. DB 연결 및 사용자 관리

**파일:** `scripts/database_user.py`

**기능:**
- PostgreSQL DB 연결
- 사용자 조회 (Google ID로 찾기)
- 사용자 생성 (새 사용자 저장)
- 사용자 조회 또는 생성 (없으면 자동 생성)

**주요 함수:**
- `get_user_by_google_id(db, google_id)`: Google ID로 사용자 찾기
- `create_user(db, google_id, email, nickname, profile_img)`: 새 사용자 만들기
- `get_or_create_user(db, google_id, email, name, picture)`: 있으면 가져오고 없으면 만들기

### 2-5. API 엔드포인트

**파일:** `scripts/auth_routes.py`

#### POST /auth/login - 로그인

**요청:**
```json
{
  "google_token": "Google에서 받은 토큰"
}
```

**응답:**
```json
{
  "access_token": "우리 서비스 토큰",
  "user_id": 123,
  "email": "user@gmail.com",
  "nickname": "홍길동",
  "profile_img": "https://..."
}
```

**동작 순서:**
1. Google 토큰 검증
2. DB에서 사용자 찾기 (없으면 새로 만들기)
3. JWT 토큰 발급
4. 사용자 정보와 토큰 반환

#### GET /auth/me - 내 정보 조회

**요청:**
```
GET /auth/me
Headers: Authorization: Bearer {토큰}
```

**응답:**
```json
{
  "user_id": 123,
  "email": "user@gmail.com",
  "nickname": "홍길동"
}
```

**동작 순서:**
1. 토큰 검증
2. 사용자 정보 반환

### 2-6. FastAPI 서버

**파일:** `scripts/main.py`

**기능:**
- FastAPI 서버 실행
- API 엔드포인트 등록
- CORS 설정 (프론트엔드 연동용)

**실행 방법:**
```bash
uv run python scripts/main.py
```

**서버 주소:** `http://localhost:8000`

---

## 3. 전체 동작 흐름

### 로그인 과정

```
1. 사용자가 프론트엔드에서 "Google 로그인" 클릭
   ↓
2. Google이 사용자 인증 후 토큰 발급
   ↓
3. 프론트엔드가 토큰을 백엔드로 전송
   POST /auth/login {"google_token": "..."}
   ↓
4. 백엔드에서 Google 토큰 검증
   ↓
5. DB에서 사용자 찾기 (없으면 새로 만들기)
   ↓
6. JWT 토큰 발급
   ↓
7. 프론트엔드에 토큰과 사용자 정보 반환
   {"access_token": "...", "user_id": 123, ...}
   ↓
8. 프론트엔드가 토큰 저장
```

### API 호출 과정

```
1. 프론트엔드가 API 호출
   GET /auth/me
   Headers: Authorization: Bearer {토큰}
   ↓
2. 백엔드에서 토큰 검증
   ↓
3. 토큰이 유효하면 사용자 정보 반환
   {"user_id": 123, "email": "...", ...}
```

---

## 4. 파일 구조

```
backend/
├─ scripts/
│  ├─ user_auth_api.py        # 인증 로직 (토큰 검증, 생성, 미들웨어)
│  ├─ database_user.py         # DB 연결 및 사용자 관리
│  ├─ auth_routes.py           # API 엔드포인트 (로그인, 내 정보)
│  ├─ main.py                  # FastAPI 서버 실행
│  ├─ user_auth_test.py        # 인증 로직 테스트
│  └─ test_database.py         # DB 연결 테스트
├─ docs/
│  └─ UserAuthAPI.md           # 이 문서
└─ .env                        # 환경 변수 (DB 주소, JWT 키 등)
```

---

## 5. 환경 변수 설정

**파일:** `.env`

```env
GOOGLE_CLIENT_ID="Google 클라이언트 ID"
GOOGLE_CLIENT_SECRET="Google 클라이언트 시크릿"
JWT_SECRET_KEY="JWT 암호화 키"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DB_URL="postgresql://postgres:pass1234@3.35.238.161:5432/meme-fluencer"
```

---

## 6. 테스트 방법

### 방법 1: 자동 API 문서에서 테스트

1. 서버 실행
   ```bash
   uv run python scripts/main.py
   ```

2. 브라우저에서 접속
   ```
   http://localhost:8000/docs
   ```

3. `POST /auth/login` 클릭
4. "Try it out" 버튼 클릭
5. `google_token` 입력
6. "Execute" 버튼 클릭

### 방법 2: 테스트 코드 실행

```bash
# 인증 로직 테스트
uv run python scripts/user_auth_test.py

# DB 연결 테스트
uv run python scripts/test_database.py
```

---

## 7. 주요 기술

- **FastAPI**: Python API 서버 프레임워크
- **SQLAlchemy**: Python DB 연결 도구 (ORM)
- **PostgreSQL**: 데이터베이스
- **JWT**: 토큰 기반 인증
- **Google OAuth 2.0**: Google 로그인

---

## 8. 완료된 작업

✅ users 테이블 설계 및 생성
✅ Google OAuth 토큰 검증 로직
✅ JWT 토큰 생성 로직
✅ 인증 미들웨어 구현
✅ DB 연결 및 사용자 관리 함수
✅ 로그인 API 엔드포인트
✅ 내 정보 조회 API 엔드포인트
✅ FastAPI 서버 구축
✅ 테스트 코드 작성
✅ 환경 변수 설정

---

## 9. 다음 단계 (선택사항)

- 리프레시 토큰 구현 (토큰 자동 갱신)
- 로그아웃 기능 추가
- 사용자 정보 수정 API
- YouTube 연동 기능
- 프로필 이미지 업로드

---

## 10. 프론트엔드 연동 가이드

### 로그인 구현

```javascript
// 1. Google 로그인 후 토큰 받기
const googleToken = "Google에서 받은 토큰";

// 2. 백엔드 로그인 API 호출
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    google_token: googleToken
  })
});

const data = await response.json();
// data = {access_token: "...", user_id: 123, email: "...", ...}

// 3. 토큰 저장
localStorage.setItem('access_token', data.access_token);
```

### API 호출 시 토큰 사용

```javascript
// 저장된 토큰 가져오기
const token = localStorage.getItem('access_token');

// API 호출
const response = await fetch('http://localhost:8000/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const userData = await response.json();
// userData = {user_id: 123, email: "...", nickname: "..."}
```

---

## 11. 문제 해결

### 서버가 안 켜져요
```bash
# 포트가 이미 사용 중일 수 있음
# 다른 터미널에서 실행 중인 서버 종료 후 다시 시도
```

### DB 연결 안 돼요
```bash
# .env 파일의 DB_URL 확인
# DB 서버가 실행 중인지 확인
```

### 토큰 검증 실패
```bash
# .env 파일의 JWT_SECRET_KEY 확인
# 토큰이 만료되었는지 확인 (30분 후 자동 만료)
```

---

## 작업 완료일

2026.01.19
