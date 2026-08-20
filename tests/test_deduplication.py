import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.notification_event import NotificationEvent
from app.services.notification_service import process_notification_background


@pytest.mark.asyncio
async def test_open_loop_deduplication_and_updating(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """
    Notification 1: 'Can you send me the investor deck tomorrow?' -> Creates OpenLoop
    Notification 2: 'Hey, just checking on that deck.' -> Updates existing OpenLoop rather than creating duplicate
    """
    now = datetime.now(timezone.utc)

    # 1. First Notification
    event1 = NotificationEvent(
        user_id=test_user.id,
        source_app="WhatsApp",
        source_package="com.whatsapp",
        sender="Rahul",
        title="Rahul",
        body="Can you send me the investor deck tomorrow?",
        received_at=now,
        processing_status="pending",
    )
    db_session.add(event1)
    await db_session.commit()
    await db_session.refresh(event1)

    await process_notification_background(event1.id)

    # Check 1 OpenLoop created
    res1 = await client.get(f"/api/v1/open-loops?user_id={test_user.id}")
    assert res1.status_code == 200
    assert res1.json()["total"] == 1
    original_loop_id = res1.json()["items"][0]["id"]

    # 2. Second Related Notification from same person on same topic
    event2 = NotificationEvent(
        user_id=test_user.id,
        source_app="WhatsApp",
        source_package="com.whatsapp",
        sender="Rahul",
        title="Rahul",
        body="Hey, just checking on that deck.",
        received_at=now,
        processing_status="pending",
    )
    db_session.add(event2)
    await db_session.commit()
    await db_session.refresh(event2)

    await process_notification_background(event2.id)

    # Check still only 1 OpenLoop exists, and it's updated
    res2 = await client.get(f"/api/v1/open-loops?user_id={test_user.id}")
    assert res2.status_code == 200
    data = res2.json()
    assert data["total"] == 1
    updated_loop = data["items"][0]
    assert updated_loop["id"] == original_loop_id
    assert "Follow-up" in updated_loop["reason"] or "inquiry" in updated_loop["reason"].lower()
