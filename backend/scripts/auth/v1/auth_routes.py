# 인증 관련 API 엔드포인트
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from user_auth_api import verify_google_token, create_access_token, auth_middleware
from database_user import get_db, get_or_create_user

router = APIRouter(prefix="/auth", tags=["인증"])


# 요청 모델
class GoogleLoginRequest(BaseModel):
    google_token: str


# 응답 모델
class LoginResponse(BaseModel):
    access_token: str
    user_id: int
    email: str
    nickname: str
    profile_img: str = None


@router.post("/login", response_model=LoginResponse)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Google OAuth 로그인
    
    1. Google 토큰 검증
    2. 사용자 조회 또는 생성
    3. JWT 토큰 발급
    """
    # 1. Google 토큰 검증
    user_info = verify_google_token(request.google_token)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="유효하지 않은 Google 토큰입니다")
    
    # 2. 사용자 조회 또는 생성
    user, is_new = get_or_create_user(
        db=db,
        google_id=user_info["sub"],
        email=user_info["email"],
        name=user_info.get("name", user_info["email"]),
        picture=user_info.get("picture")
    )
    
    # 3. JWT 토큰 발급
    access_token = create_access_token({
        "user_id": user.user_id,
        "email": user.email,
        "nickname": user.nickname
    })
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.user_id,
        email=user.email,
        nickname=user.nickname,
        profile_img=user.profile_img
    )


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    현재 로그인한 사용자 정보 조회
    
    Authorization 헤더에 JWT 토큰 필요
    """
    # 토큰 검증
    await auth_middleware(request)
    
    # 검증된 사용자 정보
    user_data = request.state.user
    
    return {
        "user_id": user_data.get("user_id"),
        "email": user_data.get("email"),
        "nickname": user_data.get("nickname")
    }
