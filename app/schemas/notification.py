import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationIngestRequest(BaseModel):
    user_id: uuid.UUID = Field(..., description="ID of the user who received the notification")
    device_id: Optional[uuid.UUID] = Field(default=None, description="ID of the device capturing the notification")
    client_event_id: Optional[str] = Field(default=None, max_length=255, description="Client-side unique event ID for idempotency", examples=["msg-12345"])
    source_app: str = Field(..., max_length=100, description="Display name of the source app", examples=["WhatsApp"])
    source_package: str = Field(..., max_length=255, description="Android package or iOS bundle ID", examples=["com.whatsapp"])
    sender: Optional[str] = Field(default=None, max_length=255, description="Sender name or handle", examples=["Rahul"])
    title: Optional[str] = Field(default=None, max_length=255, description="Notification title", examples=["Rahul"])
    body: str = Field(..., min_length=1, description="Notification body text", examples=["Can you send me the investor deck tomorrow?"])
    received_at: datetime = Field(..., description="ISO-8601 timestamp when notification was received on client")


class NotificationIngestResponse(BaseModel):
    event_id: uuid.UUID = Field(..., description="ID of the persisted notification event")
    status: str = Field(..., description="Current processing status: processing, processed, ignored, failed")


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: Optional[uuid.UUID] = None
    client_event_id: Optional[str] = None
    source_app: str
    source_package: str
    sender: Optional[str] = None
    title: Optional[str] = None
    body: str
    received_at: datetime
    created_at: datetime
    processing_status: str
    processing_error: Optional[str] = None
    ai_result: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    limit: int
    offset: int
