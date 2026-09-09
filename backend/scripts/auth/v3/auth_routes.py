"""
인증 API 엔드포인트 V3
새로운 스키마 적용: accounts, clients, companies, company_members
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from .auth_v3 import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    auth_middleware_v3,
    generate_reset_token,
    create_reset_token_expiry
)
from .database_v3 import (
    get_db,
    get_account_by_email,
    get_account_by_id,
    get_client_by_account_id,
    get_client_by_reset_token,
    create_client_with_company,
    update_client_refresh_token,
    update_client_reset_token,
    clear_client_reset_token,
    update_client_password,
    get_user_info
)

router = APIRouter(prefix="/auth/v3", tags=["인증 V3"])


# ============================================
# 요청/응답 모델
# ============================================
class SignupRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="최소 8자 이상")
    company_name: str = Field(..., min_length=1, max_length=100)
    member_name: str = Field(..., min_length=1, max_length=100, description="담당자 이름")
    department: str = Field(None, max_length=100, description="부서명 (선택)")


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
    company_id: int
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
    account_id: int
    email: str
    account_type: str
    company_id: int
    company_name: str
    role: str
    member_name: str
    department: str = None
    is_active: bool


# ============================================
# 1. 회원가입 (Client만 가능)
# ============================================
@router.post("/signup", response_model=TokenResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    회원가입 엔드포인트 (Client만 가능)
    Account + Client + Company + CompanyMember 생성
    """
    # 1. 이메일 중복 확인
    existing_account = get_account_by_email(db, request.email)
    if existing_account:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
    
    # 2. 비밀번호 해싱
    hashed_pw = hash_password(request.password)
    
    # 3. Account + Client + Company + CompanyMember 생성
    result = create_client_with_company(
        db=db,
        email=request.email,
        hashed_password=hashed_pw,
        company_name=request.company_name,
        member_name=request.member_name
    )
    
    account = result['account']
    company = result['company']
    member = result['member']
    
    # 4. JWT 토큰 발급
    user_data = {
        "account_id": account.account_id,
        "email": account.email,
        "account_type": account.account_type,
        "company_id": company.company_id,
        "role": member.role
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # 5. Refresh Token DB 저장
    rt_expires = datetime.utcnow() + timedelta(days=7)
    update_client_refresh_token(db, account.account_id, refresh_token, rt_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id,
        role=member.role
    )


# ============================================
# 2. 로그인
# ============================================
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 엔드포인트
    """
    # 1. 계정 조회
    account = get_account_by_email(db, request.email)
    if not account:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")
    
    # 2. 계정 타입 확인 (client만 로그인 가능)
    if account.account_type != 'client':
        raise HTTPException(status_code=401, detail="클라이언트 계정만 로그인 가능합니다")
    
    # 3. Client 정보 조회
    client = get_client_by_account_id(db, account.account_id)
    if not client:
        raise HTTPException(status_code=401, detail="클라이언트 정보를 찾을 수 없습니다")
    
    # 4. 비밀번호 검증
    if not verify_password(request.password, client.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")
    
    # 5. 계정 활성화 확인
    if not account.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")
    
    # 6. 사용자 정보 조회 (회사, 역할)
    user_info = get_user_info(db, account.account_id)
    if not user_info or not user_info['member']:
        raise HTTPException(status_code=500, detail="회사 정보를 찾을 수 없습니다")
    
    member = user_info['member']
    company = user_info['company']
    
    # 7. JWT 토큰 발급
    user_data = {
        "account_id": account.account_id,
        "email": account.email,
        "account_type": account.account_type,
        "company_id": company.company_id,
        "role": member.role
    }
    
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # 8. Refresh Token DB 저장
    rt_expires = datetime.utcnow() + timedelta(days=7)
    update_client_refresh_token(db, account.account_id, refresh_token, rt_expires)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id,
        role=member.role
    )


# ============================================
# 3. 로그아웃
# ============================================
@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """로그아웃 엔드포인트"""
    # 토큰 검증
    await auth_middleware_v3(request)
    user_info = request.state.user
    
    # Refresh Token 삭제
    client = get_client_by_account_id(db, user_info["account_id"])
    if client:
        client.refresh_token = None
        client.rt_expires_at = None
        db.commit()
    
    return {"message": "로그아웃 되었습니다"}


# ============================================
# 4. 토큰 갱신
# ============================================
@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Access Token 갱신"""
    # 1. Refresh Token 검증
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
    
    # 2. 계정 조회
    account = get_account_by_id(db, payload["account_id"])
    if not account:
        raise HTTPException(status_code=401, detail="계정을 찾을 수 없습니다")
    
    # 3. Client 조회
    client = get_client_by_account_id(db, account.account_id)
    if not client:
        raise HTTPException(status_code=401, detail="클라이언트 정보를 찾을 수 없습니다")
    
    # 4. DB에 저장된 Refresh Token과 비교
    if client.refresh_token != request.refresh_token:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")
    
    # 5. 만료 시간 확인
    if client.rt_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="만료된 Refresh Token입니다")
    
    # 6. 사용자 정보 조회
    user_info = get_user_info(db, account.account_id)
    if not user_info or not user_info['member']:
        raise HTTPException(status_code=500, detail="회사 정보를 찾을 수 없습니다")
    
    member = user_info['member']
    company = user_info['company']
    
    # 7. 새 Access Token 발급
    user_data = {
        "account_id": account.account_id,
        "email": account.email,
        "account_type": account.account_type,
        "company_id": company.company_id,
        "role": member.role
    }
    
    access_token = create_access_token(user_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # 기존 Refresh Token 유지
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id,
        role=member.role
    )


