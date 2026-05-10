from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as aioredis


async def get_overview(redis: aioredis.Redis) -> dict:
    total_raw, errors_4xx_raw, errors_5xx_raw = await redis.mget(
        "metrics:requests:total",
        "metrics:errors:4xx",
        "metrics:errors:5xx",
    )
    total = int(total_raw or 0)
    errors_4xx = int(errors_4xx_raw or 0)
    errors_5xx = int(errors_5xx_raw or 0)
    return {
        "total_requests": total,
        "errors_4xx": errors_4xx,
        "errors_5xx": errors_5xx,
        "error_rate_4xx_pct": round(errors_4xx / total * 100, 2) if total else 0.0,
        "error_rate_5xx_pct": round(errors_5xx / total * 100, 2) if total else 0.0,
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


async def get_saturation(redis: aioredis.Redis) -> dict:
    try:
        info_memory = await redis.info("memory")
        info_clients = await redis.info("clients")
        info_stats = await redis.info("stats")
    except Exception:
        info_memory = {}
        info_clients = {}
        info_stats = {}

    used_memory = int(info_memory.get("used_memory", 0))
    used_memory_peak = int(info_memory.get("used_memory_peak", 0))
    maxmemory = int(info_memory.get("maxmemory", 0))
    memory_usage_pct = round(used_memory / maxmemory * 100, 2) if maxmemory > 0 else None

    return {
        "redis": {
            "used_memory_bytes": used_memory,
            "used_memory_peak_bytes": used_memory_peak,
            "maxmemory_bytes": maxmemory,
            "memory_usage_pct": memory_usage_pct,
            "connected_clients": int(info_clients.get("connected_clients", 0)),
            "blocked_clients": int(info_clients.get("blocked_clients", 0)),
            "rejected_connections": int(info_stats.get("rejected_connections", 0)),
        }
    }
