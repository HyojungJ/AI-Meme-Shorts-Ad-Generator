"""
인증 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserInfoResponse,
    UpdateUserRequest,
    UpdateUserResponse
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    generate_reset_token,
    create_reset_token_expiry
)
from app.crud.auth import (
    get_account_by_email,
    get_account_by_id,
    get_client_by_account_id,
    get_client_by_reset_token,
    create_client_with_company,
    update_client_refresh_token,
    update_client_reset_token,
    clear_client_reset_token,
    update_client_password,
    get_user_info,
    update_user_profile
)
from app.db.session import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/signup", response_model=TokenResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """회원가입"""

    # Mock 모드: DB 없이 테스트
    if settings.MOCK_MODE:
        user_data = {
            "account_id": 1,
            "email": request.email,
            "account_type": "client",
            "company_id": 1,
            "role": "manager"
        }

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=1,
            email=request.email,
            account_type="client",
            company_id=1,
            role="manager"
        )

    # 이메일 중복 확인
    existing_account = get_account_by_email(db, request.email)
    if existing_account:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    # 비밀번호 해싱
    hashed_pw = hash_password(request.password)

    # Account + Client + Company + CompanyMember 생성
    result = create_client_with_company(
        db=db,
        email=request.email,
        hashed_password=hashed_pw,
        company_name=request.company_name,
        member_name=request.member_name,
        department=request.department,
        role='member'  # 모든 사용자를 member로 통일
    )

    account = result['account']
    company = result['company']
    member = result['member']

    # JWT 토큰 발급
    user_data = {
        "account_id": account.account_id,
        "email": account.email,
        "account_type": account.account_type,
        "company_id": company.company_id,
        "role": member.role
    }

    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    # Refresh Token DB 저장
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


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """로그인 (Client 및 Admin)"""

    # Mock 모드: DB 없이 테스트
    if settings.MOCK_MODE:
        # Mock Admin 로그인
        if request.email == "admin@meme-fluencer.com" and request.password == "admin123":
            user_data = {
                "account_id": 999,
                "email": request.email,
                "account_type": "admin",
                "company_id": None,
                "role": None
            }

            access_token = create_access_token(user_data)
            refresh_token = create_refresh_token(user_data)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                account_id=999,
                email=request.email,
                account_type="admin",
                company_id=None,
                role=None
            )

        # Mock Client 로그인
        user_data = {
            "account_id": 1,
            "email": request.email,
            "account_type": "client",
            "company_id": 1,
            "role": "manager"
        }

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=1,
            email=request.email,
            account_type="client",
            company_id=1,
            role="manager"
        )

    # 계정 조회
    account = get_account_by_email(db, request.email)
    if not account:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")

    # 계정 활성화 확인
    if not account.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다")

    # Admin 로그인
    if account.account_type == 'admin':
        from app.models.account import Admin

        admin = db.query(Admin).filter(Admin.account_id == account.account_id).first()
        if not admin:
            raise HTTPException(status_code=401, detail="Admin 정보를 찾을 수 없습니다")

        # 비밀번호 검증
        if not verify_password(request.password, admin.hashed_password):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")

        # JWT 토큰 발급 (Admin은 company_id, role이 없음)
        user_data = {
            "account_id": account.account_id,
            "email": account.email,
            "account_type": account.account_type,
            "company_id": None,
            "role": None
        }

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        # Refresh Token DB 저장
        rt_expires = datetime.utcnow() + timedelta(days=7)
        admin.refresh_token = refresh_token
        admin.rt_expires_at = rt_expires
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            account_id=account.account_id,
            email=account.email,
            account_type=account.account_type,
            company_id=None,
            role=None
        )

    # Client 로그인
    elif account.account_type == 'client':
        # Client 정보 조회
        client = get_client_by_account_id(db, account.account_id)
        if not client:
            raise HTTPException(status_code=401, detail="클라이언트 정보를 찾을 수 없습니다")

        # 비밀번호 검증
        if not verify_password(request.password, client.hashed_password):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다")

        # 사용자 정보 조회
        user_info = get_user_info(db, account.account_id)
        if not user_info or not user_info['member']:
            raise HTTPException(status_code=500, detail="회사 정보를 찾을 수 없습니다")

        member = user_info['member']
        company = user_info['company']

        # JWT 토큰 발급
        user_data = {
            "account_id": account.account_id,
            "email": account.email,
            "account_type": account.account_type,
            "company_id": company.company_id,
            "role": member.role
        }

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        # Refresh Token DB 저장
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

    else:
        raise HTTPException(status_code=401, detail="유효하지 않은 계정 유형입니다")


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    """로그아웃"""
    user_info = await get_current_user(request)

    # Refresh Token 삭제
    client = get_client_by_account_id(db, user_info["account_id"])
    if client:
        client.refresh_token = None
        client.rt_expires_at = None
        db.commit()

    return {"message": "로그아웃 되었습니다"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Access Token 갱신"""
    # Refresh Token 검증
    try:
        payload = verify_token(request.refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")

    # 계정 조회
    account = get_account_by_id(db, payload["account_id"])
    if not account:
        raise HTTPException(status_code=401, detail="계정을 찾을 수 없습니다")

    # Client 조회
    client = get_client_by_account_id(db, account.account_id)
    if not client:
        raise HTTPException(status_code=401, detail="클라이언트 정보를 찾을 수 없습니다")

    # DB에 저장된 Refresh Token과 비교
    if client.refresh_token != request.refresh_token:
        raise HTTPException(status_code=401, detail="유효하지 않은 Refresh Token입니다")

    # 만료 시간 확인
    if client.rt_expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="만료된 Refresh Token입니다")

    # 사용자 정보 조회
    user_info = get_user_info(db, account.account_id)
    if not user_info or not user_info['member']:
        raise HTTPException(status_code=500, detail="회사 정보를 찾을 수 없습니다")

    member = user_info['member']
    company = user_info['company']

    # 새 Access Token 발급
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
        refresh_token=request.refresh_token,
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id,
        role=member.role
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user_info(request: Request, db: Session = Depends(get_db)):
    """현재 로그인한 사용자 정보 조회"""
    user_info_token = await get_current_user(request)

    # Mock 모드: DB 없이 테스트
    if settings.MOCK_MODE:
        return UserInfoResponse(
            account_id=user_info_token["account_id"],
            email=user_info_token["email"],
            account_type=user_info_token["account_type"],
            company_id=user_info_token.get("company_id", 1),
            company_name="테스트회사",
            role=user_info_token.get("role", "manager"),
            member_name="홍길동",
            department="마케팅팀",  # None이 아닌 기본값
            is_active=True
        )

    # 사용자 상세 정보 조회
    user_info = get_user_info(db, user_info_token["account_id"])
    if not user_info:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    account = user_info['account']

    # Admin 계정 처리
    if account.account_type == 'admin':
        return UserInfoResponse(
            account_id=account.account_id,
            email=account.email,
            account_type=account.account_type,
            company_id=None,
            company_name=None,
            role="admin",
            member_name="Admin",
            department=None,
            is_active=account.is_active
        )

    # Client 계정 처리
    member = user_info.get('member')
    company = user_info.get('company')

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


