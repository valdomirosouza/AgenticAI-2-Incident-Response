import logging

from fastapi import FastAPI, HTTPException

from app.agents.orchestrator import run_analysis
from app.models.report import IncidentReport

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Incident Response Agent",
    description="Multi-agent AI copilot for MTTD/MTTR reduction — PPGCA/Unisinos",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.post("/analyze", response_model=IncidentReport, summary="Run a full multi-agent analysis cycle")
async def analyze() -> IncidentReport:
    try:
        return await run_analysis()
    except Exception as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
