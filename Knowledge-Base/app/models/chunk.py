from enum import Enum

from pydantic import BaseModel, Field


class ChunkType(str, Enum):
    SYMPTOM_FINGERPRINT = "symptom_fingerprint"
    LOG_EVIDENCE = "log_evidence"
    RUNBOOK_STEP = "runbook_step"
    METRIC_SNAPSHOT = "metric_snapshot"
    POSTMORTEM = "postmortem"
    LESSON_LEARNED = "lesson_learned"
    REASONING_TRANSCRIPT = "reasoning_transcript"
    DEPLOYMENT_EVENT = "deployment_event"
    RECOVERY_COMMAND = "recovery_command"
    ERROR_BUDGET = "error_budget"
    CUJ_IMPACT = "cuj_impact"
    PRECURSOR_SIGNAL = "precursor_signal"


class GoldenSignal(str, Enum):
    LATENCY = "latency"
    ERRORS = "errors"
    SATURATION = "saturation"
    TRAFFIC = "traffic"
    MULTIPLE = "multiple"


class RootCauseCategory(str, Enum):
    DEPLOY_REGRESSION = "deploy_regression"
    RESOURCE_SATURATION = "resource_saturation"
    AUTH_FAILURE = "auth_failure"
    UPSTREAM_CRASH = "upstream_crash"
    CONFIG_CHANGE = "config_change"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ResolutionType(str, Enum):
    HITL = "HITL"
    HOTL = "HOTL"
    AUTO = "auto"
    UNRESOLVED = "unresolved"


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    OK = "ok"


# ---------------------------------------------------------------------------
# Chunk metadata — every stored vector carries this as Qdrant payload
# ---------------------------------------------------------------------------

class ChunkMetadata(BaseModel):
    incident_id: str
    chunk_type: ChunkType
    golden_signal: GoldenSignal | None = None
    severity: Severity | None = None
    root_cause_category: RootCauseCategory | None = None
    resolution_type: ResolutionType | None = None
    affected_services: list[str] = Field(default_factory=list)
    affected_cujs: list[str] = Field(default_factory=list)
    mttd_minutes: int | None = None
    mttr_minutes: int | None = None
    incident_date: str | None = None
    step_number: int | None = None  # for runbook_step ordering


# ---------------------------------------------------------------------------
# Single-chunk ingest
# ---------------------------------------------------------------------------

class KBChunkRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Texto a ser embedado e armazenado")
    metadata: ChunkMetadata


class KBChunkResponse(BaseModel):
    id: str
    content: str
    metadata: ChunkMetadata
    score: float | None = None  # populated only in search results


# ---------------------------------------------------------------------------
# Full incident ingest — auto-explodes into multiple typed chunks
# ---------------------------------------------------------------------------

class MetricSnapshot(BaseModel):
    phase: str  # "detection" | "peak" | "recovery"
    p50_ms: float | None = None
    p95_ms: float | None = None
    p99_ms: float | None = None
    error_rate_5xx_pct: float | None = None
    error_rate_4xx_pct: float | None = None
    rps: float | None = None
    redis_memory_pct: float | None = None


class RecoveryCommand(BaseModel):
    command: str
    description: str
    phase: str = "remediation"  # "mitigation" | "remediation" | "optimization"


class LogExcerpt(BaseModel):
    content: str
    source: str  # "haproxy.log", "app.log", etc.
    context: str | None = None


class RunbookStep(BaseModel):
    step_number: int
    description: str
    action_type: str = "HOTL"  # "HOTL" | "HITL" | "observe"
    command: str | None = None


class ErrorBudget(BaseModel):
    slo_target_pct: float
    duration_minutes: int
    budget_consumed_pct: float
    budget_remaining_after_pct: float | None = None


class IncidentIngestRequest(BaseModel):
    incident_id: str
    title: str
    date: str  # ISO date string, e.g. "2026-05-10"
    severity: Severity
    golden_signals: list[GoldenSignal] = Field(default_factory=list)
    root_cause_category: RootCauseCategory = RootCauseCategory.UNKNOWN
    resolution_type: ResolutionType = ResolutionType.HITL
    affected_services: list[str] = Field(default_factory=list)
    affected_cujs: list[str] = Field(default_factory=list)
    mttd_minutes: int | None = None
    mttr_minutes: int | None = None

    # Each field below produces one or more chunks
    summary: str
    postmortem_text: str | None = None
    symptom_patterns: list[str] = Field(default_factory=list)
    log_excerpts: list[LogExcerpt] = Field(default_factory=list)
    recovery_commands: list[RecoveryCommand] = Field(default_factory=list)
    runbook_steps: list[RunbookStep] = Field(default_factory=list)
    lessons_learned: list[str] = Field(default_factory=list)
    metric_snapshots: list[MetricSnapshot] = Field(default_factory=list)
    error_budget: ErrorBudget | None = None
    precursor_signals: list[str] = Field(default_factory=list)


class IncidentIngestResponse(BaseModel):
    incident_id: str
    chunks_created: int
    chunk_ids: list[str]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    chunk_types: list[ChunkType] | None = None
    golden_signal: GoldenSignal | None = None
    severity: Severity | None = None
    root_cause_category: RootCauseCategory | None = None
    incident_id: str | None = None


class SearchResponse(BaseModel):
    results: list[KBChunkResponse]
    total: int
