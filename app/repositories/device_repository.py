import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device import Device
from app.repositories.base import BaseRepository


class DeviceRepository(BaseRepository[Device]):
    def __init__(self, db: AsyncSession):
        super().__init__(Device, db)

    async def get_or_create(
        self,
        device_id: Optional[uuid.UUID],
        user_id: uuid.UUID,
        platform: str = "android",
        device_name: str = "Default Device",
    ) -> Device:
        """Fetch device by id or create a new device."""
        if device_id:
            device = await self.get_by_id(device_id)
            if device:
                device.last_seen_at = datetime.now(timezone.utc)
                self.db.add(device)
                await self.db.flush()
                return device
            device = Device(
                id=device_id,
                user_id=user_id,
                platform=platform,
                device_name=device_name,
            )
        else:
            device = Device(
                user_id=user_id,
                platform=platform,
                device_name=device_name,
            )

        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)
        return device
