from src.app.clients import opera_cloud_client as opera
from src.app.mappers import room_mapper
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.db.session import SessionLocal, get_or_create_default_property
from src.app.db.repositories.sync_state_repository import SyncStateRepository

logger = get_logger(__name__)
HOTEL = settings.opera_hotel_id


def record_sync_result(sync_type: str, error_code: str | None = None, error_message: str | None = None) -> None:
    """Ghi nhận kết quả đồng bộ vào bảng sync_states. Lỗi ở đây chỉ log, không raise,
    để không làm hỏng luồng nghiệp vụ chính vì lý do phụ trợ (ghi log)."""
    try:
        with SessionLocal() as db:
            prop = get_or_create_default_property(db)
            repo = SyncStateRepository(db)
            if error_code:
                repo.mark_error(prop.id, sync_type, error_code, error_message or "")
            else:
                repo.mark_success(prop.id, sync_type)
    except Exception:
        logger.exception("record_sync_result_failed", sync_type=sync_type)


async def sync_room_statuses(trace_id: str) -> dict:
    logger.info("sync_room_statuses_start", trace_id=trace_id)
    try:
        data = await opera.get(f"/hsk/v1/hotels/{HOTEL}/housekeepingOverview", trace_id, params={"limit": 500})
    except Exception as exc:
        record_sync_result("room_status", error_code="OPERA_ERROR", error_message=str(exc))
        raise
    rooms_raw = data.get("housekeepingRoomInfo", {}).get("housekeepingRooms", {}).get("room", [])
    rooms = [room_mapper.to_internal_room_status(r) for r in rooms_raw]
    logger.info("sync_room_statuses_done", count=len(rooms), trace_id=trace_id)
    record_sync_result("room_status")
    return {"synced_count": len(rooms), "rooms": [r.model_dump() for r in rooms]}
