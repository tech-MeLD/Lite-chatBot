from pydantic import BaseModel


class ChatSendRequest(BaseModel):
    session_id: str
    content: str


class ChatSendResponse(BaseModel):
    message_id: str
    session_id: str
    content: str
    role: str = "assistant"
