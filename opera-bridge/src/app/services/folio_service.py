from src.app.clients import opera_cloud_client as opera
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.mappers import folio_mapper
from src.app.schemas.internal.folio import FolioSummary, PaymentStatus
from src.app.utils.error_normalizer import normalize_opera_error

logger = get_logger(__name__)
HOTEL = settings.opera_hotel_id


async def get_folio_summary(reservation_id: str, trace_id: str, actor_role: str) -> FolioSummary:
    logger.info(
        "cashiering_folio_access",
        reservation_id=reservation_id,
        trace_id=trace_id,
        actor_role=actor_role,
        action="get_folio_summary",
    )
    data = await opera.get(
        f"/csh/v1/hotels/{HOTEL}/reservations/{reservation_id}/folios",
        trace_id,
        params={"summaryOnly": "true", "limit": 20},
    )
    folio_info = data.get("reservationFolioInformation")
    if not folio_info:
        raise normalize_opera_error("FOLIO_NOT_FOUND", f"Không tìm thấy folio cho reservation {reservation_id}.", trace_id)
    return folio_mapper.to_internal_folio_summary(data, reservation_id)


async def get_payment_status(reservation_id: str, trace_id: str, actor_role: str) -> PaymentStatus:
    logger.info(
        "cashiering_folio_access",
        reservation_id=reservation_id,
        trace_id=trace_id,
        actor_role=actor_role,
        action="get_payment_status",
    )
    data = await opera.get(
        f"/csh/v1/hotels/{HOTEL}/reservations/{reservation_id}/advancePaymentBalance",
        trace_id,
    )
    return folio_mapper.to_internal_payment_status(data, reservation_id)
