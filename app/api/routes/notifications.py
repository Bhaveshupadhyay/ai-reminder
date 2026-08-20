import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from app.api.dependencies import get_notification_service
from app.schemas.notification import (
    NotificationIngestRequest,
    NotificationIngestResponse,
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "",
    response_model=NotificationIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest Notification Event",
    description="""
    Captures a raw notification from client (Android/iOS).
    Validates, saves immediately, schedules background AI analysis, and returns instantly without blocking.
    Idempotent when client_event_id is provided.
    """,
)
async def ingest_notification(
    request: NotificationIngestRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationIngestResponse:
    return await service.ingest_notification(request, background_tasks=background_tasks)


@router.get(
    "/{event_id}",
    response_model=NotificationResponse,
    summary="Get Notification Event",
    description="Retrieve notification details, processing status, and extracted AI analysis.",
)
async def get_notification(
    event_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    event = await service.get_by_id(event_id)
    return NotificationResponse.model_validate(event)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List Notification Events",
    description="Retrieve a paginated list of ingested notifications with optional filters.",
)
async def list_notifications(
    user_id: Optional[uuid.UUID] = Query(default=None, description="Filter by user ID"),
    source_app: Optional[str] = Query(default=None, description="Filter by source app name (e.g. WhatsApp)"),
    processing_status: Optional[str] = Query(
        default=None,
        description="Filter by status (pending, processing, processed, ignored, failed)",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    items, total = await service.list_notifications(
        user_id=user_id,
        source_app=source_app,
        processing_status=processing_status,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
