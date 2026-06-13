from src.app.clients import opera_cloud_client as opera
from src.app.mappers import room_mapper
from src.app.core.config import settings
from src.app.core.logging import get_logger

logger = get_logger(__name__)
HOTEL = settings.opera_hotel_id


async def sync_room_statuses(trace_id: str) -> dict:
    logger.info("sync_room_statuses_start", trace_id=trace_id)
    data = await opera.get(f"/hsk/v1/hotels/{HOTEL}/rooms", trace_id)
    rooms_raw = data.get("rooms", {}).get("room", [])
    rooms = [room_mapper.to_internal_room_status(r) for r in rooms_raw]
    logger.info("sync_room_statuses_done", count=len(rooms), trace_id=trace_id)
    return {"synced_count": len(rooms), "rooms": [r.model_dump() for r in rooms]}
