import uuid

import redis.asyncio as aioredis

from app.config import settings
from app.models.log_entry import HAProxyLogEntry


async def process_log(entry: HAProxyLogEntry, redis: aioredis.Redis) -> None:
    pipe = redis.pipeline()

    pipe.incr("metrics:requests:total")
    pipe.incr(f"metrics:status:{entry.status_code}")
    pipe.incr(f"metrics:backend:{entry.backend_name}")
    pipe.incr(f"metrics:frontend:{entry.frontend_name}")

    if 400 <= entry.status_code < 500:
        pipe.incr("metrics:errors:4xx")
    elif entry.status_code >= 500:
        pipe.incr("metrics:errors:5xx")

    # Sorted set of response times; trimmed to avoid unbounded growth
    pipe.zadd("metrics:response_times", {str(uuid.uuid4()): entry.time_active})
    pipe.zremrangebyrank("metrics:response_times", 0, -(settings.response_time_max_entries + 1))

    # Per-minute request bucket with 2-hour TTL
    minute_key = f"metrics:rps:{entry.time_local.strftime('%Y-%m-%dT%H:%M')}"
    pipe.incr(minute_key)
    pipe.expire(minute_key, 7200)

    await pipe.execute()
