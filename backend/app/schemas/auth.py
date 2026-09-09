"""
인증 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


from typing import Optional


class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="최소 8자 이상")
    company_name: str = Field(..., min_length=1, max_length=100)
    member_name: str = Field(..., min_length=1, max_length=100, description="담당자 이름")
    department: Optional[str] = Field(None, max_length=100, description="부서명 (선택)")


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    account_id: int
    email: str
    account_type: str
    company_id: Optional[int] = None
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인"""
    reset_token: str
    new_password: str = Field(..., min_length=8)


class UserInfoResponse(BaseModel):
    """사용자 정보 응답"""
    account_id: int
    email: str
    account_type: str
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    member_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool


class UpdateProfileRequest(BaseModel):
    """프로필 수정 요청"""
    member_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class UpdatePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str = Field(..., min_length=8)



class UpdateUserRequest(BaseModel):
    """회원정보 수정 요청"""
    member_name: Optional[str] = Field(None, min_length=1, max_length=100, description="회원 이름")
    department: Optional[str] = Field(None, max_length=100, description="부서명")
    company_name: Optional[str] = Field(None, min_length=1, max_length=100, description="회사명")
    password: Optional[str] = Field(None, min_length=8, description="새 비밀번호")
    current_password: Optional[str] = Field(None, description="현재 비밀번호 (비밀번호 변경 시 필수)")


class UpdateUserResponse(BaseModel):
    """회원정보 수정 응답"""
    account_id: int
    email: str
    account_type: str
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    role: Optional[str] = None
    member_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    message: str
