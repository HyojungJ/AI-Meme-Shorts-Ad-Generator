# 인증 시스템 V2 - 아키텍처 및 워크플로우 설명

## 📁 파일 구조 및 역할

```
backend/
├── scripts/
│   ├── auth_v2.py              # 핵심 인증 로직
│   ├── database_v2.py          # 데이터베이스 모델 및 함수
│   ├── auth_routes_v2.py       # API 엔드포인트 정의
│   ├── main_v2.py              # FastAPI 서버 실행
│   └── test_auth_v2.py         # 단위 테스트
├── docs/
│   ├── AuthV2_API.md           # API 사용 문서
│   └── AuthV2_Architecture.md  # 이 문서
└── .env                        # 환경 변수 (비밀키, DB 정보)
```

---

## 🔧 각 파일의 역할

### 1. `auth_v2.py` - 인증 핵심 로직
**역할**: 비밀번호 암호화, JWT 토큰 생성/검증, 보안 관련 핵심 기능

**주요 함수들**:
```python
# 비밀번호 관련
hash_password(password)           # 비밀번호를 bcrypt로 암호화
verify_password(plain, hashed)    # 비밀번호 검증

# JWT 토큰 관련
create_access_token(user_data)    # Access Token 생성 (1시간)
create_refresh_token(user_data)   # Refresh Token 생성 (7일)
verify_token(token, type)         # 토큰 검증

# 미들웨어
auth_middleware_v2(request)       # 요청마다 토큰 검증
require_role(request, roles)      # 특정 역할만 접근 허용

# 비밀번호 재설정
generate_reset_token()            # 재설정 토큰 생성
```

**왜 필요한가?**
- 비밀번호를 평문으로 저장하면 해킹 위험 → bcrypt로 암호화
- 로그인 상태 유지를 위해 JWT 토큰 사용
- 보안 로직을 한 곳에 모아서 관리하기 쉽게

---

### 2. `database_v2.py` - 데이터베이스 관리
**역할**: DB 연결, 테이블 모델 정의, 데이터 CRUD 함수

**테이블 모델**:
```python
class Company:
    - company_id      # 회사 고유 ID
    - name            # 회사명
    - contact_email   # 연락처 이메일
    - contact_phone   # 연락처 전화번호
    - is_active       # 활성화 여부
    - created_at      # 생성 일시
    - updated_at      # 수정 일시

class User:
    - user_id         # 사용자 고유 ID
    - company_id      # 소속 회사 (외래키)
    - email           # 로그인 이메일
    - hashed_password # 암호화된 비밀번호
    - role            # 역할 (admin/client)
    - is_active       # 계정 활성화 여부
    - refresh_token   # Refresh Token 저장
    - rt_expires_at   # Refresh Token 만료 시간
    - reset_token     # 비밀번호 재설정 토큰
    - reset_expires_at # 재설정 토큰 만료 시간
    - last_login_at   # 마지막 로그인 시간
    - created_at      # 가입 일시
    - updated_at      # 정보 수정 일시
```

**주요 함수들**:
```python
# 회사 관련
get_company_by_id(db, company_id)
create_company(db, name, email, phone)

# 사용자 관련
get_user_by_email(db, email)
get_user_by_id(db, user_id)
create_user(db, company_id, email, hashed_password, role)

# 토큰 관리
update_user_refresh_token(db, user_id, token, expires_at)
update_user_reset_token(db, user_id, token, expires_at)

# 비밀번호 관리
update_user_password(db, user_id, new_hashed_password)
get_user_by_reset_token(db, reset_token)
```

**왜 필요한가?**
- 사용자 정보를 영구적으로 저장
- 로그인 시 이메일/비밀번호 확인
- 토큰 관리 및 비밀번호 재설정 기능

---

### 3. `auth_routes_v2.py` - API 엔드포인트
**역할**: 클라이언트(프론트엔드)가 호출할 수 있는 API 정의

**엔드포인트 목록**:
```python
POST /auth/v2/signup              # 회원가입
POST /auth/v2/login               # 로그인
POST /auth/v2/logout              # 로그아웃
POST /auth/v2/refresh             # 토큰 갱신
GET  /auth/v2/me                  # 현재 사용자 정보
POST /auth/v2/password-reset/request   # 비밀번호 재설정 요청
POST /auth/v2/password-reset/confirm   # 비밀번호 재설정 확인
```

**각 엔드포인트가 하는 일**:

1. **회원가입** (`/signup`)
   - 이메일 중복 확인
   - 회사 생성
   - 비밀번호 암호화
   - 사용자 생성
   - JWT 토큰 발급

2. **로그인** (`/login`)
   - 이메일로 사용자 찾기
   - 비밀번호 검증
   - JWT 토큰 발급

3. **로그아웃** (`/logout`)
   - Refresh Token 삭제

4. **토큰 갱신** (`/refresh`)
   - Refresh Token 검증
   - 새 Access Token 발급

5. **사용자 정보** (`/me`)
   - Access Token 검증
   - 사용자 정보 반환

