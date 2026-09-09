"""
FastAPI 메인 애플리케이션
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# 폴링 엔드포인트 로그 필터 (로그 도배 방지)
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # generation-poll 요청 로그 제외
        return "generation-poll" not in record.getMessage()

# uvicorn 로거에 필터 추가
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

# Import endpoints
try:
    from app.api.v1.endpoints import (
        auth, video, status, final, admin, scenario, analytics,
        users, costs, quality, client_analytics, health, memes,
        content_pipeline, sse
    )
except Exception as e:
    logger.error("Error importing core endpoints: %s", e)
    raise

try:
    from app.api.v1.endpoints import character_profiles
except Exception as e:
    logger.warning("Error importing character_profiles: %s", e, exc_info=True)
    character_profiles = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: AI 함수 프리로딩 (DIRECT_MODE에서 첫 호출 블로킹 방지)
    if settings.AI_PIPELINE_DIRECT_MODE:
        try:
            from app.services.ai_pipeline_direct import _load_ai_functions
            _load_ai_functions()
            logger.info("AI 함수 프리로딩 완료")
        except Exception as e:
            logger.warning("AI 함수 프리로딩 실패 (첫 호출 시 로딩됨): %s", e)

    # startup: 밈 정렬용 임베딩 모델 프리로딩 (프로덕션만)
    if not settings.DEBUG:
        try:
            from meme_collector.meme_sorting import _get_model
            _get_model()
            logger.info("BGE-m3-ko 모델 로딩 완료")
        except Exception as e:
            logger.warning("모델 프리로딩 실패 (정렬 API 첫 호출 시 로딩됨): %s", e)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="밈 기반 광고 영상 자동 생성 플랫폼",
    version=settings.APP_VERSION,
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)

# OpenAPI 스키마 커스터마이징 (Bearer 토큰 인증 추가)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="밈 기반 광고 영상 자동 생성 플랫폼",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # 모든 엔드포인트에 보안 적용 (로그인/회원가입 제외)
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if path not in ["/api/v1/auth/login", "/api/v1/auth/signup", "/", "/health"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS 설정 - Vercel 프리뷰 도메인 동적 허용
from starlette.middleware.cors import CORSMiddleware as BaseCORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

class DynamicCORSMiddleware(BaseCORSMiddleware):
    """Vercel 프리뷰 도메인을 동적으로 허용하는 CORS 미들웨어"""
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode("utf-8")
            
            # Vercel 프리뷰 도메인 패턴 체크
            if origin and (
                origin.endswith(".vercel.app") or 
                origin.endswith("admeme.com") or
                origin in settings.cors_origins_list
            ):
                # 동적으로 origin 추가
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)
        
        await super().__call__(scope, receive, send)

app.add_middleware(
    DynamicCORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# 라우터 등록
app.include_router(health.router, prefix="/api/v1/health", tags=["Health Check"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["인증"])
app.include_router(memes.router, prefix="/api/v1/memes", tags=["밈 목록"])

# character_profiles 라우터 등록 (import 성공 시에만)
if character_profiles is not None:
    app.include_router(character_profiles.router, prefix="/api/v1/character-profiles", tags=["캐릭터 프로필"])
else:
    logger.warning("character_profiles router NOT registered (import failed)")

app.include_router(video.router, prefix="/api/v1/videos", tags=["영상 생성"])
app.include_router(content_pipeline.router, prefix="/api/v1/video", tags=["Content Pipeline"])
app.include_router(status.router, prefix="/api/v1/status", tags=["상태 추적"])
app.include_router(final.router, prefix="/api/v1/videos", tags=["영상 다운로드"])
app.include_router(scenario.router, prefix="/api/v1/videos", tags=["시나리오 검수"])
app.include_router(client_analytics.router, prefix="/api/v1/analytics", tags=["성과 분석 (Client)"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin 관리"])
app.include_router(analytics.router, prefix="/api/v1/admin/analytics", tags=["성과 분석 (Admin)"])
app.include_router(users.router, prefix="/api/v1/admin/users", tags=["사용자 관리"])
app.include_router(costs.router, prefix="/api/v1/admin/costs", tags=["비용 관리"])
app.include_router(quality.router, prefix="/api/v1/admin/quality", tags=["품질 관리"])
app.include_router(sse.router, prefix="/api/v1/sse", tags=["SSE"])
# 호환성을 위해 /api/v1에도 등록 (프론트엔드가 /api/v1/generation-poll 호출)
app.include_router(sse.router, prefix="/api/v1", tags=["Generation Status"], include_in_schema=False)

# 정적 파일 서빙 (캐릭터 프로필 샘플)
character_profiles_path = Path(__file__).parent.parent / "data" / "character_profiles"
character_profiles_path.mkdir(parents=True, exist_ok=True)
app.mount("/static/character-profiles", StaticFiles(directory=str(character_profiles_path)), name="character_profiles")


@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "밈 기반 광고 영상 자동 생성 플랫폼",
        "docs": "/docs",
        "api": {
            "v1": "/api/v1"
        },
        "features": {
            "인증": "회원가입, 로그인, 토큰 관리",
            "영상 생성": "캐릭터 생성, 영상 제작 요청",
            "시나리오 검수": "시나리오 승인/수정 요청",
            "영상 다운로드": "영상 다운로드 및 승인/거부",
            "Admin 관리": "전체 영상 관리, 워크플로우 모니터링"
        }
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
