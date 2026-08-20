import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.exceptions import EntityNotFoundError
from app.core.logging import logger
from app.models.notification_event import NotificationEvent
from app.models.reminder import Reminder
from app.repositories.device_repository import DeviceRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import (
    NotificationIngestRequest,
    NotificationIngestResponse,
)
from app.schemas.reminder import ReminderCreate
from app.services.ai.base import AIProvider
from app.services.ai.provider import get_ai_provider
from app.services.filter_service import NotificationFilterService
from app.services.open_loop_service import OpenLoopService
from app.services.reminder_service import ReminderService


async def process_notification_background(event_id: uuid.UUID) -> None:
    """
    Isolated background task for processing a notification.
    Runs asynchronously without blocking the HTTP response.
    Can later be easily adapted to Celery, ARQ, or Kafka.
    """
    async with AsyncSessionLocal() as db:
        try:
            notif_repo = NotificationRepository(db)
            event = await notif_repo.get_by_id(event_id)
            if not event:
                logger.error(f"NotificationEvent {event_id} not found in background processing")
                return

            # Update status to processing
            event.processing_status = "processing"
            await db.flush()

            # 1. Heuristic filtering before LLM
            should_ignore, ignore_reason = NotificationFilterService.should_ignore(
                source_package=event.source_package,
                source_app=event.source_app,
                body=event.body,
                title=event.title,
            )

            if should_ignore:
                event.processing_status = "ignored"
                event.ai_result = {
                    "actionable": False,
                    "reason": f"Filtered: {ignore_reason}",
                }
                await db.commit()
                logger.info(f"Notification {event_id} filtered out: {ignore_reason}")
                return

            # 2. Get user timezone context
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(event.user_id)
            user_tz = user.timezone if user else "UTC"

            # 3. Call AI provider
            ai_provider: AIProvider = get_ai_provider()
            analysis = await ai_provider.analyze_notification(
                body=event.body,
                title=event.title,
                sender=event.sender,
                source_app=event.source_app,
                reference_time=event.received_at,
                user_timezone=user_tz,
            )

            # 4. Save AI Result
            event.ai_result = analysis.model_dump(mode="json")
            event.processing_status = "processed"

            # 5. If actionable, manage OpenLoop and Reminders
            if analysis.actionable:
                open_loop_service = OpenLoopService(db)
                open_loop, is_created = await open_loop_service.process_actionable_notification(
                    user_id=event.user_id,
                    notification_id=event.id,
                    analysis=analysis,
                )

                # If deadline exists, create a reminder if one isn't already scheduled
                if analysis.deadline:
                    reminder_service = ReminderService(db)
                    existing_reminders = await reminder_service.repo.find_by_open_loop_id(open_loop.id)
                    active_scheduled = [r for r in existing_reminders if r.status == "scheduled"]
                    if not active_scheduled:
                        await reminder_service.create_reminder(
                            ReminderCreate(
                                user_id=event.user_id,
                                open_loop_id=open_loop.id,
                                scheduled_for=analysis.deadline,
                            )
                        )

            await db.commit()
            logger.info(f"Successfully processed Notification {event_id}. Actionable: {analysis.actionable}")

        except Exception as e:
            logger.exception(f"Error during background processing of notification {event_id}: {str(e)}")
            try:
                event = await notif_repo.get_by_id(event_id)
                if event:
                    event.processing_status = "failed"
                    event.processing_error = str(e)
                    await db.commit()
            except Exception as rollback_err:
                logger.error(f"Failed to record failure status for notification {event_id}: {str(rollback_err)}")


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = NotificationRepository(db)
        self.user_repo = UserRepository(db)
        self.device_repo = DeviceRepository(db)

    async def get_by_id(self, event_id: uuid.UUID) -> NotificationEvent:
        event = await self.repo.get_by_id(event_id)
        if not event:
            raise EntityNotFoundError("NotificationEvent", event_id)
        return event

    async def ingest_notification(
        self,
        request: NotificationIngestRequest,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> NotificationIngestResponse:
        """
        Ingest a raw notification event:
        1. Validates and ensures User & Device records exist.
        2. Checks idempotency via (user_id, device_id, client_event_id).
        3. Persists raw notification before AI processing.
        4. Dispatches background processing without blocking.
        5. Returns immediately.
        """
        # Ensure user exists
        await self.user_repo.get_or_create(user_id=request.user_id)

        # Ensure device exists if provided
        if request.device_id:
            await self.device_repo.get_or_create(
                device_id=request.device_id,
                user_id=request.user_id,
                platform="android",
                device_name=f"{request.source_app} Ingestion Device",
            )

        # Check idempotency
        if request.client_event_id:
            existing = await self.repo.find_by_client_event_id(
                user_id=request.user_id,
                device_id=request.device_id,
                client_event_id=request.client_event_id,
            )
            if existing:
                logger.info(
                    f"Duplicate notification received (client_event_id={request.client_event_id}). Returning existing event {existing.id}."
                )
                return NotificationIngestResponse(
                    event_id=existing.id,
                    status=existing.processing_status,
                )

        # Persist raw notification
        event = NotificationEvent(
            user_id=request.user_id,
            device_id=request.device_id,
            client_event_id=request.client_event_id,
            source_app=request.source_app,
            source_package=request.source_package,
            sender=request.sender,
            title=request.title,
            body=request.body,
            received_at=request.received_at,
            processing_status="processing",
        )
        created_event = await self.repo.create(event)
        await self.db.commit()

        # Enqueue background processing
        if background_tasks is not None:
            background_tasks.add_task(process_notification_background, created_event.id)
        else:
            # Direct execution fallback for testing environments without BackgroundTasks
            import asyncio
            asyncio.create_task(process_notification_background(created_event.id))

        return NotificationIngestResponse(
            event_id=created_event.id,
            status=created_event.processing_status,
        )

    async def list_notifications(
        self,
        user_id: Optional[uuid.UUID] = None,
        source_app: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[NotificationEvent], int]:
        return await self.repo.list_notifications(
            user_id=user_id,
            source_app=source_app,
            processing_status=processing_status,
            limit=limit,
            offset=offset,
        )
