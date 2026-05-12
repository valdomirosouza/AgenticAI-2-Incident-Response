from functools import lru_cache

from app.services.embeddings import EmbeddingService
from app.services.qdrant_service import QdrantService


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    from app.config import settings
    return EmbeddingService(model_name=settings.embedding_model)


@lru_cache()
def get_qdrant_service() -> QdrantService:
    from qdrant_client import AsyncQdrantClient
    from app.config import settings
    return QdrantService(AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    ))
