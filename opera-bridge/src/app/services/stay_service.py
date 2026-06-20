from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timeutil import now_vn
from app.db.models import Reservation, Room, Stay, User
from app.schemas.stay import CheckInRequest, CheckOutRequest


class RoomNotFoundError(Exception):
    pass


class NoActiveStayError(Exception):
    pass


def _get_room_by_number(db: Session, room_number: str) -> Room:
    room = db.scalar(select(Room).where(Room.room_number == room_number))
    if room is None:
        raise RoomNotFoundError(f"Không tìm thấy phòng room_number={room_number}")
    return room


def check_in(db: Session, data: CheckInRequest, *, actor: User) -> Stay:
    room = _get_room_by_number(db, data.room_number)

    reservation = Reservation(
        username=data.username,
        gender=data.gender,
        phone_number=data.phone_number,
        number_of_guests=data.number_of_guests,
        expected_departure_date=data.expected_departure_date,
        status="BOOKED",
    )
    db.add(reservation)
    db.flush()

    stay = Stay(
        reservation_id=reservation.reservation_id,
        room_id=room.room_id,
        username=data.username,
        gender=data.gender,
        phone_number=data.phone_number,
        number_of_guests=data.number_of_guests,
        expected_arrival_date=data.expected_arrival_date,
        expected_departure_date=data.expected_departure_date,
        checked_in_at=now_vn(),
        checked_in_by=actor.id,
        status="CHECKED_IN",
    )
    db.add(stay)

    room.status = "Occupied"
    room.updated_at = now_vn()
    db.add(room)

    db.commit()
    db.refresh(stay)
    return stay


def check_out(db: Session, data: CheckOutRequest, *, actor: User) -> tuple[Stay, Room]:
    room = _get_room_by_number(db, data.room_number)

    stay = db.scalar(
        select(Stay)
        .where(Stay.room_id == room.room_id, Stay.status == "CHECKED_IN")
        .order_by(Stay.stay_id.desc())
    )
    if stay is None:
        raise NoActiveStayError(f"Phòng room_number={data.room_number} chưa có khách check-in")

    stay.checked_out_at = now_vn()
    stay.checked_out_by = actor.id
    stay.status = "CHECKED_OUT"
    db.add(stay)

    room.status = "Cleaning"
    room.updated_at = now_vn()
    db.add(room)

    db.commit()
    db.refresh(stay)
    db.refresh(room)
    return stay, room
