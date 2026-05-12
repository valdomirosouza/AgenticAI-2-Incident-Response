import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request, status

from app.auth import require_api_key
from app.limiter import limiter
from app.models.log_entry import HAProxyLogEntry
from app.redis_client import get_redis
from app.services.ingestion import process_log

router = APIRouter(prefix="/logs", tags=["ingestion"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(require_api_key)])
@limiter.limit("600/minute")
async def ingest_log(
    request: Request,
    entry: HAProxyLogEntry,
    redis: aioredis.Redis = Depends(get_redis),
):
    await process_log(entry, redis)
    return {"status": "accepted"}
