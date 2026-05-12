async def test_search_empty_store_returns_empty(client):
    response = await client.post("/kb/search", json={"query": "HAProxy down"})
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["total"] == 0


async def test_search_returns_ingested_chunks(client):
    await client.post("/kb/ingest/chunk", json={
        "content": "HAProxy crashed, RPS dropped to zero, total outage",
        "metadata": {
            "incident_id": "INC-004",
            "chunk_type": "postmortem",
            "severity": "critical",
            "golden_signal": "traffic",
        },
    })

    response = await client.post("/kb/search", json={"query": "HAProxy down total outage"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["score"] == 0.9
    assert data["results"][0]["metadata"]["incident_id"] == "INC-004"


async def test_search_respects_limit(client):
    for i in range(5):
        await client.post("/kb/ingest/chunk", json={
            "content": f"Incident chunk {i}",
            "metadata": {"incident_id": f"INC-00{i}", "chunk_type": "postmortem"},
        })

    response = await client.post("/kb/search", json={"query": "incident", "limit": 3})
    assert response.status_code == 200
    assert response.json()["total"] <= 3


async def test_search_with_golden_signal_filter(client):
    response = await client.post("/kb/search", json={
        "query": "redis memory saturation",
        "golden_signal": "saturation",
        "severity": "critical",
        "limit": 5,
    })
    assert response.status_code == 200


async def test_search_with_chunk_type_filter(client):
    response = await client.post("/kb/search", json={
        "query": "rollback command",
        "chunk_types": ["recovery_command", "runbook_step"],
    })
    assert response.status_code == 200


async def test_search_with_incident_id_filter(client):
    response = await client.post("/kb/search", json={
        "query": "any query",
        "incident_id": "INC-001",
    })
    assert response.status_code == 200


async def test_search_limit_max_50(client):
    response = await client.post("/kb/search", json={"query": "test", "limit": 51})
    assert response.status_code == 422


async def test_search_empty_query_returns_422(client):
    response = await client.post("/kb/search", json={"query": ""})
    assert response.status_code == 422
