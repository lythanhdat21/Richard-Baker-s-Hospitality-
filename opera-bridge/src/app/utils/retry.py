from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fastapi import HTTPException


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, HTTPException):
        return exc.status_code in (429, 502, 503, 504)
    return False


opera_retry = retry(
    retry=retry_if_exception_type(HTTPException) | retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
