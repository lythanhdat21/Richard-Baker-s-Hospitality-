import time
import httpx
from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger(__name__)

_token_cache: dict = {"access_token": None, "expires_at": 0}


async def get_access_token() -> str:
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    logger.info("Fetching new OPERA Cloud access token")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.opera_base_url}/oauth/v1/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.opera_client_id,
                "client_secret": settings.opera_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + settings.opera_token_ttl
    return _token_cache["access_token"]


def invalidate_token() -> None:
    _token_cache["access_token"] = None
    _token_cache["expires_at"] = 0
