import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_open_loop_service
from app.schemas.open_loop import (
    OpenLoopListResponse,
    OpenLoopResponse,
    OpenLoopUpdate,
)
from app.services.open_loop_service import OpenLoopService

router = APIRouter(prefix="/open-loops", tags=["Open Loops"])


@router.get(
    "",
    response_model=OpenLoopListResponse,
    summary="List Open Loops",
    description="Retrieve open obligations/tasks with optional filtering by user and status.",
)
async def list_open_loops(
    user_id: Optional[uuid.UUID] = Query(default=None, description="Filter by user ID"),
    status: Optional[str] = Query(
        default=None, description="Filter by status (open, completed, dismissed, snoozed)"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: OpenLoopService = Depends(get_open_loop_service),
) -> OpenLoopListResponse:
    items, total = await service.list_open_loops(
        user_id=user_id, status=status, limit=limit, offset=offset
    )
    return OpenLoopListResponse(
        items=[OpenLoopResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{id}",
    response_model=OpenLoopResponse,
    summary="Get Open Loop by ID",
    description="Retrieve a single open loop by its UUID.",
)
async def get_open_loop(
    id: uuid.UUID,
    service: OpenLoopService = Depends(get_open_loop_service),
) -> OpenLoopResponse:
    loop = await service.get_by_id(id)
    return OpenLoopResponse.model_validate(loop)


@router.patch(
    "/{id}",
    response_model=OpenLoopResponse,
    summary="Update Open Loop",
    description="Update open loop fields such as status, deadline, task, importance.",
)
async def update_open_loop(
    id: uuid.UUID,
    data: OpenLoopUpdate,
    service: OpenLoopService = Depends(get_open_loop_service),
) -> OpenLoopResponse:
    loop = await service.update_open_loop(id, data)
    return OpenLoopResponse.model_validate(loop)


@router.post(
    "/{id}/complete",
    response_model=OpenLoopResponse,
    summary="Complete Open Loop",
    description="Marks an open loop as completed and sets completed_at timestamp.",
)
async def complete_open_loop(
    id: uuid.UUID,
    service: OpenLoopService = Depends(get_open_loop_service),
) -> OpenLoopResponse:
    loop = await service.complete_open_loop(id)
    return OpenLoopResponse.model_validate(loop)


@router.post(
    "/{id}/dismiss",
    response_model=OpenLoopResponse,
    summary="Dismiss Open Loop",
    description="Dismisses an open loop without completing it.",
)
async def dismiss_open_loop(
    id: uuid.UUID,
    service: OpenLoopService = Depends(get_open_loop_service),
) -> OpenLoopResponse:
    loop = await service.dismiss_open_loop(id)
    return OpenLoopResponse.model_validate(loop)
