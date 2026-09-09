"""admin 패키지 공통 의존성"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session

from app.schemas.admin import (
    VideoListResponse,
    PublishVideoRequest,
    PublishVideoResponse,
    WorkflowListResponse,
    WorkflowActionResponse,
)
from app.crud import admin as admin_crud
from app.core.security import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.company import Company
from app.models.video import Video
from app.models.ad_request import AdRequest
from app.models.meme import Meme
from app.models.scenario import ScenarioScript
from app.services.s3_service import get_presigned_url

logger = logging.getLogger(__name__)


async def check_admin_permission(request: Request):
    """Admin 권한 확인"""
    user_info = await get_current_user(request)

    if user_info.get("account_type") != 'admin':
        raise HTTPException(status_code=403, detail="Admin 권한이 필요합니다")

    return user_info
