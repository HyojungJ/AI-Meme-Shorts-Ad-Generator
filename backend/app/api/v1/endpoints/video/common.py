"""video 패키지 공통 의존성"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import httpx

from app.schemas.video import (
    VideoGenerateResponse,
    CharacterPromptSuggestRequest,
    CharacterPromptSuggestResponse,
    CharacterPreviewResponse,
    CharacterListResponse,
    ApprovalRequest,
    ApprovalResponse,
    ProjectListResponse,
    CharacterGenerateRequest,
    CharacterGenerateResponse,
    VoiceGenerateRequest,
    VoiceGenerateResponse,
    VoicePreviewResponse,
    VoiceApprovalRequest,
    VoiceReviseRequest,
    CharacterReviseRequest,
    CharacterRegenerateResponse,
)

from app.crud import video as video_crud
from app.core.security import get_current_user
from app.services.s3_service import get_presigned_url
from app.db.session import get_db
from app.models.workflow import WorkflowExecution
from app.core.config import settings

logger = logging.getLogger(__name__)

# S3 서비스 import (Mock 모드 지원)
if settings.MOCK_MODE:
    from scripts.generation.s3_handler_mock import (
        upload_file_to_s3,
        validate_product_image,
    )
else:
    from app.services.s3_service import (
        upload_file_to_s3,
        validate_product_image,
    )

from app.services.ai_pipeline_factory import AIPipelineClient
