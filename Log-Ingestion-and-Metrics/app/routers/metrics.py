import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query

from app.redis_client import get_redis
from app.services import metrics as metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview")
async def overview(redis: aioredis.Redis = Depends(get_redis)):
    return await metrics_service.get_overview(redis)


@router.get("/status-codes")
async def status_codes(redis: aioredis.Redis = Depends(get_redis)):
    return await metrics_service.get_status_codes(redis)


@router.get("/backends")
async def backends(redis: aioredis.Redis = Depends(get_redis)):
    return await metrics_service.get_backends(redis)


@router.get("/frontends")
async def frontends(redis: aioredis.Redis = Depends(get_redis)):
    return await metrics_service.get_frontends(redis)


@router.get("/response-times")
async def response_times(redis: aioredis.Redis = Depends(get_redis)):
    return await metrics_service.get_response_time_percentiles(redis)


@router.get("/rps")
async def rps(
    minutes: int = Query(default=60, ge=1, le=1440),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await metrics_service.get_rps(redis, minutes)
