from src.app.schemas.internal.room import RoomStatus


def to_internal_room_status(opera_room: dict) -> RoomStatus:
    """Map 1 room item từ OPERA Cloud `housekeepingOverview` (housekeepingRoomInfo.housekeepingRooms.room[])
    sang RoomStatus nội bộ.
    """
    room_info = opera_room.get("room", opera_room)
    housekeeping_status_block = room_info.get("housekeeping", {}).get("housekeepingRoomStatus", {})
    occupancy = housekeeping_status_block.get("frontOfficeStatus")
    housekeeping = housekeeping_status_block.get("housekeepingRoomStatus")
    room_number = room_info.get("roomId") or room_info.get("roomNumber") or ""
    room_type_raw = room_info.get("roomType")
    room_type = room_type_raw.get("roomType") if isinstance(room_type_raw, dict) else room_type_raw
    floor = room_info.get("floor")

    return RoomStatus(
        room_number=room_number,
        occupancy_status=occupancy,
        housekeeping_status=housekeeping,
        room_type=room_type,
        floor=floor,
    )
