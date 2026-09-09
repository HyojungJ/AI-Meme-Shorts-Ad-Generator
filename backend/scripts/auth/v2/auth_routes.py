"""
인증 API 엔드포인트 V2
작업내용 2번: 회원가입/로그인 API 구현
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from datetime import datetime

from auth_v2 import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    auth_middleware_v2,
    generate_reset_token,
    create_reset_token_expiry
)
from database_v2 import (
    get_db,
    get_user_by_email,
    get_user_by_id,
    create_user,
    create_company,
    update_user_refresh_token,
    update_user_reset_token,
    clear_user_reset_token,
    update_user_password,
    get_user_by_reset_token
)

router = APIRouter(prefix="/auth/v2", tags=["인증 V2"])


# ============================================
# 요청/응답 모델
# ============================================
class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="최소 8자 이상")
    company_name: str = Field(..., min_length=1, max_length=100)
    contact_email: EmailStr
    contact_phone: str = None


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    role: str


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
    user_id: int
    email: str
    role: str
    company_id: int
    company_name: str
    is_active: bool


# ============================================
# 1. 회원가입 (Client만 가능)
# ============================================
@router.post("/signup", response_model=TokenResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    회원가입 엔드포인트 (Client만 가능)
    UMS-AUT-01: 이메일 기반 회원가입
    작업내용 2번: 회원가입 엔드포인트 구현
    """
    # 1. 이메일 중복 확인
    existing_user = get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    # 2. 회사 생성
    company = create_company(
        db=db,
        name=request.company_name,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone
    )
    
    # 3. 비밀번호 해싱 (UMS-AUT-04)
    hashed_pw = hash_password(request.password)
    
    # 4. 사용자 생성 (role은 기본값 'client')
    user = create_user(
        db=db,
        company_id=company.company_id,
        email=request.email,
        hashed_password=hashed_pw,
        role="client"
    )
    
    # 5. JWT 토큰 발급
    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "company_id": user.company_id
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # 6. Refresh Token DB 저장
    rt_expires = datetime.utcnow()
    from datetime import timedelta
    rt_expires += timedelta(days=7)
    update_user_refresh_token(db, user.user_id, refresh_token, rt_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.user_id,
        email=user.email,
        role=user.role
    )


# ============================================
# 2. 로그인
# ============================================
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 엔드포인트
    UMS-AUT-01: JWT 토큰 기반 인증
    작업내용 2번: 로그인 엔드포인트 구현
    """
    # 1. 사용자 조회
    user = get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")
    
    # 2. 비밀번호 검증
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")
    
    # 3. 계정 활성화 확인
    if not user.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
    
    # 4. JWT 토큰 발급
    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "company_id": user.company_id
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # 5. Refresh Token DB 저장
    from datetime import timedelta
    rt_expires = datetime.utcnow() + timedelta(days=7)
    update_user_refresh_token(db, user.user_id, refresh_token, rt_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.user_id,
        email=user.email,
        role=user.role
    )


# ============================================
# 3. 로그아웃
# ============================================
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """
    로그아웃 엔드포인트
    작업내용 2번: 로그아웃 엔드포인트 구현
    """
    # 토큰 검증
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # Refresh Token 삭제
    user = get_user_by_id(db, user_info["user_id"])
    if user:
        user.refresh_token = None
        user.rt_expires_at = None
        db.commit()
    
    return {"message": "로그아웃 되었습니다"}


# ============================================
# 4. 토큰 갱신
# ============================================
@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Access Token 갱신
    작업내용 3번: Refresh Token으로 Access Token 재발급
    """
    # 1. Refresh Token 검증
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
    
    # 2. 사용자 조회
    user = get_user_by_id(db, payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")
    
    # 3. DB에 저장된 Refresh Token과 비교
    if user.refresh_token != request.refresh_token:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
    
    # 4. 만료 시간 확인
    if user.rt_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="만료된 Refresh Token입니다")
    
    # 5. 새 Access Token 발급
    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "company_id": user.company_id
    }
    
    access_token = create_access_token(user_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 기존 Refresh Token 유지
        user_id=user.user_id,
        email=user.email,
        role=user.role
    )


# ============================================
# 5. 현재 사용자 정보 조회
# ============================================
@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자 정보 조회
    작업내용 2번: 현재 사용자 정보 조회 엔드포인트
    """
    # 토큰 검증
    await auth_middleware_v2(request)
    user_info = request.state.user
    
    # 사용자 상세 정보 조회
    user = get_user_by_id(db, user_info["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    return UserInfoResponse(
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        company_id=user.company_id,
        company_name=user.company.name,
        is_active=user.is_active
    )


# ============================================
# 6. 비밀번호 재설정 요청
# ============================================
@router.post("/password-reset/request")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    비밀번호 재설정 요청
    UMS-AUT-03: 이메일 기반 비밀번호 재설정
    작업내용 2번: 비밀번호 재설정 엔드포인트
    """
    # 1. 사용자 조회
    user = get_user_by_email(db, request.email)
    if not user:
        # 보안상 사용자 존재 여부를 노출하지 않음
        return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}
    
    # 2. 재설정 토큰 생성
    reset_token = generate_reset_token()
    expires_at = create_reset_token_expiry()
    
    # 3. DB에 저장
    update_user_reset_token(db, user.user_id, reset_token, expires_at)
    
    # 4. 이메일 발송 (TODO: 실제 이메일 발송 로직 구현)
    print(f"[이메일 발송] {user.email}에게 재설정 링크 발송")
    print(f"재설정 토큰: {reset_token}")
    
    return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}


# ============================================
# 7. 비밀번호 재설정 확인
# ============================================
@router.post("/password-reset/confirm")
def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    비밀번호 재설정 확인 및 변경
    UMS-AUT-03: 비밀번호 재설정
    """
    # 1. 재설정 토큰으로 사용자 조회
    user = get_user_by_reset_token(db, request.reset_token)
    if not user:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 재설정 토큰입니다")
    
    # 2. 새 비밀번호 해싱
    new_hashed_pw = hash_password(request.new_password)
    
    # 3. 비밀번호 업데이트
    update_user_password(db, user.user_id, new_hashed_pw)
    
    # 4. 재설정 토큰 삭제
    clear_user_reset_token(db, user.user_id)
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}
