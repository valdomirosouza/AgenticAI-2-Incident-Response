import logging

import httpx

import app.config as _cfg

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return _cfg.settings.kb_api_url


async def search_kb(query: str, limit: int = 5) -> list[dict]:
    """Search the Knowledge Base for similar historical incidents.

    Always returns a list — empty on any error so callers degrade gracefully
    without needing their own try/except.
    """
    try:
        async with httpx.AsyncClient(base_url=_base_url(), timeout=5.0) as client:
            response = await client.post(
                "/kb/search",
                json={
                    "query": query,
                    "limit": limit,
                    "chunk_types": [
                        "symptom_fingerprint",
                        "runbook_step",
                        "lesson_learned",
                    ],
                },
            )
            response.raise_for_status()
            return response.json().get("results", [])
    except Exception as exc:
        logger.warning("KB unavailable — continuing without historical context: %s", exc)
        return []
