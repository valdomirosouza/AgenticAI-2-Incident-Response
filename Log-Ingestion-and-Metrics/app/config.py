from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    response_time_max_entries: int = 100000
    log_level: str = "info"
    log_format: str = "json"
    otel_service_name: str = "log-ingestion-and-metrics"
    otel_exporter_otlp_endpoint: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