@router.post("/password-reset/request")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """비밀번호 재설정 요청"""
    # 계정 조회
    account = get_account_by_email(db, request.email)
    if not account or account.account_type != 'client':
        return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}

    # 재설정 토큰 생성
    reset_token = generate_reset_token()
    expires_at = create_reset_token_expiry()

    # DB에 저장
    update_client_reset_token(db, account.account_id, reset_token, expires_at)

    # 이메일 발송 (TODO: 실제 이메일 발송 로직 구현)
    logger.info("비밀번호 재설정 요청: %s", account.email)

    # 개발 모드: 토큰을 응답에 포함 (프로덕션에서는 제거!)
    if settings.MOCK_MODE:
        return {
            "message": "비밀번호 재설정 이메일이 발송되었습니다",
            "reset_token": reset_token,  # 개발용
            "expires_at": expires_at.isoformat()  # 개발용
        }

    return {"message": "비밀번호 재설정 이메일이 발송되었습니다"}


@router.post("/password-reset/confirm")
def confirm_password_reset(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """비밀번호 재설정 확인 및 변경"""
    # 재설정 토큰으로 클라이언트 조회
    client = get_client_by_reset_token(db, request.reset_token)
    if not client:
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 재설정 토큰입니다")

    # 새 비밀번호 해싱
    new_hashed_pw = hash_password(request.new_password)

    # 비밀번호 업데이트
    update_client_password(db, client.account_id, new_hashed_pw)

    # 재설정 토큰 삭제
    clear_client_reset_token(db, client.account_id)

    return {"message": "비밀번호가 성공적으로 변경되었습니다"}


@router.patch("/me", response_model=UpdateUserResponse)
async def update_user_info(
    request: Request,
    update_request: UpdateUserRequest,
    db: Session = Depends(get_db)
):
    """회원정보 수정 (프로필 및 비밀번호)"""
    user_info_token = await get_current_user(request)

    # Client만 정보 수정 가능
    if user_info_token["account_type"] != "client":
        raise HTTPException(status_code=403, detail="Client만 회원정보를 수정할 수 있습니다")

    # 비밀번호 변경 요청 시 current_password 필수 확인
    if update_request.password and not update_request.current_password:
        raise HTTPException(
            status_code=400,
            detail="비밀번호를 변경하려면 현재 비밀번호를 입력해야 합니다"
        )

    # 비밀번호 변경 처리
    if update_request.password and update_request.current_password:
        client = get_client_by_account_id(db, user_info_token["account_id"])
        if not client:
            raise HTTPException(status_code=404, detail="클라이언트를 찾을 수 없습니다")

        # 현재 비밀번호 확인
        if not verify_password(update_request.current_password, client.hashed_password):
            raise HTTPException(status_code=401, detail="현재 비밀번호가 일치하지 않습니다")

        # 새 비밀번호 해싱 및 업데이트
        new_hashed_pw = hash_password(update_request.password)
        update_client_password(db, user_info_token["account_id"], new_hashed_pw)

    # 프로필 업데이트 (member_name, department, company_name)
    if update_request.member_name is not None or update_request.department is not None or update_request.company_name is not None:
        updated_member = update_user_profile(
            db,
            user_info_token["account_id"],
            member_name=update_request.member_name,
            department=update_request.department,
            company_name=update_request.company_name
        )

        if not updated_member:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    # 업데이트된 정보 조회
    user_info = get_user_info(db, user_info_token["account_id"])
    if not user_info:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    account = user_info['account']
    member = user_info['member']
    company = user_info['company']

    return UpdateUserResponse(
        account_id=account.account_id,
        email=account.email,
        account_type=account.account_type,
        company_id=company.company_id if company else None,
        company_name=company.company_name if company else None,
        role=member.role if member else None,
        member_name=member.member_name if member else None,
        department=member.department if member else None,
        is_active=account.is_active,
        message="회원 정보가 수정되었습니다"
    )


