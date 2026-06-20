from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.core.timeutil import to_vn_str
from app.db.models import User
from app.db.session import get_db
from app.schemas.room import DndRequest
from app.services.room_service import (
    RoomNotFoundError,
    complete_make_up_room,
    request_make_up_room,
    set_dnd,
)

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


@router.patch("/{room_number}/do-not-disturb")
def do_not_disturb_endpoint(
    room_number: str,
    payload: DndRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("RECEPTIONIST", "CUSTOMER")),
):
    try:
        room = set_dnd(db, room_number, turn_on=payload.status, actor=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )

    message = (
        "Cập nhật trạng thái DND thành công. Không nên làm phiền khách."
        if payload.status
        else "Đã tắt trạng thái Do Not Disturb."
    )

    return {
        "message": message,
        "status": "success",
        "data": {
            "room_number": room.room_number,
            "room_name": room.room_type.name,
            "do_not_disturb": room.do_not_disturb,
            "updated_at": to_vn_str(room.updated_at),
        },
    }


@router.post("/{room_number}/make-up-room")
def make_up_room_endpoint(
    room_number: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("CUSTOMER")),
):
    try:
        room = request_make_up_room(db, room_number, actor=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )

    return {
        "message": "Đã gửi yêu cầu dọn phòng",
        "status": "success",
        "data": {
            "room_number": room.room_number,
            "room_name": room.room_type.name,
            "make_up_room": room.make_up_room,
            "updated_at": to_vn_str(room.updated_at),
        },
    }


@router.patch("/{room_number}/service")
def complete_make_up_room_endpoint(
    room_number: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles("RECEPTIONIST")),
):
    try:
        room = complete_make_up_room(db, room_number, actor=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(exc), "status": "error"},
        )

    return {
        "message": "Đã hoàn thành yêu cầu dọn phòng",
        "status": "success",
        "data": {
            "room_number": room.room_number,
            "room_name": room.room_type.name,
            "make_up_room": room.make_up_room,
            "updated_at": to_vn_str(room.updated_at),
        },
    }
