import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.open_loop import OpenLoop


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    open_loop_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("open_loops.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="scheduled", nullable=False, index=True
        # "scheduled", "triggered", "cancelled"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    triggered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reminders")
    open_loop: Mapped["OpenLoop"] = relationship("OpenLoop", back_populates="reminders")

    __table_args__ = (
        Index("ix_reminders_user_status_scheduled", "user_id", "status", "scheduled_for"),
    )
