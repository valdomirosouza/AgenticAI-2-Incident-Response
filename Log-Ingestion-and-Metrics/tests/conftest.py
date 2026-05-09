import pytest_asyncio
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport

from app.main import app
from app import redis_client


@pytest_asyncio.fixture
async def fake_redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture
async def client(fake_redis):
    app.dependency_overrides[redis_client.get_redis] = lambda: fake_redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
