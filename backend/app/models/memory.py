import uuid
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


class LongTermMemory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "long_term_memories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    memory_type: Mapped[str] = mapped_column(String(32), default="fact")
    content: Mapped[dict] = mapped_column(JSON, default=dict)
