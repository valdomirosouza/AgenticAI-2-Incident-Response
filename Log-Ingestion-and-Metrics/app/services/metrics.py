from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as aioredis


async def get_overview(redis: aioredis.Redis) -> dict:
    total, errors_4xx, errors_5xx = await redis.mget(
        "metrics:requests:total",
        "metrics:errors:4xx",
        "metrics:errors:5xx",
    )
    return {
        "total_requests": int(total or 0),
        "errors_4xx": int(errors_4xx or 0),
        "errors_5xx": int(errors_5xx or 0),
    }


async def get_status_codes(redis: aioredis.Redis) -> dict:
    keys = await redis.keys("metrics:status:*")
    if not keys:
        return {}
    values = await redis.mget(*keys)
    return {k.split(":")[-1]: int(v) for k, v in zip(keys, values) if v}


async def get_backends(redis: aioredis.Redis) -> dict:
    keys = await redis.keys("metrics:backend:*")
    if not keys:
        return {}
    values = await redis.mget(*keys)
    return {":".join(k.split(":")[2:]): int(v) for k, v in zip(keys, values) if v}


async def get_frontends(redis: aioredis.Redis) -> dict:
    keys = await redis.keys("metrics:frontend:*")
    if not keys:
        return {}
    values = await redis.mget(*keys)
    return {":".join(k.split(":")[2:]): int(v) for k, v in zip(keys, values) if v}


async def get_response_time_percentiles(redis: aioredis.Redis) -> dict:
    total = await redis.zcard("metrics:response_times")
    if total == 0:
        return {"p50": None, "p95": None, "p99": None, "count": 0}

    async def _percentile(pct: float) -> Optional[float]:
        idx = max(0, int(total * pct / 100) - 1)
        results = await redis.zrange("metrics:response_times", idx, idx, withscores=True)
        return results[0][1] if results else None

    return {
        "p50": await _percentile(50),
        "p95": await _percentile(95),
        "p99": await _percentile(99),
        "count": total,
    }


async def get_rps(redis: aioredis.Redis, minutes: int = 60) -> dict:
    now = datetime.now(timezone.utc)
    keys = [
        f"metrics:rps:{(now - timedelta(minutes=i)).strftime('%Y-%m-%dT%H:%M')}"
        for i in range(minutes)
    ]
    values = await redis.mget(*keys)
    return {
        k.split(":", 2)[-1]: int(v) if v else 0
        for k, v in zip(keys, values)
    }
