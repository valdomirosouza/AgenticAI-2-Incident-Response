import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(redis: aioredis.Redis = Depends(get_redis)):
    redis_ok = False
    try:
        redis_ok = await redis.ping()
    except Exception:
        pass

    status = "healthy" if redis_ok else "degraded"
    return JSONResponse(
        status_code=200 if redis_ok else 503,
        content={
            "status": status,
            "components": {
                "api": "healthy",
                "redis": "healthy" if redis_ok else "unhealthy",
            },
        },
    )
