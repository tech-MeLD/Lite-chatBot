import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.session import Session, SessionStatus
from app.models.message import Message
from app.models.feedback import Feedback
from app.schemas.session import SessionCreate, SessionUpdate, SessionOut, MessageOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
):
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        SessionOut(
            id=str(s.id),
            title=s.title,
            status=s.status.value,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    body: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = Session(
        user_id=user.id,
        title=body.title or "新对话",
        langgraph_thread_id=str(uuid.uuid4()),
    )
    db.add(session)
    await db.flush()
    return SessionOut(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionOut(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    messages = msg_result.scalars().all()
    return [
        MessageOut(
            id=str(m.id),
            role=m.role.value,
            content=m.content,
            intent=m.intent,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.patch("/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: str,
    body: SessionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.status is not None:
        session.status = SessionStatus(body.status)
    if body.title is not None:
        session.title = body.title

    await db.flush()
    return SessionOut(
        id=str(session.id),
        title=session.title,
        status=session.status.value,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete feedbacks linked to messages in this session
    msg_subquery = select(Message.id).where(Message.session_id == session.id)
    await db.execute(delete(Feedback).where(Feedback.message_id.in_(msg_subquery)))

    # Delete messages in this session
    await db.execute(delete(Message).where(Message.session_id == session.id))

    # Delete the session itself
    await db.execute(delete(Session).where(Session.id == session.id))
    await db.flush()
    return Response(status_code=204)
