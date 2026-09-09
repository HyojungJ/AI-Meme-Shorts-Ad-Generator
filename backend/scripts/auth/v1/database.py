# 데이터베이스 연결 설정
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()


# User 모델 정의
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    yt_channel_id = Column(String(100))
    yt_access_token = Column(Text)
    yt_refresh_token = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 데이터베이스 세션 가져오기
def get_db():
    """
    데이터베이스 세션을 생성하고 반환
    사용 후 자동으로 닫힘
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 사용자 조회 함수
def get_user_by_google_id(db, google_id: str):
    """
    Google ID로 사용자 조회
    
    매개변수:
        db: 데이터베이스 세션
        google_id: Google 사용자 ID
    
    반환값:
        User 객체 또는 None
    """
    return db.query(User).filter(User.google_id == google_id).first()


def get_user_by_email(db, email: str):
    """
    이메일로 사용자 조회
    
    매개변수:
        db: 데이터베이스 세션
        email: 사용자 이메일
    
    반환값:
        User 객체 또는 None
    """
    return db.query(User).filter(User.email == email).first()


# 사용자 생성 함수
def create_user(db, google_id: str, email: str, nickname: str, profile_img: str = None):
    """
    새로운 사용자 생성
    
    매개변수:
        db: 데이터베이스 세션
        google_id: Google 사용자 ID
        email: 사용자 이메일
        nickname: 사용자 닉네임
        profile_img: 프로필 이미지 URL (선택)
    
    반환값:
        생성된 User 객체
    """
    new_user = User(
        google_id=google_id,
        email=email,
        nickname=nickname,
        profile_img=profile_img
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# 사용자 조회 또는 생성
def get_or_create_user(db, google_id: str, email: str, name: str, picture: str = None):
    """
    사용자를 조회하고, 없으면 생성
    
    매개변수:
        db: 데이터베이스 세션
        google_id: Google 사용자 ID
        email: 사용자 이메일
        name: 사용자 이름
        picture: 프로필 이미지 URL (선택)
    
    반환값:
        (User 객체, 새로 생성 여부)
    """
    user = get_user_by_google_id(db, google_id)
    
    if user:
        print(f"기존 사용자 로그인: {user.email}")
        return user, False
    
    # 새 사용자 생성
    user = create_user(db, google_id, email, name, picture)
    print(f"새 사용자 생성: {user.email}")
    return user, True
