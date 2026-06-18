from src.app.clients import opera_cloud_client as opera
from src.app.mappers import reservation_mapper
from src.app.schemas.internal.reservation import (
    ReservationSearchRequest, ReservationSummary, ReservationDetail,
    CheckInResponse, CheckOutResponse,
)
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.db.session import record_audit_event
from src.app.utils.error_normalizer import normalize_opera_error

logger = get_logger(__name__)
HOTEL = settings.opera_hotel_id


async def search_reservations(req: ReservationSearchRequest, trace_id: str) -> list[ReservationSummary]:
    params = reservation_mapper.to_opera_search_params(req)
    query = params.to_query_params()
    if not query:
        raise normalize_opera_error("VALIDATION_ERROR", "Cần ít nhất một tiêu chí tìm kiếm.", trace_id)

    data = await opera.get(f"/rsv/v1/hotels/{HOTEL}/reservations", trace_id, params=query)
    reservations = data.get("reservations", {}).get("reservation", [])
    return [reservation_mapper.to_internal_summary(r) for r in reservations]


async def get_reservation(reservation_id: str, trace_id: str) -> ReservationDetail:
    data = await opera.get(f"/rsv/v1/hotels/{HOTEL}/reservations/{reservation_id}", trace_id)
    reservation = data.get("reservation")
    if not reservation:
        raise normalize_opera_error("RESERVATION_NOT_FOUND", f"Không tìm thấy đặt phòng {reservation_id}.", trace_id)
    return reservation_mapper.to_internal_detail(reservation)


async def check_in(reservation_id: str, trace_id: str) -> CheckInResponse:
    logger.info("check_in_start", reservation_id=reservation_id, trace_id=trace_id)
    try:
        data = await opera.post(
            f"/fof/v1/hotels/{HOTEL}/reservations/{reservation_id}/checkIns",
            trace_id,
            json={"reservation": {"ignoreWarnings": True}},
        )
    except Exception:
        record_audit_event(trace_id, "internal_api", "check_in", "reservation", reservation_id, "failed")
        raise
    room_number = (
        data.get("reservation", {})
        .get("roomStay", {})
        .get("currentRoomInfo", {})
        .get("roomId")
    )
    logger.info("check_in_done", reservation_id=reservation_id, trace_id=trace_id)
    record_audit_event(trace_id, "internal_api", "check_in", "reservation", reservation_id, "success")
    return CheckInResponse(reservation_id=reservation_id, status="CHECKED_IN", room_number=room_number)


async def check_out(reservation_id: str, trace_id: str) -> CheckOutResponse:
    logger.info("check_out_start", reservation_id=reservation_id, trace_id=trace_id)
    try:
        await opera.post(
            f"/csh/v1/hotels/{HOTEL}/reservations/{reservation_id}/checkOuts",
            trace_id,
            json={"reservation": {}},
        )
    except Exception:
        record_audit_event(trace_id, "internal_api", "check_out", "reservation", reservation_id, "failed")
        raise
    logger.info("check_out_done", reservation_id=reservation_id, trace_id=trace_id)
    record_audit_event(trace_id, "internal_api", "check_out", "reservation", reservation_id, "success")
    return CheckOutResponse(reservation_id=reservation_id, status="CHECKED_OUT")
