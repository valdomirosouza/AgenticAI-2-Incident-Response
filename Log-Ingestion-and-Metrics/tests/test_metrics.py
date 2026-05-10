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


# --- Overview (Errors + Error Rate) ---

async def test_overview_empty(client):
    response = await client.get("/metrics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_requests"] == 0
    assert data["errors_4xx"] == 0
    assert data["errors_5xx"] == 0
    assert data["error_rate_4xx_pct"] == 0.0
    assert data["error_rate_5xx_pct"] == 0.0


async def test_overview_after_ingest(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/overview")).json()
    assert data["total_requests"] == 1
    assert data["errors_4xx"] == 0
    assert data["errors_5xx"] == 0
    assert data["error_rate_4xx_pct"] == 0.0
    assert data["error_rate_5xx_pct"] == 0.0


async def test_overview_counts_errors(client):
    await client.post("/logs", json={**SAMPLE_LOG, "status_code": 500})
    data = (await client.get("/metrics/overview")).json()
    assert data["errors_5xx"] == 1


async def test_overview_error_rate(client):
    await client.post("/logs", json=SAMPLE_LOG)
    await client.post("/logs", json=SAMPLE_LOG)
    await client.post("/logs", json={**SAMPLE_LOG, "status_code": 500})
    data = (await client.get("/metrics/overview")).json()
    assert data["total_requests"] == 3
    assert data["errors_5xx"] == 1
    assert data["error_rate_5xx_pct"] == pytest.approx(33.33, abs=0.01)
    assert data["error_rate_4xx_pct"] == 0.0


async def test_overview_error_rate_4xx(client):
    await client.post("/logs", json=SAMPLE_LOG)
    await client.post("/logs", json={**SAMPLE_LOG, "status_code": 404})
    data = (await client.get("/metrics/overview")).json()
    assert data["error_rate_4xx_pct"] == pytest.approx(50.0)


# --- Status codes ---

async def test_status_codes(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/status-codes")).json()
    assert data["200"] == 1


async def test_status_codes_empty(client):
    data = (await client.get("/metrics/status-codes")).json()
    assert data == {}


# --- Backends / Frontends (Traffic) ---

async def test_backends(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/backends")).json()
    assert data["api-backend"] == 1


async def test_frontends(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/frontends")).json()
    assert data["http-in"] == 1


# --- Latency ---

async def test_response_times_empty(client):
    data = (await client.get("/metrics/response-times")).json()
    assert data == {"p50": None, "p95": None, "p99": None, "count": 0}


async def test_response_times_single_entry(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/response-times")).json()
    assert data["count"] == 1
    assert data["p50"] == 13.0


# --- Traffic (RPS) ---

async def test_rps_returns_dict(client):
    await client.post("/logs", json=SAMPLE_LOG)
    data = (await client.get("/metrics/rps?minutes=5")).json()
    assert isinstance(data, dict)
    assert len(data) == 5


async def test_rps_invalid_minutes(client):
    response = await client.get("/metrics/rps?minutes=0")
    assert response.status_code == 422


# --- Saturation ---

async def test_saturation_returns_redis_fields(client, fake_redis):
    from unittest.mock import AsyncMock
    fake_redis.info = AsyncMock(return_value={
        "used_memory": 1048576,
        "used_memory_peak": 2097152,
        "maxmemory": 0,
        "connected_clients": 3,
        "blocked_clients": 0,
        "rejected_connections": 0,
    })
    data = (await client.get("/metrics/saturation")).json()
    redis_info = data["redis"]
    assert "used_memory_bytes" in redis_info
    assert "used_memory_peak_bytes" in redis_info
    assert "maxmemory_bytes" in redis_info
    assert "memory_usage_pct" in redis_info
    assert "connected_clients" in redis_info
    assert "blocked_clients" in redis_info
    assert "rejected_connections" in redis_info


async def test_saturation_memory_pct_null_when_no_limit(client, fake_redis):
    from unittest.mock import AsyncMock
    fake_redis.info = AsyncMock(return_value={
        "used_memory": 1048576,
        "used_memory_peak": 1048576,
        "maxmemory": 0,
        "connected_clients": 1,
        "blocked_clients": 0,
        "rejected_connections": 0,
    })
    data = (await client.get("/metrics/saturation")).json()
    assert data["redis"]["maxmemory_bytes"] == 0
    assert data["redis"]["memory_usage_pct"] is None


async def test_saturation_memory_pct_calculated_when_limit_set(client, fake_redis):
    from unittest.mock import AsyncMock
    fake_redis.info = AsyncMock(return_value={
        "used_memory": 536870912,   # 512MB used
        "used_memory_peak": 536870912,
        "maxmemory": 1073741824,    # 1GB limit
        "connected_clients": 2,
        "blocked_clients": 0,
        "rejected_connections": 0,
    })
    data = (await client.get("/metrics/saturation")).json()
    assert data["redis"]["memory_usage_pct"] == pytest.approx(50.0)
