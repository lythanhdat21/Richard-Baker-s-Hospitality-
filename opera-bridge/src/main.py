import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.app.core.config import settings
from src.app.core.logging import configure_logging, get_logger
from src.app.middlewares.request_logging import RequestLoggingMiddleware
from src.app.api.routes import health, reservations, rooms, guests
from src.app.mqtt.subscriber import run_subscriber

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_task = asyncio.create_task(run_subscriber())
    logger.info("mqtt_subscriber_started")
    yield
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass
    logger.info("mqtt_subscriber_stopped")


app = FastAPI(
    title="Opera Bridge",
    description="Cầu nối giữa hệ điều khiển khách sạn và Oracle OPERA Cloud.",
    version="1.0.0",
    lifespan=lifespan,
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
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "code": "INTERNAL_ERROR", "message": "Lỗi hệ thống không xác định."},
    )
