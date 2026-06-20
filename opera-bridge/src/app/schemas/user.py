from enum import Enum

from pydantic import BaseModel


class Gender(str, Enum):
    male = "Male"
    female = "Female"


class Role(str, Enum):
    customer = "CUSTOMER"
    receptionist = "RECEPTIONIST"


class LoginRequest(BaseModel):
    phone_number: str
    password: str
