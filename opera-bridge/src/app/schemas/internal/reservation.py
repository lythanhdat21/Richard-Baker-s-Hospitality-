from pydantic import BaseModel
from typing import Any


class ReservationSearchRequest(BaseModel):
    confirmation_number: str | None = None
    guest_name: str | None = None
    arrival_date: str | None = None
    departure_date: str | None = None


class ReservationSummary(BaseModel):
    reservation_id: str
    confirmation_number: str | None = None
    guest_name: str | None = None
    arrival_date: str | None = None
    departure_date: str | None = None
    status: str | None = None
    room_number: str | None = None


class ReservationDetail(ReservationSummary):
    hotel_id: str | None = None
    adults: int | None = None
    children: int | None = None
    room_type: str | None = None
    rate_plan: str | None = None
    extra: dict[str, Any] | None = None


class CheckInResponse(BaseModel):
    reservation_id: str
    status: str
    room_number: str | None = None


class CheckOutResponse(BaseModel):
    reservation_id: str
    status: str


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
