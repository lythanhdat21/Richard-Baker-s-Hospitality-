import uuid
from sqlalchemy import (
    Boolean, Column, Integer, Text, ForeignKey,
    UniqueConstraint, Index, func, TIMESTAMP, String,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

TIMESTAMPTZ = TIMESTAMP(timezone=True)


class Base(DeclarativeBase):
    pass


class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_code = Column(String(64), nullable=False)
    hotel_id = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    opera_base_url = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("property_code", name="uq_properties_property_code"),
        Index("idx_properties_hotel_id", "hotel_id"),
        Index("idx_properties_is_active", "is_active"),
    )

    integration_mappings = relationship("IntegrationMapping", back_populates="property")
    sync_states = relationship("SyncState", back_populates="property")
    retry_queue = relationship("RetryQueue", back_populates="property")
    audit_events = relationship("AuditEvent", back_populates="property")


class IntegrationMapping(Base):
    __tablename__ = "integration_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    entity_type = Column(String(64), nullable=False)
    internal_id = Column(String(128), nullable=False)
    opera_id = Column(String(128), nullable=True)
    opera_confirmation_number = Column(String(128), nullable=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("property_id", "entity_type", "internal_id", name="uq_integration_mappings_internal"),
        Index("idx_integration_mappings_opera_id", "property_id", "entity_type", "opera_id"),
        Index("idx_integration_mappings_confirmation", "opera_confirmation_number"),
    )

    property = relationship("Property", back_populates="integration_mappings")


class SyncState(Base):
    __tablename__ = "sync_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    sync_type = Column(String(64), nullable=False)
    last_synced_at = Column(TIMESTAMPTZ, nullable=True)
    last_success_at = Column(TIMESTAMPTZ, nullable=True)
    last_error_at = Column(TIMESTAMPTZ, nullable=True)
    last_error_code = Column(String(128), nullable=True)
    last_error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("property_id", "sync_type", name="uq_sync_states_property_sync"),
        Index("idx_sync_states_last_success_at", "last_success_at"),
        Index("idx_sync_states_last_error_at", "last_error_at"),
    )

    property = relationship("Property", back_populates="sync_states")


class ApiRequestLog(Base):
    __tablename__ = "api_request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(128), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=True)
    internal_endpoint = Column(Text, nullable=False)
    opera_endpoint = Column(Text, nullable=True)
    http_method = Column(String(16), nullable=False)
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False)
    error_code = Column(String(128), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_api_request_logs_trace_id", "trace_id"),
        Index("idx_api_request_logs_property_created", "property_id", "created_at"),
        Index("idx_api_request_logs_success_created", "success", "created_at"),
        Index("idx_api_request_logs_error_code", "error_code"),
    )


class RetryQueue(Base):
    __tablename__ = "retry_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    operation_type = Column(String(64), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(TIMESTAMPTZ, nullable=True)
    last_error_code = Column(String(128), nullable=True)
    last_error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_retry_queue_status_next_retry", "status", "next_retry_at"),
        Index("idx_retry_queue_property_operation", "property_id", "operation_type"),
        Index("idx_retry_queue_created_at", "created_at"),
    )

    property = relationship("Property", back_populates="retry_queue")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String(128), nullable=False)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    actor_type = Column(String(32), nullable=False)
    actor_id = Column(String(128), nullable=True)
    action = Column(String(128), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(128), nullable=False)
    result = Column(String(32), nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(TIMESTAMPTZ, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("idx_audit_events_trace_id", "trace_id"),
        Index("idx_audit_events_property_created", "property_id", "created_at"),
        Index("idx_audit_events_entity", "entity_type", "entity_id"),
        Index("idx_audit_events_action_created", "action", "created_at"),
    )

    property = relationship("Property", back_populates="audit_events")
