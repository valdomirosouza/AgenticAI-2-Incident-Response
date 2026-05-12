from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_api_key
from app.dependencies import get_embedding_service, get_qdrant_service
from app.limiter import limiter
from app.models.chunk import (
    IncidentIngestRequest,
    IncidentIngestResponse,
    KBChunkRequest,
    KBChunkResponse,
)
from app.services.embeddings import EmbeddingService
from app.services.ingestion import incident_to_chunks
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/kb", tags=["ingest"])


@router.post("/ingest/chunk", response_model=KBChunkResponse, status_code=201,
             dependencies=[Depends(require_api_key)])
@limiter.limit("60/minute")
async def ingest_chunk(
    request: Request,
    body: KBChunkRequest,
    embeddings: EmbeddingService = Depends(get_embedding_service),
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> KBChunkResponse:
    chunk_id = str(uuid4())
    vector = await embeddings.embed(body.content)
    await qdrant.upsert(chunk_id, vector, body.content, body.metadata)
    return KBChunkResponse(id=chunk_id, content=body.content, metadata=body.metadata)


@router.post("/ingest/incident", response_model=IncidentIngestResponse, status_code=201,
             dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
async def ingest_incident(
    request: Request,
    body: IncidentIngestRequest,
    embeddings: EmbeddingService = Depends(get_embedding_service),
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> IncidentIngestResponse:
    chunks = incident_to_chunks(body)
    if not chunks:
        raise HTTPException(status_code=422, detail="Incident produced no chunks")

    vectors = await embeddings.embed_batch([c[0] for c in chunks])

    chunk_ids: list[str] = []
    for (content, metadata), vector in zip(chunks, vectors):
        chunk_id = str(uuid4())
        await qdrant.upsert(chunk_id, vector, content, metadata)
        chunk_ids.append(chunk_id)

    return IncidentIngestResponse(
        incident_id=body.incident_id,
        chunks_created=len(chunk_ids),
        chunk_ids=chunk_ids,
    )
