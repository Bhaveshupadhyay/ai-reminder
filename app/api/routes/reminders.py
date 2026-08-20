import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_reminder_service
from app.schemas.reminder import (
    ReminderCreate,
    ReminderListResponse,
    ReminderResponse,
    ReminderUpdate,
)
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["Reminders"])


@router.get(
    "",
    response_model=ReminderListResponse,
    summary="List Reminders",
    description="Retrieve a paginated list of reminders with optional filters.",
)
async def list_reminders(
    user_id: Optional[uuid.UUID] = Query(default=None, description="Filter by user ID"),
    status: Optional[str] = Query(
        default=None, description="Filter by status (scheduled, triggered, cancelled)"
    ),
    open_loop_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by associated open loop ID"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderListResponse:
    items, total = await service.list_reminders(
        user_id=user_id,
        status=status,
        open_loop_id=open_loop_id,
        limit=limit,
        offset=offset,
    )
    return ReminderListResponse(
        items=[ReminderResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Reminder",
    description="Create a manual reminder linked to an open loop.",
)
async def create_reminder(
    data: ReminderCreate,
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderResponse:
    reminder = await service.create_reminder(data)
    return ReminderResponse.model_validate(reminder)


@router.patch(
    "/{id}",
    response_model=ReminderResponse,
    summary="Update Reminder",
    description="Update reminder schedule or status.",
)
async def update_reminder(
    id: uuid.UUID,
    data: ReminderUpdate,
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderResponse:
    reminder = await service.update_reminder(id, data)
    return ReminderResponse.model_validate(reminder)


@router.post(
    "/{id}/cancel",
    response_model=ReminderResponse,
    summary="Cancel Reminder",
    description="Cancel a scheduled reminder.",
)
async def cancel_reminder(
    id: uuid.UUID,
    service: ReminderService = Depends(get_reminder_service),
) -> ReminderResponse:
    reminder = await service.cancel_reminder(id)
    return ReminderResponse.model_validate(reminder)
