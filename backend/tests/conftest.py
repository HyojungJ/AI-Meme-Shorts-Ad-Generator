"""
공통 테스트 픽스처
DB 없이 Mock으로 엔드포인트 테스트 가능.
"""
import os
import pytest
from unittest.mock import MagicMock, AsyncMock

# Mock 모드 활성화 (import 전에 설정)
os.environ["AI_PIPELINE_MOCK_MODE"] = "true"
os.environ["MOCK_MODE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///test.db"


@pytest.fixture
def mock_db():
    """Mock DB 세션"""
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def mock_user_info():
    """테스트용 사용자 정보"""
    return {
        "account_id": 1,
        "company_id": 1,
        "email": "test@test.com",
        "account_type": "company",
    }


@pytest.fixture
def auth_token(mock_user_info):
    """JWT 테스트 토큰 생성"""
    from app.core.security import create_access_token
    return create_access_token(mock_user_info)


@pytest.fixture
def auth_headers(auth_token):
    """인증 헤더"""
    return {"Authorization": f"Bearer {auth_token}"}
