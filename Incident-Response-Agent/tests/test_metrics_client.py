from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.metrics_client import (
    fetch_backends,
    fetch_overview,
    fetch_response_times,
    fetch_rps,
    fetch_saturation,
    fetch_status_codes,
)


def _mock_response(payload: dict):
    resp = MagicMock()
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client(payload: dict):
    mock_resp = _mock_response(payload)
    mock_session = AsyncMock()
    mock_session.get.return_value = mock_resp
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return patch("httpx.AsyncClient", return_value=ctx), mock_session


async def test_fetch_overview():
    payload = {"total_requests": 10, "errors_4xx": 0, "errors_5xx": 0,
               "error_rate_4xx_pct": 0.0, "error_rate_5xx_pct": 0.0}
    patcher, _ = _patch_client(payload)
    with patcher:
        result = await fetch_overview()
    assert result["total_requests"] == 10


async def test_fetch_response_times():
    payload = {"p50": 5.0, "p95": 20.0, "p99": 50.0, "count": 100}
    patcher, _ = _patch_client(payload)
    with patcher:
        result = await fetch_response_times()
    assert result["p99"] == 50.0


async def test_fetch_status_codes():
    payload = {"200": 95, "500": 5}
    patcher, _ = _patch_client(payload)
    with patcher:
        result = await fetch_status_codes()
    assert result["500"] == 5


async def test_fetch_saturation():
    payload = {"redis": {"used_memory_bytes": 1000, "memory_usage_pct": None}}
    patcher, _ = _patch_client(payload)
    with patcher:
        result = await fetch_saturation()
    assert "redis" in result


async def test_fetch_rps():
    payload = {"2026-01-01T10:00": 10}
    patcher, mock_session = _patch_client(payload)
    with patcher:
        result = await fetch_rps(minutes=5)
    call_args = mock_session.get.call_args
    assert "minutes=5" in call_args[0][0]


async def test_fetch_backends():
    payload = {"api-backend": 42}
    patcher, _ = _patch_client(payload)
    with patcher:
        result = await fetch_backends()
    assert result["api-backend"] == 42
