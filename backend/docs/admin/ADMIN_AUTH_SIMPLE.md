# Admin 계정 인증 가이드 (간소화 버전)

Admin과 Client 모두 **비밀번호 로그인**을 사용합니다. Google OAuth는 YouTube 업로드 시에만 사용됩니다.

---

## 로그인 방식

### Client (일반 사용자)
- **회원가입**: `POST /api/v1/auth/signup`
- **로그인**: `POST /api/v1/auth/login`
- **인증 방식**: 이메일/비밀번호

### Admin (관리자)
- **회원가입**: 스크립트로 생성 (`python scripts/create_admin.py`)
- **로그인**: `POST /api/v1/auth/login` (Client와 동일)
- **인증 방식**: 이메일/비밀번호

---

## Admin 계정 생성

### 스크립트 사용

```bash
python scripts/create_admin.py
```

**입력:**
```
Admin 이메일: admin@meme-fluencer.com
비밀번호: admin123
비밀번호 확인: admin123
Admin 이름: Test Admin
```

**결과:**
```
✅ Admin 계정이 생성되었습니다!
   이메일: admin@meme-fluencer.com
   이름: Test Admin
   Account ID: 1
```

---

## 로그인

### Client와 Admin 모두 동일한 엔드포인트 사용

**엔드포인트**: `POST /api/v1/auth/login`

**요청:**
```json
{
  "email": "admin@meme-fluencer.com",
  "password": "admin123"
}
```

**응답 (Admin):**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "account_id": 1,
  "email": "admin@meme-fluencer.com",
  "account_type": "admin",
  "company_id": null,
  "role": null
}
```

**응답 (Client):**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "account_id": 10,
  "email": "user@example.com",
  "account_type": "client",
  "company_id": 5,
  "role": "manager"
}
```

**차이점:**
- Admin: `company_id`, `role`이 `null`
- Client: `company_id`, `role`이 필수

---

## 프론트엔드 구현

### 로그인 화면 분리 (권장)

#### Client 로그인 (`/login`)

```tsx
function ClientLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    // Client만 허용
    if (data.account_type !== 'client') {
      alert('일반 사용자 로그인 화면입니다');
      return;
    }
    
    localStorage.setItem('access_token', data.access_token);
    router.push('/dashboard');
  };
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin(email, password);
    }}>
      <h1>로그인</h1>
      <input type="email" placeholder="이메일" />
      <input type="password" placeholder="비밀번호" />
      <button>로그인</button>
    </form>
  );
}
```

#### Admin 로그인 (`/admin/login`)

```tsx
function AdminLogin() {
  const handleLogin = async (email: string, password: string) => {
    const response = await fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    // Admin만 허용
    if (data.account_type !== 'admin') {
      alert('관리자 로그인 화면입니다');
      return;
    }
    
    localStorage.setItem('access_token', data.access_token);
    router.push('/admin/dashboard');
  };
  
  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin(email, password);
    }}>
      <h1>관리자 로그인</h1>
      <input type="email" placeholder="이메일" />
      <input type="password" placeholder="비밀번호" />
      <button>로그인</button>
    </form>
  );
}
```

---

## Google OAuth는 언제 사용?

### YouTube 업로드 시에만 사용

Admin이 로그인한 후, **설정 페이지**에서 YouTube 채널을 연동할 때 Google OAuth를 사용합니다.

```tsx
// Admin 대시보드 > 설정
function YouTubeSettings() {
  const connectYouTube = () => {
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?
      client_id=${GOOGLE_CLIENT_ID}&
      redirect_uri=${REDIRECT_URI}&
      scope=https://www.googleapis.com/auth/youtube.upload&
      response_type=code`;
    
    window.open(authUrl, '_blank');
  };
  
  return (
    <div>
      <h2>YouTube 채널 연동</h2>
      {youtubeConnected ? (
        <p>✅ 연동됨</p>
      ) : (
        <button onClick={connectYouTube}>
          YouTube 채널 연동하기
        </button>
      )}
    </div>
  );
}
```

---

## DB 구조

### Admin 테이블

```sql
CREATE TABLE admins (
    admin_id SERIAL PRIMARY KEY,
    account_id INT REFERENCES accounts(account_id),
    name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    rt_expires_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

**특징:**
- `hashed_password` 필수
- OAuth 필드 없음 (단순화)

---

## API 명세

### 로그인 (Client & Admin 공통)

```
POST /api/v1/auth/login
Content-Type: application/json

Request:
{
  "email": "admin@meme-fluencer.com",
  "password": "admin123"
}

Response (200 OK):
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "account_id": 1,
  "email": "admin@meme-fluencer.com",
  "account_type": "admin",
  "company_id": null,
  "role": null
}

Errors:
- 401: 이메일 또는 비밀번호 오류
- 403: 비활성화된 계정
```

---

## 요약

| 구분 | Client | Admin |
|------|--------|-------|
| **회원가입** | API (`/signup`) | 스크립트 |
| **로그인 API** | `/api/v1/auth/login` | `/api/v1/auth/login` (동일) |
| **로그인 방식** | 이메일/비밀번호 | 이메일/비밀번호 |
| **로그인 화면** | `/login` | `/admin/login` |
| **company_id** | 필수 | null |
| **role** | 필수 | null |
| **Google OAuth** | ❌ 없음 | ❌ 로그인에는 없음 (YouTube 연동 시에만) |

---

## 관련 파일

- 모델: `app/models/account.py`
- API: `app/api/v1/endpoints/auth.py`
- 스크립트: `scripts/create_admin.py`
- 스키마: `app/schemas/auth.py`
