import uuid
from fastapi import APIRouter, Depends
from src.app.core.security import require_internal_api_key
from src.app.services import guest_service

router = APIRouter(prefix="/guests", tags=["Guests"])


def _trace() -> str:
    return str(uuid.uuid4())


@router.get("/{profile_id}", dependencies=[Depends(require_internal_api_key)])
async def get_guest_profile(profile_id: str):
    trace_id = _trace()
    data = await guest_service.get_guest_profile(profile_id, trace_id)
    return {"success": True, "data": data.model_dump()}
