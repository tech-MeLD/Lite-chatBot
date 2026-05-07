from pydantic import BaseModel
from datetime import datetime


class SessionCreate(BaseModel):
    title: str | None = None


class SessionUpdate(BaseModel):
    status: str | None = None
    title: str | None = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    intent: str | None = None
    created_at: datetime


class SessionOut(BaseModel):
    id: str
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
