from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "incidents"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    search_limit_default: int = 10
    log_level: str = "info"
    enable_docs: bool = True  # set to False in production

    model_config = {"env_file": ".env"}


settings = Settings()
