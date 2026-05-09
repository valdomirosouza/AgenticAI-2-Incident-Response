from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    response_time_max_entries: int = 100000
    log_level: str = "info"

    model_config = {"env_file": ".env"}


settings = Settings()
