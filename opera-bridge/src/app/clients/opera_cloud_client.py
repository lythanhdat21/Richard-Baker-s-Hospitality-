import time
import httpx
from src.app.clients.opera_auth_client import get_access_token, invalidate_token
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.db.models import ApiRequestLog
from src.app.db.session import SessionLocal, get_or_create_default_property
from src.app.utils.error_normalizer import normalize_opera_error
from src.app.utils.retry import opera_retry

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 30
RETRYABLE_STATUS_CODES = (429, 502, 503, 504)


class _RetryableStatus(Exception):
    """Đánh dấu response có status retryable (429/502/503/504) để opera_retry bắt và thử lại."""

    def __init__(self, response: httpx.Response):
        self.response = response


def _log_request(
    trace_id: str, method: str, path: str, status_code: int | None,
    success: bool, error_code: str | None, duration_ms: int,
) -> None:
    try:
        with SessionLocal() as db:
            prop = get_or_create_default_property(db)
            db.add(ApiRequestLog(
                trace_id=trace_id,
                property_id=prop.id,
                internal_endpoint="",
                opera_endpoint=path,
                http_method=method,
                status_code=status_code,
                success=success,
                error_code=error_code,
                duration_ms=duration_ms,
            ))
            db.commit()
    except Exception:
        logger.exception("api_request_log_failed", path=path)


@opera_retry
async def _send(method: str, url: str, headers: dict, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        resp = await client.request(method, url, headers=headers, **kwargs)
    if resp.status_code in RETRYABLE_STATUS_CODES:
        raise _RetryableStatus(resp)
    return resp


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
        resp = await _send(method, url, headers, **kwargs)
    except _RetryableStatus as exc:
        resp = exc.response
    except httpx.TimeoutException:
        duration_ms = int((time.monotonic() - start) * 1000)
        _log_request(trace_id, method, path, None, False, "OPERA_TIMEOUT", duration_ms)
        raise normalize_opera_error("OPERA_TIMEOUT", "OPERA Cloud request timed out.", trace_id)
    except httpx.RequestError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        _log_request(trace_id, method, path, None, False, "OPERA_CONNECTION_ERROR", duration_ms)
        raise normalize_opera_error("OPERA_CONNECTION_ERROR", str(exc), trace_id)

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "opera_request", method=method, path=path,
        status=resp.status_code, duration_ms=duration_ms, trace_id=trace_id,
    )

    if resp.status_code == 401:
        invalidate_token()
        _log_request(trace_id, method, path, resp.status_code, False, "AUTH_FAILED", duration_ms)
        raise normalize_opera_error("AUTH_FAILED", "OPERA Cloud authentication failed.", trace_id)

    if resp.status_code == 429:
        _log_request(trace_id, method, path, resp.status_code, False, "OPERA_RATE_LIMIT", duration_ms)
        raise normalize_opera_error("OPERA_RATE_LIMIT", "OPERA Cloud rate limit exceeded.", trace_id)

    if resp.status_code >= 500:
        _log_request(trace_id, method, path, resp.status_code, False, "OPERA_ERROR", duration_ms)
        raise normalize_opera_error("OPERA_ERROR", f"OPERA Cloud server error: {resp.status_code}", trace_id)

    if not resp.is_success:
        body = resp.text[:500]
        _log_request(trace_id, method, path, resp.status_code, False, "OPERA_ERROR", duration_ms)
        raise normalize_opera_error("OPERA_ERROR", f"OPERA Cloud error {resp.status_code}: {body}", trace_id)

    _log_request(trace_id, method, path, resp.status_code, True, None, duration_ms)
    return resp.json()


async def get(path: str, trace_id: str, params: dict | None = None) -> dict:
    return await _request("GET", path, trace_id, params=params)


async def post(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("POST", path, trace_id, json=json)


async def put(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("PUT", path, trace_id, json=json)


async def patch(path: str, trace_id: str, json: dict | None = None) -> dict:
    return await _request("PATCH", path, trace_id, json=json)
