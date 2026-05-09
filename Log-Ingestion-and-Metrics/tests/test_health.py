from unittest.mock import AsyncMock


async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["components"]["api"] == "healthy"
    assert body["components"]["redis"] == "healthy"


async def test_health_redis_down(client, fake_redis):
    fake_redis.ping = AsyncMock(side_effect=Exception("down"))
    response = await client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["components"]["redis"] == "unhealthy"
