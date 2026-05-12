import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import app.config as _cfg
from app.agents.orchestrator import run_analysis
from app.models.report import IncidentReport

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Incident Response Agent",
    description="Multi-agent AI copilot for MTTD/MTTR reduction — PPGCA/Unisinos",
    version="1.0.0",
    docs_url="/docs" if _cfg.settings.enable_docs else None,
    redoc_url="/redoc" if _cfg.settings.enable_docs else None,
    openapi_url="/openapi.json" if _cfg.settings.enable_docs else None,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "An internal error occurred"})


app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.post("/analyze", response_model=IncidentReport, summary="Run a full multi-agent analysis cycle")
async def analyze():
    if not _cfg.settings.anthropic_api_key:
        return Response(status_code=503)

    try:
        return await run_analysis()
    except Exception as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        return Response(status_code=500)
