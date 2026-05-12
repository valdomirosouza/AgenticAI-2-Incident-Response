# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic AI Incident Response system with three modules:

- **`Log-Ingestion-and-Metrics/`** — FastAPI service that ingests HAProxy logs and exposes aggregated metrics via Redis (port 8000)
- **`Incident-Response-Agent/`** — Multi-agent AI copilot that queries the metrics service and produces structured `IncidentReport` objects using Claude tool-use (port 8001)
- **`Knowledge-Base/`** — Vector knowledge base (Qdrant + sentence-transformers) that stores historical incident knowledge and exposes semantic search (port 8002)

All three services run together via `docker compose up --build` from the project root.

## Module: Incident-Response-Agent

### Commands

```bash
cd Incident-Response-Agent

# Install dependencies
pip install -r requirements.txt

# Run development server (requires ANTHROPIC_API_KEY in .env)
uvicorn app.main:app --reload --port 8001

# Run tests (no API key or running services required)
pytest

# Run a single test file
pytest tests/test_specialists.py -v
```

### Architecture

```
Incident-Response-Agent/
  app/
    main.py                    # FastAPI app, SecurityHeadersMiddleware, POST /analyze
    config.py                  # Settings (ANTHROPIC_API_KEY, thresholds, model)
    agents/
      orchestrator.py          # Runs 4 specialists via asyncio.gather, calls Claude to synthesize
      specialists/
        base.py                # SpecialistAgent: tool-use loop until stop_reason != "tool_use"
        latency.py             # Latency specialist — GET /metrics/response-times
        errors.py              # Errors specialist  — GET /metrics/overview + /status-codes
        saturation.py          # Saturation specialist — GET /metrics/saturation
        traffic.py             # Traffic specialist  — GET /metrics/rps + /backends
    tools/
      metrics_client.py        # httpx async client wrapping all Log-Ingestion-and-Metrics endpoints
    models/
      report.py                # SpecialistFinding, IncidentReport (Pydantic), Severity enum
  tests/
    conftest.py                # FakeTextBlock, FakeToolUseBlock, FakeResponse helpers + client fixture
    test_specialists.py        # Per-specialist unit tests with mocked Anthropic + metrics client
    test_orchestrator.py       # Orchestrator integration tests + /analyze endpoint test
    test_metrics_client.py     # HTTP client unit tests with mocked httpx
  requirements.txt
  .env.example                 # ANTHROPIC_API_KEY= (empty — .env is loaded by docker-compose)
```

### Key Design Decisions

- **Multi-agent pattern**: each specialist is an independent Claude API call with its own system prompt and tools; the orchestrator makes a fifth call to synthesize all four findings.
- **Tool-use loop** (`base.py`): sends messages to Claude, executes any `tool_use` blocks by calling the metrics HTTP API, appends results, and loops until `stop_reason == "end_turn"`.
- **Parallel execution**: `asyncio.gather(*[agent.analyze() for agent in agents])` runs all specialists concurrently, bounded only by Claude API latency.
- **Graceful degradation**: JSON parse failures in specialist or orchestrator responses fall back to a safe `SpecialistFinding` / `IncidentReport` with WARNING severity and raw text details.
- **Security**: returns `503` with empty body when `ANTHROPIC_API_KEY` is not configured; `SecurityHeadersMiddleware` adds `X-Content-Type-Options` and `Cross-Origin-Resource-Policy` to all responses.
- **Testability**: tool handlers reference `_mc.function` (module-level lookup) so `patch("app.tools.metrics_client.X")` correctly intercepts calls inside lambdas at test time.

### Environment Variables

