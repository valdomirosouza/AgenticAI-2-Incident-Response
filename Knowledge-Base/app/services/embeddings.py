import asyncio

from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingService:
    def __init__(self, model_name: str = settings.embedding_model):
        self._model = SentenceTransformer(model_name)

    async def embed(self, text: str) -> list[float]:
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(None, self._model.encode, text)
        return vector.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(None, self._model.encode, texts)
        return [v.tolist() for v in vectors]
