import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification_event import NotificationEvent
from app.models.open_loop import OpenLoop
from app.models.user import User
from app.scripts.seed import DEMO_DEVICE_ID, DEMO_USER_ID, seed_database


@pytest.mark.asyncio
async def test_seed_database(db_session: AsyncSession):
    await seed_database()

    # Verify user seeded
    user = await db_session.get(User, DEMO_USER_ID)
    assert user is not None
    assert user.timezone == "America/New_York"

    # Verify notifications seeded
    from sqlalchemy import select
    notifs = (await db_session.execute(select(NotificationEvent))).scalars().all()
    assert len(notifs) >= 5

    # Verify open loops seeded
    loops = (await db_session.execute(select(OpenLoop))).scalars().all()
    assert len(loops) >= 3