| Variable                       | Default                 | Description                                  |
| ------------------------------ | ----------------------- | -------------------------------------------- |
| `ANTHROPIC_API_KEY`            | _(empty)_               | Anthropic API key — required for /analyze    |
| `METRICS_API_URL`              | `http://localhost:8000` | URL of the Log-Ingestion-and-Metrics service |
| `MODEL`                        | `claude-sonnet-4-6`     | Claude model used by all agents              |
| `MAX_TOKENS`                   | `2048`                  | Max tokens per agent call                    |
| `LATENCY_P95_THRESHOLD_MS`     | `500`                   | P95 WARNING threshold (ms)                   |
| `LATENCY_P99_THRESHOLD_MS`     | `1000`                  | P99 CRITICAL threshold (ms)                  |
| `ERROR_RATE_5XX_THRESHOLD_PCT` | `5.0`                   | 5xx rate WARNING threshold (%)               |
| `ERROR_RATE_4XX_THRESHOLD_PCT` | `20.0`                  | 4xx rate WARNING threshold (%)               |
| `MEMORY_USAGE_THRESHOLD_PCT`   | `80.0`                  | Redis memory WARNING threshold (%)           |

---

## Module: Knowledge-Base

### Commands

```bash
cd Knowledge-Base

# Install dependencies
pip install -r requirements.txt

# Run development server (requires Qdrant running)
uvicorn app.main:app --reload --port 8002

# Run tests (no Qdrant or embedding model required)
pytest

# Seed the 4 historical incidents (requires Qdrant on localhost:6333)
USE_DIRECT=1 python3 ../scripts/seed_kb.py

# Seed via HTTP API (requires KB service running on localhost:8002)
python3 ../scripts/seed_kb.py
```

### Architecture

```
Knowledge-Base/
  app/
    main.py               # FastAPI app, SecurityHeadersMiddleware
    config.py             # Settings (QDRANT_URL, EMBEDDING_MODEL, EMBEDDING_DIM)
    dependencies.py       # @lru_cache singletons — get_embedding_service, get_qdrant_service
    models/
      chunk.py            # ChunkType (12 types), ChunkMetadata, KBChunkRequest/Response,
                          # IncidentIngestRequest, SearchRequest/Response (all Pydantic)
    routers/
      health.py           # GET /health — verifies Qdrant connectivity
      ingest.py           # POST /kb/ingest/chunk, POST /kb/ingest/incident
      search.py           # POST /kb/search (semantic + metadata filters)
      incidents.py        # GET /kb/incidents, GET /kb/incidents/{id}, DELETE /kb/incidents/{id}
    services/
      embeddings.py       # EmbeddingService — all-MiniLM-L6-v2 (384-dim), runs in executor
      qdrant_service.py   # QdrantService — AsyncQdrantClient, query_points API (v1.18+)
      ingestion.py        # incident_to_chunks — explodes IncidentIngestRequest into typed chunks
  tests/
    conftest.py           # FakeEmbeddingService, FakeQdrantService, client fixture
    test_ingest.py        # Chunk + incident ingest tests (chunk count assertions)
    test_search.py        # Semantic search + filter + validation tests
    test_incidents.py     # CRUD, dedup, cascading delete + health endpoint
  requirements.txt
  .env.example
scripts/
  seed_kb.py             # Seeds INC-001..004 — 98 chunks — supports HTTP and direct mode
```

### Chunk Types

| Type                   | Content                                                  |
| ---------------------- | -------------------------------------------------------- |
| `postmortem`           | Executive summary and full post-mortem narrative         |
| `symptom_fingerprint`  | Canonical signal patterns → root cause mappings          |
| `log_evidence`         | Raw log excerpts with source and context                 |
| `recovery_command`     | Shell commands used to restore services                  |
| `runbook_step`         | Ordered playbook steps with HITL/HOTL classification     |
| `lesson_learned`       | Actionable learnings from each incident                  |
| `metric_snapshot`      | P50/P95/P99/error rates/RPS at detection, peak, recovery |
| `error_budget`         | SLO target, duration, and budget consumed per incident   |
| `precursor_signal`     | Early warning patterns that preceded the incident        |
| `deployment_event`     | Deploy timestamps, versions, services (future use)       |
| `reasoning_transcript` | Agent diagnostic reasoning (future use)                  |
| `cuj_impact`           | Critical User Journey affected (future use)              |

