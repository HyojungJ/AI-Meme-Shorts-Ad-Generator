from fastapi import APIRouter
from .generation import router as generation_router
from .approval import router as approval_router
from .content import router as content_router

router = APIRouter()
router.include_router(generation_router)
router.include_router(approval_router)
router.include_router(content_router)