6. **비밀번호 재설정**
   - 요청: 재설정 토큰 생성 및 이메일 발송
   - 확인: 토큰 검증 후 비밀번호 변경

---

### 4. `main_v2.py` - FastAPI 서버
**역할**: API 서버 실행 및 설정

```python
app = FastAPI(...)              # FastAPI 앱 생성
app.add_middleware(CORS)        # CORS 설정 (프론트엔드 연동)
app.include_router(auth_v2_router)  # 인증 API 등록

# 서버 실행
uvicorn.run(app, host="0.0.0.0", port=8000)
```

**왜 필요한가?**
- API 서버를 실제로 실행하는 진입점
- 여러 라우터를 하나로 모아서 관리

---

### 5. `test_auth_v2.py` - 단위 테스트
**역할**: 핵심 기능이 제대로 작동하는지 테스트

```python
test_password_hashing()   # 비밀번호 암호화/검증 테스트
test_jwt_tokens()         # JWT 토큰 생성/검증 테스트
```

**왜 필요한가?**
- 코드 변경 시 기존 기능이 깨지지 않았는지 확인
- 배포 전 안전성 검증

---

## 🔄 전체 워크플로우

### 1️⃣ 회원가입 플로우
```
사용자 입력
  ↓
[auth_routes_v2.py] /signup 엔드포인트
  ↓
이메일 중복 확인 (database_v2.py)
  ↓
회사 생성 (database_v2.py)
  ↓
비밀번호 암호화 (auth_v2.py - bcrypt)
  ↓
사용자 생성 (database_v2.py)
  ↓
JWT 토큰 발급 (auth_v2.py)
  ↓
Refresh Token DB 저장 (database_v2.py)
  ↓
응답: Access Token + Refresh Token
```

### 2️⃣ 로그인 플로우
```
사용자 입력 (이메일, 비밀번호)
  ↓
[auth_routes_v2.py] /login 엔드포인트
  ↓
이메일로 사용자 조회 (database_v2.py)
  ↓
비밀번호 검증 (auth_v2.py - bcrypt)
  ↓
JWT 토큰 발급 (auth_v2.py)
  ↓
Refresh Token DB 저장 (database_v2.py)
  ↓
응답: Access Token + Refresh Token
```

### 3️⃣ 인증이 필요한 API 호출 플로우
```
클라이언트 요청 (Authorization: Bearer {token})
  ↓
[auth_v2.py] auth_middleware_v2
  ↓
토큰 추출 및 검증
  ↓
사용자 정보 추출
  ↓
request.state.user에 저장
  ↓
API 로직 실행
  ↓
응답
```

### 4️⃣ 비밀번호 재설정 플로우
```
1단계: 재설정 요청
  사용자 이메일 입력
    ↓
  [auth_routes_v2.py] /password-reset/request
    ↓
  재설정 토큰 생성 (auth_v2.py)
    ↓
  DB에 토큰 저장 (database_v2.py)
    ↓
  이메일 발송 (TODO: 실제 구현 필요)

2단계: 비밀번호 변경
  재설정 토큰 + 새 비밀번호 입력
    ↓
  [auth_routes_v2.py] /password-reset/confirm
    ↓
  토큰 검증 (database_v2.py)
    ↓
  새 비밀번호 암호화 (auth_v2.py)
    ↓
  비밀번호 업데이트 (database_v2.py)
    ↓
  재설정 토큰 삭제
```

---

## 🛠️ 실행했던 명령어들

### 1. 패키지 설치
```bash
# bcrypt 설치 (비밀번호 암호화용)
uv add bcrypt

# email-validator 설치 (이메일 검증용)
uv add email-validator
```

**왜 필요했나?**
- `bcrypt`: 비밀번호를 안전하게 암호화하기 위해
- `email-validator`: Pydantic의 EmailStr 타입을 사용하기 위해

---

### 2. 단위 테스트 실행
```bash
uv run python scripts/test_auth_v2.py
```

**결과**:
- ✅ 비밀번호 해싱 테스트 통과
- ✅ JWT 토큰 생성/검증 테스트 통과

**왜 실행했나?**
- 핵심 기능(비밀번호 암호화, JWT 토큰)이 제대로 작동하는지 확인

---

### 3. API 서버 실행
```bash
uv run python scripts/main_v2.py
```

**결과**:
- 서버가 `http://localhost:8000`에서 실행됨
- API 문서: `http://localhost:8000/docs`

**왜 실행했나?**
- 실제 API를 테스트하기 위해 서버 시작

---

### 4. API 테스트 (PowerShell)

