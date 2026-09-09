import os
from datetime import datetime, timedelta
from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import Request, HTTPException
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # JWT 암호화 키
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # Google 클라이언트 ID
ALGORITHM = "HS256"  # JWT 암호화 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 토큰 만료 시간 (30분)


def verify_google_token(token):
    try:
        user_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        return user_info
    except Exception:
        return None


def create_access_token(user_data):
    token_data = user_data.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data["exp"] = expire_time
    return jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)


async def auth_middleware(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="토큰이 없습니다")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="토큰 형식이 잘못되었습니다")

    token = auth_header.replace("Bearer ", "")

    try:
        user_info = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        request.state.user = user_info
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
