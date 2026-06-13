from pydantic import BaseModel


class ErrorResponse(BaseModel):
    success: bool = False
    code: str
    message: str
    traceId: str = ""
