from src.app.clients import opera_cloud_client as opera
from src.app.mappers import guest_mapper
from src.app.schemas.internal.guest import GuestProfile
from src.app.core.config import settings
from src.app.utils.error_normalizer import normalize_opera_error

HOTEL = settings.opera_hotel_id


async def get_guest_profile(profile_id: str, trace_id: str) -> GuestProfile:
    data = await opera.get(f"/crm/v1/profiles/{profile_id}", trace_id)
    profile = data.get("profile") or data
    if not profile:
        raise normalize_opera_error("GUEST_NOT_FOUND", f"Không tìm thấy profile khách {profile_id}.", trace_id)
    return guest_mapper.to_internal_guest(profile)
