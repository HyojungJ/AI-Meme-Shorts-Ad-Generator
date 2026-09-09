"""
인증 시스템 V3 - 새로운 스키마 적용
accounts, clients, admins 테이블 구조
"""
import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, Request
import secrets

load_dotenv()

# 환경 변수 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1  # Access Token 1시간 유효
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Refresh Token 7일 유효


# ============================================
# 1. 비밀번호 해싱 (bcrypt)
# ============================================
def hash_password(password: str) -> str:
    """비밀번호를 bcrypt로 해싱"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ============================================
# 2. JWT 토큰 생성
# ============================================
def create_access_token(user_data: dict) -> str:
    """
    Access Token 생성 (1시간 유효)
    user_data: {
        'account_id': int,
        'email': str,
        'account_type': str,
        'company_id': int,
        'role': str
    }
    """
    token_data = user_data.copy()
    expire_time = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    token_data["exp"] = expire_time
    token_data["type"] = "access"
    
    token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    print(f"Access Token 생성: {user_data.get('email')}")
    return token


def create_refresh_token(user_data: dict) -> str:
    """
    Refresh Token 생성 (7일 유효)
    """
    token_data = {
        "account_id": user_data.get("account_id"),
        "email": user_data.get("email"),
        "type": "refresh"
    }
    expire_time = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    token_data["exp"] = expire_time
    
    token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=ALGORITHM)
    print(f"Refresh Token 생성: {user_data.get('email')}")
    return token


# ============================================
# 3. 토큰 검증
# ============================================
def verify_token(token: str, token_type: str = "access") -> dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        
        # 토큰 타입 확인
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=401,
                detail=f"잘못된 토큰 타입입니다. {token_type} 토큰이 필요합니다."
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


# ============================================
# 4. 인증 미들웨어
# ============================================
async def auth_middleware_v3(request: Request):
    """
    토큰 검증 미들웨어 V3
    """
    # Authorization 헤더 확인
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="토큰 형식이 잘못되었습니다")
    
    # 토큰 추출 및 검증
    token = auth_header.replace("Bearer ", "")
    user_info = verify_token(token, token_type="access")
    
    # 사용자 정보 저장
    request.state.user = user_info
    print(f"사용자 인증 성공: {user_info.get('email')} (account_type: {user_info.get('account_type')})")


# ============================================
# 5. 권한 검증 미들웨어
# ============================================
async def require_account_type(request: Request, allowed_types: list):
    """
    특정 계정 타입만 접근 가능하도록 제한
    allowed_types: ['client', 'admin']
    """
    await auth_middleware_v3(request)
    
    user = request.state.user
    account_type = user.get("account_type")
    
    if account_type not in allowed_types:
        raise HTTPException(
            status_code=403,
            detail=f"접근 권한이 없습니다. 필요 권한: {', '.join(allowed_types)}"
        )


async def require_role(request: Request, allowed_roles: list):
    """
    특정 역할만 접근 가능하도록 제한
    allowed_roles: ['manager', 'member']
    """
    await auth_middleware_v3(request)
    
    user = request.state.user
    role = user.get("role")
    
    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"접근 권한이 없습니다. 필요 역할: {', '.join(allowed_roles)}"
        )


# ============================================
# 6. 비밀번호 재설정 토큰 생성
# ============================================
def generate_reset_token() -> str:
    """비밀번호 재설정용 랜덤 토큰 생성"""
    return secrets.token_urlsafe(32)


def create_reset_token_expiry() -> datetime:
    """재설정 토큰 만료 시간 (1시간)"""
    return datetime.utcnow() + timedelta(hours=1)
