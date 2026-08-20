import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User


@pytest.mark.asyncio
async def test_create_notification(client: AsyncClient, test_user: User):
    payload = {
        "user_id": str(test_user.id),
        "source_app": "WhatsApp",
        "source_package": "com.whatsapp",
        "sender": "Rahul",
        "title": "Rahul",
        "body": "Can you send me the investor deck tomorrow?",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "client_event_id": "test-msg-001",
    }
    response = await client.post("/api/v1/notifications", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "event_id" in data
    assert data["status"] in ["processing", "processed", "pending"]

    # Verify retrieval
    event_id = data["event_id"]
    get_res = await client.get(f"/api/v1/notifications/{event_id}")
    assert get_res.status_code == 200
    notif_data = get_res.json()
    assert notif_data["id"] == event_id
    assert notif_data["sender"] == "Rahul"
    assert notif_data["body"] == "Can you send me the investor deck tomorrow?"


@pytest.mark.asyncio
async def test_idempotency_duplicate_notification(client: AsyncClient, test_user: User):
    client_event_id = "unique-client-event-12345"
    payload = {
        "user_id": str(test_user.id),
        "source_app": "Slack",
        "source_package": "com.Slack",
        "sender": "Alice",
        "title": "Product Channel",
        "body": "Please review the roadmap deck.",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "client_event_id": client_event_id,
    }

    # First request
    res1 = await client.post("/api/v1/notifications", json=payload)
    assert res1.status_code == 202
    event_id_1 = res1.json()["event_id"]

    # Duplicate request with same client_event_id
    res2 = await client.post("/api/v1/notifications", json=payload)
    assert res2.status_code == 202
    event_id_2 = res2.json()["event_id"]

    # Must return identical event_id
    assert event_id_1 == event_id_2


@pytest.mark.asyncio
async def test_list_notifications_with_filters(client: AsyncClient, test_user: User):
    # Ingest two notifications
    for i, app_name in enumerate(["WhatsApp", "Slack"]):
        await client.post(
            "/api/v1/notifications",
            json={
                "user_id": str(test_user.id),
                "source_app": app_name,
                "source_package": f"com.{app_name.lower()}",
                "body": f"Notification {i}",
                "received_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Filter by user_id
    res = await client.get(f"/api/v1/notifications?user_id={test_user.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # Filter by source_app
    res_filtered = await client.get(f"/api/v1/notifications?source_app=Slack")
    assert res_filtered.status_code == 200
    filtered_data = res_filtered.json()
    assert filtered_data["total"] == 1
    assert filtered_data["items"][0]["source_app"] == "Slack"
