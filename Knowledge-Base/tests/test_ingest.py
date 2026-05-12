import pytest


_CHUNK_BODY = {
    "content": "Backend P99 spiked to 1800ms after deploy",
    "metadata": {
        "incident_id": "INC-001",
        "chunk_type": "symptom_fingerprint",
        "severity": "critical",
        "golden_signal": "latency",
        "affected_services": ["backend-api"],
    },
}

_INCIDENT_BODY = {
    "incident_id": "INC-001",
    "title": "P99 CRITICAL por Regressão de Deploy",
    "date": "2026-05-10",
    "severity": "critical",
    "golden_signals": ["latency", "errors"],
    "root_cause_category": "deploy_regression",
    "resolution_type": "HITL",
    "affected_services": ["backend-api"],
    "affected_cujs": ["/api/checkout"],
    "mttd_minutes": 65,
    "mttr_minutes": 75,
    "summary": "Deploy introduziu regressão no backend. P99 atingiu 1.800ms.",
    "symptom_patterns": ["P99 > 1800ms + 5xx > 8% + deploy recente"],
    "log_excerpts": [
        {
            "content": "503 0/0/0/1800/1801 - 0 FFFFFFFF - backend/srv1",
            "source": "haproxy.log",
            "context": "Timeout cascade após deploy",
        }
    ],
    "recovery_commands": [
        {
            "command": "kubectl rollout undo deployment/backend",
            "description": "Rollback para versão anterior ao deploy",
            "phase": "remediation",
        }
    ],
    "runbook_steps": [
        {
            "step_number": 1,
            "description": "Coletar snapshot de métricas pré-rollback",
            "action_type": "HOTL",
        },
        {
            "step_number": 2,
            "description": "Confirmar timestamp do último deploy",
            "action_type": "HOTL",
        },
        {
            "step_number": 3,
            "description": "Escalar réplicas defensivamente",
            "action_type": "HOTL",
            "command": "kubectl scale deployment/backend --replicas=6",
        },
        {
            "step_number": 4,
            "description": "Aprovar rollback com on-call",
            "action_type": "HITL",
        },
    ],
    "lessons_learned": [
        "MTTD de 1h — adicionar alerta automático P99 > 800ms",
        "Implementar smoke test de latência no pipeline CI/CD",
    ],
    "metric_snapshots": [
        {
            "phase": "peak",
            "p50_ms": 420,
            "p95_ms": 1100,
            "p99_ms": 1800,
            "error_rate_5xx_pct": 8.2,
            "rps": 312,
        }
    ],
    "error_budget": {
        "slo_target_pct": 99.9,
        "duration_minutes": 75,
        "budget_consumed_pct": 1.7,
        "budget_remaining_after_pct": 31.2,
    },
    "precursor_signals": [
        "P95 subindo de 250ms → 450ms nos 30min anteriores ao P99 disparar"
    ],
}


async def test_ingest_chunk_returns_201(client):
    response = await client.post("/kb/ingest/chunk", json=_CHUNK_BODY)
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == _CHUNK_BODY["content"]
    assert data["metadata"]["incident_id"] == "INC-001"
    assert data["metadata"]["chunk_type"] == "symptom_fingerprint"
    assert "id" in data
    assert data["score"] is None


async def test_ingest_chunk_security_headers(client):
    response = await client.post("/kb/ingest/chunk", json=_CHUNK_BODY)
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("cross-origin-resource-policy") == "same-origin"


async def test_ingest_chunk_missing_content_returns_422(client):
    body = {"metadata": {"incident_id": "INC-001", "chunk_type": "postmortem"}}
    response = await client.post("/kb/ingest/chunk", json=body)
    assert response.status_code == 422


async def test_ingest_chunk_empty_content_returns_422(client):
    body = {**_CHUNK_BODY, "content": ""}
    response = await client.post("/kb/ingest/chunk", json=body)
    assert response.status_code == 422


async def test_ingest_incident_returns_201(client):
    response = await client.post("/kb/ingest/incident", json=_INCIDENT_BODY)
    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] == "INC-001"
    assert data["chunks_created"] > 0
    assert len(data["chunk_ids"]) == data["chunks_created"]


async def test_ingest_incident_chunk_count(client):
    response = await client.post("/kb/ingest/incident", json=_INCIDENT_BODY)
    data = response.json()
    # summary(1) + symptom(1) + log(1) + cmd(1) + runbook(4) + lessons(2) + metric(1) + budget(1) + precursor(1) = 13
    assert data["chunks_created"] == 13


async def test_ingest_incident_minimal_body(client):
    minimal = {
        "incident_id": "INC-MIN",
        "title": "Minimal Incident",
        "date": "2026-05-10",
        "severity": "warning",
        "summary": "Just a summary.",
    }
    response = await client.post("/kb/ingest/incident", json=minimal)
    assert response.status_code == 201
    data = response.json()
    assert data["chunks_created"] == 1  # only summary chunk
    assert data["incident_id"] == "INC-MIN"


async def test_ingest_incident_chunks_stored_in_qdrant(client, fake_qdrant):
    await client.post("/kb/ingest/incident", json=_INCIDENT_BODY)
    assert len(fake_qdrant._store) == 13
