import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import GUID

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.notification_event import NotificationEvent
    from app.models.open_loop import OpenLoop
    from app.models.reminder import Reminder


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False
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

    # Relationships
    devices: Mapped[List["Device"]] = relationship(
        "Device", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["NotificationEvent"]] = relationship(
        "NotificationEvent", back_populates="user", cascade="all, delete-orphan"
    )
    open_loops: Mapped[List["OpenLoop"]] = relationship(
        "OpenLoop", back_populates="user", cascade="all, delete-orphan"
    )
    reminders: Mapped[List["Reminder"]] = relationship(
        "Reminder", back_populates="user", cascade="all, delete-orphan"
    )
