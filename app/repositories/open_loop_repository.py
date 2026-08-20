import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.open_loop import OpenLoop
from app.repositories.base import BaseRepository


class OpenLoopRepository(BaseRepository[OpenLoop]):
    def __init__(self, db: AsyncSession):
        super().__init__(OpenLoop, db)

    async def find_recent_open_by_user(
        self, user_id: uuid.UUID, window_days: int = 14
    ) -> List[OpenLoop]:
        """Fetch all currently open loops for a user within a recent timeframe."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        stmt = (
            select(OpenLoop)
            .where(
                OpenLoop.user_id == user_id,
                OpenLoop.status == "open",
                OpenLoop.updated_at >= cutoff,
            )
            .order_by(OpenLoop.updated_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_open_loops(
        self,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[OpenLoop], int]:
        """List open loops with optional user_id and status filters."""
        query = select(OpenLoop)
        count_query = select(func.count()).select_from(OpenLoop)

        if user_id:
            query = query.where(OpenLoop.user_id == user_id)
            count_query = count_query.where(OpenLoop.user_id == user_id)
        if status:
            query = query.where(OpenLoop.status == status)
            count_query = count_query.where(OpenLoop.status == status)

        query = query.order_by(OpenLoop.created_at.desc()).offset(offset).limit(limit)

        total_res = await self.db.execute(count_query)
        total = total_res.scalar() or 0

        items_res = await self.db.execute(query)
        items = list(items_res.scalars().all())

        return items, total
