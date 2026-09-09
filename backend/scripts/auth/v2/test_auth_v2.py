"""
인증 시스템 V2 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from auth_v2 import hash_password, verify_password, create_access_token, verify_token


def test_password_hashing():
    """비밀번호 해싱 테스트"""
    print("\n=== 비밀번호 해싱 테스트 ===")
    
    password = "mySecurePassword123!"
    
    # 해싱
    hashed = hash_password(password)
    print(f"원본 비밀번호: {password}")
    print(f"해시된 비밀번호: {hashed[:50]}...")
    
    # 검증 성공
    is_valid = verify_password(password, hashed)
    print(f"비밀번호 검증 (올바른 비밀번호): {is_valid}")
    assert is_valid == True
    
    # 검증 실패
    is_invalid = verify_password("wrongPassword", hashed)
    print(f"비밀번호 검증 (잘못된 비밀번호): {is_invalid}")
    assert is_invalid == False
    
    print("✅ 비밀번호 해싱 테스트 통과")


def test_jwt_tokens():
    """JWT 토큰 생성 및 검증 테스트"""
    print("\n=== JWT 토큰 테스트 ===")
    
    user_data = {
        "user_id": 1,
        "email": "test@example.com",
        "role": "client",
        "company_id": 1
    }
    
    # Access Token 생성
    access_token = create_access_token(user_data)
    print(f"Access Token 생성: {access_token[:50]}...")
    
    # 토큰 검증
    payload = verify_token(access_token, token_type="access")
    print(f"토큰 검증 성공: {payload}")
    
    assert payload["user_id"] == 1
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "client"
    assert payload["type"] == "access"
    
    print("✅ JWT 토큰 테스트 통과")


if __name__ == "__main__":
    print("인증 시스템 V2 단위 테스트 시작")
    
    test_password_hashing()
    test_jwt_tokens()
    
    print("\n✅ 모든 테스트 통과!")
