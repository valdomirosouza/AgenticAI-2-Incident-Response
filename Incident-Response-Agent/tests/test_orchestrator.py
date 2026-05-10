import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.orchestrator import run_analysis
from app.models.report import IncidentReport, Severity, SpecialistFinding
from tests.conftest import FakeResponse, FakeTextBlock

_OK_FINDING = SpecialistFinding(specialist="Latency", severity=Severity.OK,
                                 summary="OK", details="All good")
_WARN_FINDING = SpecialistFinding(specialist="Errors", severity=Severity.WARNING,
                                   summary="High 4xx", details="4xx rate 25%")
_CRIT_FINDING = SpecialistFinding(specialist="Saturation", severity=Severity.CRITICAL,
                                   summary="Memory full", details="95% used")
_OK_TRAFFIC = SpecialistFinding(specialist="Traffic", severity=Severity.OK,
                                  summary="Stable", details="50 RPS")


def _synth_response(data: dict) -> FakeResponse:
    return FakeResponse(stop_reason="end_turn", content=[FakeTextBlock(text=json.dumps(data))])


async def test_run_analysis_all_ok():
    synth_data = {
        "overall_severity": "ok",
        "title": "System Healthy",
        "diagnosis": "All signals within normal bounds.",
        "recommendations": ["Continue monitoring."],
    }

    with patch("app.agents.specialists.latency.create_latency_agent") as mock_la, \
         patch("app.agents.specialists.errors.create_errors_agent") as mock_ea, \
         patch("app.agents.specialists.saturation.create_saturation_agent") as mock_sa, \
         patch("app.agents.specialists.traffic.create_traffic_agent") as mock_ta, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        for mock_factory, finding in [
            (mock_la, _OK_FINDING),
            (mock_ea, _OK_FINDING),
            (mock_sa, _OK_FINDING),
            (mock_ta, _OK_TRAFFIC),
        ]:
            mock_agent = AsyncMock()
            mock_agent.analyze.return_value = finding
            mock_factory.return_value = mock_agent

        # Call orchestrator directly
        from app.agents.orchestrator import run_analysis as _run
        report = await _run()

    assert isinstance(report, IncidentReport)
    assert report.overall_severity == Severity.OK
    assert report.title == "System Healthy"
    assert len(report.findings) == 4


async def test_run_analysis_critical_severity():
    synth_data = {
        "overall_severity": "critical",
        "title": "Redis Memory Exhausted",
        "diagnosis": "Redis is at 95% memory usage.",
        "recommendations": ["Scale Redis", "Flush stale keys"],
    }

    with patch("app.agents.specialists.latency.create_latency_agent") as mock_la, \
         patch("app.agents.specialists.errors.create_errors_agent") as mock_ea, \
         patch("app.agents.specialists.saturation.create_saturation_agent") as mock_sa, \
         patch("app.agents.specialists.traffic.create_traffic_agent") as mock_ta, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        for mock_factory, finding in [
            (mock_la, _OK_FINDING),
            (mock_ea, _WARN_FINDING),
            (mock_sa, _CRIT_FINDING),
            (mock_ta, _OK_TRAFFIC),
        ]:
            mock_agent = AsyncMock()
            mock_agent.analyze.return_value = finding
            mock_factory.return_value = mock_agent

        from app.agents.orchestrator import run_analysis as _run
        report = await _run()

    assert report.overall_severity == Severity.CRITICAL
    assert "Redis" in report.title
    assert len(report.recommendations) == 2


async def test_orchestrator_fallback_on_bad_json():  # noqa: no client fixture needed
    bad_response = FakeResponse(stop_reason="end_turn", content=[FakeTextBlock(text="not json")])

    with patch("app.agents.specialists.latency.create_latency_agent") as mock_la, \
         patch("app.agents.specialists.errors.create_errors_agent") as mock_ea, \
         patch("app.agents.specialists.saturation.create_saturation_agent") as mock_sa, \
         patch("app.agents.specialists.traffic.create_traffic_agent") as mock_ta, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=bad_response)
        for mock_factory, finding in [
            (mock_la, _OK_FINDING),
            (mock_ea, _WARN_FINDING),
            (mock_sa, _OK_FINDING),
            (mock_ta, _OK_TRAFFIC),
        ]:
            mock_agent = AsyncMock()
            mock_agent.analyze.return_value = finding
            mock_factory.return_value = mock_agent

        from app.agents.orchestrator import run_analysis as _run
        report = await _run()

    # Fallback derives severity from findings (max = WARNING)
    assert report.overall_severity == Severity.WARNING


async def test_analyze_endpoint_returns_200(client):
    synth_data = {
        "overall_severity": "ok",
        "title": "System Healthy",
        "diagnosis": "Everything is fine.",
        "recommendations": [],
    }

    with patch("app.agents.specialists.latency.create_latency_agent") as mock_la, \
         patch("app.agents.specialists.errors.create_errors_agent") as mock_ea, \
         patch("app.agents.specialists.saturation.create_saturation_agent") as mock_sa, \
         patch("app.agents.specialists.traffic.create_traffic_agent") as mock_ta, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        for mock_factory, finding in [
            (mock_la, _OK_FINDING),
            (mock_ea, _OK_FINDING),
            (mock_sa, _OK_FINDING),
            (mock_ta, _OK_TRAFFIC),
        ]:
            mock_agent = AsyncMock()
            mock_agent.analyze.return_value = finding
            mock_factory.return_value = mock_agent

        response = await client.post("/analyze")

    assert response.status_code == 200
    data = response.json()
    assert data["overall_severity"] == "ok"
    assert "findings" in data
    assert len(data["findings"]) == 4
