import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.device import Device
    from app.models.open_loop import OpenLoop


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    device_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    client_event_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    source_app: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    source_package: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    sender: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    body: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
        # "pending", "processing", "processed", "ignored", "failed"
    )
    processing_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    ai_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="notifications")
    open_loops: Mapped[list["OpenLoop"]] = relationship("OpenLoop", back_populates="source_notification")

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", "client_event_id", name="uq_user_device_client_event"),
        Index("ix_notification_events_status_received", "processing_status", "received_at"),
    )
