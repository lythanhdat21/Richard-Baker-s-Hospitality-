import uuid
from fastapi import APIRouter, Depends
from src.app.core.security import require_internal_api_key
from src.app.services import room_service
from src.app.schemas.internal.room import RoomStatusUpdateRequest

router = APIRouter(prefix="/rooms", tags=["Rooms"])


def _trace() -> str:
    return str(uuid.uuid4())


@router.get("/{room_number}/status", dependencies=[Depends(require_internal_api_key)])
async def get_room_status(room_number: str):
    trace_id = _trace()
    data = await room_service.get_room_status(room_number, trace_id)
    return {"success": True, "data": data.model_dump()}


@router.patch("/{room_number}/status", dependencies=[Depends(require_internal_api_key)])
async def update_room_status(room_number: str, req: RoomStatusUpdateRequest):
    trace_id = _trace()
    data = await room_service.update_room_status(room_number, req, trace_id)
    return {"success": True, "data": data.model_dump()}
