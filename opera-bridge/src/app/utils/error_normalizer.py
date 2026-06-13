from fastapi import HTTPException, status


ERROR_HTTP_STATUS = {
    "AUTH_FAILED": status.HTTP_401_UNAUTHORIZED,
    "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
    "RESERVATION_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "ROOM_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "GUEST_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "BALANCE_NOT_CLEARED": status.HTTP_409_CONFLICT,
    "OPERA_TIMEOUT": status.HTTP_504_GATEWAY_TIMEOUT,
    "OPERA_RATE_LIMIT": status.HTTP_429_TOO_MANY_REQUESTS,
    "OPERA_ERROR": status.HTTP_502_BAD_GATEWAY,
    "OPERA_CONNECTION_ERROR": status.HTTP_502_BAD_GATEWAY,
}


def normalize_opera_error(code: str, message: str, trace_id: str = "") -> HTTPException:
    http_status = ERROR_HTTP_STATUS.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return HTTPException(
        status_code=http_status,
        detail={"success": False, "code": code, "message": message, "traceId": trace_id},
    )
