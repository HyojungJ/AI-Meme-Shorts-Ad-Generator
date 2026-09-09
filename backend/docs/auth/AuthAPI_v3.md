# 인증 시스템 V3 API 문서

## 개요
새로운 멀티 테이블 구조 기반 인증 시스템 (accounts, clients, companies, company_members)

## 주요 기능
- ✅ 이메일 기반 회원가입/로그인 (Client 전용)
- ✅ JWT Access Token (1시간) / Refresh Token (7일)
- ✅ bcrypt 비밀번호 해싱
- ✅ 비밀번호 재설정
- ✅ 계정 타입 분리 (client/admin)
- ✅ 회사별 멤버 관리 (manager/member)
- ✅ 멀티 테이블 구조로 확장성 향상

## 데이터베이스 구조

### accounts 테이블 (계정 공통)
```sql
CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('client', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### clients 테이블 (클라이언트 전용)
```sql
CREATE TABLE clients (
    client_id SERIAL PRIMARY KEY,
    account_id INT UNIQUE NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    hashed_password VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP WITH TIME ZONE,
    reset_token TEXT,
    reset_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### admins 테이블 (어드민 전용)
```sql
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    account_id INT UNIQUE NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    oauth_provider VARCHAR(50) NOT NULL,
    oauth_provider_id VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(oauth_provider, oauth_provider_id)
);
```

### companies 테이블
```sql
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### company_members 테이블
```sql
CREATE TABLE company_members (
    member_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('manager', 'member')),
    member_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## API 엔드포인트

### 1. 회원가입 (Client만 가능)
**POST** `/auth/v3/signup`

**요청 본문:**
```json
{
  "email": "user@company.com",
  "password": "securePassword123!",
  "company_name": "회사명",
  "member_name": "홍길동",
  "department": "개발팀"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

**동작 순서:**
1. 이메일 중복 확인
2. 비밀번호 bcrypt 해싱
3. Account 생성 (account_type='client')
4. Client 생성 (hashed_password 저장)
5. Company 생성
6. CompanyMember 생성 (role='manager', is_primary=True)
7. JWT 토큰 발급 (Access + Refresh)
8. Refresh Token DB 저장

### 2. 로그인
**POST** `/auth/v3/login`

**요청 본문:**
```json
{
  "email": "user@company.com",
  "password": "securePassword123!"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

**동작 순서:**
1. 이메일로 Account 조회
2. account_type='client' 확인
3. Client 정보 조회
4. 비밀번호 검증 (bcrypt)
5. 계정 활성화 확인 (is_active)
6. CompanyMember 정보 조회 (회사, 역할)
7. JWT 토큰 발급
8. Refresh Token DB 저장 및 last_login_at 업데이트

### 3. 로그아웃
**POST** `/auth/v3/logout`

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "message": "로그아웃 되었습니다"
}
```

**동작 순서:**
1. Access Token 검증
2. Client의 Refresh Token 삭제

### 4. 토큰 갱신
**POST** `/auth/v3/refresh`

**요청 본문:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**응답:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "role": "manager"
}
```

**동작 순서:**
1. Refresh Token 검증 (JWT)
2. Account 조회
3. Client 조회
4. DB 저장된 Refresh Token과 비교
5. 만료 시간 확인 (rt_expires_at)
6. CompanyMember 정보 조회
7. 새 Access Token 발급 (Refresh Token은 유지)

### 5. 현재 사용자 정보 조회
**GET** `/auth/v3/me`

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "회사명",
  "role": "manager",
  "member_name": "홍길동",
  "department": "개발팀",
  "is_active": true
}
```

**동작 순서:**
1. Access Token 검증
2. Account, Client, CompanyMember, Company 정보 조회
3. 통합된 사용자 정보 반환

### 6. 비밀번호 재설정 요청
**POST** `/auth/v3/password-reset/request`

**요청 본문:**
```json
{
  "email": "user@company.com"
}
```

**응답:**
```json
{
  "message": "비밀번호 재설정 이메일이 발송되었습니다"
}
```

**동작 순서:**
1. 이메일로 Account 조회 (account_type='client' 확인)
2. 재설정 토큰 생성 (32바이트 랜덤)
3. 만료 시간 설정 (1시간)
4. Client 테이블에 reset_token, reset_expires_at 저장
5. 이메일 발송 (TODO: 실제 구현 필요)

### 7. 비밀번호 재설정 확인
**POST** `/auth/v3/password-reset/confirm`

**요청 본문:**
```json
{
  "reset_token": "abc123...",
  "new_password": "newSecurePassword123!"
}
```

**응답:**
```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다"
}
```

**동작 순서:**
1. reset_token으로 Client 조회 (만료 시간 확인)
2. 새 비밀번호 bcrypt 해싱
3. Client의 hashed_password 업데이트
4. reset_token, reset_expires_at 삭제

## 보안 사항

### 비밀번호 요구사항
- 최소 8자 이상
- bcrypt로 해싱 저장

### 토큰 유효기간
- Access Token: 1시간
- Refresh Token: 7일
- 비밀번호 재설정 토큰: 1시간

### 환경 변수 (.env)
```env
JWT_SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## 실행 방법

