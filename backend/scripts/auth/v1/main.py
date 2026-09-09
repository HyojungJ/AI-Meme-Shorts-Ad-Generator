# FastAPI 메인 애플리케이션
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from auth_routes import router as auth_router

app = FastAPI(
    title="Meme Influencer API",
    description="사용자 인증 API",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)


@app.get("/")
def root():
    """
    API 루트 엔드포인트
    """
    return {
        "message": "Meme Influencer API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
