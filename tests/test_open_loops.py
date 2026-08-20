import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.open_loop import OpenLoop
from app.models.user import User


@pytest.mark.asyncio
async def test_open_loop_lifecycle(client: AsyncClient, db_session: AsyncSession, test_user: User):
    # 1. Seed an open loop
    loop = OpenLoop(
        user_id=test_user.id,
        task="Finish quarterly review presentation",
        person="Manager",
        deadline=datetime.now(timezone.utc) + timedelta(days=2),
        importance="high",
        confidence=0.95,
        reason="Explicit request from manager",
        status="open",
    )
    db_session.add(loop)
    await db_session.commit()
    await db_session.refresh(loop)

    # 2. GET by ID
    get_res = await client.get(f"/api/v1/open-loops/{loop.id}")
    assert get_res.status_code == 200
    assert get_res.json()["task"] == "Finish quarterly review presentation"

    # 3. PATCH update
    patch_res = await client.patch(
        f"/api/v1/open-loops/{loop.id}",
        json={"importance": "medium", "task": "Finish Q3 review"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["importance"] == "medium"
    assert patch_res.json()["task"] == "Finish Q3 review"

    # 4. Complete
    comp_res = await client.post(f"/api/v1/open-loops/{loop.id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"
    assert comp_res.json()["completed_at"] is not None

    # 5. Dismiss
    loop2 = OpenLoop(
        user_id=test_user.id,
        task="Optional webinar",
        importance="low",
        confidence=0.8,
        reason="Optional invite",
        status="open",
    )
    db_session.add(loop2)
    await db_session.commit()
    await db_session.refresh(loop2)

    dism_res = await client.post(f"/api/v1/open-loops/{loop2.id}/dismiss")
    assert dism_res.status_code == 200
    assert dism_res.json()["status"] == "dismissed"
