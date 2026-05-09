import pytest

SAMPLE_LOG = {
    "time_local": "2024-01-15T10:30:00",
    "client_ip": "10.0.0.1",
    "frontend_name": "http-in",
    "backend_name": "api-backend",
    "http_request": "POST /api/data HTTP/1.1",
    "status_code": 200,
    "bytes_read": 1024,
    "time_request": 1,
    "time_connect": 2,
    "time_response": 10,
    "time_active": 13,
    "termination_state": "----",
}


@pytest.mark.asyncio
async def test_overview_empty(client):
    response = await client.get("/metrics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data == {"total_requests": 0, "errors_4xx": 0, "errors_5xx": 0}


@pytest.mark.asyncio
async def test_overview_after_ingest(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/overview")).json()
    assert data["total_requests"] == 1
    assert data["errors_4xx"] == 0
    assert data["errors_5xx"] == 0


@pytest.mark.asyncio
async def test_overview_counts_errors(client):
    await client.post("/logs", json={**SAMPLE_LOG, "status_code": 500})
    data = (await client.get("/metrics/overview")).json()
    assert data["errors_5xx"] == 1


@pytest.mark.asyncio
async def test_status_codes(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/status-codes")).json()
    assert data["200"] == 1


@pytest.mark.asyncio
async def test_status_codes_empty(client):
    data = (await client.get("/metrics/status-codes")).json()
    assert data == {}


@pytest.mark.asyncio
async def test_backends(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/backends")).json()
    assert data["api-backend"] == 1


@pytest.mark.asyncio
async def test_frontends(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/frontends")).json()
    assert data["http-in"] == 1


@pytest.mark.asyncio
async def test_response_times_empty(client):
    data = (await client.get("/metrics/response-times")).json()
    assert data == {"p50": None, "p95": None, "p99": None, "count": 0}


@pytest.mark.asyncio
async def test_response_times_single_entry(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/response-times")).json()
    assert data["count"] == 1
    assert data["p50"] == 13.0


@pytest.mark.asyncio
async def test_rps_returns_dict(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/rps?minutes=5")).json()
    assert isinstance(data, dict)
    assert len(data) == 5


@pytest.mark.asyncio
async def test_rps_invalid_minutes(client):
    response = await client.get("/metrics/rps?minutes=0")
    assert response.status_code == 422
