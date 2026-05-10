# AgenticAI-2-Incident-Response

Research project exploring **Agentic AI as a Copilot** for reducing **MTTD** (Mean Time to Detect) and **MTTR** (Mean Time to Recovery) in IT incident response — developed as part of a Master's dissertation at **PPGCA / Unisinos**.

---

## Architecture

```mermaid
flowchart TB
    subgraph sources["Log Sources"]
        HA["HAProxy / Load Balancer"]
    end

    subgraph compose["Docker Compose"]
        subgraph service["Log-Ingestion-and-Metrics  ·  FastAPI :8000"]
            direction TB

            subgraph middleware["Middleware"]
                RLM["RequestLoggingMiddleware\nX-Request-ID  ·  JSON access log"]
                SHM["SecurityHeadersMiddleware\nX-Content-Type-Options  ·  CORP"]
            end

            subgraph routers["Routers"]
                RI["POST /logs"]
                RM["GET /metrics/*\noverview · status-codes · backends\nfrontends · response-times · rps · saturation"]
                RH["GET /health"]
                RP["GET /prometheus/metrics"]
            end

            subgraph services["Services"]
                SI["ingestion.py\nprocess_log()"]
                SM["metrics.py\nget_overview()  ·  get_saturation()\nget_response_time_percentiles()"]
            end

            subgraph observability["Observability"]
                OT["OpenTelemetry SDK\nFastAPI + Redis auto-instrumentation"]
                PI["prometheus-fastapi-instrumentator\nLatency · Traffic · Errors · Saturation"]
                JL["python-json-logger\nStructured JSON stdout"]
            end
        end

        REDIS[("Redis  :6379\n─────────────────\nmetrics:requests:total\nmetrics:status:{code}\nmetrics:errors:4xx / 5xx\nmetrics:response_times  ← P50/P95/P99\nmetrics:rps:{YYYY-MM-DDTHH:MM}\nmetrics:backend:{name}\nmetrics:frontend:{name}")]
    end

    subgraph obs_backends["Observability Backends  (external / optional)"]
        PROM["Prometheus"]
        GRAFANA["Grafana"]
        COLLECTOR["OTel Collector"]
        JAEGER["Jaeger / Tempo"]
        LOKI["Loki / ELK / Splunk"]
    end

    %% Ingestion path
    HA -->|"POST /logs  (JSON)"| RI
    RI --> SI
    SI -->|"pipeline: INCR · ZADD · EXPIRE"| REDIS

    %% Metrics query path
    RM --> SM
    SM -->|"MGET · ZRANGE · INFO"| REDIS

    %% Health check
    RH -->|"PING"| REDIS

    %% Observability outputs
    RP -->|"scrape"| PROM
    PROM --> GRAFANA
    OT -->|"OTLP gRPC"| COLLECTOR
    COLLECTOR --> JAEGER
    JL -->|"stdout JSON"| LOKI

    %% Middleware wraps all routes
    middleware -.->|"wraps"| routers
```

### Four Golden Signals coverage

| Signal         | How it is measured                                                                                                         |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Latency**    | P50 / P95 / P99 via `GET /metrics/response-times` · Histogram at `GET /prometheus/metrics`                                 |
| **Traffic**    | RPS per minute via `GET /metrics/rps` · `http_requests_total` counter in Prometheus                                        |
| **Errors**     | Error counts + rates (%) via `GET /metrics/overview` · `http_requests_total{status="5xx"}` in Prometheus                   |
| **Saturation** | Redis memory, clients, rejected connections via `GET /metrics/saturation` · `http_requests_inprogress` gauge in Prometheus |

---

## Modules

### `Log-Ingestion-and-Metrics`

FastAPI service that ingests HAProxy logs and exposes aggregated metrics via Redis. Serves as the observability data layer for the Agentic AI pipeline.

**Stack:** Python · FastAPI · Redis (aioredis) · Pydantic v2

#### API

| Method | Endpoint                  | Description                                              |
| ------ | ------------------------- | -------------------------------------------------------- |
| `GET`  | `/health`                 | Liveness check (API + Redis)                             |
| `POST` | `/logs`                   | Ingest a HAProxy log entry (JSON)                        |
| `GET`  | `/metrics/overview`       | Total requests, error counts and error rates (4xx/5xx %) |
| `GET`  | `/metrics/status-codes`   | Request count per HTTP status code                       |
| `GET`  | `/metrics/backends`       | Request count per HAProxy backend (Traffic)              |
| `GET`  | `/metrics/frontends`      | Request count per HAProxy frontend (Traffic)             |
| `GET`  | `/metrics/response-times` | Latency percentiles: P50, P95, P99                       |
| `GET`  | `/metrics/rps`            | Requests per minute for the last N minutes (Traffic)     |
| `GET`  | `/metrics/saturation`     | Redis memory, connected/blocked clients, rejected conns  |
| `GET`  | `/prometheus/metrics`     | Prometheus scrape endpoint (OpenMetrics)                 |

#### Metrics collected

