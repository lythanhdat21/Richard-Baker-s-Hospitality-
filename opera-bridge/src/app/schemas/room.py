from pydantic import BaseModel


class DndRequest(BaseModel):
    status: bool
