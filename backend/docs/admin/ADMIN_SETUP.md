# Admin 계정 설정 가이드

## Admin 계정 생성 방법

Admin 계정은 보안상 일반 회원가입 API를 통해 생성할 수 없습니다. 다음 방법 중 하나를 사용하세요.

---

## 방법 1: 스크립트 사용 (권장)

초기 Admin 계정 생성 스크립트를 실행합니다.

### 실행 방법

```bash
# 프로젝트 루트에서 실행
python scripts/create_admin.py
```

### 입력 정보

스크립트 실행 시 다음 정보를 입력합니다:

1. **Admin 이메일**: 로그인에 사용할 이메일 주소
2. **비밀번호**: 최소 8자 이상 권장
3. **비밀번호 확인**: 비밀번호 재입력
4. **Admin 이름**: 관리자 이름 (기본값: System Admin)

### 실행 예시

```
============================================================
Admin 계정 생성 스크립트
============================================================

Admin 이메일: admin@example.com
비밀번호: ********
비밀번호 확인: ********
Admin 이름 (기본값: System Admin): Super Admin

입력 정보:
  이메일: admin@example.com
  이름: Super Admin

Admin 계정을 생성하시겠습니까? (y/n): y

✅ Admin 계정이 생성되었습니다!
   이메일: admin@example.com
   이름: Super Admin
   Account ID: 1
```

---

## 방법 2: 직접 DB에 삽입

PostgreSQL에 직접 접속하여 Admin 계정을 생성합니다.

### SQL 스크립트

```sql
-- 1. Account 생성
INSERT INTO accounts (
    email,
    account_type,
    status,
    is_active,
    is_email_verified,
    email_verified_at,
    created_at,
    updated_at
) VALUES (
    'admin@example.com',
    'admin',
    'active',
    true,
    true,
    NOW(),
    NOW(),
    NOW()
) RETURNING account_id;

-- 2. Admin 생성 (위에서 반환된 account_id 사용)
INSERT INTO admins (
    account_id,
    name,
    hashed_password,
    created_at,
    updated_at
) VALUES (
    1,  -- 위에서 생성된 account_id
    'System Admin',
    '$2b$12$...',  -- bcrypt 해시된 비밀번호
    NOW(),
    NOW()
);
```

**주의**: `hashed_password`는 bcrypt로 해시된 값이어야 합니다.

### 비밀번호 해시 생성

Python으로 비밀번호 해시를 생성할 수 있습니다:

```python
from app.core.security import hash_password

password = "your_password_here"
hashed = hash_password(password)
print(hashed)
```

---

## Admin 로그인

Admin 계정 생성 후 일반 로그인 API를 사용합니다.

### API 엔드포인트

```
POST /api/v1/auth/login
```

### 요청 예시

```json
{
  "email": "admin@example.com",
  "password": "your_password"
}
```

### 응답 예시

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "account_id": 1,
  "email": "admin@example.com",
  "account_type": "admin",
  "company_id": null,
  "role": null
}
```

**주의**: Admin은 `company_id`와 `role`이 `null`입니다.

---

## Admin 권한 확인

모든 Admin API는 자동으로 권한을 확인합니다.

### 권한 체크 로직

```python
if user_info.get("account_type") != 'admin':
    raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
```

### Admin 전용 API 목록

- `/api/v1/admin/*` - 모든 Admin 관리 API
- `/api/v1/admin/analytics/*` - 성과 분석 API
- `/api/v1/admin/users/*` - 사용자 관리 API
- `/api/v1/admin/costs/*` - 비용 관리 API
- `/api/v1/admin/quality/*` - 품질 관리 API

---

## 보안 권장사항

### 1. 강력한 비밀번호 사용

- 최소 12자 이상
- 대소문자, 숫자, 특수문자 조합
- 사전에 있는 단어 사용 금지

### 2. 이메일 보안

- 업무용 이메일 사용
- 2단계 인증 활성화 (이메일 계정)

### 3. 접근 제한

- Admin 계정 수를 최소화
- 필요한 사람에게만 부여
- 퇴사자 계정 즉시 비활성화

### 4. 정기적인 비밀번호 변경

- 3개월마다 비밀번호 변경 권장
- 비밀번호 재사용 금지

### 5. 로그 모니터링

- Admin 활동 로그 정기 확인
- 비정상적인 접근 패턴 감지

---

## 문제 해결

### Q: 스크립트 실행 시 "ModuleNotFoundError" 발생

**A**: 프로젝트 루트에서 실행하고 있는지 확인하세요.

```bash
# 현재 위치 확인
pwd

# 프로젝트 루트로 이동
cd /path/to/backend

# 스크립트 실행
python scripts/create_admin.py
```

### Q: "이미 존재하는 이메일입니다" 오류

**A**: 해당 이메일로 이미 계정이 생성되어 있습니다. 다른 이메일을 사용하거나 기존 계정을 삭제하세요.

```sql
-- 기존 계정 삭제 (주의!)
DELETE FROM admins WHERE account_id = (
    SELECT account_id FROM accounts WHERE email = 'admin@example.com'
);
DELETE FROM accounts WHERE email = 'admin@example.com';
```

### Q: Admin 로그인 시 "클라이언트 계정만 로그인 가능합니다" 오류

**A**: 현재 `/api/v1/auth/login`은 client 전용입니다. Admin 로그인 엔드포인트를 별도로 만들거나, 로그인 로직을 수정해야 합니다.

**해결 방법**: `app/api/v1/endpoints/auth.py`의 `login` 함수에서 account_type 체크 부분을 수정하세요.

```python
# 기존 코드
if account.account_type != 'client':
    raise HTTPException(status_code=401, detail="클라이언트 계정만 로그인 가능합니다")

# 수정 코드
if account.account_type not in ['client', 'admin']:
    raise HTTPException(status_code=401, detail="유효하지 않은 계정 유형입니다")
```

---

## 추가 Admin 생성

초기 Admin이 생성된 후, 추가 Admin은 다음 방법으로 생성할 수 있습니다:

### 방법 1: 스크립트 재실행

```bash
python scripts/create_admin.py
```

### 방법 2: Admin API 사용 (향후 구현 예정)

```
POST /api/v1/admin/create-admin
Authorization: Bearer {admin_access_token}

{
  "email": "new_admin@example.com",
  "password": "secure_password",
  "name": "New Admin"
}
```

---

## 관련 파일

- 스크립트: `scripts/create_admin.py`
- 모델: `app/models/account.py`
- 보안: `app/core/security.py`
- 인증 API: `app/api/v1/endpoints/auth.py`
