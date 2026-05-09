from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.redis_client import close_redis, init_redis
from app.routers import ingest, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="HAProxy Log Ingestion & Metrics",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(ingest.router)
app.include_router(metrics.router)