### Key Design Decisions

- **No lifespan**: services are initialized lazily via `@lru_cache` in `dependencies.py` and injected with `Depends` — same pattern as `Incident-Response-Agent`. Tests use `app.dependency_overrides` to inject fakes without touching real services.
- **Batch embedding**: `POST /kb/ingest/incident` embeds all chunks in a single `encode()` call via `embed_batch`, minimizing model overhead.
- **`query_points` API**: qdrant-client ≥ 1.13 replaced `client.search()` with `client.query_points()`. The service uses the new API; do not revert to `search()`.
- **Hybrid filters**: `_build_filter` in `qdrant_service.py` maps `SearchRequest` fields to Qdrant `Filter(must=[...])` — multi-value `chunk_types` uses `Filter(should=[...])` (OR logic) nested inside the `must` clause.
- **Payload serialization**: `metadata.model_dump(mode="json", exclude_none=True)` ensures enum values are stored as plain strings in Qdrant payload, enabling filter comparisons.

### Endpoints

| Method   | Path                  | Description                                                                              |
| -------- | --------------------- | ---------------------------------------------------------------------------------------- |
| `GET`    | `/health`             | Service status + Qdrant connectivity                                                     |
| `POST`   | `/kb/ingest/chunk`    | Store a single typed chunk (201)                                                         |
| `POST`   | `/kb/ingest/incident` | Auto-explode a full incident into N chunks (201)                                         |
| `POST`   | `/kb/search`          | Semantic search with optional filters (golden_signal, severity, chunk_type, incident_id) |
| `GET`    | `/kb/incidents`       | List all incident IDs stored in the KB                                                   |
| `GET`    | `/kb/incidents/{id}`  | Retrieve all chunks for an incident (404 if missing)                                     |
| `DELETE` | `/kb/incidents/{id}`  | Remove all chunks for an incident (204 / 404)                                            |

### Environment Variables

| Variable               | Default                 | Description                         |
| ---------------------- | ----------------------- | ----------------------------------- |
| `QDRANT_URL`           | `http://localhost:6333` | Qdrant connection URL               |
| `QDRANT_COLLECTION`    | `incidents`             | Qdrant collection name              |
| `EMBEDDING_MODEL`      | `all-MiniLM-L6-v2`      | sentence-transformers model name    |
| `EMBEDDING_DIM`        | `384`                   | Vector dimension (must match model) |
| `SEARCH_LIMIT_DEFAULT` | `10`                    | Default result count for search     |

---

## Module: Log-Ingestion-and-Metrics

### Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Run a single test file
pytest tests/test_ingest.py -v

# Run a single test
pytest tests/test_ingest.py::test_function_name -v

# Check Redis connection (requires Redis running)
redis-cli ping
```

### Architecture

```
Log-Ingestion-and-Metrics/
  app/
    main.py           # FastAPI app factory, mounts routers, lifespan (Redis pool)
    routers/
      ingest.py       # POST /logs — validates & processes HAProxy log entries
      metrics.py      # GET /metrics/* — reads aggregated data from Redis
    models/
      log_entry.py    # Pydantic model for HAProxy JSON log schema
    services/
      ingestion.py    # Business logic: parse log, update Redis counters
      metrics.py      # Business logic: query and format Redis metrics
    redis_client.py   # Shared async Redis connection pool (aioredis)
  tests/
  requirements.txt
  .env.example
