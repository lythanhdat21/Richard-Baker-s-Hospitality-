from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.app.core.config import settings
from src.app.core.logging import get_logger
from src.app.db.models import AuditEvent, Property

logger = get_logger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_default_property(db: Session) -> Property:
    """Trả về (hoặc tạo) Property duy nhất khớp settings.opera_hotel_id.

    Vận hành single-tenant ở MVP hiện tại, nhưng vẫn dùng đúng schema multi-tenant
    (properties/sync_states/audit_events đều có property_id) để không phải migrate lại
    khi mở rộng nhiều khách sạn.
    """
    prop = db.query(Property).filter(Property.hotel_id == settings.opera_hotel_id).first()
    if prop:
        return prop
    prop = Property(
        property_code=settings.opera_hotel_id,
        hotel_id=settings.opera_hotel_id,
        name=settings.opera_hotel_id,
        opera_base_url=settings.opera_base_url,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def record_audit_event(
    trace_id: str,
    actor_type: str,
    action: str,
    entity_type: str,
    entity_id: str,
    result: str,
    actor_id: str | None = None,
) -> None:
    """Ghi 1 dòng audit_events. Lỗi ở đây chỉ log, không raise — audit log là phụ trợ,
    không được làm hỏng luồng nghiệp vụ chính (check-in/check-out/cập nhật phòng)."""
    try:
        with SessionLocal() as db:
            prop = get_or_create_default_property(db)
            db.add(AuditEvent(
                trace_id=trace_id,
                property_id=prop.id,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                result=result,
            ))
            db.commit()
    except Exception:
        logger.exception("record_audit_event_failed", action=action, entity_id=entity_id)
