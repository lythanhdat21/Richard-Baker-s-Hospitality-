from pydantic import BaseModel


class OperaRoomStatusUpdateRequest(BaseModel):
    housekeeping_status: str

    def to_opera_payload(self) -> dict:
        return {
            "roomStatus": {
                "housekeeping": {"status": self.housekeeping_status}
            }
        }
