from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message_id: str
    rating: int = Field(ge=1, le=5)
    is_liked: bool | None = None
    comment: str | None = None


class FeedbackOut(BaseModel):
    id: str
    message_id: str
    rating: int
    is_liked: bool | None = None
    comment: str | None = None
