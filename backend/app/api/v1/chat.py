import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.main import get_db
from app.api.deps import get_current_user, get_chat_service
from app.models.user import User
from app.models.session import Session
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatSendRequest
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService

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

    # Retrieve relevant long-term memories for this user
    memory_service = MemoryService(db)
    memories = await memory_service.retrieve_relevant(
        user_id=str(user.id),
        query=request.content,
        top_k=3,
    )

    assistant_msg_ref = []

    async def event_generator():
        nonlocal assistant_msg_ref

        async for event in chat_service.send_message(
            session_id=session_id,
            user_id=str(user.id),
            content=request.content,
            user_memories=memories,
        ):
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
                assistant_msg_ref = [assistant_msg]

                event_with_id = json.dumps({
                    "type": "done",
                    "data": {
                        "answer": answer_text,
                        "message_id": str(assistant_msg.id),
                        "needs_human": done_data.get("data", {}).get("needs_human", False),
                    }
                })
                yield f"data: {event_with_id}\n\n"

                # Extract and store new memories from this conversation
                conversation = f"用户: {request.content}\n助手: {answer_text}"
                await memory_service.extract_and_store(
                    user_id=str(user.id),
                    conversation=conversation,
                    llm=chat_service.llm,
                )
            else:
                yield event

    return EventSourceResponse(event_generator())
