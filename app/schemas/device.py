import uuid
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    platform: Literal["android", "ios"] = Field(..., description="Device platform")
    device_name: str = Field(..., max_length=100, description="Human-readable device name", examples=["Pixel 8 Pro", "iPhone 15"])


class DeviceCreate(DeviceBase):
    id: Optional[uuid.UUID] = Field(default=None)
    user_id: uuid.UUID


class DeviceResponse(DeviceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    last_seen_at: datetime

    model_config = ConfigDict(from_attributes=True)
