# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic AI Incident Response system. The `Log-Ingestion-and-Metrics/` module is a single FastAPI service with two route groups:

- **Ingestion API** — receives HAProxy logs in JSON format and stores metrics in Redis
- **Metrics API** — reads aggregated metrics from Redis

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
