from src.app.clients import opera_cloud_client as opera
from src.app.mappers import room_mapper
from src.app.schemas.internal.room import RoomStatus, RoomStatusUpdateRequest
from src.app.core.config import settings
from src.app.db.session import record_audit_event
from src.app.utils.error_normalizer import normalize_opera_error

HOTEL = settings.opera_hotel_id


async def get_room_status(room_number: str, trace_id: str) -> RoomStatus:
    data = await opera.get(
        f"/hsk/v1/hotels/{HOTEL}/housekeepingOverview",
        trace_id,
        params={"roomIdText": room_number, "limit": 1},
    )
    rooms = data.get("housekeepingRoomInfo", {}).get("housekeepingRooms", {}).get("room", [])
    if not rooms:
        raise normalize_opera_error("ROOM_NOT_FOUND", f"Không tìm thấy phòng {room_number}.", trace_id)
    return room_mapper.to_internal_room_status(rooms[0])


async def update_room_status(
    room_number: str, req: RoomStatusUpdateRequest, trace_id: str, record_audit: bool = True
) -> RoomStatus:
    """`record_audit=False` dùng cho luồng RCU đồng bộ hàng loạt (mqtt/handlers/room_handler.py) —
    luồng đó đã có sync_state riêng (sync_type=rcu_room_status), ghi audit_event cho từng phòng
    mỗi lần publish sẽ làm phình bảng audit_events vô nghĩa."""
    payload = {"roomList": [{"roomId": room_number}], "housekeepingRoomStatus": req.housekeeping_status}
    try:
        await opera.put(f"/hsk/v1/hotels/{HOTEL}/rooms/status", trace_id, json=payload)
    except Exception:
        if record_audit:
            record_audit_event(trace_id, "internal_api", "update_room_status", "room", room_number, "failed")
        raise
    result = await get_room_status(room_number, trace_id)
    if record_audit:
        record_audit_event(trace_id, "internal_api", "update_room_status", "room", room_number, "success")
    return result
