"""
인증 및 보안 관련 로직
"""
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, Request
import secrets
from cryptography.fernet import Fernet
import base64
import hashlib

from .config import settings


# ============================================
# 비밀번호 해싱
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
# JWT 토큰
# ============================================
def create_access_token(user_data: dict) -> str:
    """Access Token 생성"""
    token_data = user_data.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data["exp"] = expire_time
    token_data["type"] = "access"
    
    token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def create_refresh_token(user_data: dict) -> str:
    """Refresh Token 생성"""
    token_data = {
        "account_id": user_data.get("account_id"),
        "email": user_data.get("email"),
        "type": "refresh"
    }
    expire_time = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_data["exp"] = expire_time
    
    token = jwt.encode(token_data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def verify_token(token: str, token_type: str = "access") -> dict:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
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
# 인증 미들웨어
# ============================================
async def get_current_user(request: Request) -> dict:
    """현재 사용자 정보 추출"""
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="인증 토큰이 없습니다")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="토큰 형식이 잘못되었습니다")

    token = auth_header.replace("Bearer ", "")
    user_info = verify_token(token, token_type="access")

    return user_info


async def check_admin_permission(request: Request) -> dict:
    """Admin 권한 확인"""
    user_info = await get_current_user(request)
    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")
    return user_info


async def check_client_permission(request: Request) -> dict:
    """Client 권한 확인"""
    user_info = await get_current_user(request)
    if user_info.get("account_type") != 'client':
        raise HTTPException(status_code=403, detail="Client만 접근 가능합니다")
    return user_info


# ============================================
# 비밀번호 재설정 토큰
# ============================================
def generate_reset_token() -> str:
    """비밀번호 재설정용 랜덤 토큰 생성"""
    return secrets.token_urlsafe(32)


def create_reset_token_expiry() -> datetime:
    """재설정 토큰 만료 시간 (1시간)"""
    return datetime.utcnow() + timedelta(hours=1)


def create_refresh_token_expiry() -> datetime:
    """Refresh Token 만료 시간 (7일)"""
    return datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


# ============================================
# 토큰 암호화 (OAuth 토큰 등)
# ============================================
def _get_encryption_key() -> bytes:
    """JWT_SECRET_KEY를 기반으로 Fernet 암호화 키 생성"""
    # JWT_SECRET_KEY를 32바이트로 정규화
    key_material = settings.JWT_SECRET_KEY.encode('utf-8')
    # SHA256으로 해시하고 base64 인코딩
    hashed = hashlib.sha256(key_material).digest()
    return base64.urlsafe_b64encode(hashed)


def encrypt_token(token: str) -> str:
    """토큰 암호화 (OAuth 토큰 저장용)"""
    try:
        key = _get_encryption_key()
        cipher = Fernet(key)
        encrypted = cipher.encrypt(token.encode('utf-8'))
        return encrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"토큰 암호화 실패: {str(e)}")


def decrypt_token(encrypted_token: str) -> str:
    """토큰 복호화"""
    try:
        key = _get_encryption_key()
        cipher = Fernet(key)
        decrypted = cipher.decrypt(encrypted_token.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        raise Exception(f"토큰 복호화 실패: {str(e)}")
