import uuid
from sqlalchemy import Enum as SAEnum, ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.models.base import Base, TimestampMixin, UUIDMixin


class SessionStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    closed = "closed"


class Session(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status"),
        default=SessionStatus.active,
    )
    langgraph_thread_id: Mapped[str] = mapped_column(
        String(128), unique=True
    )
    metadata_: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="sessions")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="session", lazy="selectin", order_by="Message.created_at"
    )


from app.models.user import User  # noqa: E402, F811
from app.models.message import Message  # noqa: E402
