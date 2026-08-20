import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.open_loop import OpenLoop
from app.models.user import User


@pytest.mark.asyncio
async def test_complete_api_suite_all_14_endpoints(client: AsyncClient, db_session: AsyncSession, test_user: User):
    """
    Comprehensive test hitting every single one of the 14 API endpoints:
    1. GET /health
    2. GET /health/db
    3. POST /api/v1/notifications
    4. GET /api/v1/notifications/{event_id}
    5. GET /api/v1/notifications
    6. GET /api/v1/open-loops
    7. GET /api/v1/open-loops/{id}
    8. PATCH /api/v1/open-loops/{id}
    9. POST /api/v1/open-loops/{id}/complete
    10. POST /api/v1/open-loops/{id}/dismiss
    11. POST /api/v1/reminders
    12. GET /api/v1/reminders
    13. PATCH /api/v1/reminders/{id}
    14. POST /api/v1/reminders/{id}/cancel
    """
    # 1. Health Endpoints
    r_health = await client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json() == {"status": "ok"}

    r_health_db = await client.get("/health/db")
    assert r_health_db.status_code == 200
    assert r_health_db.json()["database"] == "connected"

    # 2. Notification Endpoints (POST, GET by ID, GET list)
    notif_payload = {
        "user_id": str(test_user.id),
        "source_app": "WhatsApp",
        "source_package": "com.whatsapp",
        "sender": "Alice",
        "title": "Alice",
        "body": "Can you review the design mockups tomorrow?",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "client_event_id": "test-e2e-001",
    }
    r_post_notif = await client.post("/api/v1/notifications", json=notif_payload)
    assert r_post_notif.status_code == 202
    event_id = r_post_notif.json()["event_id"]

    r_get_notif = await client.get(f"/api/v1/notifications/{event_id}")
    assert r_get_notif.status_code == 200
    assert r_get_notif.json()["id"] == event_id
    assert r_get_notif.json()["sender"] == "Alice"

    r_list_notif = await client.get(f"/api/v1/notifications?user_id={test_user.id}&limit=10&offset=0")
    assert r_list_notif.status_code == 200
    assert r_list_notif.json()["total"] >= 1

    # 3. Open Loop Endpoints (GET list, GET by ID, PATCH, complete, dismiss)
    loop = OpenLoop(
        user_id=test_user.id,
        task="Review design mockups",
        person="Alice",
        deadline=datetime.now(timezone.utc) + timedelta(days=1),
        deadline_text="tomorrow",
        importance="medium",
        confidence=0.95,
        reason="Action request from Alice",
        status="open",
    )
    db_session.add(loop)
    await db_session.commit()
    await db_session.refresh(loop)

    # 3a. GET /api/v1/open-loops
    r_list_loops = await client.get(f"/api/v1/open-loops?user_id={test_user.id}&status=open")
    assert r_list_loops.status_code == 200
    assert r_list_loops.json()["total"] >= 1

    # 3b. GET /api/v1/open-loops/{id}
    r_get_loop = await client.get(f"/api/v1/open-loops/{loop.id}")
    assert r_get_loop.status_code == 200
    assert r_get_loop.json()["task"] == "Review design mockups"

    # 3c. PATCH /api/v1/open-loops/{id}
    r_patch_loop = await client.patch(
        f"/api/v1/open-loops/{loop.id}",
        json={"importance": "high", "task": "Review and approve design mockups"},
    )
    assert r_patch_loop.status_code == 200
    assert r_patch_loop.json()["importance"] == "high"
    assert r_patch_loop.json()["task"] == "Review and approve design mockups"

    # 3d. POST /api/v1/open-loops/{id}/complete
    r_complete = await client.post(f"/api/v1/open-loops/{loop.id}/complete")
    assert r_complete.status_code == 200
    assert r_complete.json()["status"] == "completed"
    assert r_complete.json()["completed_at"] is not None

    # 3e. POST /api/v1/open-loops/{id}/dismiss
    loop2 = OpenLoop(
        user_id=test_user.id,
        task="Optional sync",
        person="Bob",
        importance="low",
        confidence=0.80,
        reason="Optional invite",
        status="open",
    )
    db_session.add(loop2)
    await db_session.commit()
    await db_session.refresh(loop2)

    r_dismiss = await client.post(f"/api/v1/open-loops/{loop2.id}/dismiss")
    assert r_dismiss.status_code == 200
    assert r_dismiss.json()["status"] == "dismissed"

    # 4. Reminder Endpoints (POST, GET list, PATCH, cancel)
    rem_time = datetime.now(timezone.utc) + timedelta(hours=6)
    r_post_rem = await client.post(
        "/api/v1/reminders",
        json={
            "user_id": str(test_user.id),
            "open_loop_id": str(loop.id),
            "scheduled_for": rem_time.isoformat(),
        },
    )
    assert r_post_rem.status_code == 201
    reminder_id = r_post_rem.json()["id"]
    assert r_post_rem.json()["status"] == "scheduled"

    # 4b. GET /api/v1/reminders
    r_list_rem = await client.get(f"/api/v1/reminders?user_id={test_user.id}&open_loop_id={loop.id}")
    assert r_list_rem.status_code == 200
    assert r_list_rem.json()["total"] == 1

    # 4c. PATCH /api/v1/reminders/{id}
    new_rem_time = rem_time + timedelta(hours=2)
    r_patch_rem = await client.patch(
        f"/api/v1/reminders/{reminder_id}",
        json={"scheduled_for": new_rem_time.isoformat()},
    )
    assert r_patch_rem.status_code == 200

    # 4d. POST /api/v1/reminders/{id}/cancel
    r_cancel_rem = await client.post(f"/api/v1/reminders/{reminder_id}/cancel")
    assert r_cancel_rem.status_code == 200
    assert r_cancel_rem.json()["status"] == "cancelled"
