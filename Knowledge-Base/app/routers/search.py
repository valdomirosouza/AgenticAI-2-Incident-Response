from fastapi import APIRouter, Depends, Request

from app.dependencies import get_embedding_service, get_qdrant_service
from app.limiter import limiter
from app.models.chunk import SearchRequest, SearchResponse
from app.services.embeddings import EmbeddingService
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/kb", tags=["search"])


@router.post("/search", response_model=SearchResponse)
@limiter.limit("60/minute")
async def search(
    request: Request,
    body: SearchRequest,
    embeddings: EmbeddingService = Depends(get_embedding_service),
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> SearchResponse:
    vector = await embeddings.embed(body.query)
    results = await qdrant.search(vector=vector, limit=body.limit, search_request=body)
    return SearchResponse(results=results, total=len(results))
