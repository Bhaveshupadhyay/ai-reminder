import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EntityNotFoundError
from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository
from app.schemas.reminder import ReminderCreate, ReminderUpdate


class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReminderRepository(db)

    async def get_by_id(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = await self.repo.get_by_id(reminder_id)
        if not reminder:
            raise EntityNotFoundError("Reminder", reminder_id)
        return reminder

    async def create_reminder(self, data: ReminderCreate) -> Reminder:
        reminder = Reminder(
            user_id=data.user_id,
            open_loop_id=data.open_loop_id,
            scheduled_for=data.scheduled_for,
            status="scheduled",
        )
        return await self.repo.create(reminder)

    async def update_reminder(
        self, reminder_id: uuid.UUID, data: ReminderUpdate
    ) -> Reminder:
        reminder = await self.get_by_id(reminder_id)
        return await self.repo.update(reminder, data.model_dump(exclude_unset=True))

    async def cancel_reminder(self, reminder_id: uuid.UUID) -> Reminder:
        reminder = await self.get_by_id(reminder_id)
        return await self.repo.update(reminder, {"status": "cancelled"})

    async def list_reminders(
        self,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        open_loop_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Reminder], int]:
        return await self.repo.list_reminders(
            user_id=user_id,
            status=status,
            open_loop_id=open_loop_id,
            limit=limit,
            offset=offset,
        )
