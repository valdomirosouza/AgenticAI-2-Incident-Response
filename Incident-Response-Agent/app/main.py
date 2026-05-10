import logging

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import app.config as _cfg
from app.agents.orchestrator import run_analysis
from app.models.report import IncidentReport

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Incident Response Agent",
    description="Multi-agent AI copilot for MTTD/MTTR reduction — PPGCA/Unisinos",
    version="1.0.0",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return response


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
