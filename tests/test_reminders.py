import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.open_loop import OpenLoop
from app.models.user import User


@pytest.mark.asyncio
async def test_reminders_crud_and_cancel(client: AsyncClient, db_session: AsyncSession, test_user: User):
    # Create Open Loop
    loop = OpenLoop(
        user_id=test_user.id,
        task="Submit tax forms",
        importance="high",
        confidence=0.99,
        reason="Government deadline",
        status="open",
    )
    db_session.add(loop)
    await db_session.commit()
    await db_session.refresh(loop)

    # 1. Create Reminder via POST
    target_time = datetime.now(timezone.utc) + timedelta(days=1)
    create_res = await client.post(
        "/api/v1/reminders",
        json={
            "user_id": str(test_user.id),
            "open_loop_id": str(loop.id),
            "scheduled_for": target_time.isoformat(),
        },
    )
    assert create_res.status_code == 201
    reminder_data = create_res.json()
    reminder_id = reminder_data["id"]
    assert reminder_data["status"] == "scheduled"

    # 2. List Reminders
    list_res = await client.get(f"/api/v1/reminders?user_id={test_user.id}")
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    # 3. PATCH Reminder
    new_time = target_time + timedelta(hours=3)
    patch_res = await client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"scheduled_for": new_time.isoformat()},
    )
    assert patch_res.status_code == 200

    # 4. Cancel Reminder
    cancel_res = await client.post(f"/api/v1/reminders/{reminder_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
