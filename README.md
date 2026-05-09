# AgenticAI-2-Incident-Response

Research project exploring **Agentic AI as a Copilot** for reducing **MTTD** (Mean Time to Detect) and **MTTR** (Mean Time to Recovery) in IT incident response — developed as part of a Master's dissertation at **PPGCA / Unisinos**.

---

## Modules

### `Log-Ingestion-and-Metrics`

FastAPI service that ingests HAProxy logs and exposes aggregated metrics via Redis. Serves as the observability data layer for the Agentic AI pipeline.

**Stack:** Python · FastAPI · Redis (aioredis) · Pydantic v2

#### API

| Method | Endpoint     | Description                        |
| ------ | ------------ | ---------------------------------- |
| `POST` | `/logs`      | Ingest a HAProxy log entry (JSON)  |
| `GET`  | `/metrics/*` | Read aggregated metrics from Redis |

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

```bash
# Install dependencies
pip install -r Log-Ingestion-and-Metrics/requirements.txt

# Start Redis (required)
redis-cli ping

# Run the service
uvicorn app.main:app --reload --port 8000

# Run tests
cd Log-Ingestion-and-Metrics && pytest
```

#### Environment variables

| Variable                    | Default                    | Description                              |
| --------------------------- | -------------------------- | ---------------------------------------- |
| `REDIS_URL`                 | `redis://localhost:6379/0` | Redis connection string                  |
| `RESPONSE_TIME_MAX_ENTRIES` | `100000`                   | Max entries in response times sorted set |
| `LOG_LEVEL`                 | `info`                     | Uvicorn log level                        |

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
