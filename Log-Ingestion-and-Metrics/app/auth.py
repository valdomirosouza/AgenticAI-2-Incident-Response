from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

import app.config as _cfg

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str = Security(_header)) -> None:
    """Validates X-API-Key header. Auth is disabled when API_KEY is empty (development)."""
    if not _cfg.settings.api_key:
        return
    if key != _cfg.settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
