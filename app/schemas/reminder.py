import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    user_id: uuid.UUID = Field(..., description="User ID")
    open_loop_id: uuid.UUID = Field(..., description="Open Loop ID associated with this reminder")
    scheduled_for: datetime = Field(..., description="UTC timestamp when reminder is scheduled to trigger")


class ReminderUpdate(BaseModel):
    scheduled_for: Optional[datetime] = None
    status: Optional[Literal["scheduled", "triggered", "cancelled"]] = None


class ReminderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    open_loop_id: uuid.UUID
    scheduled_for: datetime
    status: str
    created_at: datetime
    triggered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReminderListResponse(BaseModel):
    items: List[ReminderResponse]
    total: int
    limit: int
    offset: int
