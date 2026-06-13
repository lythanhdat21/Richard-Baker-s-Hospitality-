from src.app.schemas.internal.room import RoomStatus


def to_internal_room_status(opera_room: dict) -> RoomStatus:
    room_info = opera_room.get("room", opera_room)
    occupancy = room_info.get("roomAssignments", {}).get("roomStatus") or room_info.get("occupancyStatus")
    housekeeping = room_info.get("housekeeping", {}).get("status") or room_info.get("housekeepingStatus")
    room_number = room_info.get("roomId") or room_info.get("roomNumber") or ""
    room_type = room_info.get("roomType") or room_info.get("roomTypeCode")
    floor = room_info.get("floor")

    return RoomStatus(
        room_number=room_number,
        occupancy_status=occupancy,
        housekeeping_status=housekeeping,
        room_type=room_type,
        floor=floor,
    )
