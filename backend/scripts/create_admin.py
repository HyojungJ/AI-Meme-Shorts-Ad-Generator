"""
초기 Admin 계정 생성 스크립트

사용법:
    python scripts/create_admin.py

환경 변수 필요:
    DATABASE_URL - PostgreSQL 연결 문자열
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import SessionLocal
from app.models.account import Account, Admin
from app.core.security import hash_password


def create_admin_account(
    db: Session,
    email: str,
    password: str
):
    """Admin 계정 생성"""
    
    # 이메일 중복 확인
    existing = db.query(Account).filter(Account.email == email).first()
    if existing:
        print(f"❌ 이미 존재하는 이메일입니다: {email}")
        return None
    
    # Account 생성 (현재 스키마에 맞춤)
    account = Account(
        email=email,
        account_type='admin',
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(account)
    db.flush()  # account_id 생성
    
    # Admin 생성 (현재 스키마에 맞춤)
    hashed_pw = hash_password(password)
    admin = Admin(
        account_id=account.account_id,
        hashed_password=hashed_pw,
        updated_at=datetime.utcnow()
    )
    db.add(admin)
    
    db.commit()
    db.refresh(account)
    
    print(f"✅ Admin 계정이 생성되었습니다!")
    print(f"   이메일: {email}")
    print(f"   Account ID: {account.account_id}")
    print(f"   Admin ID: {admin.admin_id}")
    
    return account


def main():
    """메인 함수"""
    print("=" * 60)
    print("Admin 계정 생성 스크립트")
    print("=" * 60)
    print()
    
    # 사용자 입력
    email = input("Admin 이메일: ").strip()
    if not email:
        print("❌ 이메일을 입력해주세요.")
        return
    
    password = input("비밀번호: ").strip()
    if not password:
        print("❌ 비밀번호를 입력해주세요.")
        return
    
    password_confirm = input("비밀번호 확인: ").strip()
    if password != password_confirm:
        print("❌ 비밀번호가 일치하지 않습니다.")
        return
    
    print()
    print("입력 정보:")
    print(f"  이메일: {email}")
    print()
    
    confirm = input("Admin 계정을 생성하시겠습니까? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 취소되었습니다.")
        return
    
    # DB 연결
    db = SessionLocal()
    
    try:
        create_admin_account(db, email, password)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
