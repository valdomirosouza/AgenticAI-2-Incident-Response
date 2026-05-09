import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status

from app.models.log_entry import HAProxyLogEntry
from app.redis_client import get_redis
from app.services.ingestion import process_log

router = APIRouter(prefix="/logs", tags=["ingestion"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_log(
    entry: HAProxyLogEntry,
    redis: aioredis.Redis = Depends(get_redis),
):
    await process_log(entry, redis)
    return {"status": "accepted"}
