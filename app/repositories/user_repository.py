import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_or_create(self, user_id: Optional[uuid.UUID] = None, timezone: str = "UTC") -> User:
        """Fetch user by id or create a new user record if not found."""
        if user_id:
            user = await self.get_by_id(user_id)
            if user:
                return user
            user = User(id=user_id, timezone=timezone)
        else:
            user = User(timezone=timezone)

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
