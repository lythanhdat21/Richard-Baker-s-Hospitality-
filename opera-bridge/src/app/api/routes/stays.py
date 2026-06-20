from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.core.timeutil import to_vn_str
from app.db.models import User
from app.db.session import get_db
from app.schemas.stay import CheckInRequest, CheckOutRequest
from app.services.stay_service import (
    NoActiveStayError,
    RoomNotFoundError,
    check_in,
    check_out,
)

router = APIRouter(prefix="/api/stays", tags=["stays"])


@router.post("/check-in")
def check_in_endpoint(
    payload: CheckInRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("RECEPTIONIST")),
):
    try:
        stay = check_in(db, payload, actor=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )

    return {
        "message": "Check-in thành công",
        "status": "success",
        "data": {
            "stay_id": stay.stay_id,
            "reservation_id": stay.reservation_id,
            "room_number": stay.room.room_number,
            "room_name": stay.room.room_type.name,
            "username": stay.username,
            "gender": stay.gender,
            "phone_number": stay.phone_number,
            "number_of_guests": stay.number_of_guests,
            "expected_arrival_date": stay.expected_arrival_date.isoformat(),
            "expected_departure_date": stay.expected_departure_date.isoformat(),
            "status": stay.status,
            "checked_in_at": to_vn_str(stay.checked_in_at),
            "checked_in_by": stay.checked_in_by,
        },
    }


@router.post("/check-out")
def check_out_endpoint(
    payload: CheckOutRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("RECEPTIONIST")),
):
    try:
        stay, room = check_out(db, payload, actor=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )
    except NoActiveStayError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )

    return {
        "message": "Check-out thành công",
        "status": "success",
        "data": {
            "stay_id": stay.stay_id,
            "reservation_id": stay.reservation_id,
            "room_number": room.room_number,
            "room_name": room.room_type.name,
            "username": stay.username,
            "gender": stay.gender,
            "phone_number": stay.phone_number,
            "number_of_guests": stay.number_of_guests,
            "expected_arrival_date": stay.expected_arrival_date.isoformat(),
            "expected_departure_date": stay.expected_departure_date.isoformat(),
            "status": stay.status,
            "checked_out_at": to_vn_str(stay.checked_out_at),
            "checked_out_by": stay.checked_out_by,
        },
    }
