import pytest

SAMPLE_LOG = {
    "time_local": "2024-01-15T10:30:00",
    "client_ip": "192.168.1.1",
    "frontend_name": "http-in",
    "backend_name": "web-backend",
    "http_request": "GET /api/health HTTP/1.1",
    "status_code": 200,
    "bytes_read": 512,
    "time_request": 0,
    "time_connect": 1,
    "time_response": 5,
    "time_active": 6,
    "termination_state": "----",
}


@pytest.mark.asyncio
async def test_ingest_returns_202(client):
    response = await client.post("/logs", json=SAMPLE_LOG)
    assert response.status_code == 202


@pytest.mark.asyncio
async def test_ingest_increments_total(client, fake_redis):
    await client.post("/logs", json=SAMPLE_LOG)
    total = await fake_redis.get("metrics:requests:total")
    assert int(total) == 1


@pytest.mark.asyncio
async def test_ingest_multiple_increments(client, fake_redis):
    for _ in range(3):
        await client.post("/logs", json=SAMPLE_LOG)
    total = await fake_redis.get("metrics:requests:total")
    assert int(total) == 3


@pytest.mark.asyncio
async def test_ingest_tracks_status_code(client, fake_redis):
    await client.post("/logs", json=SAMPLE_LOG)
    count = await fake_redis.get("metrics:status:200")
    assert int(count) == 1


@pytest.mark.asyncio
async def test_ingest_tracks_backend(client, fake_redis):
    await client.post("/logs", json=SAMPLE_LOG)
    count = await fake_redis.get("metrics:backend:web-backend")
    assert int(count) == 1


@pytest.mark.asyncio
async def test_ingest_tracks_4xx_error(client, fake_redis):
    log = {**SAMPLE_LOG, "status_code": 404}
    await client.post("/logs", json=log)
    count = await fake_redis.get("metrics:errors:4xx")
    assert int(count) == 1
    assert await fake_redis.get("metrics:errors:5xx") is None


@pytest.mark.asyncio
async def test_ingest_tracks_5xx_error(client, fake_redis):
    log = {**SAMPLE_LOG, "status_code": 503}
    await client.post("/logs", json=log)
    count = await fake_redis.get("metrics:errors:5xx")
    assert int(count) == 1
    assert await fake_redis.get("metrics:errors:4xx") is None


@pytest.mark.asyncio
async def test_ingest_records_response_time(client, fake_redis):
    await client.post("/logs", json=SAMPLE_LOG)
    count = await fake_redis.zcard("metrics:response_times")
    assert count == 1


@pytest.mark.asyncio
async def test_ingest_invalid_payload(client):
    response = await client.post("/logs", json={"invalid": "data"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_missing_field(client):
    log = {k: v for k, v in SAMPLE_LOG.items() if k != "status_code"}
    response = await client.post("/logs", json=log)
    assert response.status_code == 422
