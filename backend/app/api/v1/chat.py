import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.main import get_db
from app.api.deps import get_current_user, get_chat_service
from app.models.user import User
from app.models.session import Session, SessionStatus
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatSendRequest
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/send")
async def send_message(
    request: ChatSendRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service),
):
    session_id = request.session_id

    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(
        session_id=session.id,
        role=MessageRole.user,
        content=request.content,
    )
    db.add(user_msg)
    await db.flush()

    async def event_generator():
        answer_chunks = []
        async for event in chat_service.send_message(
            session_id=session_id,
            user_id=str(user.id),
            content=request.content,
        ):
            # If it's a 'done' event, capture the answer
            if '"type": "done"' in event:
                try:
                    data_str = event.replace("data: ", "").strip()
                    done_data = json.loads(data_str)
                    answer_text = done_data.get("data", {}).get("answer", "")
                except Exception:
                    answer_text = ""

                assistant_msg = Message(
                    session_id=session.id,
                    role=MessageRole.assistant,
                    content=answer_text,
                )
                db.add(assistant_msg)
                await db.flush()

                event_with_id = json.dumps({
                    "type": "done",
                    "data": {
                        "answer": answer_text,
                        "message_id": str(assistant_msg.id),
                        "needs_human": done_data.get("data", {}).get("needs_human", False),
                    }
                })
                yield f"data: {event_with_id}\n\n"
            else:
                yield event

    return EventSourceResponse(event_generator())
