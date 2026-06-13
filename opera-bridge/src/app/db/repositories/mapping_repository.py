from uuid import UUID
from sqlalchemy.orm import Session
from src.app.db.models import IntegrationMapping


class MappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, property_id: UUID, entity_type: str, internal_id: str) -> IntegrationMapping | None:
        return (
            self.db.query(IntegrationMapping)
            .filter(
                IntegrationMapping.property_id == property_id,
                IntegrationMapping.entity_type == entity_type,
                IntegrationMapping.internal_id == internal_id,
            )
            .first()
        )

    def get_by_opera_id(self, property_id: UUID, entity_type: str, opera_id: str) -> IntegrationMapping | None:
        return (
            self.db.query(IntegrationMapping)
            .filter(
                IntegrationMapping.property_id == property_id,
                IntegrationMapping.entity_type == entity_type,
                IntegrationMapping.opera_id == opera_id,
            )
            .first()
        )

    def upsert(self, property_id: UUID, entity_type: str, internal_id: str, opera_id: str | None = None, opera_confirmation_number: str | None = None) -> IntegrationMapping:
        mapping = self.get(property_id, entity_type, internal_id)
        if mapping:
            if opera_id is not None:
                mapping.opera_id = opera_id
            if opera_confirmation_number is not None:
                mapping.opera_confirmation_number = opera_confirmation_number
        else:
            mapping = IntegrationMapping(
                property_id=property_id,
                entity_type=entity_type,
                internal_id=internal_id,
                opera_id=opera_id,
                opera_confirmation_number=opera_confirmation_number,
            )
            self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping
