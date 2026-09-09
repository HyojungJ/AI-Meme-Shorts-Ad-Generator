# 회원정보 수정 API 명세서

## 엔드포인트
```
PATCH /api/v1/auth/me
```

## 설명
현재 로그인한 사용자의 회원 정보를 수정합니다.

## 인증
- **필수**: Bearer Token (JWT Access Token)
- Header: `Authorization: Bearer {access_token}`

## 요청 (Request)

### Headers
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### Request Body
```json
{
  "member_name": "홍길동",
  "department": "마케팅팀",
  "password": "newPassword123!",
  "current_password": "oldPassword123!"
}
```

### 필드 설명
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `member_name` | string | 선택 | 회원 이름 (회사 멤버 이름) |
| `department` | string | 선택 | 부서명 |
| `password` | string | 선택 | 새 비밀번호 (변경 시) |
| `current_password` | string | 조건부 | 현재 비밀번호 (비밀번호 변경 시 필수) |

**참고**: 
- 모든 필드는 선택 사항이며, 변경하고자 하는 필드만 포함하면 됩니다.
- 비밀번호를 변경하려면 `password`와 `current_password` 모두 필요합니다.

## 응답 (Response)

### 성공 응답 (200 OK)
```json
{
  "account_id": 1,
  "email": "user@example.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "ABC 마케팅",
  "role": "manager",
  "member_name": "홍길동",
  "department": "마케팅팀",
  "is_active": true,
  "message": "회원 정보가 수정되었습니다"
}
```

### 응답 필드 설명
| 필드 | 타입 | 설명 |
|------|------|------|
| `account_id` | integer | 계정 ID |
| `email` | string | 이메일 주소 |
| `account_type` | string | 계정 유형 (client, admin) |
| `company_id` | integer | 회사 ID |
| `company_name` | string | 회사명 |
| `role` | string | 권한 (manager, member) |
| `member_name` | string | 회원 이름 |
| `department` | string | 부서명 |
| `is_active` | boolean | 계정 활성화 상태 |
| `message` | string | 성공 메시지 |

### 에러 응답

#### 401 Unauthorized - 인증 실패
```json
{
  "detail": "유효하지 않은 토큰입니다"
}
```

#### 400 Bad Request - 현재 비밀번호 불일치
```json
{
  "detail": "현재 비밀번호가 일치하지 않습니다"
}
```

#### 400 Bad Request - 비밀번호 변경 시 current_password 누락
```json
{
  "detail": "비밀번호를 변경하려면 현재 비밀번호를 입력해야 합니다"
}
```

#### 404 Not Found - 사용자 정보 없음
```json
{
  "detail": "사용자를 찾을 수 없습니다"
}
```

## 예제

### 예제 1: 이름과 부서 변경
**Request**
```bash
curl -X PATCH "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "member_name": "김철수",
    "department": "영업팀"
  }'
```

**Response**
```json
{
  "account_id": 1,
  "email": "user@example.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "ABC 마케팅",
  "role": "manager",
  "member_name": "김철수",
  "department": "영업팀",
  "is_active": true,
  "message": "회원 정보가 수정되었습니다"
}
```

### 예제 2: 비밀번호 변경
**Request**
```bash
curl -X PATCH "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "password": "newSecurePassword123!",
    "current_password": "oldPassword123!"
  }'
```

**Response**
```json
{
  "account_id": 1,
  "email": "user@example.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "ABC 마케팅",
  "role": "manager",
  "member_name": "홍길동",
  "department": "마케팅팀",
  "is_active": true,
  "message": "회원 정보가 수정되었습니다"
}
```

## 구현 상태
⚠️ **현재 미구현**: 이 엔드포인트는 아직 구현되지 않았습니다.

구현이 필요한 사항:
1. `app/api/v1/endpoints/auth.py`에 PATCH `/me` 엔드포인트 추가
2. `app/crud/auth.py`에 회원 정보 수정 함수 추가
3. `app/schemas/auth.py`에 UpdateUserRequest, UpdateUserResponse 스키마 추가

## 보안 고려사항
- 비밀번호 변경 시 반드시 현재 비밀번호 확인 필요
- 비밀번호는 해싱하여 저장
- 이메일 주소는 변경 불가 (보안상 이유)
- 계정 유형(account_type)은 변경 불가
- 회사 정보(company_id, role)는 이 API로 변경 불가 (관리자 권한 필요)
