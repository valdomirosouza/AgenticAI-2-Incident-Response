async def test_health_returns_healthy(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["qdrant"] == "connected"


async def test_list_incidents_empty(client):
    response = await client.get("/kb/incidents")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_incident_not_found(client):
    response = await client.get("/kb/incidents/INC-999")
    assert response.status_code == 404


async def test_delete_incident_not_found(client):
    response = await client.delete("/kb/incidents/INC-999")
    assert response.status_code == 404


async def test_get_incident_after_chunk_ingest(client):
    await client.post("/kb/ingest/chunk", json={
        "content": "Redis at 90% memory — INC-002",
        "metadata": {
            "incident_id": "INC-002",
            "chunk_type": "metric_snapshot",
            "severity": "critical",
            "golden_signal": "saturation",
        },
    })

    response = await client.get("/kb/incidents/INC-002")
    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["incident_id"] == "INC-002"
    assert chunks[0]["metadata"]["chunk_type"] == "metric_snapshot"


async def test_list_incidents_after_multi_ingest(client):
    for inc_id in ["INC-001", "INC-002", "INC-003"]:
        await client.post("/kb/ingest/chunk", json={
            "content": f"Summary of {inc_id}",
            "metadata": {"incident_id": inc_id, "chunk_type": "postmortem"},
        })

    response = await client.get("/kb/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert set(incidents) == {"INC-001", "INC-002", "INC-003"}
    assert incidents == sorted(incidents)  # must be sorted


async def test_delete_incident_removes_all_chunks(client, fake_qdrant):
    # Ingest 2 chunks for INC-004 and 1 for INC-001
    for _ in range(2):
        await client.post("/kb/ingest/chunk", json={
            "content": "INC-004 chunk",
            "metadata": {"incident_id": "INC-004", "chunk_type": "postmortem"},
        })
    await client.post("/kb/ingest/chunk", json={
        "content": "INC-001 chunk",
        "metadata": {"incident_id": "INC-001", "chunk_type": "postmortem"},
    })

    assert len(fake_qdrant._store) == 3

    response = await client.delete("/kb/incidents/INC-004")
    assert response.status_code == 204

    # INC-004 gone, INC-001 remains
    assert len(fake_qdrant._store) == 1
    response = await client.get("/kb/incidents/INC-004")
    assert response.status_code == 404
    response = await client.get("/kb/incidents/INC-001")
    assert response.status_code == 200


async def test_list_incidents_deduplicates(client):
    for _ in range(3):
        await client.post("/kb/ingest/chunk", json={
            "content": "Duplicate INC-001",
            "metadata": {"incident_id": "INC-001", "chunk_type": "lesson_learned"},
        })

    response = await client.get("/kb/incidents")
    assert response.status_code == 200
    assert response.json().count("INC-001") == 1
