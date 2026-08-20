import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    timezone: str = Field(default="UTC", description="User IANA timezone identifier, e.g. UTC, America/New_York, Asia/Kolkata")


class UserCreate(UserBase):
    id: Optional[uuid.UUID] = Field(default=None, description="Optional predetermined UUID")


class UserUpdate(BaseModel):
    timezone: Optional[str] = Field(default=None)


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