#### 회원가입 테스트
```powershell
$body = @{
    email="test@company.com"
    password="securePass123!"
    company_name="테스트회사"
    contact_email="contact@company.com"
    contact_phone="010-1234-5678"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/signup" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

**결과**: Access Token + Refresh Token 발급 ✅

---

#### 로그인 테스트
```powershell
$body = @{
    email="test@company.com"
    password="securePass123!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/login" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

**결과**: 로그인 성공, 토큰 발급 ✅

---

#### 사용자 정보 조회 테스트
```powershell
$token = "eyJhbGc..."  # 로그인에서 받은 Access Token
$headers = @{Authorization="Bearer $token"}

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/me" `
    -Method GET -Headers $headers -UseBasicParsing
```

**결과**: 사용자 정보 조회 성공 ✅

---

#### 비밀번호 재설정 요청
```powershell
$body = @{email="test@company.com"} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/password-reset/request" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

**결과**: 재설정 토큰 생성 ✅

---

#### 비밀번호 재설정 확인
```powershell
$body = @{
    reset_token="bKTUL44ay8_cgx4hlG163mBmjJlcrXrrqk6fM_fWWz4"
    new_password="newPassword123!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/password-reset/confirm" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

**결과**: 비밀번호 변경 성공 ✅

---

#### 새 비밀번호로 로그인
```powershell
$body = @{
    email="test@company.com"
    password="newPassword123!"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/v2/login" `
    -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

**결과**: 새 비밀번호로 로그인 성공 ✅

---

## 🔐 보안 요소

### 1. 비밀번호 암호화 (bcrypt)
```python
# 평문 비밀번호를 절대 저장하지 않음
password = "myPassword123"
hashed = hash_password(password)  # $2b$12$xq9GIF...

# DB에는 해시만 저장
user.hashed_password = hashed
```

**왜 안전한가?**
- 해시는 일방향 암호화 (복호화 불가능)
- 같은 비밀번호도 매번 다른 해시 생성 (salt 사용)
- 해커가 DB를 탈취해도 원본 비밀번호를 알 수 없음

---

### 2. JWT 토큰
```python
# Access Token (1시간)
{
  "user_id": 1,
  "email": "test@company.com",
  "role": "client",
  "exp": 1768894940  # 만료 시간
}

# Refresh Token (7일)
{
  "user_id": 1,
  "email": "test@company.com",
  "type": "refresh",
  "exp": 1769496140
}
```

**왜 안전한가?**
- 서버에 세션 저장 불필요 (Stateless)
- 토큰에 서명이 있어 위조 불가능
- 만료 시간이 있어 탈취되어도 제한적 피해

---

### 3. 환경 변수 (.env)
```env
JWT_SECRET_KEY="6mKbc4canTK3OKkvlDwkXsyYUnawCd58fcpTmZYwV3U"
DB_URL="postgresql://user:pass@host:port/db"
```

**왜 안전한가?**
- 비밀키를 코드에 하드코딩하지 않음
- Git에 커밋되지 않음 (.gitignore)
- 배포 환경마다 다른 키 사용 가능

---

## 📊 데이터 흐름 다이어그램

```
┌─────────────┐
│  클라이언트  │ (웹/앱)
└──────┬──────┘
       │ HTTP 요청
       ↓
┌─────────────────────────────────┐
│     FastAPI 서버 (main_v2.py)    │
│  ┌───────────────────────────┐  │
│  │ auth_routes_v2.py         │  │
│  │ (API 엔드포인트)           │  │
│  └───────┬───────────────────┘  │
│          │                       │
│  ┌───────↓───────────────────┐  │
│  │ auth_v2.py                │  │
│  │ (인증 로직, JWT, bcrypt)   │  │
│  └───────┬───────────────────┘  │
│          │                       │
│  ┌───────↓───────────────────┐  │
│  │ database_v2.py            │  │
│  │ (DB 모델, CRUD 함수)       │  │
│  └───────┬───────────────────┘  │
└──────────┼───────────────────────┘
           │
           ↓
    ┌──────────────┐
    │  PostgreSQL  │
    │  (데이터베이스) │
    └──────────────┘
```

---

## 🎯 핵심 개념 정리

### JWT (JSON Web Token)
- **목적**: 로그인 상태 유지
- **구조**: Header.Payload.Signature
- **특징**: 서버에 세션 저장 불필요, 확장성 좋음

### bcrypt
- **목적**: 비밀번호 안전하게 저장
- **특징**: 일방향 암호화, salt 자동 생성, 느린 속도(무차별 대입 공격 방어)

### Access Token vs Refresh Token
- **Access Token**: 짧은 수명(1시간), API 호출 시 사용
- **Refresh Token**: 긴 수명(7일), Access Token 재발급용

### Role-Based Access Control (RBAC)
- **admin**: 모든 기능 접근 가능
- **client**: 제한된 기능만 접근 가능

---

## 🚀 다음 단계

1. **이메일 발송 기능 구현**
   - 비밀번호 재설정 링크 실제 발송
   - SMTP 또는 SendGrid 연동

2. **Rate Limiting**
   - 로그인 시도 제한 (무차별 대입 공격 방어)
   - API 호출 횟수 제한

3. **로깅 및 모니터링**
   - 로그인 실패 기록
   - 의심스러운 활동 감지

4. **2FA (Two-Factor Authentication)**
   - OTP 인증 추가
   - 보안 강화

---

