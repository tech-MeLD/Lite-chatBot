from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.session import router as session_router
from app.api.v1.feedback import router as feedback_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(session_router)
router.include_router(feedback_router)
