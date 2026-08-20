import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invalid_request_validation(client: AsyncClient):
    # Missing required body field in notification ingest
    res = await client.post(
        "/api/v1/notifications",
        json={
            "user_id": str(uuid.uuid4()),
            "source_app": "WhatsApp",
            # missing source_package, body, received_at
        },
    )
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "ValidationError"


@pytest.mark.asyncio
async def test_not_found_errors(client: AsyncClient):
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/open-loops/{random_id}")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "EntityNotFoundError"


@pytest.mark.asyncio
async def test_invalid_uuid_parameter(client: AsyncClient):
    res = await client.get("/api/v1/open-loops/not-a-valid-uuid")
    assert res.status_code == 422
