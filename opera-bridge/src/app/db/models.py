from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class RoomType(Base):
    __tablename__ = "room_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    rooms: Mapped[list["Room"]] = relationship(back_populates="room_type")


class Room(Base):
    __tablename__ = "rooms"

    room_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    room_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("room_types.id"), nullable=False)
    floor: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Vacant")
    do_not_disturb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    make_up_room: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    room_type: Mapped["RoomType"] = relationship(back_populates="rooms")
    stays: Mapped[list["Stay"]] = relationship(back_populates="room")


class Reservation(Base):
    __tablename__ = "reservations"

    reservation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="BOOKED")

    stays: Mapped[list["Stay"]] = relationship(back_populates="reservation")


class Stay(Base):
    __tablename__ = "stays"

    stay_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reservation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reservations.reservation_id"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    number_of_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CHECKED_IN")

    reservation: Mapped["Reservation"] = relationship(back_populates="stays")
    room: Mapped["Room"] = relationship(back_populates="stays")


class RoomServiceLog(Base):
    __tablename__ = "room_service_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stay_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("stays.stay_id"), nullable=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("rooms.room_id"), nullable=False)
    service: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    requested_role: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
