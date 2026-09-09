# 데이터베이스 연결 테스트
import sys
import os

sys.path.append(os.path.dirname(__file__))

from scripts.database_user import engine, SessionLocal, get_user_by_google_id, create_user

print("=" * 50)
print("데이터베이스 연결 테스트")
print("=" * 50)

# 테스트 1: 데이터베이스 연결
print("\n[테스트 1] 데이터베이스 연결")
print("-" * 50)

try:
    connection = engine.connect()
    print("데이터베이스 연결 성공")
    connection.close()
except Exception as e:
    print(f"데이터베이스 연결 실패: {e}")
    exit(1)


# 테스트 2: 세션 생성
print("\n[테스트 2] 세션 생성")
print("-" * 50)

try:
    db = SessionLocal()
    print("세션 생성 성공")
    db.close()
except Exception as e:
    print(f"세션 생성 실패: {e}")
    exit(1)


# 테스트 3: 사용자 조회 (존재하지 않는 사용자)
print("\n[테스트 3] 사용자 조회")
print("-" * 50)

try:
    db = SessionLocal()
    user = get_user_by_google_id(db, "test_google_id_12345")
    
    if user:
        print(f"사용자 찾음: {user.email}")
    else:
        print("사용자 없음 (정상)")
    
    db.close()
except Exception as e:
    print(f"사용자 조회 실패: {e}")


print("\n" + "=" * 50)
print("테스트 완료")
print("=" * 50)