### 1. 의존성 설치
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose bcrypt python-dotenv pydantic[email]
```

### 2. 데이터베이스 초기화
```bash
# 테이블 생성 SQL 실행
psql -U postgres -d your_database -f create_tables_v3.sql
```

### 3. 서버 실행
```bash
cd scripts
python main.py
```

### 4. API 문서 확인
브라우저에서 `http://localhost:8000/docs` 접속

## 에러 코드

| 상태 코드 | 설명 |
|---------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (이메일 중복, 유효하지 않은 토큰) |
| 401 | 인증 실패 (토큰 만료, 잘못된 비밀번호) |
| 403 | 권한 없음 (비활성화된 계정, 접근 권한 없음) |
| 404 | 리소스 없음 (사용자 정보 없음) |
| 500 | 서버 오류 |

## 권한 관리

### Account Type
- **client**: 일반 사용자 (이메일/비밀번호 인증)
- **admin**: 관리자 (OAuth 인증, 향후 구현)

### Company Role
- **manager**: 회사 관리자 (모든 권한)
- **member**: 일반 멤버 (제한된 권한)

### 권한 확인 예시
```python
from auth_v3 import require_account_type, require_role

# Client만 접근 가능
@router.get("/client/dashboard")
async def client_dashboard(request: Request):
    await require_account_type(request, ["client"])
    return {"message": "클라이언트 대시보드"}

# Manager만 접근 가능
@router.post("/company/settings")
async def update_settings(request: Request):
    await require_role(request, ["manager"])
    return {"message": "설정 업데이트"}
```

## V3의 주요 변경사항

### V2 대비 개선점
1. **멀티 테이블 구조**: accounts, clients, admins 분리로 확장성 향상
2. **회사 관리**: companies, company_members 테이블로 조직 관리 가능
3. **역할 관리**: manager/member 역할로 세밀한 권한 제어
4. **계정 타입 분리**: client/admin 분리로 향후 OAuth 통합 용이
5. **Primary 멤버**: is_primary 플래그로 주 소속 회사 구분

### 데이터 구조 비교
**V2**: users 테이블 단일 구조
**V3**: accounts → clients/admins → company_members → companies (관계형 구조)

## 파일 구조

```
scripts/
├─ auth/
│  └─ v3/
│     ├─ __init__.py
│     ├─ auth_v3.py              # 인증 로직 (토큰, 비밀번호 해싱)
│     ├─ database_v3.py          # DB 모델 및 함수
│     └─ auth_routes_v3.py       # API 엔드포인트
├─ main.py                       # FastAPI 서버 실행
docs/
└─ auth/
   └─ AuthAPI_v3.md              # 이 문서
```

## 다음 단계
- [ ] Admin OAuth 인증 구현 (Google, GitHub 등)
- [ ] 이메일 발송 기능 구현 (비밀번호 재설정)
- [ ] 회사 멤버 초대 기능
- [ ] 멤버 역할 변경 API
- [ ] Rate Limiting 추가
- [ ] 로그인 시도 제한
- [ ] 2FA (Two-Factor Authentication) 추가

## 프론트엔드 연동 가이드

### 회원가입 구현
```javascript
const response = await fetch('http://localhost:8000/auth/v3/signup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'securePassword123!',
    company_name: '회사명',
    member_name: '홍길동',
    department: '개발팀'
  })
});

const data = await response.json();
// data = {access_token: "...", refresh_token: "...", account_id: 1, ...}

// 토큰 저장
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### 로그인 구현
```javascript
const response = await fetch('http://localhost:8000/auth/v3/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@company.com',
    password: 'securePassword123!'
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### API 호출 시 토큰 사용
```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/auth/v3/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const userData = await response.json();
// userData = {account_id: 1, email: "...", company_name: "...", ...}
```

### 토큰 갱신 구현
```javascript
const refreshToken = localStorage.getItem('refresh_token');

const response = await fetch('http://localhost:8000/auth/v3/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    refresh_token: refreshToken
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
// Refresh Token은 동일하게 유지
```

## 문제 해결

### 서버가 안 켜져요
```bash
# 포트가 이미 사용 중일 수 있음
# 다른 터미널에서 실행 중인 서버 종료 후 다시 시도
```

### DB 연결 안 돼요
```bash
# .env 파일의 DATABASE_URL 확인
# DB 서버가 실행 중인지 확인
```

### 토큰 검증 실패
```bash
# .env 파일의 JWT_SECRET_KEY 확인
# Access Token 만료 확인 (1시간 후 자동 만료)
# Refresh Token으로 갱신 필요
```

### 회원가입 시 이메일 중복 오류
```bash
# 이미 등록된 이메일입니다
# 다른 이메일 사용 또는 로그인 시도
```

---

## 작업 완료일

2026.01.22
