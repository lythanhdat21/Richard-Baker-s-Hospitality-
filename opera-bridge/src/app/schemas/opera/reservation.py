from pydantic import BaseModel
from typing import Any


class OperaReservationSearchParams(BaseModel):
    confirmation_number: str | None = None
    given_name: str | None = None
    surname: str | None = None
    arrival_date_start: str | None = None
    arrival_date_end: str | None = None

    def to_query_params(self) -> dict:
        params = {}
        if self.confirmation_number:
            params["confirmationNumber"] = self.confirmation_number
        if self.given_name:
            params["givenName"] = self.given_name
        if self.surname:
            params["surname"] = self.surname
        if self.arrival_date_start:
            params["arrivalStartDate"] = self.arrival_date_start
        if self.arrival_date_end:
            params["arrivalEndDate"] = self.arrival_date_end
        return params


class OperaCheckInRequest(BaseModel):
    room_number: str | None = None
    extra: dict[str, Any] | None = None
