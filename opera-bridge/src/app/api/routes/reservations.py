import uuid

from fastapi import APIRouter, Depends, Query

from src.app.core.security import require_cashiering_access, require_internal_api_key
from src.app.schemas.internal.reservation import ReservationSearchRequest
from src.app.services import folio_service, reservation_service

router = APIRouter(prefix="/reservations", tags=["Reservations"])


def _trace() -> str:
    return str(uuid.uuid4())


@router.get("/search", dependencies=[Depends(require_internal_api_key)])
async def search_reservations(
    confirmation_number: str | None = Query(None),
    guest_name: str | None = Query(None),
    arrival_date: str | None = Query(None),
    departure_date: str | None = Query(None),
):
    trace_id = _trace()
    req = ReservationSearchRequest(
        confirmation_number=confirmation_number,
        guest_name=guest_name,
        arrival_date=arrival_date,
        departure_date=departure_date,
    )
    data = await reservation_service.search_reservations(req, trace_id)
    return {"success": True, "data": [r.model_dump() for r in data]}


@router.get("/{reservation_id}", dependencies=[Depends(require_internal_api_key)])
async def get_reservation(reservation_id: str):
    trace_id = _trace()
    data = await reservation_service.get_reservation(reservation_id, trace_id)
    return {"success": True, "data": data.model_dump()}


@router.post("/{reservation_id}/check-in", dependencies=[Depends(require_internal_api_key)])
async def check_in(reservation_id: str):
    trace_id = _trace()
    data = await reservation_service.check_in(reservation_id, trace_id)
    return {"success": True, "data": data.model_dump()}


@router.post("/{reservation_id}/check-out", dependencies=[Depends(require_internal_api_key)])
async def check_out(reservation_id: str):
    trace_id = _trace()
    data = await reservation_service.check_out(reservation_id, trace_id)
    return {"success": True, "data": data.model_dump()}


@router.get("/{reservation_id}/folio")
async def get_folio_summary(
    reservation_id: str,
    actor_role: str = Depends(require_cashiering_access),
):
    trace_id = _trace()
    data = await folio_service.get_folio_summary(reservation_id, trace_id, actor_role)
    return {"success": True, "data": data.model_dump()}


@router.get("/{reservation_id}/payment-status")
async def get_payment_status(
    reservation_id: str,
    actor_role: str = Depends(require_cashiering_access),
):
    trace_id = _trace()
    data = await folio_service.get_payment_status(reservation_id, trace_id, actor_role)
    return {"success": True, "data": data.model_dump()}
