from pydantic import BaseModel
from typing import Any


class RoomStatus(BaseModel):
    room_number: str
    occupancy_status: str | None = None
    housekeeping_status: str | None = None
    room_type: str | None = None
    floor: str | None = None


class RoomStatusUpdateRequest(BaseModel):
    housekeeping_status: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
