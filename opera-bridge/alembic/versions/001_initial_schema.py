"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-11

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import TIMESTAMP
TIMESTAMPTZ = TIMESTAMP(timezone=True)

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "properties",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_code", sa.String(64), nullable=False),
        sa.Column("hotel_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("opera_base_url", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("property_code", name="uq_properties_property_code"),
    )
    op.create_index("idx_properties_hotel_id", "properties", ["hotel_id"])
    op.create_index("idx_properties_is_active", "properties", ["is_active"])

    op.create_table(
        "integration_mappings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("internal_id", sa.String(128), nullable=False),
        sa.Column("opera_id", sa.String(128), nullable=True),
        sa.Column("opera_confirmation_number", sa.String(128), nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("property_id", "entity_type", "internal_id", name="uq_integration_mappings_internal"),
    )
    op.create_index("idx_integration_mappings_opera_id", "integration_mappings", ["property_id", "entity_type", "opera_id"])
    op.create_index("idx_integration_mappings_confirmation", "integration_mappings", ["opera_confirmation_number"])

    op.create_table(
        "sync_states",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("sync_type", sa.String(64), nullable=False),
        sa.Column("last_synced_at", TIMESTAMPTZ, nullable=True),
        sa.Column("last_success_at", TIMESTAMPTZ, nullable=True),
        sa.Column("last_error_at", TIMESTAMPTZ, nullable=True),
        sa.Column("last_error_code", sa.String(128), nullable=True),
        sa.Column("last_error_message", sa.Text, nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("property_id", "sync_type", name="uq_sync_states_property_sync"),
    )
    op.create_index("idx_sync_states_last_success_at", "sync_states", ["last_success_at"])
    op.create_index("idx_sync_states_last_error_at", "sync_states", ["last_error_at"])

    op.create_table(
        "api_request_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trace_id", sa.String(128), nullable=False),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=True),
        sa.Column("internal_endpoint", sa.Text, nullable=False),
        sa.Column("opera_endpoint", sa.Text, nullable=True),
        sa.Column("http_method", sa.String(16), nullable=False),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error_code", sa.String(128), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_api_request_logs_trace_id", "api_request_logs", ["trace_id"])
    op.create_index("idx_api_request_logs_property_created", "api_request_logs", ["property_id", "created_at"])
    op.create_index("idx_api_request_logs_success_created", "api_request_logs", ["success", "created_at"])
    op.create_index("idx_api_request_logs_error_code", "api_request_logs", ["error_code"])

    op.create_table(
        "retry_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("operation_type", sa.String(64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("next_retry_at", TIMESTAMPTZ, nullable=True),
        sa.Column("last_error_code", sa.String(128), nullable=True),
        sa.Column("last_error_message", sa.Text, nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_retry_queue_status_next_retry", "retry_queue", ["status", "next_retry_at"])
    op.create_index("idx_retry_queue_property_operation", "retry_queue", ["property_id", "operation_type"])
    op.create_index("idx_retry_queue_created_at", "retry_queue", ["created_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("trace_id", sa.String(128), nullable=False),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", TIMESTAMPTZ, nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_events_trace_id", "audit_events", ["trace_id"])
    op.create_index("idx_audit_events_property_created", "audit_events", ["property_id", "created_at"])
    op.create_index("idx_audit_events_entity", "audit_events", ["entity_type", "entity_id"])
    op.create_index("idx_audit_events_action_created", "audit_events", ["action", "created_at"])

    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_properties_updated_at
        BEFORE UPDATE ON properties FOR EACH ROW EXECUTE FUNCTION set_updated_at();

        CREATE TRIGGER trg_integration_mappings_updated_at
        BEFORE UPDATE ON integration_mappings FOR EACH ROW EXECUTE FUNCTION set_updated_at();

        CREATE TRIGGER trg_sync_states_updated_at
        BEFORE UPDATE ON sync_states FOR EACH ROW EXECUTE FUNCTION set_updated_at();

        CREATE TRIGGER trg_retry_queue_updated_at
        BEFORE UPDATE ON retry_queue FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("retry_queue")
    op.drop_table("api_request_logs")
    op.drop_table("sync_states")
    op.drop_table("integration_mappings")
    op.drop_table("properties")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at CASCADE")
