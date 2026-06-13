from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from src.app.core.config import settings

_api_key_header = APIKeyHeader(name="X-Internal-API-Key", auto_error=False)


async def require_internal_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    if not api_key or api_key != settings.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "code": "AUTH_FAILED", "message": "Invalid or missing API key."},
        )
    return api_key