# ============================================
# 5. 현재 사용자 정보 조회
# ============================================
@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """현재 로그인한 사용자 정보 조회"""
    # 토큰 검증
    await auth_middleware_v3(request)
    user_info_token = request.state.user
    
    # 사용자 상세 정보 조회
    user_info = get_user_info(db, user_info_token["account_id"])
    if not user_info:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    
    account = user_info['account']
    member = user_info['member']
    company = user_info['company']
    
    if not member or not company:
        raise HTTPException(status_code=404, detail="회사 정보를 찾을 수 없습니다")
    
    return UserInfoResponse(
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id,
        company_name=company.company_name,
        role=member.role,
        member_name=member.member_name,
        department=member.department,
        is_active=account.is_active
    )


# ============================================
# 6. 비밀번호 재설정 요청
# ============================================
@router.post("/password-reset/request")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """비밀번호 재설정 요청"""
    # 1. 계정 조회
    account = get_account_by_email(db, request.email)
    if not account or account.account_type != 'client':
        # 보안상 계정 존재 여부를 노출하지 않음
        return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}
    
    # 2. 재설정 토큰 생성
    reset_token = generate_reset_token()
    expires_at = create_reset_token_expiry()
    
    # 3. DB에 저장
    update_client_reset_token(db, account.account_id, reset_token, expires_at)
    
    # 4. 이메일 발송 (TODO: 실제 이메일 발송 로직 구현)
    print(f"[이메일 발송] {account.email}에게 재설정 링크 발송")
    print(f"재설정 토큰: {reset_token}")
    
    return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}


# ============================================
# 7. 비밀번호 재설정 확인
# ============================================
@router.post("/password-reset/confirm")
def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """비밀번호 재설정 확인 및 변경"""
    # 1. 재설정 토큰으로 클라이언트 조회
    client = get_client_by_reset_token(db, request.reset_token)
    if not client:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 재설정 토큰입니다")
    
    # 2. 새 비밀번호 해싱
    new_hashed_pw = hash_password(request.new_password)
    
    # 3. 비밀번호 업데이트
    update_client_password(db, client.account_id, new_hashed_pw)
    
    # 4. 재설정 토큰 삭제
    clear_client_reset_token(db, client.account_id)
    
    return {"message": "비밀번호가 성공적으로 변경되었습니다"}
