import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from app.core.database import AsyncSessionLocal
from app.core.logging import logger, setup_logging
from app.models.device import Device
from app.models.notification_event import NotificationEvent
from app.models.open_loop import OpenLoop
from app.models.reminder import Reminder
from app.models.user import User
from app.services.ai.mock import MockAIProvider
from app.services.filter_service import NotificationFilterService

DEMO_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_DEVICE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

EXAMPLES = [
    {
        "client_event_id": "seed-001",
        "source_app": "WhatsApp",
        "source_package": "com.whatsapp",
        "sender": "Rahul",
        "title": "Rahul",
        "body": "Can you send me the investor deck tomorrow?",
        "received_at_offset_hours": -2,
    },
    {
        "client_event_id": "seed-002",
        "source_app": "Slack",
        "source_package": "com.Slack",
        "sender": "Sarah Miller",
        "title": "#product-sync",
        "body": "Let's catch up sometime next week.",
        "received_at_offset_hours": -5,
    },
    {
        "client_event_id": "seed-003",
        "source_app": "Gmail",
        "source_package": "com.google.android.gm",
        "sender": "Alex Vance",
        "title": "Partnership Proposal",
        "body": "Hey, just checking if you got a chance to look at the proposal.",
        "received_at_offset_hours": -12,
    },
    {
        "client_event_id": "seed-004",
        "source_app": "WhatsApp",
        "source_package": "com.whatsapp",
        "sender": "Dave",
        "title": "Weekend Plans",
        "body": "lol that's hilarious 😂",
        "received_at_offset_hours": -1,
    },
    {
        "client_event_id": "seed-005",
        "source_app": "SMS",
        "source_package": "com.google.android.apps.messaging",
        "sender": "Dr. Smith",
        "title": "Dr. Smith",
        "body": "Please call me after 6.",
        "received_at_offset_hours": -3,
    },
]


async def seed_database():
    setup_logging()
    logger.info("Seeding database with demo data...")
    ai_provider = MockAIProvider()

    async with AsyncSessionLocal() as session:
        # 1. Create or get Demo User
        user = await session.get(User, DEMO_USER_ID)
        if not user:
            user = User(
                id=DEMO_USER_ID,
                timezone="America/New_York",
            )
            session.add(user)
            await session.flush()
            logger.info(f"Created demo user with ID: {DEMO_USER_ID}")
        else:
            logger.info(f"Demo user already exists: {DEMO_USER_ID}")

        # 2. Create or get Demo Device
        device = await session.get(Device, DEMO_DEVICE_ID)
        if not device:
            device = Device(
                id=DEMO_DEVICE_ID,
                user_id=DEMO_USER_ID,
                platform="android",
                device_name="Google Pixel 8 Pro",
            )
            session.add(device)
            await session.flush()
            logger.info(f"Created demo device with ID: {DEMO_DEVICE_ID}")
        else:
            logger.info(f"Demo device already exists: {DEMO_DEVICE_ID}")

        now = datetime.now(timezone.utc)

        # 3. Ingest & Process Example Notifications
        for item in EXAMPLES:
            client_event_id = item["client_event_id"]
            received_at = now + timedelta(hours=item["received_at_offset_hours"])

            event = NotificationEvent(
                user_id=DEMO_USER_ID,
                device_id=DEMO_DEVICE_ID,
                client_event_id=client_event_id,
                source_app=item["source_app"],
                source_package=item["source_package"],
                sender=item["sender"],
                title=item["title"],
                body=item["body"],
                received_at=received_at,
                processing_status="processing",
            )
            session.add(event)
            await session.flush()

            # Filter check
            should_ignore, ignore_reason = NotificationFilterService.should_ignore(
                item["source_package"], item["source_app"], item["body"], item["title"]
            )

            if should_ignore:
                event.processing_status = "ignored"
                event.ai_result = {"actionable": False, "reason": ignore_reason}
                await session.flush()
                continue

            # Analyze with AI
            analysis = await ai_provider.analyze_notification(
                body=item["body"],
                title=item["title"],
                sender=item["sender"],
                source_app=item["source_app"],
                reference_time=received_at,
                user_timezone=user.timezone,
            )

            event.ai_result = analysis.model_dump(mode="json")
            event.processing_status = "processed"
            await session.flush()

            # Create Open Loop & Reminder if actionable
            if analysis.actionable:
                open_loop = OpenLoop(
                    user_id=DEMO_USER_ID,
                    source_notification_id=event.id,
                    task=analysis.task or "Follow up",
                    person=analysis.person,
                    deadline=analysis.deadline,
                    deadline_text=analysis.deadline_text,
                    importance=analysis.importance or "medium",
                    confidence=analysis.confidence,
                    reason=analysis.reason,
                    status="open",
                )
                session.add(open_loop)
                await session.flush()

                if analysis.deadline:
                    reminder = Reminder(
                        user_id=DEMO_USER_ID,
                        open_loop_id=open_loop.id,
                        scheduled_for=analysis.deadline,
                        status="scheduled",
                    )
                    session.add(reminder)
                    await session.flush()

                logger.info(f"[ACTIONABLE] Created OpenLoop '{open_loop.task}' (person: {open_loop.person})")
            else:
                logger.info(f"[NON-ACTIONABLE] Skipped OpenLoop for: '{item['body']}'")

        await session.commit()
        logger.info("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
