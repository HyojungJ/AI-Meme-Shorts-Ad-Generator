"""
FastAPI 메인 애플리케이션
통합 API 서버 (인증 + 영상 생성)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'auth', 'v3'))
sys.path.insert(0, os.path.join(current_dir, 'generation', 'v3'))
sys.path.insert(0, os.path.join(current_dir, 'status', 'v2'))
sys.path.insert(0, os.path.join(current_dir, 'scenario', 'v1'))
sys.path.insert(0, os.path.join(current_dir, 'final'))
sys.path.insert(0, os.path.join(current_dir, 'admin'))

from auth.v3.auth_routes_v3 import router as auth_v3_router
from generation.v3.video_routes_v3 import router as video_v3_router
from status.v2.video_routes_v2 import router as status_v2_router
from scenario.v1.scenario_routes import router as scenario_v1_router
from final.video_routes import router as final_video_router
from admin.admin_routes import router as admin_router

app = FastAPI(
    title="Meme Influencer API",
    description="밈 기반 광고 영상 자동 생성 플랫폼",
    version="3.4.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_v3_router)       # 인증 API (V3 - 새 스키마)
app.include_router(video_v3_router)      # 영상 생성 API (V3 - 새 스키마)
app.include_router(status_v2_router)     # 영상 상태 추적 API (V2 - 새 스키마)
app.include_router(scenario_v1_router)   # 시나리오 검수 API (V1)
app.include_router(final_video_router)   # 영상 다운로드 및 승인/거부 API
app.include_router(admin_router)         # Admin 관리 API


@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Meme Influencer API",
        "version": "3.4.0",
        "description": "밈 기반 광고 영상 자동 생성 플랫폼",
        "docs": "/docs",
        "features": {
            "인증": [
                "V3 - 새로운 스키마 적용 (accounts, clients, companies, company_members)",
                "이메일 기반 회원가입/로그인",
                "JWT Access Token (1시간) / Refresh Token (7일)",
                "bcrypt 비밀번호 해싱",
                "비밀번호 재설정",
                "Role 기반 권한 관리 (manager/member)"
            ],
            "영상 생성": [
                "V3 - 새로운 스키마 적용 (video_projects, company_characters)",
                "기존 캐릭터 선택 또는 새 캐릭터 생성",
                "캐릭터 승인 워크플로우",
                "비동기 영상 제작 요청 (POST /api/videos/generate)",
                "워크플로우 상태 조회 (GET /api/videos/status/{execution_id})",
                "내 프로젝트 목록 조회 (GET /api/videos/my-projects)"
            ],
            "시나리오 검수": [
                "V1 - 시나리오 후보 조회 (GET /api/videos/{job_id}/scenarios)",
                "시나리오 승인 (POST /api/videos/{job_id}/scenarios/{script_id}/approve)",
                "시나리오 수정 요청 (POST /api/videos/{job_id}/scenarios/{script_id}/revise)",
                "최대 3회 수정 요청 가능",
                "24시간 미응답 시 자동 승인"
            ],
            "영상 다운로드 및 승인": [
                "V1 - 영상 다운로드 링크 생성 (GET /api/videos/{video_id}/download)",
                "영상 승인 (POST /api/videos/{video_id}/approve)",
                "영상 거부 (POST /api/videos/{video_id}/reject)",
                "S3 Signed URL 생성 (7일 유효)",
                "다운로드 권한 검증 (본인 회사 영상만)",
                "2단계 승인 프로세스 (기업 → Admin)"
            ],
            "Admin 관리": [
                "V1 - 전체 영상 목록 관리 (GET /api/admin/videos/all)",
                "게시 대기 영상 조회 (GET /api/admin/videos/pending)",
                "YouTube 게시 승인 (POST /api/admin/videos/{video_id}/publish)",
                "게시 보류 (POST /api/admin/videos/{video_id}/hold)",
                "워크플로우 모니터링 (GET /api/admin/workflows)",
                "워크플로우 상세 로그 (GET /api/admin/workflows/{execution_id}/logs)",
                "워크플로우 재시도 (POST /api/admin/workflows/{execution_id}/retry)",
                "워크플로우 취소 (POST /api/admin/workflows/{execution_id}/cancel)"
            ]
        }
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "version": "3.4.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