```

### HAProxy Log JSON Schema

Expected fields on `POST /logs`:

| Field               | Type             | Description                                   |
| ------------------- | ---------------- | --------------------------------------------- |
| `time_local`        | string (ISO8601) | Request timestamp                             |
| `client_ip`         | string           | Client IP address                             |
| `frontend_name`     | string           | HAProxy frontend                              |
| `backend_name`      | string           | HAProxy backend                               |
| `http_request`      | string           | Full request line (e.g. `GET /path HTTP/1.1`) |
| `status_code`       | int              | HTTP response status                          |
| `bytes_read`        | int              | Response body size in bytes                   |
| `time_request`      | int              | ms waiting for full request                   |
| `time_connect`      | int              | ms to establish backend connection            |
| `time_response`     | int              | ms waiting for backend response header        |
| `time_active`       | int              | ms total active time                          |
| `termination_state` | string           | HAProxy termination flags (e.g. `----`)       |

### Redis Metrics Keys

| Key pattern                      | Type             | Description                                                            |
| -------------------------------- | ---------------- | ---------------------------------------------------------------------- |
| `metrics:requests:total`         | String (counter) | Total log entries ingested                                             |
| `metrics:status:{code}`          | String (counter) | Count per HTTP status code                                             |
| `metrics:backend:{name}`         | String (counter) | Count per backend name                                                 |
| `metrics:frontend:{name}`        | String (counter) | Count per frontend name                                                |
| `metrics:errors:4xx`             | String (counter) | Total 4xx responses                                                    |
| `metrics:errors:5xx`             | String (counter) | Total 5xx responses                                                    |
| `metrics:response_times`         | Sorted Set       | `time_active` values (score=value, member=uuid) for percentile queries |
| `metrics:rps:{YYYY-MM-DDTHH:MM}` | String (counter) | Requests per minute bucket (TTL: 2h)                                   |

### Key Design Decisions

- Redis pipeline/multi-exec is used in `ingestion.py` to update all counters atomically per log entry.
- Response time percentiles (p50/p95/p99) are computed via `ZRANGEBYSCORE` on the `metrics:response_times` sorted set; the set is capped by a `ZREMRANGEBYRANK` trim after each insert to bound memory.
- The Redis connection pool is created once at app startup via FastAPI `lifespan` and injected via `Depends`.
- All ingestion logic is async to avoid blocking the event loop during Redis I/O.

### Environment Variables

| Variable                    | Default                    | Description                                  |
| --------------------------- | -------------------------- | -------------------------------------------- |
| `REDIS_URL`                 | `redis://localhost:6379/0` | Redis connection string                      |
| `RESPONSE_TIME_MAX_ENTRIES` | `100000`                   | Max entries in the response times sorted set |
| `LOG_LEVEL`                 | `info`                     | Uvicorn log level                            |

---

## Validated Incident Scenarios

Four end-to-end scenarios validated with the Agentic AI Copilot skill, covering all Four Golden Signals. Post-mortems in `docs/post-mortems/`.

| ID      | Signal           | Symptom                           | Root Cause                                 | Resolution                            |
| ------- | ---------------- | --------------------------------- | ------------------------------------------ | ------------------------------------- |
| INC-001 | Latency + Errors | P99 = 1.800ms + 5xx spike         | Backend deploy regression                  | Rollback (HITL)                       |
| INC-002 | Saturation       | Redis memory at 90%               | Counters without TTL + `noeviction` policy | `maxmemory-policy allkeys-lru` (HITL) |
| INC-003 | Errors           | 25% 4xx on `/api/checkout` (401)  | Auth service deploy broke JWT validation   | Rollback (HITL)                       |
| INC-004 | Traffic          | RPS = 0 for 5+ min (total outage) | HAProxy process crashed                    | HAProxy restart (HITL)                |

**Key patterns to recognize:**

- P99 spike + 5xx → backend timeout cascade → check for recent deploy first
- Redis > 80% + `noeviction` → imminent write failure → change eviction policy before touching data
- 4xx dominant on critical endpoint → check specific code (401 = auth, 404 = routing, 429 = rate limit)
- RPS = 0 + health check OK → upstream problem (load balancer, DNS, network), not application
