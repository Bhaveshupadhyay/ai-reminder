import asyncio
import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.notification_event import NotificationEvent
from app.models.open_loop import OpenLoop
from app.models.reminder import Reminder
from app.services.notification_service import process_notification_background


@pytest.mark.asyncio
async def test_actionable_notification_pipeline(client: AsyncClient, db_session: AsyncSession, test_user: User):
    # Create and persist notification
    received_time = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)
    event = NotificationEvent(
        user_id=test_user.id,
        source_app="WhatsApp",
        source_package="com.whatsapp",
        sender="Rahul",
        title="Rahul",
        body="Can you send me the investor deck tomorrow?",
        received_at=received_time,
        processing_status="pending",
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    # Trigger background processing
    await process_notification_background(event.id)

    # Check notification status
    await db_session.refresh(event)
    assert event.processing_status == "processed"
    assert event.ai_result is not None
    assert event.ai_result["actionable"] is True
    assert event.ai_result["task"] == "Send the investor deck"
    assert event.ai_result["person"] == "Rahul"

    # Verify Open Loop created
    res = await client.get(f"/api/v1/open-loops?user_id={test_user.id}")
    assert res.status_code == 200
    loops = res.json()
    assert loops["total"] == 1
    loop = loops["items"][0]
    assert loop["task"] == "Send the investor deck"
    assert loop["person"] == "Rahul"
    assert loop["status"] == "open"
    assert loop["deadline"] is not None

    # Verify Reminder created for deadline
    rem_res = await client.get(f"/api/v1/reminders?user_id={test_user.id}")
    assert rem_res.status_code == 200
    reminders = rem_res.json()
    assert reminders["total"] == 1
    assert reminders["items"][0]["status"] == "scheduled"


@pytest.mark.asyncio
async def test_non_actionable_notification_pipeline(client: AsyncClient, db_session: AsyncSession, test_user: User):
    event = NotificationEvent(
        user_id=test_user.id,
        source_app="WhatsApp",
        source_package="com.whatsapp",
        sender="Friend",
        title="Friend",
        body="lol that's hilarious 😂",
        received_at=datetime.now(timezone.utc),
        processing_status="pending",
    )
    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    await process_notification_background(event.id)

    await db_session.refresh(event)
    assert event.processing_status == "processed"
    assert event.ai_result["actionable"] is False

    # Ensure no open loop was created
    res = await client.get(f"/api/v1/open-loops?user_id={test_user.id}")
    assert res.status_code == 200
    assert res.json()["total"] == 0
