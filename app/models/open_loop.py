import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.notification_event import NotificationEvent
    from app.models.reminder import Reminder


class OpenLoop(Base):
    __tablename__ = "open_loops"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("notification_events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    person: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deadline_text: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    importance: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True  # "low", "medium", "high"
    )
    confidence: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )
    reason: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False, index=True
        # "open", "completed", "dismissed", "snoozed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="open_loops")
    source_notification: Mapped[Optional["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="open_loops"
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder", back_populates="open_loop", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_open_loops_user_status", "user_id", "status"),
    )
