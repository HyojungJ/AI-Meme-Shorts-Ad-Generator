import sys
import os

sys.path.append(os.path.dirname(__file__))

from user_auth_api import create_access_token, verify_google_token, JWT_SECRET_KEY, ALGORITHM
from jose import jwt

print("=" * 50)
print("인증 시스템 테스트 시작")
print("=" * 50)

# 테스트 1: JWT 토큰 생성
print("\n[테스트 1] JWT 토큰 생성")
print("-" * 50)

test_user = {
    "user_id": 123,
    "email": "test@example.com",
    "name": "테스트 유저"
}

try:
    token = create_access_token(test_user)
    print("토큰 생성 성공")
    print(f"생성된 토큰: {token[:50]}...")
except Exception as e:
    print(f"토큰 생성 실패: {e}")


# 테스트 2: JWT 토큰 복호화
print("\n[테스트 2] JWT 토큰 복호화")
print("-" * 50)

try:
    decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    print("토큰 복호화 성공")
    print(f"복호화된 데이터:")
    print(f"  user_id: {decoded.get('user_id')}")
    print(f"  email: {decoded.get('email')}")
    print(f"  name: {decoded.get('name')}")
    print(f"  만료시간: {decoded.get('exp')}")
except Exception as e:
    print(f"토큰 복호화 실패: {e}")


# 테스트 3: 잘못된 토큰 검증
print("\n[테스트 3] 잘못된 토큰 검증")
print("-" * 50)

fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.token"

try:
    decoded = jwt.decode(fake_token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    print("가짜 토큰이 통과됨 (문제 있음)")
except jwt.JWTError:
    print("가짜 토큰 차단 성공")
except Exception as e:
    print(f"예상치 못한 에러: {e}")


# 테스트 4: Google 토큰 검증
print("\n[테스트 4] Google 토큰 검증")
print("-" * 50)
print("실제 Google 토큰이 필요합니다")
print("자동 테스트에서는 건너뜁니다")


print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)
