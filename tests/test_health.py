import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_get_and_head_endpoints(client: AsyncClient):
    # GET /health
    res_get = await client.get("/health")
    assert res_get.status_code == 200
    assert res_get.json() == {"status": "ok"}

    # HEAD /health
    res_head = await client.head("/health")
    assert res_head.status_code == 200
    assert res_head.text == ""

    # GET /api/v1/health
    res_v1_get = await client.get("/api/v1/health")
    assert res_v1_get.status_code == 200
    assert res_v1_get.json() == {"status": "ok"}

    # HEAD /api/v1/health
    res_v1_head = await client.head("/api/v1/health")
    assert res_v1_head.status_code == 200
    assert res_v1_head.text == ""


@pytest.mark.asyncio
async def test_health_db_get_and_head_endpoints(client: AsyncClient):
    # GET /health/db
    res_get = await client.get("/health/db")
    assert res_get.status_code == 200
    assert res_get.json() == {"status": "ok", "database": "connected"}

    # HEAD /health/db
    res_head = await client.head("/health/db")
    assert res_head.status_code == 200
    assert res_head.text == ""

    # GET /api/v1/health/db
    res_v1_get = await client.get("/api/v1/health/db")
    assert res_v1_get.status_code == 200
    assert res_v1_get.json() == {"status": "ok", "database": "connected"}

    # HEAD /api/v1/health/db
    res_v1_head = await client.head("/api/v1/health/db")
    assert res_v1_head.status_code == 200
    assert res_v1_head.text == ""
