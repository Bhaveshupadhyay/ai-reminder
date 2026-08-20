import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class OpenLoopBase(BaseModel):
    task: str = Field(..., description="Task description of the open loop")
    person: Optional[str] = Field(default=None, description="Person associated with this open loop")
    deadline: Optional[datetime] = Field(default=None, description="Target completion deadline in UTC")
    deadline_text: Optional[str] = Field(default=None, description="Raw deadline phrase")
    importance: Optional[Literal["low", "medium", "high"]] = Field(default="medium")


class OpenLoopCreate(OpenLoopBase):
    user_id: uuid.UUID
    source_notification_id: Optional[uuid.UUID] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(default="Manually created")


class OpenLoopUpdate(BaseModel):
    task: Optional[str] = None
    person: Optional[str] = None
    deadline: Optional[datetime] = None
    deadline_text: Optional[str] = None
    importance: Optional[Literal["low", "medium", "high"]] = None
    status: Optional[Literal["open", "completed", "dismissed", "snoozed"]] = None


class OpenLoopResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    source_notification_id: Optional[uuid.UUID] = None
    task: str
    person: Optional[str] = None
    deadline: Optional[datetime] = None
    deadline_text: Optional[str] = None
    importance: Optional[str] = None
    confidence: float
    reason: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OpenLoopListResponse(BaseModel):
    items: List[OpenLoopResponse]
    total: int
    limit: int
    offset: int
