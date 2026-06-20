"""initial schema: users, room_types, rooms, reservations, stays, room_service_logs

Revision ID: 001
Revises:
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ROOM_TYPES_SEED = [
    {"id": 1, "code": "PK", "name": "Premium King", "max_guests": 2, "description": None},
    {"id": 2, "code": "DT", "name": "Deluxe Twin", "max_guests": 2, "description": None},
    {"id": 3, "code": "JSK", "name": "Junior Suite King", "max_guests": 4, "description": None},
]

ROOMS_SEED = [
    {"room_number": "11", "room_type_id": 1, "floor": 1},
    {"room_number": "15", "room_type_id": 1, "floor": 1},
    {"room_number": "17", "room_type_id": 1, "floor": 1},
    {"room_number": "202", "room_type_id": 2, "floor": 2},
    {"room_number": "205", "room_type_id": 2, "floor": 2},
    {"room_number": "209", "room_type_id": 2, "floor": 2},
    {"room_number": "403", "room_type_id": 3, "floor": 4},
    {"room_number": "408", "room_type_id": 3, "floor": 4},
    {"room_number": "409", "room_type_id": 3, "floor": 4},
]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("avatar", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("phone_number", name="uq_users_phone_number"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "room_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("max_guests", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_room_types_code"),
    )

    op.create_table(
        "rooms",
        sa.Column("room_id", sa.Integer(), primary_key=True),
        sa.Column("room_number", sa.String(10), nullable=False),
        sa.Column("room_type_id", sa.Integer(), sa.ForeignKey("room_types.id"), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="Vacant"),
        sa.Column("do_not_disturb", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("make_up_room", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("room_number", name="uq_rooms_room_number"),
    )

    op.create_table(
        "reservations",
        sa.Column("reservation_id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("number_of_guests", sa.Integer(), nullable=False),
        sa.Column("expected_departure_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="BOOKED"),
    )

    op.create_table(
        "stays",
        sa.Column("stay_id", sa.Integer(), primary_key=True),
        sa.Column(
            "reservation_id",
            sa.Integer(),
            sa.ForeignKey("reservations.reservation_id"),
            nullable=False,
        ),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.room_id"), nullable=False),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("number_of_guests", sa.Integer(), nullable=False),
        sa.Column("expected_arrival_date", sa.Date(), nullable=False),
        sa.Column("expected_departure_date", sa.Date(), nullable=False),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="CHECKED_IN"),
    )

    op.create_table(
        "room_service_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stay_id", sa.Integer(), sa.ForeignKey("stays.stay_id"), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.room_id"), nullable=False),
        sa.Column("service", sa.String(32), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("requested_role", sa.String(20), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    room_types_table = sa.table(
        "room_types",
        sa.column("id", sa.Integer),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("max_guests", sa.Integer),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(room_types_table, ROOM_TYPES_SEED)

    rooms_table = sa.table(
        "rooms",
        sa.column("room_number", sa.String),
        sa.column("room_type_id", sa.Integer),
        sa.column("floor", sa.Integer),
    )
    op.bulk_insert(rooms_table, ROOMS_SEED)


def downgrade() -> None:
    op.drop_table("room_service_logs")
    op.drop_table("stays")
    op.drop_table("reservations")
    op.drop_table("rooms")
    op.drop_table("room_types")
    op.drop_table("users")
