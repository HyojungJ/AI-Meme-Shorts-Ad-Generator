"""
데이터베이스 세션 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# SQLAlchemy 엔진 생성 (연결 풀 설정 추가)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 전 ping으로 유효성 확인
    pool_recycle=3600,   # 1시간마다 연결 재생성
    pool_size=10,        # 연결 풀 크기
    max_overflow=20,     # 최대 추가 연결 수
    echo=False,          # SQL 로그 출력 (개발 시 True)
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
