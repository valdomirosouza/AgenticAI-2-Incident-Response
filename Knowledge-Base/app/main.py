import logging

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.routers import health, incidents, ingest, search

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Base",
    description="Vector knowledge base for incident response — AgenticAI-2-Incident-Response",
    version="1.0.0",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(search.router)
app.include_router(incidents.router)
