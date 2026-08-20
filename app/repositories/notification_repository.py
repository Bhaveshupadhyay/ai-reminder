import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification_event import NotificationEvent
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[NotificationEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(NotificationEvent, db)

    async def find_by_client_event_id(
        self, user_id: uuid.UUID, device_id: Optional[uuid.UUID], client_event_id: str
    ) -> Optional[NotificationEvent]:
        """Find an existing notification by idempotent client_event_id."""
        stmt = select(NotificationEvent).where(
            NotificationEvent.user_id == user_id,
            NotificationEvent.client_event_id == client_event_id,
        )
        if device_id:
            stmt = stmt.where(NotificationEvent.device_id == device_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_notifications(
        self,
        user_id: Optional[uuid.UUID] = None,
        source_app: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[NotificationEvent], int]:
        """List notifications with filtering and total count."""
        query = select(NotificationEvent)
        count_query = select(func.count()).select_from(NotificationEvent)

        if user_id:
            query = query.where(NotificationEvent.user_id == user_id)
            count_query = count_query.where(NotificationEvent.user_id == user_id)
        if source_app:
            query = query.where(NotificationEvent.source_app.ilike(f"%{source_app}%"))
            count_query = count_query.where(NotificationEvent.source_app.ilike(f"%{source_app}%"))
        if processing_status:
            query = query.where(NotificationEvent.processing_status == processing_status)
            count_query = count_query.where(NotificationEvent.processing_status == processing_status)

        query = query.order_by(NotificationEvent.received_at.desc()).offset(offset).limit(limit)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0

        items_res = await self.db.execute(query)
        items = list(items_res.scalars().all())

        return items, total
