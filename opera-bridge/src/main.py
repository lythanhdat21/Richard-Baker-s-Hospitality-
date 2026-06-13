from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.app.core.config import settings
from src.app.core.logging import configure_logging
from src.app.core.logging import get_logger
from src.app.middlewares.request_logging import RequestLoggingMiddleware
from src.app.api.routes import health, reservations, rooms, guests

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Opera Bridge",
    description="Cầu nối giữa hệ điều khiển khách sạn và Oracle OPERA Cloud.",
    version="1.0.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health.router)
app.include_router(reservations.router)
app.include_router(rooms.router)
app.include_router(guests.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "code": "INTERNAL_ERROR", "message": "Lỗi hệ thống không xác định."},
    )
