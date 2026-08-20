import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reminder import Reminder
from app.repositories.base import BaseRepository


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, db: AsyncSession):
        super().__init__(Reminder, db)

    async def find_by_open_loop_id(self, open_loop_id: uuid.UUID) -> List[Reminder]:
        """Fetch all reminders for a specific open loop."""
        stmt = (
            select(Reminder)
            .where(Reminder.open_loop_id == open_loop_id)
            .order_by(Reminder.scheduled_for.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_reminders(
        self,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        open_loop_id: Optional[uuid.UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Reminder], int]:
        """List reminders with filtering."""
        query = select(Reminder)
        count_query = select(func.count()).select_from(Reminder)

        if user_id:
            query = query.where(Reminder.user_id == user_id)
            count_query = count_query.where(Reminder.user_id == user_id)
        if status:
            query = query.where(Reminder.status == status)
            count_query = count_query.where(Reminder.status == status)
        if open_loop_id:
            query = query.where(Reminder.open_loop_id == open_loop_id)
            count_query = count_query.where(Reminder.open_loop_id == open_loop_id)

        query = query.order_by(Reminder.scheduled_for.asc()).offset(offset).limit(limit)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0

        items_res = await self.db.execute(query)
        items = list(items_res.scalars().all())

        return items, total
