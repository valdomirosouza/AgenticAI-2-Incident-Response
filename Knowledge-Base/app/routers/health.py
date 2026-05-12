from fastapi import APIRouter, Depends

from app.dependencies import get_qdrant_service
from app.services.qdrant_service import QdrantService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(qdrant: QdrantService = Depends(get_qdrant_service)) -> dict:
    try:
        await qdrant.ensure_collection()
        return {"status": "healthy", "qdrant": "connected"}
    except Exception as exc:
        return {"status": "degraded", "qdrant": str(exc)}
