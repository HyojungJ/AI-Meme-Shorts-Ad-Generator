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
    profile_img = Column(String(500))
    yt_channel_id = Column(String(100))
    yt_access_token = Column(Text)
    yt_refresh_token = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_google_id(db, google_id: str):
    return db.query(User).filter(User.google_id == google_id).first()


def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db, google_id: str, email: str, nickname: str, profile_img: str = None):
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


def get_or_create_user(db, google_id: str, email: str, name: str, picture: str = None):
    user = get_user_by_google_id(db, google_id)
    if user:
        return user, False
    user = create_user(db, google_id, email, name, picture)
    return user, True
