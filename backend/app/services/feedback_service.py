import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.feedback import Feedback


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_feedback(
        self,
        message_id: str,
        user_id: str,
        rating: int,
        is_liked: bool | None = None,
        comment: str | None = None,
    ) -> Feedback:
        feedback = Feedback(
            message_id=uuid.UUID(message_id),
            user_id=uuid.UUID(user_id),
            rating=rating,
            is_liked=is_liked,
            comment=comment,
        )
        self.db.add(feedback)
        await self.db.flush()
        return feedback

    async def get_stats(self) -> dict:
        result = await self.db.execute(
            select(
                func.count(Feedback.id).label("total"),
                func.avg(Feedback.rating).label("avg_rating"),
                func.count().filter(Feedback.is_liked == True).label("likes"),
            )
        )
        row = result.one()
        return {
            "total_feedback": row.total,
            "average_rating": round(float(row.avg_rating or 0), 2),
            "total_likes": row.likes,
        }
