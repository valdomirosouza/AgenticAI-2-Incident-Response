from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_qdrant_service
from app.models.chunk import KBChunkResponse
from app.services.qdrant_service import QdrantService

router = APIRouter(prefix="/kb", tags=["incidents"])


@router.get("/incidents", response_model=list[str])
async def list_incidents(
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> list[str]:
    return await qdrant.list_incidents()


@router.get("/incidents/{incident_id}", response_model=list[KBChunkResponse])
async def get_incident(
    incident_id: str,
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> list[KBChunkResponse]:
    chunks = await qdrant.get_by_incident(incident_id)
    if not chunks:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id!r} not found")
    return chunks


@router.delete("/incidents/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: str,
    qdrant: QdrantService = Depends(get_qdrant_service),
) -> None:
    deleted = await qdrant.delete_by_incident(incident_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id!r} not found")
