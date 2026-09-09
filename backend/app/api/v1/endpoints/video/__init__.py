from fastapi import APIRouter
from .character import router as character_router
from .voice import router as voice_router
from .project import router as project_router

router = APIRouter()
router.include_router(character_router)
router.include_router(voice_router)
router.include_router(project_router)
