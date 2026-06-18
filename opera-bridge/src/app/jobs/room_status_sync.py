import asyncio
import uuid
from src.app.services.sync_service import sync_room_statuses
from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger(__name__)


async def run():
    trace_id = str(uuid.uuid4())
    logger.info("room_status_sync_job_start", trace_id=trace_id)
    try:
        result = await sync_room_statuses(trace_id)
        logger.info("room_status_sync_job_done", result=result, trace_id=trace_id)
    except Exception as exc:
        logger.error("room_status_sync_job_error", error=str(exc), trace_id=trace_id)


async def run_periodic() -> None:
    """Chạy `run()` lặp lại mỗi `room_status_sync_interval_seconds` giây cho tới khi bị cancel."""
    while True:
        try:
            await asyncio.sleep(settings.room_status_sync_interval_seconds)
            await run()
        except asyncio.CancelledError:
            logger.info("room_status_sync_periodic_stopped")
            return
