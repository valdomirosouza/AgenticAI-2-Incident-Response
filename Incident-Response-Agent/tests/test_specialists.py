import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.specialists.errors import create_errors_agent
from app.agents.specialists.latency import create_latency_agent
from app.agents.specialists.saturation import create_saturation_agent
from app.agents.specialists.traffic import create_traffic_agent
from app.models.report import Severity
from tests.conftest import FakeResponse, FakeTextBlock, FakeToolUseBlock

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_RT_DATA = {"p50": 10.0, "p95": 50.0, "p99": 100.0, "count": 100}
_OVERVIEW_DATA = {"total_requests": 200, "errors_4xx": 2, "errors_5xx": 1,
                  "error_rate_4xx_pct": 1.0, "error_rate_5xx_pct": 0.5}
_STATUS_DATA = {"200": 197, "404": 2, "500": 1}
_SAT_DATA = {"redis": {"used_memory_bytes": 500000, "used_memory_peak_bytes": 600000,
                        "maxmemory_bytes": 0, "memory_usage_pct": None,
                        "connected_clients": 2, "blocked_clients": 0, "rejected_connections": 0}}
_RPS_DATA = {"2026-01-01T10:00": 50, "2026-01-01T10:01": 55}
_BACKENDS_DATA = {"api-backend": 200}


def _make_tool_then_text(tool_name: str, tool_input: dict, finding_json: dict):
    """Returns two FakeResponse objects: first triggers tool_use, second returns text."""
    return [
        FakeResponse(
            stop_reason="tool_use",
            content=[FakeToolUseBlock(id="tu_1", name=tool_name, input=tool_input)],
        ),
        FakeResponse(
            stop_reason="end_turn",
            content=[FakeTextBlock(text=json.dumps(finding_json))],
        ),
    ]


# ---------------------------------------------------------------------------
# Latency specialist
# ---------------------------------------------------------------------------

async def test_latency_agent_ok():
    finding_json = {"severity": "ok", "summary": "Latency is normal", "details": "P99=100ms well below threshold"}
    responses = _make_tool_then_text("get_response_times", {}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_response_times", new_callable=AsyncMock) as mock_rt:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_rt.return_value = _RT_DATA

        finding = await create_latency_agent().analyze()

    assert finding.severity == Severity.OK
    assert finding.specialist == "Latency"
    assert "normal" in finding.summary.lower()


async def test_latency_agent_critical():
    finding_json = {"severity": "critical", "summary": "P99 above 1000ms", "details": "P99=1500ms exceeds 1000ms threshold"}
    responses = _make_tool_then_text("get_response_times", {}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_response_times", new_callable=AsyncMock) as mock_rt:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_rt.return_value = {"p50": 200.0, "p95": 900.0, "p99": 1500.0, "count": 50}

        finding = await create_latency_agent().analyze()

    assert finding.severity == Severity.CRITICAL


# ---------------------------------------------------------------------------
# Errors specialist
# ---------------------------------------------------------------------------

async def test_errors_agent_ok():
    finding_json = {"severity": "ok", "summary": "Error rates within normal bounds", "details": "5xx rate 0.5%"}
    responses = _make_tool_then_text("get_overview", {}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_overview", new_callable=AsyncMock) as mock_ov, \
         patch("app.tools.metrics_client.fetch_status_codes", new_callable=AsyncMock) as mock_sc:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_ov.return_value = _OVERVIEW_DATA
        mock_sc.return_value = _STATUS_DATA

        finding = await create_errors_agent().analyze()

    assert finding.severity == Severity.OK
    assert finding.specialist == "Errors"


async def test_errors_agent_parses_warning():
    finding_json = {"severity": "warning", "summary": "5xx rate at 7%", "details": "7% exceeds 5% threshold"}
    responses = _make_tool_then_text("get_overview", {}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_overview", new_callable=AsyncMock) as mock_ov, \
         patch("app.tools.metrics_client.fetch_status_codes", new_callable=AsyncMock) as mock_sc:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_ov.return_value = _OVERVIEW_DATA
        mock_sc.return_value = _STATUS_DATA

        finding = await create_errors_agent().analyze()

    assert finding.severity == Severity.WARNING


# ---------------------------------------------------------------------------
# Saturation specialist
# ---------------------------------------------------------------------------

async def test_saturation_agent_ok():
    finding_json = {"severity": "ok", "summary": "Redis resources healthy", "details": "No maxmemory limit set"}
    responses = _make_tool_then_text("get_saturation", {}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_saturation", new_callable=AsyncMock) as mock_sat:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_sat.return_value = _SAT_DATA

        finding = await create_saturation_agent().analyze()

    assert finding.severity == Severity.OK
    assert finding.specialist == "Saturation"


# ---------------------------------------------------------------------------
# Traffic specialist
# ---------------------------------------------------------------------------

async def test_traffic_agent_ok():
    finding_json = {"severity": "ok", "summary": "Traffic is stable", "details": "~50 RPS, no anomalies"}
    responses = _make_tool_then_text("get_rps", {"minutes": 10}, finding_json)

    with patch("anthropic.AsyncAnthropic") as mock_cls, \
         patch("app.tools.metrics_client.fetch_rps", new_callable=AsyncMock) as mock_rps, \
         patch("app.tools.metrics_client.fetch_backends", new_callable=AsyncMock) as mock_be:
        mock_cls.return_value.messages.create = AsyncMock(side_effect=responses)
        mock_rps.return_value = _RPS_DATA
        mock_be.return_value = _BACKENDS_DATA

        finding = await create_traffic_agent().analyze()

    assert finding.severity == Severity.OK
    assert finding.specialist == "Traffic"


# ---------------------------------------------------------------------------
# Base fallback: invalid JSON → falls back gracefully
# ---------------------------------------------------------------------------

async def test_specialist_fallback_on_bad_json():
    bad_response = FakeResponse(stop_reason="end_turn", content=[FakeTextBlock(text="not valid json")])

    with patch("anthropic.AsyncAnthropic") as mock_cls:
        mock_cls.return_value.messages.create = AsyncMock(return_value=bad_response)

        finding = await create_latency_agent().analyze()

    assert finding.severity == Severity.WARNING
    assert finding.specialist == "Latency"
    assert finding.details == "not valid json"
