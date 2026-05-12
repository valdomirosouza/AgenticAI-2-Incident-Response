from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    metrics_api_url: str = "http://localhost:8000"
    kb_api_url: str = "http://localhost:8002"
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 2048

    error_rate_5xx_threshold_pct: float = 5.0
    error_rate_4xx_threshold_pct: float = 20.0
    latency_p95_threshold_ms: float = 500.0
    latency_p99_threshold_ms: float = 1000.0
    memory_usage_threshold_pct: float = 80.0

    model_config = {"env_file": ".env"}


settings = Settings()
