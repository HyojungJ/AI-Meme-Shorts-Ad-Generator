"""
FastAPI 메인 애플리케이션 V2
이메일/비밀번호 기반 인증 시스템
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from auth_routes_v2 import router as auth_v2_router

app = FastAPI(
    title="Meme Influencer API V2",
    description="이메일/비밀번호 기반 사용자 인증 API",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# V2 라우터 등록
app.include_router(auth_v2_router)


@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Meme Influencer API V2",
        "version": "2.0.0",
        "description": "이메일/비밀번호 기반 인증 시스템",
        "docs": "/docs",
        "features": [
            "이메일 기반 회원가입/로그인 (UMS-AUT-01)",
            "JWT Access Token (1시간) / Refresh Token (7일)",
            "bcrypt 비밀번호 해싱 (UMS-AUT-04)",
            "비밀번호 재설정 (UMS-AUT-03)",
            "Role 기반 권한 관리 (admin/client)"
        ]
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
