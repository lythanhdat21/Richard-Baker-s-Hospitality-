from datetime import date

from pydantic import BaseModel


class CheckInRequest(BaseModel):
    room_number: str
    room_name: str | None = None
    username: str
    gender: str
    phone_number: str
    number_of_guests: int
    expected_arrival_date: date
    expected_departure_date: date


class CheckOutRequest(BaseModel):
    room_number: str
