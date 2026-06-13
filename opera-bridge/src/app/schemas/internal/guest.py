from pydantic import BaseModel
from typing import Any


class GuestProfile(BaseModel):
    profile_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    nationality: str | None = None


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
