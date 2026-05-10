import httpx

import app.config as _cfg


def _base_url() -> str:
    return _cfg.settings.metrics_api_url


async def fetch_health() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/health")
        r.raise_for_status()
        return r.json()


async def fetch_overview() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/metrics/overview")
        r.raise_for_status()
        return r.json()


async def fetch_status_codes() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/metrics/status-codes")
        r.raise_for_status()
        return r.json()


async def fetch_response_times() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/metrics/response-times")
        r.raise_for_status()
        return r.json()


async def fetch_rps(minutes: int = 10) -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get(f"/metrics/rps?minutes={minutes}")
        r.raise_for_status()
        return r.json()


async def fetch_backends() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/metrics/backends")
        r.raise_for_status()
        return r.json()


async def fetch_saturation() -> dict:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=10.0) as client:
        r = await client.get("/metrics/saturation")
        r.raise_for_status()
        return r.json()
