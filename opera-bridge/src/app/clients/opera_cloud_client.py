import time
import httpx
from src.app.clients.opera_auth_client import get_access_token, invalidate_token
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.utils.error_normalizer import normalize_opera_error

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30


async def _request(method: str, path: str, trace_id: str, **kwargs) -> dict:
    token = await get_access_token()
    url = f"{settings.opera_base_url}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-hotelid": settings.opera_hotel_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.request(method, url, headers=headers, **kwargs)
    except httpx.TimeoutException:
        raise normalize_opera_error("OPERA_TIMEOUT", "OPERA Cloud request timed out.", trace_id)
    except httpx.RequestError as exc:
        raise normalize_opera_error("OPERA_CONNECTION_ERROR", str(exc), trace_id)

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info("opera_request", method=method, path=path, status=resp.status_code, duration_ms=duration_ms, trace_id=trace_id)

    if resp.status_code == 401:
        invalidate_token()
        raise normalize_opera_error("AUTH_FAILED", "OPERA Cloud authentication failed.", trace_id)

    if resp.status_code == 429:
        raise normalize_opera_error("OPERA_RATE_LIMIT", "OPERA Cloud rate limit exceeded.", trace_id)

    if resp.status_code >= 500:
        raise normalize_opera_error("OPERA_ERROR", f"OPERA Cloud server error: {resp.status_code}", trace_id)

    if not resp.is_success:
        body = resp.text[:500]
        raise normalize_opera_error("OPERA_ERROR", f"OPERA Cloud error {resp.status_code}: {body}", trace_id)

    return resp.json()


async def get(path: str, trace_id: str, params: dict | None = None) -> dict:
    return await _request("GET", path, trace_id, params=params)


async def post(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("POST", path, trace_id, json=json)


async def put(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("PUT", path, trace_id, json=json)


async def patch(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("PATCH", path, trace_id, json=json)