| Key pattern                      | Description                            |
| -------------------------------- | -------------------------------------- |
| `metrics:requests:total`         | Total log entries ingested             |
| `metrics:status:{code}`          | Count per HTTP status code             |
| `metrics:backend:{name}`         | Count per HAProxy backend              |
| `metrics:frontend:{name}`        | Count per HAProxy frontend             |
| `metrics:errors:4xx` / `5xx`     | Error counters                         |
| `metrics:response_times`         | Sorted set for P50/P95/P99 computation |
| `metrics:rps:{YYYY-MM-DDTHH:MM}` | Requests-per-minute bucket (TTL 2h)    |

#### Quickstart

**With Docker (recommended):**

```bash
docker compose up --build
```

API available at `http://localhost:8000` · Docs at `http://localhost:8000/docs`

**Stopping:**

```bash
# Stop containers (preserves Redis data volume)
docker compose down

# Stop and remove data volume
docker compose down -v
```

**Without Docker:**

```bash
# Install dependencies
pip install -r Log-Ingestion-and-Metrics/requirements.txt

# Start Redis (required)
redis-cli ping

# Run the service
uvicorn app.main:app --reload --port 8000
```

#### Running tests

```bash
cd Log-Ingestion-and-Metrics

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run a specific test file
pytest tests/test_ingest.py -v

# Run a specific test
pytest tests/test_ingest.py::test_ingest_returns_202 -v
```

> Tests use `fakeredis` — no running Redis instance required.

#### Security testing

**SAST — Bandit** (static analysis, no running service required):

```bash
cd Log-Ingestion-and-Metrics

pip install bandit
bandit -r app
```

**DAST — OWASP ZAP** (dynamic analysis, requires Docker and running service):

```bash
# 1. Start the stack
docker compose up --build -d

# 2. Run ZAP API scan against the OpenAPI spec
docker run --rm --network host \
  -v /tmp/zap:/zap/wrk \
  ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py \
  -t http://localhost:8000/openapi.json \
  -f openapi \
  -r /zap/wrk/zap-report.html \
  -J /zap/wrk/zap-report.json \
  -I

# 3. Stop the stack
docker compose down
```

HTML and JSON reports are saved to `/tmp/zap/`.

#### Observability

The service implements the three observability pillars out of the box.

**Logs — structured JSON**

Every request is logged to stdout in JSON with the following fields:

```json
{
  "timestamp": "2026-05-09T23:00:00.000Z",
  "level": "INFO",
  "logger": "app.access",
  "message": "http_request",
  "method": "POST",
  "path": "/logs",
  "status_code": 202,
  "duration_ms": 4.21,
  "request_id": "a1b2c3d4-..."
}
```

Pass `X-Request-ID` in the request header to propagate a correlation ID across services. If absent, one is generated automatically and returned in the response.

Set `LOG_FORMAT=text` for human-readable output in local development.

**Metrics — Prometheus**

Prometheus metrics are exposed at `GET /prometheus/metrics`. Compatible with any standard scraper (Prometheus, Grafana Agent, OpenTelemetry Collector).

Metrics exposed (Golden Signals):

| Metric                          | Type      | Description                           |
| ------------------------------- | --------- | ------------------------------------- |
| `http_requests_total`           | Counter   | Request count by method, path, status |
| `http_request_duration_seconds` | Histogram | Latency distribution (P50/P95/P99)    |
| `http_requests_inprogress`      | Gauge     | In-flight requests (Saturation proxy) |

**Traces — OpenTelemetry**

FastAPI routes and Redis commands are auto-instrumented with OpenTelemetry spans.

- **Development (default):** traces printed to stdout via `ConsoleSpanExporter`
- **Production:** set `OTEL_EXPORTER_OTLP_ENDPOINT` to send traces to any OTLP-compatible backend (Jaeger, Tempo, Datadog, etc.)

```bash
# Example: export to a local Jaeger instance
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

#### Environment variables

| Variable                      | Default                      | Description                              |
| ----------------------------- | ---------------------------- | ---------------------------------------- |
| `REDIS_URL`                   | `redis://localhost:6379/0`   | Redis connection string                  |
| `RESPONSE_TIME_MAX_ENTRIES`   | `100000`                     | Max entries in response times sorted set |
| `LOG_LEVEL`                   | `info`                       | Uvicorn log level                        |
| `LOG_FORMAT`                  | `json`                       | Log output format: `json` or `text`      |
| `OTEL_SERVICE_NAME`           | `log-ingestion-and-metrics`  | Service name in traces                   |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | _(empty — console exporter)_ | OTLP gRPC endpoint for trace export      |

Copy `.env.example` to `.env` and adjust as needed.

---

## Research Context

|                 |                                                                    |
| --------------- | ------------------------------------------------------------------ |
| **Institution** | Unisinos — Universidade do Vale do Rio dos Sinos                   |
| **Program**     | PPGCA — Pós-Graduação em Computação Aplicada                       |
| **Topic**       | Agentic AI as Copilot for MTTD/MTTR reduction in Incident Response |
| **Domain**      | SRE · AIOps · NOC · LLM · Multi-agent systems                      |

---

## License

This project is for academic research purposes.
