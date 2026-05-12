import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_embedding_service, get_qdrant_service
from app.main import app
from app.models.chunk import ChunkMetadata, KBChunkResponse

FAKE_VECTOR = [0.1] * 384


class FakeEmbeddingService:
    async def embed(self, text: str) -> list[float]:
        return FAKE_VECTOR

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [FAKE_VECTOR for _ in texts]


class FakeQdrantService:
    def __init__(self):
        self._store: dict[str, tuple[str, ChunkMetadata]] = {}

    async def ensure_collection(self) -> None:
        pass

    async def upsert(self, chunk_id: str, vector, content: str, metadata: ChunkMetadata) -> str:
        self._store[chunk_id] = (content, metadata)
        return chunk_id

    async def search(self, vector, limit=10, search_request=None) -> list[KBChunkResponse]:
        results = []
        for chunk_id, (content, meta) in list(self._store.items())[:limit]:
            results.append(KBChunkResponse(id=chunk_id, content=content, metadata=meta, score=0.9))
        return results

    async def get_by_incident(self, incident_id: str) -> list[KBChunkResponse]:
        return [
            KBChunkResponse(id=cid, content=content, metadata=meta)
            for cid, (content, meta) in self._store.items()
            if meta.incident_id == incident_id
        ]

    async def delete_by_incident(self, incident_id: str) -> int:
        to_delete = [k for k, (_, m) in self._store.items() if m.incident_id == incident_id]
        for k in to_delete:
            del self._store[k]
        return len(to_delete)

    async def list_incidents(self) -> list[str]:
        return sorted({m.incident_id for _, m in self._store.values()})


@pytest.fixture
def fake_qdrant():
    return FakeQdrantService()


@pytest.fixture
async def client(fake_qdrant):
    app.dependency_overrides[get_embedding_service] = lambda: FakeEmbeddingService()
    app.dependency_overrides[get_qdrant_service] = lambda: fake_qdrant
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
