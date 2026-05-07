from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=201)
async def submit_feedback(
    body: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback_service = FeedbackService(db)
    try:
        feedback = await feedback_service.create_feedback(
            message_id=body.message_id,
            user_id=str(user.id),
            rating=body.rating,
            is_liked=body.is_liked,
            comment=body.comment,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid message_id or duplicate feedback")

    return FeedbackOut(
        id=str(feedback.id),
        message_id=str(feedback.message_id),
        rating=feedback.rating,
        is_liked=feedback.is_liked,
        comment=feedback.comment,
    )


@router.get("/stats")
async def get_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    feedback_service = FeedbackService(db)
    return await feedback_service.get_stats()
