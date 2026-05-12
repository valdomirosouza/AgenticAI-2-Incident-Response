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

_KB_CHUNK = {
    "id": "abc-123",
    "content": "Padrão de sintoma — INC-002: Redis memory > 90% + maxmemory-policy: noeviction",
    "metadata": {"incident_id": "INC-002", "chunk_type": "symptom_fingerprint"},
    "score": 0.88,
}


def _synth_response(data: dict) -> FakeResponse:
    return FakeResponse(stop_reason="end_turn", content=[FakeTextBlock(text=json.dumps(data))])


def _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta, findings):
    for mock_factory, finding in zip([mock_la, mock_ea, mock_sa, mock_ta], findings):
        mock_agent = AsyncMock()
        mock_agent.analyze.return_value = finding
        mock_factory.return_value = mock_agent


async def test_run_analysis_all_ok():
    synth_data = {
        "overall_severity": "ok",
        "title": "System Healthy",
        "diagnosis": "All signals within normal bounds.",
        "recommendations": ["Continue monitoring."],
    }

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb") as mock_kb, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _OK_FINDING, _OK_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    assert isinstance(report, IncidentReport)
    assert report.overall_severity == Severity.OK
    assert report.title == "System Healthy"
    assert len(report.findings) == 4
    assert report.similar_incidents == []
    # KB must NOT be queried when all findings are OK
    mock_kb.assert_not_called()


async def test_run_analysis_critical_severity():
    synth_data = {
        "overall_severity": "critical",
        "title": "Redis Memory Exhausted",
        "diagnosis": "Redis is at 95% memory usage.",
        "recommendations": ["Scale Redis", "Flush stale keys"],
    }

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb", AsyncMock(return_value=[])), \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _WARN_FINDING, _CRIT_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    assert report.overall_severity == Severity.CRITICAL
    assert "Redis" in report.title
    assert len(report.recommendations) == 2


async def test_run_analysis_enriches_with_kb_context():
    """KB results are surfaced in similar_incidents on the report."""
    synth_data = {
        "overall_severity": "critical",
        "title": "Redis Saturation",
        "diagnosis": "Similar to INC-002.",
        "recommendations": ["Change eviction policy to allkeys-lru"],
    }

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb", AsyncMock(return_value=[_KB_CHUNK])), \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _OK_FINDING, _CRIT_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    assert report.overall_severity == Severity.CRITICAL
    assert "INC-002" in report.similar_incidents


async def test_run_analysis_kb_unavailable_degrades_gracefully():
    """search_kb returning [] (KB down) does not affect analysis outcome."""
    synth_data = {
        "overall_severity": "warning",
        "title": "High 4xx Rate",
        "diagnosis": "Elevated 4xx errors detected.",
        "recommendations": ["Check auth service logs"],
    }

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb", AsyncMock(return_value=[])), \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _WARN_FINDING, _OK_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    assert report.overall_severity == Severity.WARNING
    assert report.similar_incidents == []


async def test_run_analysis_kb_multiple_chunks_deduplicates_incident_ids():
    """Two chunks from the same incident appear once in similar_incidents."""
    kb_results = [
        {**_KB_CHUNK, "id": "a"},
        {**_KB_CHUNK, "id": "b", "metadata": {**_KB_CHUNK["metadata"], "chunk_type": "lesson_learned"}},
    ]
    synth_data = {
        "overall_severity": "critical",
        "title": "Saturation",
        "diagnosis": "High memory.",
        "recommendations": ["Evict keys"],
    }

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb", AsyncMock(return_value=kb_results)), \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _OK_FINDING, _CRIT_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    assert report.similar_incidents.count("INC-002") == 1


async def test_orchestrator_fallback_on_bad_json():
    bad_response = FakeResponse(stop_reason="end_turn", content=[FakeTextBlock(text="not json")])

    with patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("app.tools.kb_client.search_kb", AsyncMock(return_value=[])), \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=bad_response)
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _WARN_FINDING, _OK_FINDING, _OK_TRAFFIC])

        report = await run_analysis()

    # Fallback derives severity from findings (max = WARNING)
    assert report.overall_severity == Severity.WARNING


async def test_analyze_endpoint_returns_200(client):
    synth_data = {
        "overall_severity": "ok",
        "title": "System Healthy",
        "diagnosis": "Everything is fine.",
        "recommendations": [],
    }

    import app.config as _cfg

    with patch.object(_cfg.settings, "anthropic_api_key", "test-key"), \
         patch("app.agents.orchestrator.create_latency_agent") as mock_la, \
         patch("app.agents.orchestrator.create_errors_agent") as mock_ea, \
         patch("app.agents.orchestrator.create_saturation_agent") as mock_sa, \
         patch("app.agents.orchestrator.create_traffic_agent") as mock_ta, \
         patch("anthropic.AsyncAnthropic") as mock_cls:

        mock_cls.return_value.messages.create = AsyncMock(return_value=_synth_response(synth_data))
        _mock_specialists(mock_la, mock_ea, mock_sa, mock_ta,
                          [_OK_FINDING, _OK_FINDING, _OK_FINDING, _OK_TRAFFIC])

        response = await client.post("/analyze")

    assert response.status_code == 200
    data = response.json()
    assert data["overall_severity"] == "ok"
    assert "findings" in data
    assert len(data["findings"]) == 4
    assert data["similar_incidents"] == []
