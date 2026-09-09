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
    user_info = verify_google_token(request.google_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="유효하지 않은 Google 토큰입니다")

    user, _ = get_or_create_user(
        db=db,
        google_id=user_info["sub"],
        email=user_info["email"],
        name=user_info.get("name", user_info["email"]),
        picture=user_info.get("picture")
    )

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
async def get_current_user(request: Request):
    await auth_middleware(request)
    user_data = request.state.user
    return {
        "user_id": user_data.get("user_id"),
        "email": user_data.get("email"),
        "nickname": user_data.get("nickname")
    }
