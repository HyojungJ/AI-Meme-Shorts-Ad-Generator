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


# ============================================
# 1. Google 토큰 검증 함수
# ============================================
def verify_google_token(token):
    try:
        # Google API로 토큰 검증
        user_info = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        print(f"Google 토큰 검증 성공: {user_info.get('email')}")
        return user_info
        
    except Exception as error:
        # 검증 실패
        print(f"Google 토큰 검증 실패: {error}")
        return None

# ============================================
# 2. 우리 서비스 토큰 생성 함수
# ============================================
def create_access_token(user_data):
    # 토큰에 담을 데이터 복사
    token_data = user_data.copy()
    
    # 만료 시간 계산
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data["exp"] = expire_time
    
    # JWT 토큰 생성
    token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    print(f"JWT 토큰 생성 완료: {user_data.get('email')}")
    return token

# ============================================
# 3. 토큰 검증 미들웨어
# ============================================
async def auth_middleware(request):
    # 1. 헤더에서 Authorization 가져오기
    auth_header = request.headers.get("Authorization")
    
    # 2. 토큰이 없거나 형식이 잘못된 경우
    if not auth_header:
        raise HTTPException(status_code=401, detail="토큰이 없습니다")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="토큰 형식이 잘못되었습니다")
    
    # 3. "Bearer " 뒤의 토큰 추출
    token = auth_header.replace("Bearer ", "")
    
    # 4. 토큰 검증
    try:
        # JWT 토큰 복호화
        user_info = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        
        # 검증 성공: 사용자 정보 저장
        request.state.user = user_info
        print(f"사용자 인증 성공: {user_info.get('email')}")
        
    except jwt.ExpiredSignatureError:
        # 토큰 만료
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
        
    except jwt.JWTError:
        # 유효하지 않은 토큰
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


# ============================================
# 사용 예시
# ============================================
"""
# 1단계: 로그인 API
@app.post("/auth/login")
def login(google_token: str):
    # Google 토큰 검증
    user_info = verify_google_token(google_token)
    
    if not user_info:
        return {"error": "Google 로그인 실패"}
    
    # DB에서 사용자 찾기 (없으면 생성)
    # user = db.get_or_create_user(...)
    
    # 우리 서비스 토큰 발급
    access_token = create_access_token({
        "user_id": 123,
        "email": user_info["email"]
    })
    
    return {"access_token": access_token}


# 2단계: 보호된 API (로그인 필요)
@app.get("/api/profile")
async def get_profile(request: Request):
    # 토큰 검증
    await auth_middleware(request)
    
    # 사용자 정보 사용
    user = request.state.user
    return {"email": user["email"]}
"""
