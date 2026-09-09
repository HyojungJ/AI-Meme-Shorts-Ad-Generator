# 회원정보 수정 API 개발 문서

## 개요

사용자가 자신의 프로필 정보(이름, 부서)와 비밀번호를 수정할 수 있는 API를 구현했습니다.

## 구현된 API

### 1. 프로필 정보 수정

**Endpoint**: `PATCH /api/v1/auth/me`

**설명**: 로그인한 사용자의 이름과 부서 정보를 수정합니다.

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "member_name": "홍길동",
  "department": "마케팅팀"
}
```

**필드 설명**:
- `member_name` (optional): 사용자 이름 (1-100자)
- `department` (optional): 부서명 (최대 100자)

**Response** (200):
```json
{
  "account_id": 1,
  "email": "user@company.com",
  "account_type": "client",
  "company_id": 1,
  "company_name": "회사명",
  "role": "manager",
  "member_name": "홍길동",
  "department": "마케팅팀",
  "is_active": true
}
```

**Error Responses**:
- `401 Unauthorized`: 인증 토큰이 없거나 유효하지 않음
- `404 Not Found`: 사용자를 찾을 수 없음

---

### 2. 비밀번호 변경

**Endpoint**: `PUT /api/v1/auth/me/password`

**설명**: 로그인한 사용자의 비밀번호를 변경합니다. (Client만 가능)

**Headers**:
```
Authorization: Bearer {access_token}
```

**Request Body**:
```json
{
  "current_password": "현재비밀번호",
  "new_password": "새비밀번호123"
}
```

**필드 설명**:
- `current_password` (required): 현재 비밀번호
- `new_password` (required): 새 비밀번호 (최소 8자)

**Response** (200):
```json
{
  "message": "비밀번호가 성공적으로 변경되었습니다"
}
```

**Error Responses**:
- `401 Unauthorized`: 현재 비밀번호가 일치하지 않음
- `403 Forbidden`: Admin 계정은 비밀번호 변경 불가
- `404 Not Found`: 사용자를 찾을 수 없음

---

## 구현 상세

### 스키마 (app/schemas/auth.py)

```python
class UpdateProfileRequest(BaseModel):
    """프로필 수정 요청"""
    member_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class UpdatePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str = Field(..., min_length=8)
```

### CRUD 함수 (app/crud/auth.py)

```python
def update_user_profile(db: Session, account_id: int, member_name: str = None, department: str = None):
    """사용자 프로필 업데이트"""
    members = get_company_members_by_account(db, account_id)
    primary_member = next((m for m in members if m.is_primary), members[0] if members else None)
    
    if not primary_member:
        return None
    
    if member_name is not None:
        primary_member.member_name = member_name
    if department is not None:
        primary_member.department = department
    
    primary_member.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(primary_member)
    
    return primary_member
```

### API 엔드포인트 (app/api/v1/endpoints/auth.py)

#### 프로필 수정
```python
@router.patch("/me", response_model=UserInfoResponse)
async def update_profile(
    request: Request,
    profile_request: UpdateProfileRequest,
    db: Session = Depends(get_db)
):
    """프로필 수정"""
    user_info_token = await get_current_user(request)
    
    # 프로필 업데이트
    updated_member = update_user_profile(
        db,
        user_info_token["account_id"],
        member_name=profile_request.member_name,
        department=profile_request.department
    )
    
    if not updated_member:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    # 업데이트된 정보 조회 및 반환
    # ...
```

#### 비밀번호 변경
```python
@router.put("/me/password")
async def update_password(
    request: Request,
    password_request: UpdatePasswordRequest,
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    user_info_token = await get_current_user(request)
    
    # Client만 비밀번호 변경 가능
    if user_info_token["account_type"] != "client":
        raise HTTPException(status_code=403, detail="Client만 비밀번호를 변경할 수 있습니다")
    
    # 현재 비밀번호 확인
    client = get_client_by_account_id(db, user_info_token["account_id"])
    if not verify_password(password_request.current_password, client.hashed_password):
        raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다")
    
    # 새 비밀번호로 업데이트
    # ...
```

---

## 데이터베이스 영향

### 수정되는 테이블

**company_members 테이블**:
- `member_name`: 사용자 이름 업데이트
- `department`: 부서명 업데이트
- `updated_at`: 수정 시간 자동 업데이트

**clients 테이블**:
- `hashed_password`: 비밀번호 해시값 업데이트
- `updated_at`: 수정 시간 자동 업데이트

---

## 보안 고려사항

### 1. 인증 확인
- JWT 토큰을 통해 사용자 인증
- 본인의 정보만 수정 가능

### 2. 비밀번호 변경
- 현재 비밀번호 확인 필수
- 새 비밀번호는 bcrypt로 해싱하여 저장
- Admin 계정은 비밀번호 변경 불가 (OAuth 사용)

### 3. 입력 검증
- Pydantic 스키마로 자동 검증
- 이름: 1-100자
- 부서: 최대 100자
- 비밀번호: 최소 8자

---

## 테스트 방법

### 1. 프로필 수정 테스트

```bash
# 로그인하여 토큰 획득
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "password123"
  }'

# 프로필 수정
curl -X PATCH http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "member_name": "김철수",
    "department": "개발팀"
  }'
```

### 2. 비밀번호 변경 테스트

```bash
curl -X PUT http://localhost:8000/api/v1/auth/me/password \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "password123",
    "new_password": "newpassword456"
  }'
```

---

## 프론트엔드 연동 가이드

### 프로필 수정 예시 (JavaScript)

```javascript
async function updateProfile(memberName, department) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/v1/auth/me', {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      member_name: memberName,
      department: department
    })
  });
  
  if (!response.ok) {
    throw new Error('프로필 수정 실패');
  }
  
  return await response.json();
}
```

### 비밀번호 변경 예시 (JavaScript)

```javascript
async function changePassword(currentPassword, newPassword) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/v1/auth/me/password', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '비밀번호 변경 실패');
  }
  
  return await response.json();
}
```

---

## 향후 개선 사항

1. **프로필 이미지 업로드**
   - 사용자 프로필 사진 업로드 기능
   - S3에 이미지 저장

2. **이메일 변경**
   - 이메일 변경 시 인증 메일 발송
   - 새 이메일 확인 후 변경

3. **회사 정보 수정**
   - Manager 권한 사용자가 회사명 수정 가능

4. **활동 로그**
   - 프로필 수정 이력 기록
   - 비밀번호 변경 이력 기록

---

## 관련 문서

- [인증 API 명세](../API_SPECIFICATION.md#1-인증-api-apiv1auth)
- [Admin 인증 가이드](../admin/ADMIN_AUTH_SIMPLE.md)
- [프론트엔드 연동 가이드](../FRONTEND_API_GUIDE.md)

---

**작성일**: 2026-01-24
**작성자**: Backend Team
