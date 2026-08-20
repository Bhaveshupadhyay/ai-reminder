from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.notification_service import NotificationService
from app.services.open_loop_service import OpenLoopService
from app.services.reminder_service import ReminderService


def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    return NotificationService(db)


def get_open_loop_service(
    db: AsyncSession = Depends(get_db),
) -> OpenLoopService:
    return OpenLoopService(db)


def get_reminder_service(
    db: AsyncSession = Depends(get_db),
) -> ReminderService:
    return ReminderService(db)
