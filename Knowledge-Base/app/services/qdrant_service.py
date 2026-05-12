from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

# qdrant-client >= 1.13 replaced client.search() with client.query_points()
_QDRANT_USE_QUERY_POINTS = True

from app.config import settings
from app.models.chunk import ChunkMetadata, KBChunkResponse, SearchRequest


class QdrantService:
    def __init__(self, client: AsyncQdrantClient):
        self._client = client
        self._collection_ensured = False

    async def ensure_collection(self) -> None:
        existing = {c.name for c in (await self._client.get_collections()).collections}
        if settings.qdrant_collection not in existing:
            await self._client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
            )
        self._collection_ensured = True

    async def _ensure(self) -> None:
        if not self._collection_ensured:
            await self.ensure_collection()

    async def upsert(
        self, chunk_id: str, vector: list[float], content: str, metadata: ChunkMetadata
    ) -> str:
        await self._ensure()
        payload = {"content": content, **metadata.model_dump(mode="json", exclude_none=True)}
        await self._client.upsert(
            collection_name=settings.qdrant_collection,
            points=[PointStruct(id=chunk_id, vector=vector, payload=payload)],
        )
        return chunk_id

    async def search(
        self,
        vector: list[float],
        limit: int = 10,
        search_request: SearchRequest | None = None,
    ) -> list[KBChunkResponse]:
        await self._ensure()
        qdrant_filter = _build_filter(search_request) if search_request else None
        response = await self._client.query_points(
            collection_name=settings.qdrant_collection,
            query=vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
        )
        return [_point_to_response(r) for r in response.points]

    async def get_by_incident(self, incident_id: str) -> list[KBChunkResponse]:
        await self._ensure()
        records, _ = await self._client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(
                must=[FieldCondition(key="incident_id", match=MatchValue(value=incident_id))]
            ),
            with_payload=True,
            limit=1000,
        )
        return [_point_to_response(r) for r in records]

    async def delete_by_incident(self, incident_id: str) -> int:
        existing = await self.get_by_incident(incident_id)
        if not existing:
            return 0
        await self._client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=PointIdsList(points=[r.id for r in existing]),
        )
        return len(existing)

    async def list_incidents(self) -> list[str]:
        await self._ensure()
        seen: set[str] = set()
        offset = None
        while True:
            records, next_offset = await self._client.scroll(
                collection_name=settings.qdrant_collection,
                with_payload=["incident_id"],
                limit=100,
                offset=offset,
            )
            for rec in records:
                if rec.payload and "incident_id" in rec.payload:
                    seen.add(rec.payload["incident_id"])
            if next_offset is None:
                break
            offset = next_offset
        return sorted(seen)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_filter(req: SearchRequest) -> Filter | None:
    must: list = []

    if req.chunk_types:
        cond = [FieldCondition(key="chunk_type", match=MatchValue(value=ct.value)) for ct in req.chunk_types]
        must.append(cond[0] if len(cond) == 1 else Filter(should=cond))

    if req.golden_signal:
        must.append(FieldCondition(key="golden_signal", match=MatchValue(value=req.golden_signal.value)))
    if req.severity:
        must.append(FieldCondition(key="severity", match=MatchValue(value=req.severity.value)))
    if req.root_cause_category:
        must.append(FieldCondition(key="root_cause_category", match=MatchValue(value=req.root_cause_category.value)))
    if req.incident_id:
        must.append(FieldCondition(key="incident_id", match=MatchValue(value=req.incident_id)))

    return Filter(must=must) if must else None


def _point_to_response(point) -> KBChunkResponse:
    payload = dict(point.payload or {})
    content = payload.pop("content", "")
    try:
        metadata = ChunkMetadata(**payload)
    except Exception:
        metadata = ChunkMetadata(
            incident_id=payload.get("incident_id", "unknown"),
            chunk_type=payload.get("chunk_type", "postmortem"),
        )
    return KBChunkResponse(
        id=str(point.id),
        content=content,
        metadata=metadata,
        score=getattr(point, "score", None),
    )
