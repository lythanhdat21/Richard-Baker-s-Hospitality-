from src.app.clients import opera_cloud_client as opera
from src.app.mappers import room_mapper
from src.app.schemas.internal.room import RoomStatus, RoomStatusUpdateRequest
from src.app.core.config import settings
from src.app.utils.error_normalizer import normalize_opera_error

HOTEL = settings.opera_hotel_id


async def get_room_status(room_number: str, trace_id: str) -> RoomStatus:
    data = await opera.get(f"/hsk/v1/hotels/{HOTEL}/rooms/{room_number}", trace_id)
    room = data.get("room") or data
    if not room:
        raise normalize_opera_error("ROOM_NOT_FOUND", f"Không tìm thấy phòng {room_number}.", trace_id)
    return room_mapper.to_internal_room_status(data)


async def update_room_status(room_number: str, req: RoomStatusUpdateRequest, trace_id: str) -> RoomStatus:
    payload = {"room": {"housekeeping": {"status": req.housekeeping_status}}}
    data = await opera.patch(f"/hsk/v1/hotels/{HOTEL}/rooms/{room_number}", trace_id, json=payload)
    return await get_room_status(room_number, trace_id)
