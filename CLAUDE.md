# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic AI Incident Response system with two modules:

- **`Log-Ingestion-and-Metrics/`** — FastAPI service that ingests HAProxy logs and exposes aggregated metrics via Redis (port 8000)
- **`Incident-Response-Agent/`** — Multi-agent AI copilot that queries the metrics service and produces structured `IncidentReport` objects using Claude tool-use (port 8001)

Both services run together via `docker compose up --build` from the project root.

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
