# 인증 시스템 V2 API 문서

## 개요
이메일/비밀번호 기반 인증 시스템 (Google OAuth 대체)

## 주요 기능
- ✅ 이메일 기반 회원가입/로그인 (UMS-AUT-01)
- ✅ JWT Access Token (1시간) / Refresh Token (7일)
- ✅ bcrypt 비밀번호 해싱 (UMS-AUT-04)
- ✅ 비밀번호 재설정 (UMS-AUT-03)
- ✅ Role 기반 권한 관리 (admin/client) (UMS-AUT-02)

## 데이터베이스 구조

### users 테이블
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'client',
    is_active BOOLEAN DEFAULT TRUE,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP WITH TIME ZONE,
    reset_token TEXT,
    reset_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### companies 테이블
```sql
CREATE TABLE companies (
    company_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## API 엔드포인트

### 1. 회원가입 (Client만 가능)
**POST** `/auth/v2/signup`

**요청 본문:**
```json
{
  "email": "user@company.com",
  "password": "securePassword123!",
  "company_name": "회사명",
  "contact_email": "contact@company.com",
  "contact_phone": "010-1234-5678"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@company.com",
  "role": "client"
}
```

### 2. 로그인
**POST** `/auth/v2/login`

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
  "user_id": 1,
  "email": "user@company.com",
  "role": "client"
}
```

### 3. 로그아웃
**POST** `/auth/v2/logout`

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

### 4. 토큰 갱신
**POST** `/auth/v2/refresh`

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
  "user_id": 1,
  "email": "user@company.com",
  "role": "client"
}
```

### 5. 현재 사용자 정보 조회
**GET** `/auth/v2/me`

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "user_id": 1,
  "email": "user@company.com",
  "role": "client",
  "company_id": 1,
  "company_name": "회사명",
  "is_active": true
}
```

### 6. 비밀번호 재설정 요청
**POST** `/auth/v2/password-reset/request`

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

### 7. 비밀번호 재설정 확인
**POST** `/auth/v2/password-reset/confirm`

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

## 보안 사항

### 비밀번호 요구사항
- 최소 8자 이상
- bcrypt로 해싱 저장 (UMS-AUT-04)

### 토큰 유효기간
- Access Token: 1시간 (UMS-AUT-04)
- Refresh Token: 7일 (작업내용 3번)
- 비밀번호 재설정 토큰: 1시간

### 환경 변수 (.env)
```env
JWT_SECRET_KEY=your-secret-key-here
DB_URL=postgresql://user:password@localhost:5432/dbname
```

## 실행 방법

### 1. 의존성 설치
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose bcrypt python-dotenv pydantic[email]
```

### 2. 데이터베이스 초기화
```bash
psql -U postgres -d your_database -f create_tables_v2.sql
```

### 3. 서버 실행
```bash
cd scripts
python main_v2.py
```

### 4. API 문서 확인
브라우저에서 `http://localhost:8000/docs` 접속

### 5. 테스트 실행
```bash
python test_auth_v2.py
```

## 에러 코드

| 상태 코드 | 설명 |
|---------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (이메일 중복 등) |
| 401 | 인증 실패 (토큰 만료, 잘못된 비밀번호) |
| 403 | 권한 없음 (비활성화된 계정) |
| 404 | 리소스 없음 |

## 권한 관리 (UMS-AUT-02)

### Role 종류
- **admin**: 모든 기능 접근 가능
- **client**: 자사 영상 조회 및 제작 요청만 가능

### 권한 확인 예시
```python
from auth_v2 import require_role

@router.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    # Admin만 접근 가능
    await require_role(request, ["admin"])
    return {"message": "관리자 대시보드"}
```

## 다음 단계
- [ ] 이메일 발송 기능 구현 (비밀번호 재설정)
- [ ] Rate Limiting 추가
- [ ] 로그인 시도 제한
- [ ] 2FA (Two-Factor Authentication) 추가
