from fastapi import APIRouter
from .videos import router as videos_router
from .youtube import router as youtube_router
from .workflow import router as workflow_router

router = APIRouter()
router.include_router(videos_router)
router.include_router(youtube_router)
router.include_router(workflow_router)
