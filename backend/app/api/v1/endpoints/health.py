"""
헬스 체크 및 시스템 상태 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.core.config import settings

router = APIRouter()


@router.get("")
def health_check():
    """기본 헬스 체크"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "mode": "mock" if settings.MOCK_MODE else "production"
    }


@router.get("/db")
def database_health_check(db: Session = Depends(get_db)):
    """데이터베이스 연결 확인"""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/s3")
def s3_health_check():
    """S3 연결 확인"""
    if settings.MOCK_MODE:
        return {
            "status": "mock",
            "s3": "mock mode enabled",
            "message": "S3 연결 테스트를 건너뜁니다 (Mock 모드)"
        }
    
    try:
        from app.services.s3_service import test_s3_connection
        
        success, message = test_s3_connection()
        
        if success:
            return {
                "status": "healthy",
                "s3": "connected",
                "bucket": settings.S3_BUCKET_NAME,
                "region": settings.AWS_REGION,
                "message": message
            }
        else:
            return {
                "status": "unhealthy",
                "s3": "connection_failed",
                "bucket": settings.S3_BUCKET_NAME,
                "region": settings.AWS_REGION,
                "error": message
            }
    
    except Exception as e:
        return {
            "status": "error",
            "s3": "error",
            "error": str(e)
        }


@router.get("/all")
def full_health_check(db: Session = Depends(get_db)):
    """전체 시스템 상태 확인"""
    results = {
        "app": {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "mode": "mock" if settings.MOCK_MODE else "production"
        }
    }
    
    # 데이터베이스 체크
    try:
        db.execute(text("SELECT 1"))
        results["database"] = {
            "status": "healthy",
            "connection": "connected"
        }
    except Exception as e:
        results["database"] = {
            "status": "unhealthy",
            "connection": "disconnected",
            "error": str(e)
        }
    
    # S3 체크
    if settings.MOCK_MODE:
        results["s3"] = {
            "status": "mock",
            "connection": "mock mode enabled"
        }
    else:
        try:
            from app.services.s3_service import test_s3_connection
            
            success, message = test_s3_connection()
            
            if success:
                results["s3"] = {
                    "status": "healthy",
                    "connection": "connected",
                    "bucket": settings.S3_BUCKET_NAME,
                    "region": settings.AWS_REGION
                }
            else:
                results["s3"] = {
                    "status": "unhealthy",
                    "connection": "failed",
                    "error": message
                }
        except Exception as e:
            results["s3"] = {
                "status": "error",
                "error": str(e)
            }
    
    # 전체 상태 판단
    all_healthy = all(
        component.get("status") in ["healthy", "mock"]
        for component in results.values()
    )
    
    results["overall_status"] = "healthy" if all_healthy else "unhealthy"
    
    return results
